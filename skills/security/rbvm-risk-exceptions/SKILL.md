---
name: rbvm-risk-exceptions
description: Use when patching is deferred, a finding is suppressed, a compensating control substitutes for a fix, or an existing vulnerability exception needs renewal after its assumptions change.
---

# Risk Exceptions

An exception is a bounded decision to retain residual risk, not proof that a vulnerability disappeared. Keep the technical finding and its governance decision independently observable.

## Decision record

| Field | Required evidence |
|---|---|
| Scope | Exact finding/component, asset population, environment, and excluded populations |
| Authority | Accountable risk owner, named approver, delegated authority, decision timestamp |
| Rationale | Business constraint, considered alternatives, residual likelihood/impact |
| Controls | Compensating measures, verification evidence, operating owner, failure signals |
| Lifecycle | Explicit expiry, next review, trigger conditions, remediation/retirement plan |

## Recipe

1. Separate false-positive adjudication from risk acceptance. “Not affected” needs technical evidence; “affected but cannot patch” needs a risk decision.
2. Check the organization's authority matrix and obligations. The remediation assignee is not automatically authorized to accept risk; approval cannot waive mandatory requirements.
3. Propose the narrowest scope and duration justified by the constraint. Record approval before activating suppression; link any scanner suppression to the exception ID and expiry.
4. Reassess before expiry and on changed exposure, exploitation evidence, control failure, new fix availability, expanded asset scope, or changed business impact. A review trigger invalidates assumptions and routes reassessment; it does not silently authorize a patch.
5. On expiry or missing approval, mark the exception inactive and restore ordinary triage visibility. Renewal requires fresh evidence and an authorized decision, preserving the previous record.

Example: an isolated legacy processor receives a 14-day exception while its replacement is tested. If its network policy opens external access on day three, reassess immediately rather than waiting eleven days. The duration is illustrative, not a standard deadline.

Sources: NIST SP 800-40 Rev. 4 (April 2022), §§3.5.3–3.5.5; NIST CSF 2.0 (February 2024), GV.RR-02 and ID.RA-07. Expiry mechanics are this skill's implementation pattern, not a NIST-prescribed interval. See [SOURCES.md](SOURCES.md).

## Pitfalls

- “No patch available” does not establish acceptable residual risk.
- Permanent scanner suppression conceals expired decisions and changing exposure.
- Repeated renewals without reassessment turn temporary exceptions into invisible policy.
- A compensating control's existence does not prove it blocks the relevant attack path.
