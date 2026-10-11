#!/usr/bin/env python3
"""Offline decision-contract fixture, NOT an IAM policy evaluator or AWS client.

Synthetic API-shaped responses exercise explicit action/resource coverage and
independently specified must-allow/must-deny contracts. No network or credentials.
Each invocation represents one fixed principal/context bundle. Unsupported policy
layers must be declared by the caller; this cannot detect omitted evidence.
"""
import copy
import unittest

VALID = {"allowed", "implicitDeny", "explicitDeny"}
A = "s3:GetObject"
PUBLIC = "arn:aws:s3:::example-public/object"
PRIVATE = "arn:aws:s3:::example-private/object"
BLOCKED = "arn:aws:s3:::example-blocked/object"
EXPECTED = {(A, PUBLIC), (A, PRIVATE), (A, BLOCKED)}
BINDING = ("current-policy-sha", "candidate-policy-sha", "corpus-context-sha", "evaluator-version")


def normalize(pages, expected):
    """Require complete explicit-resource results; never infer from aggregates."""
    if not expected or not isinstance(pages, list) or not pages:
        raise ValueError("empty coverage")
    decisions = {}
    for i, page in enumerate(pages):
        if not isinstance(page, dict) or "Error" in page:
            raise ValueError("invalid response")
        truncated = page.get("IsTruncated", False)
        if type(truncated) is not bool or truncated != (i < len(pages) - 1):
            raise ValueError("incomplete or inconsistent pagination")
        rows = page.get("EvaluationResults")
        if not isinstance(rows, list) or not rows:
            raise ValueError("missing evaluations")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("invalid evaluation")
            action = row.get("EvalActionName")
            resources = row.get("ResourceSpecificResults")
            if not isinstance(action, str) or not isinstance(resources, list) or not resources:
                raise ValueError("missing resource-specific evaluations")
            for resource in resources:
                if not isinstance(resource, dict):
                    raise ValueError("invalid resource evaluation")
                arn = resource.get("EvalResourceName")
                decision = resource.get("EvalResourceDecision")
                if not isinstance(arn, str) or not isinstance(decision, str) or decision not in VALID:
                    raise ValueError("invalid decision")
                key = (action, arn)
                if key not in expected or key in decisions:
                    raise ValueError("unexpected or duplicate coverage")
                for context in (row.get("MissingContextValues", []), resource.get("MissingContextValues", [])):
                    if not isinstance(context, list) or context:
                        raise ValueError("missing or malformed context")
                decisions[key] = decision
    if set(decisions) != expected:
        raise ValueError("incomplete coverage")
    return decisions


def assess(before, after, expected, required, forbidden, approved_deltas=frozenset(),
           recorded_binding=BINDING, current_binding=BINDING, supported=True):
    """Return report only; pass is scoped evidence, never execution approval."""
    if recorded_binding != current_binding or supported is not True:
        return "unknown"
    if not required <= expected or not forbidden <= expected or required & forbidden:
        return "unknown"
    try:
        old, new = normalize(before, expected), normalize(after, expected)
    except (ValueError, TypeError):
        return "unknown"
    deltas = {(key, old[key], new[key]) for key in expected if old[key] != new[key]}
    if any(new[key] != "allowed" for key in required):
        return "fail"
    if any(new[key] == "allowed" for key in forbidden):
        return "fail"
    if deltas - approved_deltas:
        return "fail"
    return "pass"


def response(public="allowed", private="implicitDeny", aggregate="explicitDeny"):
    return [{"IsTruncated": False, "EvaluationResults": [{
        "EvalActionName": A, "EvalDecision": aggregate,
        "ResourceSpecificResults": [
            {"EvalResourceName": PUBLIC, "EvalResourceDecision": public},
            {"EvalResourceName": PRIVATE, "EvalResourceDecision": private},
            {"EvalResourceName": BLOCKED, "EvalResourceDecision": "explicitDeny"},
        ],
    }]}]


class ReplayChecks(unittest.TestCase):
    def check(self, before=None, after=None, **kwargs):
        return assess(response() if before is None else before,
                      response() if after is None else after, EXPECTED,
                      {(A, PUBLIC)}, {(A, PRIVATE)}, **kwargs)

    def test_unchanged_supported_contract_passes(self):
        self.assertEqual(self.check(), "pass")

    def test_deny_all_adds_no_access_but_breaks_required_caller(self):
        before, after = response(), response(public="implicitDeny")
        old, new = normalize(before, EXPECTED), normalize(after, EXPECTED)
        self.assertFalse(any(new[k] == "allowed" and old[k] != "allowed" for k in EXPECTED))
        self.assertEqual(self.check(before, after), "fail")

    def test_equal_aggregate_denials_hide_new_resource_allow(self):
        before, after = response(), response(private="allowed")
        self.assertEqual(before[0]["EvaluationResults"][0]["EvalDecision"],
                         after[0]["EvaluationResults"][0]["EvalDecision"])
        self.assertEqual(self.check(before, after), "fail")

    def test_existing_forbidden_access_fails_without_delta(self):
        self.assertEqual(self.check(response(private="allowed"), response(private="allowed")), "fail")

    def test_intended_removal_preserves_required_access(self):
        delta = ((A, PRIVATE), "allowed", "implicitDeny")
        self.assertEqual(self.check(response(private="allowed"), response(), approved_deltas={delta}), "pass")

    def test_missing_context_is_not_a_successful_denial(self):
        for place in ("row", "resource"):
            after = response()
            row = after[0]["EvaluationResults"][0]
            target = row if place == "row" else row["ResourceSpecificResults"][1]
            target["MissingContextValues"] = ["aws:PrincipalTag/team"]
            self.assertEqual(self.check(after=after), "unknown")

    def test_missing_duplicate_or_extra_resource_is_unknown(self):
        for kind in ("missing", "duplicate", "extra"):
            after = response()
            values = after[0]["EvaluationResults"][0]["ResourceSpecificResults"]
            if kind == "missing": values.pop()
            elif kind == "duplicate": values.append(copy.deepcopy(values[0]))
            else: values.append({"EvalResourceName": "unexpected", "EvalResourceDecision": "allowed"})
            self.assertEqual(self.check(after=after), "unknown")

    def test_truncated_response_is_unknown(self):
        after = response(); after[0]["IsTruncated"] = True
        self.assertEqual(self.check(after=after), "unknown")

    def test_complete_two_page_response(self):
        first, second = response()[0], response()[0]
        first["IsTruncated"] = True
        first["EvaluationResults"][0]["ResourceSpecificResults"] = first["EvaluationResults"][0]["ResourceSpecificResults"][:1]
        second["EvaluationResults"][0]["ResourceSpecificResults"].pop(0)
        self.assertEqual(self.check(after=[first, second]), "pass")

    def test_changed_policy_context_or_engine_binding_is_unknown(self):
        for i in range(len(BINDING)):
            changed = list(BINDING); changed[i] = "changed"
            self.assertEqual(self.check(current_binding=tuple(changed)), "unknown")

    def test_unsupported_layer_is_unknown(self):
        self.assertEqual(self.check(supported=False), "unknown")

    def test_missing_resource_results_cannot_fallback_to_aggregate(self):
        after = response(); del after[0]["EvaluationResults"][0]["ResourceSpecificResults"]
        self.assertEqual(self.check(after=after), "unknown")

    def test_invalid_decision_or_boolean_type_is_unknown(self):
        for field, value in (("EvalResourceDecision", True), ("MissingContextValues", "")):
            after = response()
            after[0]["EvaluationResults"][0]["ResourceSpecificResults"][0][field] = value
            self.assertEqual(self.check(after=after), "unknown")

    def test_empty_evidence_is_unknown(self):
        self.assertEqual(self.check(before=[]), "unknown")
        self.assertEqual(self.check(after=[]), "unknown")

    def test_baseline_failure_stays_unknown(self):
        self.assertEqual(self.check(before=[{"Error": "AccessDenied"}]), "unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)
