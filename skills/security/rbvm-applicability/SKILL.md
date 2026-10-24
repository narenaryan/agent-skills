---
name: rbvm-applicability
description: Use when package matches conflict with backports, OSV revisions or withdrawals, scoped VEX assertions, or reachability evidence, especially when an old suppression survives changed advisory data.
---

# RBVM Applicability

Applicability is a versioned conclusion about a build and configuration, not a permanent property of a CVE. Its evidence dependencies can change without a deployment. Withdrawal invalidates a source record; it does not install a fix.

## Interpret without flattening

| Evidence | Semantics |
|---|---|
| OSV ranges | `introduced` inclusive; `fixed` exclusive; `last_affected` inclusive |
| OSV `limit` | Exclusive scope boundary, not proof of a fix |
| OSV identity | `aliases` means equivalent vulnerability; `upstream` and `related` are different relationships |
| OSV revision | For the same `id`, later `modified` wins; retrieval time is not revision order |
| OSV `withdrawn` | Entry withdrawn at that time; retain history and reassess other evidence |
| Vendor backport | Compare full distribution package release and advisory, not upstream version alone |
| OpenVEX time | Statement timestamp overrides document timestamp, then encapsulating timestamp |
| OpenVEX version | Revision within that document, not a ranking across publishers/documents |

## Recipe

1. Resolve ecosystem, package instance/version, distribution/release, architecture, digest, and configuration. Preserve source bytes, issuer, IDs, revision metadata, collection time, and accepted authority scope.
2. Reconcile revisions before matching. Compare OSV `modified` only for the same ID from accepted sources. Quarantine divergent equal-revision payloads and invalid/future timestamps under local clock policy. Keep withdrawal records so delayed older deliveries cannot resurrect them. A failed fetch or missing search result is not a withdrawal.
3. Evaluate explicit versions OR applicable OSV ranges using ecosystem ordering; Git ranges require repository/commit ancestry. Unsupported comparisons remain unknown. Check exact vendor patch evidence: an older upstream version may contain a backport; possibility is not proof.
4. Validate VEX authority, product/component/build scope, effective statement time, revision, and rationale. `not_affected` needs justification or impact statement; free-text-only reasoning needs review. Preserve untouched statements' original inherited time when updating documents. Do not let a newer unrelated document or publisher silently resolve contradictory claims. `under_investigation` cannot suppress.
5. Bind each reviewed verdict to artifact/configuration and every relied-on advisory/assertion snapshot. Changed ranges, relationships, withdrawal, VEX status, trust policy, or scope invalidate dependent conclusions. Recompute from remaining evidence; do not erase alias siblings or promote unknown to clean. Missing/stale/conflicting inputs enter reassessment with an owner, not silent continued suppression.
6. Save affected/not-affected/fixed/under-investigation disposition, reasons, reviewer, and next review trigger separately from enforcement. No evidence refresh grants permission to change suppressions, patch, deploy, or close tickets.

Counterexample: advisory A is withdrawn while alias B still identifies the installed package as affected. Retire A's claim, not the vulnerability globally. A newer accepted VEX `under_investigation` also defeats reuse of yesterday's `not_affected` decision; it proves neither affectedness nor a repair.

Run `python3 skills/security/rbvm-applicability/reproduce.py` for original offline revision/invalidation scenarios, not a scanner or production evaluator.

Sources: [OSV v1.9.2](https://ossf.github.io/osv-schema/), [OpenVEX v0.2.0](https://github.com/openvex/spec/blob/v0.2.0/OPENVEX-SPEC.md), [Red Hat](https://access.redhat.com/security/updates/backporting), reviewed 2026-10-24. Reassessment, trust and enforcement gates are local policy; [SOURCES.md](SOURCES.md).

## Pitfalls

- SemVer ordering is invalid for arbitrary RPM/Debian versions.
- A backport possibility is not evidence that this installed build is patched.
- Alias deduplication must not erase per-package applicability or bundle unrelated fixes.
- Runtime non-observation does not prove unreachable code.
- A fresh download cannot rejuvenate old evidence or establish publisher authority.
