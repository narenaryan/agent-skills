---
name: rbvm-asset-evidence
description: Use when scanner findings must be joined to ephemeral assets, duplicate hosts, image tags, ownership, or exposure evidence with conflicting timestamps or stale inventory.
---

# RBVM Asset Evidence

An asset is an incarnation, an artifact is content, and an observation is a time-bounded claim. Never collapse those identities into an IP address, tag, or hostname.

## Join contract

| Entity | Preserve | Reject as sole identity |
|---|---|---|
| Runtime instance | Tenant/account, region/cluster, immutable provider ID or Kubernetes UID | IP, display name |
| Artifact | Digest, descriptor media type, platform; component coordinates | Mutable image tag |
| Observation | Source, collection time, ingestion time, coverage, raw evidence reference | Latest database update time |
| Finding | Instance/artifact, component, vulnerability, detector, observation | CVE alone |

## Recipe

1. Normalize identifiers without discarding original values. Keep instance-to-artifact and artifact-to-component edges separately; one image can serve many workloads.
2. Reconcile only strong identifiers within their authority scope. Queue ambiguous matches; do not merge on matching hostnames. Record merge evidence and reversible lineage.
3. Define policy-owned freshness budgets per evidence class. Evaluate collection age, not ingestion age; reject future timestamps beyond approved clock tolerance. Recollect after deployment, routing, ownership, or configuration changes.
4. Preserve contradictory observations with provenance. Missing authentication, excluded paths, partial inventories, and failed collectors mean unknown coverage, not absence.
5. Emit affected-instance counts, owner routing, and an explicit unknown/stale queue. Decide applicability with `rbvm-applicability` only after identity is bounded.

Example: pod `checkout` is recreated with UID B after UID A was scanned. Its unchanged name and IP do not transfer A's clean result. Link B to its observed image digest, retain A historically, and request B's runtime/configuration evidence.

Run the synthetic freshness contract from the repository root:

```bash
python3 skills/security/rbvm-asset-evidence/fixture.py
```

Sources: [Kubernetes object identity](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/) and [OCI descriptor v1.1.1](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md), reviewed 2026-10-10. Freshness budgets and reconciliation gates are local policy, not standards; details in [SOURCES.md](SOURCES.md).

## Pitfalls

- Reused IPs can transfer remediation evidence to the wrong machine.
- An image-index digest and platform-manifest digest identify different objects; retain their relationship.
- A fresh ingestion timestamp cannot rejuvenate an old scan.
- Collector silence cannot prove retirement or successful remediation.
