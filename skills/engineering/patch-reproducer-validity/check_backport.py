"""Original in-memory backport model: no real kernel, parser or resource handles.

Contract: inputs longer than eight bytes are rejected without effects or retained
leases through every supported entrypoint. Accepted inputs retain their bytes.
"""
from dataclasses import dataclass
import unittest


@dataclass(frozen=True)
class Outcome:
    accepted: bool
    retained: bool
    effects: tuple
    trace: tuple


class Lease:
    def __init__(self):
        self.held = False
        self.trace = []
        self.effects = []

    def acquire(self):
        self.held = True
        self.trace.append('acquire')

    def release(self):
        if not self.held:
            raise RuntimeError('double release')
        self.held = False
        self.trace.append('release')

    def finish(self, accepted):
        return Outcome(accepted, self.held, tuple(self.effects), tuple(self.trace))


def legacy_upload(data, checked=False, release_on_reject=True):
    lease = Lease()
    lease.acquire()
    if checked and len(data) > 8:
        if release_on_reject:
            lease.release()
        return lease.finish(False)
    lease.effects.append(data)
    lease.release()
    return lease.finish(True)


def legacy_restore(data, checked=False, release_on_reject=True):
    # Deliberately duplicated old-branch site, not a shared validator.
    lease = Lease()
    lease.acquire()
    if checked and len(data) > 8:
        if release_on_reject:
            lease.release()
        return lease.finish(False)
    lease.effects.append(data)
    lease.release()
    return lease.finish(True)


def upstream_shared(data, checked):
    lease = Lease()
    # Upstream refactoring moved validation ahead of resource acquisition.
    if checked and len(data) > 8:
        return lease.finish(False)
    lease.acquire()
    lease.effects.append(data)
    lease.release()
    return lease.finish(True)


def target(entry, data, variant):
    if variant not in {'baseline', 'one-site', 'wrong-cleanup', 'complete'}:
        raise ValueError('unknown target variant')
    handler = {'upload': legacy_upload, 'restore': legacy_restore}[entry]
    checked = variant in {'wrong-cleanup', 'complete'} or (
        variant == 'one-site' and entry == 'upload')
    return handler(data, checked, variant != 'wrong-cleanup')


def upstream(entry, data, fixed):
    if entry not in {'upload', 'restore'}:
        raise ValueError('unknown upstream entrypoint')
    return upstream_shared(data, fixed)


class BackportCases(unittest.TestCase):
    def assert_rejected_safely(self, result):
        self.assertFalse(result.accepted)
        self.assertFalse(result.retained)
        self.assertEqual(result.effects, ())

    def test_upstream_one_helper_fixes_both_entrypoints(self):
        for entry in ('upload', 'restore'):
            self.assertTrue(upstream(entry, b'x' * 9, False).accepted)
            self.assert_rejected_safely(upstream(entry, b'x' * 9, True))

    def test_target_baseline_reproduces_each_site(self):
        for entry in ('upload', 'restore'):
            self.assertTrue(target(entry, b'x' * 9, 'baseline').accepted)

    def test_one_site_backport_repairs_upload(self):
        self.assert_rejected_safely(target('upload', b'x' * 9, 'one-site'))

    def test_one_site_backport_leaves_restore_unrepaired(self):
        result = target('restore', b'x' * 9, 'one-site')
        self.assertTrue(result.accepted)
        self.assertEqual(result.effects, (b'x' * 9,))

    def test_complete_backport_repairs_both(self):
        for entry in ('upload', 'restore'):
            self.assert_rejected_safely(target(entry, b'x' * 9, 'complete'))

    def test_reject_only_oracle_misses_cleanup_defect(self):
        result = target('upload', b'x' * 9, 'wrong-cleanup')
        self.assertFalse(result.accepted)  # Weak oracle passes.
        self.assertTrue(result.retained)  # Full contract still fails.
        self.assertEqual(result.effects, ())

    def test_upstream_and_target_need_different_cleanup(self):
        old_target = target('upload', b'x' * 9, 'wrong-cleanup')
        latest = upstream('upload', b'x' * 9, True)
        self.assertEqual(latest.trace, ())
        self.assertEqual(old_target.trace, ('acquire',))
        self.assertFalse(latest.retained)
        self.assertTrue(old_target.retained)

    def test_correct_target_cleanup_balances_acquisition(self):
        for entry in ('upload', 'restore'):
            result = target(entry, b'x' * 9, 'complete')
            self.assertEqual(result.trace, ('acquire', 'release'))

    def test_valid_payloads_unchanged_across_target_variants(self):
        for entry in ('upload', 'restore'):
            for size in (0, 1, 7, 8):
                data = b'x' * size
                baseline = target(entry, data, 'baseline')
                for variant in ('one-site', 'wrong-cleanup', 'complete'):
                    self.assertEqual(target(entry, data, variant), baseline)
                    self.assertEqual(baseline.effects, (data,))

    def test_multiple_rejection_boundaries(self):
        for entry in ('upload', 'restore'):
            for size in (9, 16, 257):
                self.assert_rejected_safely(target(entry, b'x' * size, 'complete'))

    def test_reverting_one_fix_reexposes_only_that_site(self):
        self.assert_rejected_safely(target('upload', b'x' * 9, 'one-site'))
        self.assertTrue(target('restore', b'x' * 9, 'one-site').accepted)

    def test_unknown_revision_is_not_silently_baseline(self):
        with self.assertRaises(ValueError):
            target('upload', b'x' * 9, 'typo')


if __name__ == '__main__':
    unittest.main(verbosity=2)
