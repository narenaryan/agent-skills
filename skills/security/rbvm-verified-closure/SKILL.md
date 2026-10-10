---
name: rbvm-verified-closure
description: Use when a vulnerability ticket, patch PR, or deployment is marked complete but closure still needs proof that the affected running assets changed and fresh evidence covers the original finding.
---

# Verified Closure

Closure is a join between the original affected population, the actual deployed state, and a successful verification result. A merged PR or clean candidate image proves neither rollout nor fleet coverage.

## Evidence join

| Evidence | Acceptance condition |
|---|---|
| Scope | Enumerated affected asset IDs, environments, resource generations, and component identities |
| Deployment | Observed running digest/configuration/version per asset, including activation/restart evidence when required |
| Verification | Successful post-change observation of the relevant component and vulnerability using recorded scanner/rule/database versions |
| Coverage | Every in-scope member accounted for; removed assets need decommission evidence; unreachable assets remain unknown |
| Health | Required functional checks passed; rollback or failed activation reopens verification |

## Closure recipe

1. Freeze the finding's baseline population and timestamps. Reconcile inventory changes explicitly rather than shrinking the denominator silently.
2. Join rollout observations to immutable artifact identity. For multi-platform images, map the approved index to the platform manifest actually running; do not compare unlike digests blindly.
3. Verify the runtime state after activation. A fresh image scan may combine with fresh runtime digest evidence; it does not require scanning every identical image repeatedly. Host/runtime changes need corresponding live evidence.
4. Compare detection scope with baseline: credentials, package ecosystem, file paths, severity filters, suppressions, database freshness, and scan errors. Missing findings count only when the relevant checks completed successfully.
5. Record disposition separately: fixed, mitigated, accepted-risk, false-positive, decommissioned, or verification-pending. Keep accepted exceptions visible through `rbvm-risk-exceptions`.

Example: 12 pods were affected; 11 run the verified replacement digest and one still runs the old image. Report 11/12 verified and keep the remaining exposure open, even if the deployment ticket says Done.

Local fixture: `python3 skills/security/rbvm-verified-closure/scripts/check_closure.py` tests evidence decisions only, not production assets.

Sources: NIST SP 800-40 Rev. 4 (April 2022), §§2.2–2.3; Kubernetes Images documentation, reviewed 2026-10-10. Original gate design and scenarios: [SOURCES.md](SOURCES.md).

## Pitfalls

- Mutable tags can name different content between build, scan, and rollout.
- A scan timestamp after deployment does not prove its input was current.
- Scanner failure, suppression, or scope reduction can masquerade as remediation.
- Reboot-pending or restarted vulnerable processes invalidate “installed equals effective.”
