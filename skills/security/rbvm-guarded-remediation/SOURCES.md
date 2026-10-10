# Source ledger and design rationale

Reviewed 2026-10-10. These are operational design recommendations, not a ready-to-run production controller. No production actions were taken.

## Primary evidence

- [AWS Config: Setting Up Auto Remediation](https://docs.aws.amazon.com/config/latest/developerguide/setup-autoremediation.html), continuously updated documentation, section “Auto remediation can be initiated even for compliant resources.” Periodic compliance snapshots may be stale; a compliant resource may still receive remediation. This motivates the live-state no-op gate rather than trusting the event.
- [Malcolm Featonby, Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), Amazon Builders' Library, undated HTML reviewed above; corresponding AWS PDF copyright 2020. Sections on client request identifiers, late requests, and changed intent support persisting the request identity and parameters, rejecting mismatches, and respecting deduplication lifetimes. Server-side token recording and mutation need atomicity; a client log alone cannot supply it.
- [Google SRE Workbook, Canarying Releases](https://sre.google/workbook/canarying-releases/), Alec Warner and Štěpán Davidovič, 2018. Sections “Requirements of a Canary Process,” “Choosing a Canary Population and Duration,” and “Canarying in Noninteractive Systems” support bounded exposure, measurable evaluation, and workload-sensitive observation. The chapter also calls for absolute SLO checks because both comparison groups can deteriorate.

## Original worked scenarios

| Situation | Decision | Why |
|---|---|---|
| Yesterday's public-access finding arrives after an owner fixed the policy | Live read confirms desired state; record no-op | Event truth is historical, not an action precondition |
| Patch API times out after accepting the request | Reconcile state; reuse the documented request key only within its valid contract | Timeout does not imply no side effect |
| Retry carries a different target digest under the old operation ID | Reject and create a separately approved operation | Same identity with changed intent defeats safe replay |
| Canary has zero requests during the observation interval | Inconclusive; wait for representative work or choose another approved validation | Elapsed time is not exercised behavior |
| Deployment health regresses and rollback restores the old vulnerable image | Report availability recovery plus reopened exposure | Operational recovery does not prove security success |

The ownership/approval gate, lease/version guard, declarative-source reconciliation, and closure handoff are original integration patterns. A workflow lease only coordinates writers that honor it; independent controllers or users require provider-enforced conditional updates or equivalent atomic preconditions. These patterns depend on the actual platform's concurrency and permission mechanisms; the cited articles do not provide one universal implementation.

## Overlap boundary

`container-image-patching` selects and builds package fixes. This skill governs permission, live-state preconditions, replay safety, and deployment scope. `ai-bug-patterns` supplies general retry/race review prompts; this skill specializes them to remediation events. `minimal-sufficient-evidence` supports retaining one decisive gate per distinct failure mode.
