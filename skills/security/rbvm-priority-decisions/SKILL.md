---
name: rbvm-priority-decisions
description: Use when a vulnerability backlog is ranked by CVSS alone, EPSS conflicts with known exploitation, or teams need reproducible KEV/SSVC decisions and explicit uncertainty handling.
---

# RBVM Priority Decisions

Separate evidence from policy. Severity, observed exploitation, forecast probability, and mission consequence answer different questions; adding their numbers does not produce calibrated risk.

## Signal contract

| Signal | Preserve and interpret |
|---|---|
| KEV | Catalog snapshot, entry, action, applicable obligation; observed exploitation, not local compromise |
| EPSS | Probability, percentile, score date, model version; next-30-day exploitation forecast, not per-asset loss |
| CVSS | Version, full vector, provider, nomenclature; technical severity with declared context |
| SSVC | Stakeholder/model version, decision-point values, evidence, path, outcome |

## Recipe

1. Bind findings to current assets and applicability evidence. Unknown applicability gets a parallel investigation deadline; it must not silently disappear from urgent triage.
2. Check credible active exploitation and KEV independently of EPSS. Local compromise evidence also requires incident-response escalation. A low forecast cannot erase observed exploitation.
3. Select an approved decision model. For CERT/CC deployer `DT_DP:1.0.0`, collect exploitation, system exposure, automatability, and human impact, then use its actual decision table. Do not substitute another stakeholder's outcome labels.
4. Attach applicable obligations separately; verify their current scope rather than imposing one catalog deadline universally. Map policy outcomes to accountable owner, response target, mitigation, remediation, and verification tasks.
5. Record unknowns, alternative paths, and what would change the decision. Save input snapshots and policy version; recompute when exploitation, exposure, mission context, or applicability changes.

Example: synthetic affected internet service, KEV=yes, EPSS=0.001. Escalate known-exploitation review under local policy; retain EPSS but do not downgrade because of it. With applicability unknown, investigate urgently rather than claiming the asset is compromised.

Sources: [CISA official KEV mirror](https://github.com/cisagov/kev-data), [FIRST EPSS](https://www.first.org/epss/), [CVSS v4.0](https://www.first.org/cvss/v4.0/specification-document), [CERT/CC deployer model](https://certcc.github.io/SSVC/howto/deployer_tree/), reviewed 2026-10-10. [SOURCES.md](SOURCES.md) contains scenarios and a local-policy fixture.

## Pitfalls

- EPSS percentile is rank, not probability; missing EPSS is not zero.
- KEV absence does not prove absence of exploitation.
- CVSS v4 Supplemental metrics do not change its numerical score.
- SSVC outcome names are not universal SLAs or permission to deploy changes.
