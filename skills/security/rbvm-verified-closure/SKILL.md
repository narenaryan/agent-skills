---
name: rbvm-verified-closure
description: Use when a vulnerability ticket, patch PR, or deployment is marked complete but closure needs proof that affected running assets changed and fresh evidence covers the original finding, or prior closure may have regressed.
---

# Verified Closure

Closure joins the original affected population, deployed state, and successful verification. A merged PR or clean candidate image proves neither rollout nor fleet coverage; later rollback can undo closure.

## Evidence join

| Evidence | Acceptance condition |
|---|---|
| Scope | Enumerated affected asset IDs, environments, resource generations, and component identities |
| Deployment | Observed running digest/configuration/version per asset, including activation/restart evidence when required |
| Verification | Successful post-change observation of the relevant component and vulnerability using recorded scanner/rule/database versions |
| Coverage | Every in-scope member accounted for; removed assets need decommission evidence; unreachable assets remain unknown |
| Health | Required functional checks passed; rollback or failed activation reopens verification |

## Closure recipe

1. Freeze baseline population and timestamps; reconcile inventory changes instead of silently shrinking the denominator.
2. Join rollout to immutable artifact identity. For multi-platform images, map the approved index to the running platform manifest; do not compare unlike digests.
3. Verify runtime after activation. A fresh image scan may combine with fresh runtime-digest evidence; identical images need not be rescanned. Host/runtime changes need live evidence.
4. Compare baseline detection scope: credentials, ecosystem, paths, severity, suppressions, database freshness, and scan errors. Missing findings count only after relevant checks succeed.
5. Record disposition separately: fixed, mitigated, accepted-risk, false-positive, decommissioned, or verification-pending. Keep exceptions visible in `rbvm-risk-exceptions`.
6. Monitor each asset's deployed artifact/version and relied-on mitigations at a risk-tiered local cadence. Rollback, vulnerable backup restore, factory reset, patch removal, or mitigation loss can reintroduce exposure. If monitoring is stale, missing, or inconclusive, mark unknown/verification-pending and investigate; infer neither clean status nor regression. Reopen as regression only when current evidence confirms the original exposure; then retain the original denominator, recompute priority/exceptions, and require fresh closure evidence.

Example: 12 pods were affected; 11 run the verified replacement digest and one still runs the old image. Report 11/12 verified and keep the remaining exposure open, even if the deployment ticket says Done.

Local fixture: `python3 skills/security/rbvm-verified-closure/scripts/check_closure.py` tests evidence decisions only, not production assets.

Sources: [NIST SP 800-40 Rev. 4 (April 2022), §§2.2(d), 2.3.4](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-40r4.pdf) supports continuous risk-response monitoring (patch removal, vulnerable backup restore, factory reset); cadence is local policy. [Kubernetes Images documentation](https://kubernetes.io/docs/concepts/containers/images/), reviewed 2026-10-12. See [SOURCES.md](SOURCES.md).

## Pitfalls

- Mutable tags can name different content between build, scan, and rollout.
- A post-deployment timestamp does not prove the scan input was current.
- Scanner failure, suppression, or scope reduction can masquerade as remediation.
- Reboot-pending or restarted vulnerable processes invalidate “installed equals effective.”
- A clean one-time scan says nothing about later rollback or mitigation loss.
