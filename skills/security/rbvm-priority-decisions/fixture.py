"""Synthetic pre-triage policy contract; not SSVC or a scanner benchmark."""
import math
import unittest


def queues(applicability, kev, observed_exploitation, local_compromise, epss):
    if applicability not in {"affected", "not_affected", "fixed", "unknown"}:
        raise ValueError("Unsupported applicability state")
    if epss is not None and (not math.isfinite(epss) or not 0 <= epss <= 1):
        raise ValueError("EPSS must be a probability or missing")
    result = set()
    if local_compromise:
        result.add("incident-response")
    if applicability == "unknown":
        result.add("applicability-investigation")
    if applicability in {"affected", "unknown"}:
        if kev or observed_exploitation:
            result.add("known-exploitation-review")
        else:
            result.add("approved-model-evaluation")
    return result


class PolicyContract(unittest.TestCase):
    def test_non_downgrade(self):
        for epss in (None, 0.0, 0.001, 1.0):
            self.assertEqual(queues("affected", True, False, False, epss),
                             {"known-exploitation-review"})

    def test_independent_queues(self):
        self.assertEqual(queues("unknown", True, False, False, 0.001),
                         {"applicability-investigation", "known-exploitation-review"})
        self.assertEqual(queues("fixed", False, False, True, None),
                         {"incident-response"})
        self.assertEqual(queues("affected", False, True, False, None),
                         {"known-exploitation-review"})
        self.assertEqual(queues("affected", False, False, False, None),
                         {"approved-model-evaluation"})

    def test_invalid_probability(self):
        for value in (-0.1, 1.1, float("nan")):
            with self.assertRaises(ValueError):
                queues("affected", False, False, False, value)


if __name__ == "__main__":
    unittest.main()
