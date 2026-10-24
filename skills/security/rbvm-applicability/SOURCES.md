# Applicability: sources and worked evidence

Initially reviewed 2026-10-10; revision and invalidation guidance reviewed 2026-10-24. Examples are original synthetic cases, not adjudications of real CVEs or package releases. No publication date is inferred from the review date.

## Primary evidence and versions

- [OpenSSF OSV schema](https://ossf.github.io/osv-schema/), **v1.9.2, October 13, 2026**, observed October 24; the initial review used v1.9.1. **modified** orders revisions of one ID; **withdrawn** timestamps that entry's withdrawal. **aliases**, **upstream**, and **related** describe different graph edges. **affected ranges/events**, **Evaluation**, and **last_affected vs fixed** support matching boundaries. These lifecycle semantics are not claimed as new v1.9.2 features. [Release reference](https://github.com/ossf/osv-schema/releases/tag/v1.9.2).
- [OpenVEX specification v0.2.0](https://github.com/openvex/spec/blob/v0.2.0/OPENVEX-SPEC.md), **Statements**, **Product Data Structure**, **Status Labels**, **Status Justifications**. Statements bind a vulnerability/status to products; `fixed` identifies fixed versions, while `under_investigation` leaves impact unresolved. The detailed field requirements allow justification or impact statement for `not_affected`; machine-readable justification is preferred. Publisher trust, acceptance gates, and reassessment deadlines in this skill are local policy, not assertions that a syntactically valid document is trustworthy.
- [Red Hat: Backporting Security Fixes](https://access.redhat.com/security/updates/backporting), unversioned vendor guidance. **Explaining Common Release-Numbering Confusion** explains why upstream-only version checks can produce false positives and why vendor advisories/machine-readable information matter. This does not establish patch state for an arbitrary installed package.
- OpenVEX v0.2.0 **Document Struct Fields**, **Statement Fields**, **Data Inheritance**, and **Updating Statements with Inherited Data** additionally support document versioning and effective timestamps. Preserve an unchanged statement's original time when a containing document is updated; `last_updated` is not a replacement for statement timestamp inheritance. Neither a numeric document version nor a more recent issuer timestamp establishes cross-publisher authority.
- [Python 3.12 datetime documentation](https://docs.python.org/3.12/library/datetime.html#datetime.datetime.fromisoformat) supports the offline example's timezone-aware instant comparisons. Documentation displayed 3.12.15; local execution used Python 3.12.14. `fromisoformat` accepts more formats than this fixture's deliberately restricted profile.

## Original revision/invalidation design

The schema defines representation, not this organization's suppression policy. This skill adds an intentionally conservative dependency-invalidation workflow: preserve immutable evidence and reviewed authority bindings, select revisions within an ID, invalidate downstream conclusions after relevant evidence changes, and route uncertain cases to review. Keeping a withdrawn entry as a historical tombstone prevents delayed delivery from restoring its old active state. A confirmed withdrawal does not withdraw every other entry connected through aliases, imply a patch was installed, or authorize enforcement changes.

Equal-revision divergence, unaccepted sources, unusable timestamps, failed collection, and stale inputs trigger reassessment under **local policy**, not a schema-prescribed universal outcome. Trust-policy changes also invalidate decisions; schemas do not authenticate an issuer. Reassess aliases and per-package scope from the remaining current records instead of globally deleting a vulnerability or manufacturing a `not_affected` result. A changed source snapshot can require review even if the eventual verdict is unchanged.

Authority/conflict resolution must precede automatic VEX use. This workflow does not invent a universal last-writer-wins order across documents, issuers, advisory IDs, or product scopes. Keep contradictory statements with provenance until an authorized reviewer resolves them. Retrieval order and `last_updated` must not masquerade as applicability time.

## Decision record (original local template)

Preserve: asset/artifact and configuration identity; package instance/coordinates and original version; advisory ID, source bytes/digest, `modified`, withdrawal and relationship metadata; candidate ranges; ecosystem comparison result; vendor evidence URL and applicable distribution/release; VEX issuer, document/version, effective statement time, product scope, status and rationale; authority-policy revision; collection coverage/freshness; contradictory evidence; final state; reviewer; assessed time; reassessment triggers. An unsupported comparison or unresolved conflict produces `under_investigation`, not `not_affected`.

## Worked scenarios and counterexamples

1. **Boundary:** imaginary package `widget` has interval `[2.4.0,2.4.3)`. Installed 2.4.2 matches; 2.4.3 does not. Replacing the end event with `last_affected=2.4.3` includes 2.4.3. Never infer a particular next release contains a fix merely from the last observed affected release.
2. **Multiple evidence paths:** imaginary advisory explicitly lists 1.8.0 and includes a 2.x range. A consumer that checks only ranges loses the explicitly listed release. Retain both paths in the explanation.
3. **Backport:** synthetic installed `widget-2.4.1-9.vendor` appears old upstream. A vendor advisory identifies that exact distribution stream and release as fixed. Conclude fixed only after the installed build matches that evidence; `2.4.1-8.vendor` cannot inherit it.
4. **Cross-build VEX:** publisher signs `not_affected` for digest A because vulnerable code was excluded. Deployment is digest B with a different build flag. Do not suppress B. Signature validity establishes neither scope equality nor the correctness of the underlying claim.
5. **Runtime non-observation:** five minutes of tracing do not execute the vulnerable handler. This is sampling evidence, not proof the handler can never execute. Investigate configuration and call paths; preserve unknown status until the claim is supported.
6. **Advisory bundle:** one downstream update addresses three upstream IDs. Do not equate the entire bundle with each upstream vulnerability or propagate one component's clean result to all components.
7. **Stale decision:** yesterday's reviewed verdict binds to advisory A revision 1. Revision 2 expands affected versions. A cache keyed only by A returns yesterday's result; the dependency-bound check instead requests new adjudication. It does not itself decide that a particular deployed artifact is affected.
8. **Withdrawn sibling:** A is withdrawn but equivalent entry B remains active and lists the installed version. Retain B's evidence and reassess; A's withdrawal is not a global clean verdict. A delayed A revision 1 cannot replace retained revision 2's withdrawal.
9. **VEX reversal:** the accepted current document changes from `not_affected` to `under_investigation`. Invalidate the old decision. Preserve scope and old decision history; do not call uncertainty a repair or introduce an automatic scanner suppression change.
10. **Inherited time:** adding a new statement updates a document timestamp. Explicitly retain the older statement's former inherited timestamp, or consumers may incorrectly treat the old claim as newly established. A document version of 999 from another issuer does not win over version 2 by magnitude.

## Validation scope

Run from the repository root:

```bash
python3 skills/security/rbvm-applicability/reproduce.py
python3 -O skills/security/rbvm-applicability/reproduce.py
```

Fifteen original standard-library test methods pass in both modes on Python 3.12.14. They cover a failing CVE-only cache baseline, stable binding, expanded affected versions, out-of-order replay, retained withdrawal, independent alias evidence, equal-revision divergence, missing/stale/incomplete retrieval, timestamps, authority mismatch, artifact/configuration/package-instance drift, VEX status changes, independent document versions, and timestamp inheritance.

The example selects synthetic OSV revisions and compares reviewed dependency bindings. `eligible_for_reviewed_reuse` is **not** an applicability verdict, suppression instruction, authorization, or closure proof. VEX dictionaries are illustrative normalized objects, not schema-valid complete OpenVEX documents. Current-document selection, schema validation, cryptographic identity, rationale quality, publisher authority, product matching, conflict adjudication, completeness and freshness truth are external preconditions; supplied labels do not prove them. The helper does not perform VEX supersession or choose a winner across documents. Hashing all selected evidence is conservative and may request review for harmless content changes.

The fixture's timestamp subset allows whole seconds with Z or minute offsets (OSV rows require Z). It does not support fractional/leap seconds or implement the full RFC3339 grammar; unsupported inputs require review, not a claim of schema invalidity. Zero future-clock tolerance and rejecting withdrawal later than record modification are fixture policy. It retains the supplied history; persistence, concurrency, source discovery, and crash recovery are untested.

No home-grown package comparator is shipped: tuple ordering would omit prereleases, epochs, distribution revisions and Git branching. The original interval/backport/reachability scenarios remain review-only. No production scanner, real advisory adjudication, signatures, package installation, deployment, live feed ingestion or model benchmark was executed. No false-positive/false-negative performance claim is made. The repository's README references `test.sh`, but that file is absent; no repository-wide suite pass is claimed.
