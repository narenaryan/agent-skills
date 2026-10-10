---
name: security-gate-rollout
description: Use when a vulnerability or infrastructure policy must move from advisory checks to blocking CI or admission without hiding unknown inputs, grandfathering new risk, or breaking every deployment.
---

# Security Gate Rollout

A policy result and its enforcement action are separate decisions. Missing evidence is `unknown`, not a passing evaluation; existing debt and newly introduced violations need different treatment.

## Decision contract

| Input | Evaluation | Rollout treatment |
|---|---|---|
| Complete, compliant evidence | pass | Allow |
| Complete, violated predicate | fail | Warn/audit initially; deny in approved scope |
| Missing scan, stale artifact, unknown plan value | unknown | Explicit retry/review path; never silently pass |
| Pre-existing violation | debt | Owned backlog; block additions or worsening separately |

## Recipe

1. Version the rule, evidence schema, artifact digest, and baseline. Evaluate the exact artifact promoted, not another build from the same commit.
2. Collect shadow decisions against representative services. Record denominators: evaluated, unmatched, unknown, failed, and exception-covered. No failures with zero matches proves nothing.
3. Test known-good, known-bad, missing-field, expired-exception, renamed-resource, and bypass-path fixtures. A baseline finding keeps its identity through scanner ID changes.
4. Promote an approved service/namespace cohort; set rollback criteria for false blocks, evaluation errors, and delivery disruption. Retain findings when reverting enforcement.
5. Require a separately approved, expiring exception for a new violation. A changed baseline must not erase debt automatically.

For Kubernetes v1.30+ `ValidatingAdmissionPolicy`, the binding supplies enforcement:

```yaml
# Fragment of ValidatingAdmissionPolicyBinding.spec
validationActions: [Warn, Audit]
# Approved blocking phase instead: [Deny, Audit]
```

`Deny` and `Warn` cannot coexist. Policy `failurePolicy` controls evaluation errors, not ordinary false results; `Ignore` can hide errors. Check selector matches and binding existence. Admission covers matching requests, not a retrospective inventory scan.

Terraform plan JSON separates `after` from `after_unknown`. An unknown public-access flag needs deferred verification or review, not `false` substitution. Preserve plan confidentiality.

Sources: [Kubernetes](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/), [Terraform JSON](https://developer.hashicorp.com/terraform/internals/json-format), [canaries](https://sre.google/workbook/canarying-releases/). [Evidence and limits](SOURCES.md).

## Pitfalls

- Blocking only pull requests leaves direct provisioning and runtime drift unchecked.
- Counting exceptions as clean assets conceals residual risk.
- Global enforcement before measuring match coverage turns schema mistakes into outages.
