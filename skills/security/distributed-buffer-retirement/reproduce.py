"""Original offline event model: no network, GPU, third-party code, or production controls."""
import itertools
import unittest
from dataclasses import dataclass, field


@dataclass
class Buffer:
    owner: str = 'A'
    value: str = 'A-marker'
    pending: set = field(default_factory=lambda: {'p0', 'p1'})

    def write(self, rank):
        self.value = 'A-late'
        self.pending.remove(rank)

    def reuse(self):
        self.owner, self.value = 'B', 'B-marker'


@dataclass
class Retirement:
    generation: int
    participants: frozenset
    armed: bool = False
    acks: set = field(default_factory=set)

    def ack(self, generation, rank, drained):
        if (self.armed and generation == self.generation
                and rank in self.participants and drained is True):
            self.acks.add(rank)

    def reusable(self):
        return self.armed and self.acks == self.participants


def intake(rejected, finished, reentry, owns_resources, guarded):
    if not guarded:
        return 'retire' if finished else 'handoff'
    # Re-entry requires its own cleanup, even if current ownership fields are empty.
    if reentry or owns_resources:
        return 'cleanup' if rejected else 'resume'
    return 'retire' if rejected or finished else 'handoff'


def readable(values, expected_owner):
    return all(owner == expected_owner and initialized is True
               for owner, initialized in values)


class ContractTests(unittest.TestCase):
    def test_pending_reject_is_not_admissible(self):
        self.assertEqual(intake(True, False, False, False, False), 'handoff')
        self.assertEqual(intake(True, False, False, False, True), 'retire')

    def test_reentry_cannot_use_intake_fast_exit(self):
        for reentry, owns in [(True, False), (False, True), (True, True)]:
            self.assertEqual(intake(True, False, reentry, owns, True), 'cleanup')
        self.assertEqual(intake(False, False, False, False, True), 'handoff')

    def test_short_transfer_leaves_stale_readable_range(self):
        pages = [('A', True)] + [('predecessor', True)] * 7
        self.assertEqual(len(pages), 8)  # reservation alone passes
        self.assertFalse(readable(pages, 'A'))
        self.assertFalse(readable([('A', False)] * 8, 'A'))
        self.assertTrue(readable([('A', True)] * 8, 'A'))

    def test_error_or_zeroing_does_not_recall_write(self):
        for failure in ['cancel', 'producer-fault', 'transport-error']:
            with self.subTest(failure=failure):
                b = Buffer()
                b.reuse()  # includes overwriting/zeroing the old contents
                b.write('p0')
                self.assertEqual((b.owner, b.value), ('B', 'A-late'))

    def test_all_write_ack_orders_withhold_reuse(self):
        count = 0
        for order in itertools.permutations(['w0', 'w1', 'a0', 'a1']):
            if any(order.index('a'+i) < order.index('w'+i) for i in ['0', '1']):
                continue
            b = Buffer()
            r = Retirement(7, frozenset({'p0', 'p1'}), armed=True)
            for event in order:
                rank = 'p'+event[1]
                if event[0] == 'w':
                    b.write(rank)
                else:
                    r.ack(7, rank, rank not in b.pending)
                if b.pending:
                    self.assertFalse(r.reusable())
            self.assertTrue(r.reusable())
            b.reuse()
            self.assertEqual(b.value, 'B-marker')
            count += 1
        self.assertEqual(count, 6)

    def test_stale_duplicate_unknown_and_unarmed_acks(self):
        r = Retirement(8, frozenset({'p0', 'p1'}))
        r.ack(8, 'p0', True)
        self.assertEqual(r.acks, set())
        r.armed = True
        for generation, rank, drained in [(7, 'p1', True), (8, 'other', True),
                                           (8, 'p1', 'unknown'), (8, 'p1', False)]:
            r.ack(generation, rank, drained)
        r.ack(8, 'p0', True)
        r.ack(8, 'p0', True)
        self.assertFalse(r.reusable())
        r.ack(8, 'p1', True)
        self.assertTrue(r.reusable())

    def test_failed_send_is_not_drained(self):
        b = Buffer()
        r = Retirement(1, frozenset({'p0', 'p1'}), armed=True)
        for rank in ['p0', 'p1']:
            r.ack(1, rank, False)  # failed call, completion unknown
        self.assertFalse(r.reusable())
        self.assertTrue(b.pending)

    def test_timeout_without_bound_still_allows_late_write(self):
        b = Buffer()
        r = Retirement(1, frozenset({'p0', 'p1'}), armed=True)
        b.write('p0')
        r.ack(1, 'p0', True)
        self.assertFalse(r.reusable())  # no clock-based safety shortcut
        b.reuse()  # unsafe policy releases anyway after an arbitrary timeout
        b.write('p1')
        self.assertEqual(b.value, 'A-late')

    def test_lost_ack_withholds_even_after_actual_drain(self):
        b = Buffer()
        b.write('p0')
        b.write('p1')
        r = Retirement(1, frozenset({'p0', 'p1'}), armed=True)
        r.ack(1, 'p0', True)
        self.assertFalse(r.reusable())  # safe but unavailable; not a liveness proof


if __name__ == '__main__':
    unittest.main(verbosity=2)
