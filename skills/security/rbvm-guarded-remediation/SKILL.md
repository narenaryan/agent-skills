---
name: rbvm-guarded-remediation
description: Use when a vulnerability finding is about to trigger an automated patch, configuration change, isolation action, or retry against live assets, especially when evidence may be stale or ownership is unclear.
---

# Guarded Remediation

A finding is not mutation approval. Remediation is a conditional transition against a particular resource generation; the triggering snapshot may be obsolete.

## Execution gates

| Gate | Required decision |
|---|---|
| Ownership | Identify accountable service owner, change authority, executor, exact asset scope, and approved action |
| Current state | Re-read resource identity/generation and vulnerable condition immediately before mutation; changed state requires replanning |
| Retry identity | Persist an operation ID with target, desired state, and parameters; reuse it only for the same intent |
| Reversibility | Record known-good artifact/configuration and tested recovery path; irreversible changes need explicit review |
| Blast radius | Choose representative canary, observation interval, health/SLO thresholds, and stop conditions before execution |

## Recipe

1. Record finding evidence, observation time, target identity, owner, approved parameters, and rollback reference. Missing ownership or approval blocks execution.
2. Revalidate live state. Already fixed means no-op; changed identity/parameters means stop. Use provider-conditional mutation or equivalent atomic preconditions against external writers; workflow leases protect only against cooperating writers.
3. Use the provider's documented idempotency mechanism. Store request parameters with the key; reject mismatches. For an uncertain timeout, reconcile remote state before retrying an action without safe replay semantics.
4. Run the bounded canary; compare against an unaffected control and absolute health limits. Missing traffic or telemetry means inconclusive, not pass. Expand only after sufficient representative observations.
5. Stop expansion on failure; perform only authorized recovery, then revalidate vulnerability state. Pass deployment evidence to `rbvm-verified-closure`.

Example: a stale finding requests disabling public access, but the live resource is already private. Record a no-op; do not restart its workload merely because the queue delivered the event twice.

Sources: AWS Config auto-remediation documentation; AWS Builders' Library, Malcolm Featonby; Google SRE Workbook, chapter 16 (2018). Reviewed 2026-10-10; source mapping and scenarios: [SOURCES.md](SOURCES.md).

## Pitfalls

- Reusing a key after changing the patch target conflates distinct intent.
- Updating only live infrastructure lets its declarative controller undo the fix.
- Rolling back to a vulnerable release restores availability while reopening security risk.
- Treating emergency priority as permission to skip identity, approval, or recovery checks.
