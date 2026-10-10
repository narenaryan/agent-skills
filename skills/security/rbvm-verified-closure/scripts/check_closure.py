"""Synthetic closure-gate regression fixture; does not inspect production systems."""
from dataclasses import dataclass, replace
import unittest


@dataclass(frozen=True)
class Evidence:
    running_digest: str
    scanned_digest: str
    activated_at: int
    observed_at: int
    scanned_at: int
    scan_succeeded: bool = True
    relevant_check_ran: bool = True
    finding_present: bool = False


def can_close(expected, records, approved_digest):
    """Strict post-activation-scan fixture, not the artifact-scan alternative or a production gate."""
    if not expected or set(records) != set(expected) or not approved_digest:
        return False
    return all(
        e.running_digest == e.scanned_digest == approved_digest
        and e.observed_at >= e.activated_at
        and e.scanned_at >= e.activated_at
        and e.scan_succeeded
        and e.relevant_check_ran
        and not e.finding_present
        for e in records.values()
    )


class ClosureGateTests(unittest.TestCase):
    def test_independent_evidence_gates(self):
        good = Evidence("digest-b", "digest-b", 20, 21, 22)
        cases = [
            ("complete", {"pod-1"}, {"pod-1": good}, True),
            ("empty scope", set(), {}, False),
            ("missing pod", {"pod-1", "pod-2"}, {"pod-1": good}, False),
            ("old runtime", {"pod-1"}, {"pod-1": replace(good, running_digest="digest-a")}, False),
            ("wrong scan input", {"pod-1"}, {"pod-1": replace(good, scanned_digest="digest-c")}, False),
            ("old observation", {"pod-1"}, {"pod-1": replace(good, observed_at=19)}, False),
            ("old scan", {"pod-1"}, {"pod-1": replace(good, scanned_at=19)}, False),
            ("failed scanner", {"pod-1"}, {"pod-1": replace(good, scan_succeeded=False)}, False),
            ("scope reduced", {"pod-1"}, {"pod-1": replace(good, relevant_check_ran=False)}, False),
            ("still vulnerable", {"pod-1"}, {"pod-1": replace(good, finding_present=True)}, False),
        ]
        for label, scope, records, result in cases:
            with self.subTest(label=label):
                self.assertEqual(can_close(scope, records, "digest-b"), result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
