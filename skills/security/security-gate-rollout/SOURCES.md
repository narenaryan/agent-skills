# Security gate rollout: provenance and validation

Reviewed 2026-10-10. Historical documentation synthesis, not a new product announcement.

## Sources and boundaries

- [Kubernetes Validating Admission Policy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/): stable since v1.30; policy and binding responsibilities, Warn/Audit/Deny combinations, error handling, selectors and parameter behavior. The skill's YAML is deliberately a binding fragment, not a deployable cluster policy. No cluster was accessed or altered.
- [Terraform JSON format](https://developer.hashicorp.com/terraform/internals/json-format): unknown planned values are represented separately. Check the runtime's supported JSON format and provider schema rather than assuming absence means a boolean false. Plan files may contain sensitive information.
- [OPA Terraform integration](https://www.openpolicyagent.org/docs/terraform): plan-time evidence limitations. Its old Terraform tutorial is not presented as a tested modern deployment recipe here.
- [Google SRE Workbook: Canarying Releases](https://sre.google/workbook/canarying-releases/): limit initial exposure and compare representative cohorts with explicit rollback signals. The security-rule promotion contract is original adaptation, not a Google-prescribed vulnerability SLA.

## Worked scenario and counterexamples

A new public-ingress rule matches 80 of 100 provisioning requests. Of those 80, 70 have complete evidence, 10 have unknown planned addresses, and 5 of the complete cases violate the rule. Reporting “95% compliant” over all requests conceals both unmatched and unknown cases. The rollout report instead preserves all denominators. An approved enforcement cohort can deny the five known new violations while routing the ten unknown cases for an explicit review or deferred verification. Existing violations retain debt ownership; changing the baseline must not make newly introduced risks disappear.

Counterexamples: an absent policy binding means no enforcement even when the rule compiles; an admission rule does not inspect existing resources without a matching request; a mutable artifact tag can change between scan and promotion; a rule that rejects every request prevents deployments but is not evidence of a correct policy.

## Validation

`python skills/security/security-gate-rollout/scripts/check_contract.py` and the same command with `python -O` passed on 2026-10-10: two unittest methods, including eleven boundary subcases and a missing-value counterexample. This original standard-library toy model verifies the stated decision contract only. It is not Kubernetes, CEL, OPA, or Terraform execution and does not prove production rollout safety. No infrastructure, credentials, network policy, CI permissions, or admissions were changed. The fixture receives prevalidated exception states; it does not calculate expiry, verify approver authority, or match exception scope. Actual engine integration, provider-specific unknown shapes, and rollback execution remain untested.
