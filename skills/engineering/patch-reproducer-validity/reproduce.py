#!/usr/bin/env python3
"""Original, isolated patch-attribution examples; no project or network access.

Toy public contract: positional pagination over a supplied list; offset >= 0,
integer limit >= 0; limit 0 returns []; negative limits must raise ValueError.
The deliberately faulty implementations below are evidence fixtures, not a
pagination library. Evidence labels are local review conventions, not a scanner.
"""

import unittest
from dataclasses import dataclass, replace


def baseline_page(items, offset, limit):
    if limit == 0:
        return []
    return items[offset : offset + limit - 1]


def candidate_page(items, offset, limit):
    # Fixes the positive-limit boundary but accidentally breaks limit=0.
    return items[offset : offset + max(1, limit)]


def repaired_page(items, offset, limit):
    # Repairs both demonstrated cases, but still lacks negative-limit validation.
    return items[offset : offset + limit]


def partial_page(items, offset, limit):
    if limit == 2:
        return items[offset : offset + limit]
    return baseline_page(items, offset, limit)


@dataclass(frozen=True)
class Context:
    case: str
    contract: str = "toy-pagination-v1"
    fixture: str = "integers-1-through-29"
    environment: str = "stdlib-only"
    entrypoint: str = "page-callable"


@dataclass(frozen=True)
class Evidence:
    context: Context
    outcomes: tuple[str, ...]


def replay(page, *, limit, expected=None, error=None):
    """Capture a contract result, not generic interpreter assertions.

    An expected exception is itself the oracle. Unexpected application exceptions
    are contract failures; setup errors are recorded separately by the caller.
    """
    try:
        actual = page(list(range(1, 30)), offset=10, limit=limit)
    except Exception as exc:
        return "pass" if error is not None and type(exc) is error else "fail"
    return "pass" if error is None and actual == expected else "fail"


def classify(before, after, *, applicable=True):
    """Classify supplied toy evidence; does not discover authority/reachability.

    Applicable means the reviewed contract applies at a demonstrated caller path.
    Context tracks unrelated controls, not intentional changes inside the patch.
    It is trusted fixture metadata, not a cryptographic attestation.
    """
    if not applicable:
        return "unsupported-claim"
    if before.context != after.context:
        return "inconclusive"
    if (not before.outcomes or not after.outcomes
            or len(set(before.outcomes)) != 1
            or len(set(after.outcomes)) != 1):
        return "inconclusive"
    pair = before.outcomes[0], after.outcomes[0]
    return {
        ("fail", "pass"): "repaired-case",
        ("pass", "fail"): "introduced-regression-candidate",
        ("fail", "fail"): "unresolved-defect",
        ("pass", "pass"): "no-failure-observed",
    }.get(pair, "inconclusive")


class PairedEvidenceTests(unittest.TestCase):
    def evidence(self, page, case, **kwargs):
        # Repetition tests fixture stability only; it is not a statistical bound.
        return Evidence(Context(case), tuple(replay(page, **kwargs) for _ in range(3)))

    def test_target_case_is_repaired(self):
        before = self.evidence(baseline_page, "positive", limit=2, expected=[11, 12])
        after = self.evidence(candidate_page, "positive", limit=2, expected=[11, 12])
        self.assertEqual(before.outcomes, ("fail",) * 3)
        self.assertEqual(after.outcomes, ("pass",) * 3)
        self.assertEqual(classify(before, after), "repaired-case")

    def test_same_patch_introduces_zero_limit_regression(self):
        before = self.evidence(baseline_page, "zero", limit=0, expected=[])
        after = self.evidence(candidate_page, "zero", limit=0, expected=[])
        self.assertEqual(baseline_page(list(range(1, 30)), 10, 0), [])
        self.assertEqual(candidate_page(list(range(1, 30)), 10, 0), [11])
        self.assertEqual(classify(before, after), "introduced-regression-candidate")
        # Controlled removal of the changed guard behavior repairs this case.
        revised = self.evidence(repaired_page, "zero", limit=0, expected=[])
        self.assertEqual(classify(before, revised), "no-failure-observed")

    def test_repaired_candidate_retains_target_fix(self):
        self.assertEqual(replay(repaired_page, limit=2, expected=[11, 12]), "pass")

    def test_incomplete_fix_remains_unresolved(self):
        before = self.evidence(baseline_page, "three", limit=3, expected=[11, 12, 13])
        after = self.evidence(partial_page, "three", limit=3, expected=[11, 12, 13])
        self.assertEqual(classify(before, after), "unresolved-defect")

    def test_preexisting_validation_defect_is_not_new(self):
        before = self.evidence(baseline_page, "negative", limit=-1, error=ValueError)
        after = self.evidence(candidate_page, "negative", limit=-1, error=ValueError)
        self.assertEqual(classify(before, after), "unresolved-defect")

    def test_expected_rejection_is_a_valid_oracle(self):
        def validated_page(items, offset, limit):
            if limit < 0:
                raise ValueError("negative limit")
            return repaired_page(items, offset, limit)

        self.assertEqual(replay(validated_page, limit=-1, error=ValueError), "pass")
        self.assertEqual(replay(validated_page, limit=-1, error=TypeError), "fail")

    def test_weak_oracle_misses_original_defect(self):
        old = baseline_page(list(range(1, 30)), 10, 2)
        new = candidate_page(list(range(1, 30)), 10, 2)
        self.assertTrue(bool(old) and bool(new))
        self.assertNotEqual(old, [11, 12])
        self.assertEqual(new, [11, 12])

    def test_setup_failure_is_inconclusive(self):
        before = Evidence(Context("zero"), ("setup-error",))
        after = self.evidence(candidate_page, "zero", limit=0, expected=[])
        self.assertEqual(classify(before, after), "inconclusive")

    def test_changed_context_cannot_attribute_a_regression(self):
        before = Evidence(Context("zero"), ("pass",))
        for field in ("case", "contract", "fixture", "environment", "entrypoint"):
            with self.subTest(field=field):
                after = Evidence(replace(before.context, **{field: "changed"}), ("fail",))
                self.assertEqual(classify(before, after), "inconclusive")

    def test_mixed_results_remain_inconclusive(self):
        before = Evidence(Context("zero"), ("pass", "fail", "pass"))
        after = Evidence(Context("zero"), ("fail",) * 3)
        self.assertEqual(classify(before, after), "inconclusive")

    def test_missing_results_remain_inconclusive(self):
        before = Evidence(Context("zero"), ())
        after = Evidence(Context("zero"), ("fail",))
        self.assertEqual(classify(before, after), "inconclusive")

    def test_unsupported_claim_is_not_a_confirmed_regression(self):
        before = Evidence(Context("private-helper-misuse"), ("pass",))
        after = Evidence(Context("private-helper-misuse"), ("fail",))
        self.assertEqual(classify(before, after, applicable=False), "unsupported-claim")

    def test_negative_input_with_rejection_contract_is_not_unsupported(self):
        # Bad input is in scope when the contract requires safely rejecting it.
        before = Evidence(Context("negative"), ("pass",))
        after = self.evidence(candidate_page, "negative", limit=-1, error=ValueError)
        self.assertEqual(classify(before, after), "introduced-regression-candidate")

    def test_fail_fail_does_not_establish_unchanged_impact(self):
        def crashes(items, offset, limit):
            raise RuntimeError("new failure mode")

        self.assertEqual(baseline_page(list(range(1, 30)), 10, 2), [11])
        with self.assertRaises(RuntimeError):
            crashes(list(range(1, 30)), 10, 2)
        before = self.evidence(baseline_page, "positive", limit=2, expected=[11, 12])
        after = self.evidence(crashes, "positive", limit=2, expected=[11, 12])
        self.assertEqual(classify(before, after), "unresolved-defect")
        # The shared label cannot establish equal failure identity or impact.

    def test_unexpected_application_exception_is_a_contract_failure(self):
        def crashes(items, offset, limit):
            raise RuntimeError("application failure, not setup failure")

        self.assertEqual(replay(crashes, limit=0, expected=[]), "fail")


if __name__ == "__main__":
    unittest.main(verbosity=2)
