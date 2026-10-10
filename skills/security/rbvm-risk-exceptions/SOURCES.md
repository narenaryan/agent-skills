# Source ledger and governance cases

Reviewed 2026-10-10. Expiry and review-trigger mechanics below are original operational recommendations. No universal exception lifetime or risk-acceptance authority is asserted.

## Primary evidence

- [NIST SP 800-40 Rev. 4](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-40r4.pdf), Murugiah Souppaya and Karen Scarfone, April 2022, §§3.5.3–3.5.5. Emergency mitigations need a path to permanent fixes; alternatives for unpatchable assets need periodic reevaluation; maintenance exceptions need tracking and regular review. These support a reviewable decision rather than permanent suppression.
- [NIST Cybersecurity Framework 2.0](https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf), NIST CSWP 29, February 26, 2024, Appendix A. GV.RR-02 addresses established cybersecurity responsibilities and authorities. ID.RA-07 addresses management, risk assessment, recording, and tracking of exceptions and changes. GV.OC-03 addresses applicable obligations. These justify checking local authority and obligations before recording acceptance; CSF does not designate a universal approver.

## Original decision examples

| Proposed disposition | Missing distinction | Correct next step |
|---|---|---|
| “The scanner is wrong; ignore it” | Incorrect detection versus accepted exposure | Request technical not-affected evidence or route an acceptance decision |
| “Vendor has no fix” | Availability of a patch versus acceptability of risk | Evaluate isolation, feature removal, replacement, and residual impact |
| “Owner approved indefinitely” | Service ownership versus delegated acceptance authority | Verify authority and propose bounded review/expiry under local policy |
| “Existing exception covers this new internet-facing deployment” | Original scoped environment versus changed exposure | Reassess the new population; do not inherit approval silently |
| “Renew last month's exception automatically” | Historic rationale versus current evidence | Verify controls, threat conditions, alternatives, and authorized decision |
| “The exception expired; patch immediately” | Loss of acceptance versus permission for a production change | Restore active triage and route the authorized remediation workflow |

Worked timeline: a fictional exception approved October 10 expires October 24. Its next scheduled review is October 17. External exposure discovered October 13 triggers immediate reassessment even though both scheduled dates are later. If no renewal is approved by October 24, acceptance becomes inactive; the underlying vulnerability remains visible. Dates illustrate lifecycle logic, not a mandated SLA.

## Overlap boundary

This skill handles governance of retained exposure. `rbvm-verified-closure` owns technical outcome evidence; `rbvm-guarded-remediation` owns safe execution. A valid exception never substitutes for a “fixed” verification result, and an expired exception never supplies execution authorization.
