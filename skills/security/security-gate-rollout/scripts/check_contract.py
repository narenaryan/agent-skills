"""Offline rollout contract fixtures, not a Kubernetes/CEL interpreter."""
import unittest


def decide(*, matched, evidence, violation, baseline, phase, worsened=False, exception="none"):
    if not matched:
        return "unmatched"
    if evidence != "complete":
        return "review"
    if not violation:
        return "allow"
    if exception == "valid":
        return "exception-recorded"
    if baseline and not worsened:
        return "debt-recorded"
    return "deny" if phase == "enforce" else "warn-audit"


class RolloutContract(unittest.TestCase):
    def test_boundaries(self):
        base = dict(matched=True, evidence="complete", violation=True,
                    baseline=False, phase="enforce")
        cases = [({}, "deny"), ({"matched": False}, "unmatched"),
                 ({"evidence": "unknown"}, "review"),
                 ({"evidence": "stale"}, "review"),
                 ({"violation": False}, "allow"),
                 ({"baseline": True}, "debt-recorded"),
                 ({"phase": "shadow"}, "warn-audit"),
                 ({"exception": "valid"}, "exception-recorded"),
                 ({"exception": "expired"}, "deny"),
                 ({"baseline": True, "worsened": True}, "deny"),
                 ({"exception": "valid", "evidence": "unknown"}, "review")]
        for overrides, expected in cases:
            with self.subTest(overrides=overrides):
                self.assertEqual(decide(**(base | overrides)), expected)

    def test_missing_is_not_false(self):
        # A common baseline silently treats missing plan evidence as compliant.
        plan = {"after": {}, "after_unknown": {"public": True}}
        self.assertFalse(plan["after"].get("public", False))
        self.assertTrue(plan["after_unknown"]["public"])
        self.assertEqual(decide(matched=True, evidence="unknown", violation=False,
                                baseline=False, phase="enforce"), "review")


if __name__ == "__main__":
    unittest.main()
