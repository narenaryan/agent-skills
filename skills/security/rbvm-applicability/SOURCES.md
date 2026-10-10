# Applicability: sources and worked evidence

Reviewed 2026-10-10. Examples are original synthetic cases, not adjudications of real CVEs or package releases.

## Primary evidence and versions

- [OpenSSF OSV schema](https://ossf.github.io/osv-schema/), **v1.9.1, September 24, 2026**. Sections **aliases**, **upstream**, **related**, **affected ranges/events**, **Evaluation**, and **last_affected vs fixed** support interval boundaries and distinct relationship semantics. Explicit version lists and ranges are alternative matching paths. Use the declared ecosystem or Git semantics, not a universal comparator. Retain record revision and withdrawal metadata.
- [OpenVEX specification v0.2.0](https://github.com/openvex/spec/blob/v0.2.0/OPENVEX-SPEC.md), **Statements**, **Product Data Structure**, **Status Labels**, **Status Justifications**. Statements bind a vulnerability/status to products; `fixed` identifies fixed versions, while `under_investigation` leaves impact unresolved. The detailed field requirements allow justification or impact statement for `not_affected`; machine-readable justification is preferred. Publisher trust, acceptance gates, and reassessment deadlines in this skill are local policy, not assertions that a syntactically valid document is trustworthy.
- [Red Hat: Backporting Security Fixes](https://access.redhat.com/security/updates/backporting), unversioned vendor guidance. **Explaining Common Release-Numbering Confusion** explains why upstream-only version checks can produce false positives and why vendor advisories/machine-readable information matter. This does not establish patch state for an arbitrary installed package.

## Decision record (original local template)

Preserve: asset/artifact identity; package coordinates and original version; advisory ID/revision; candidate ranges; ecosystem comparison result; vendor evidence URL and applicable distribution/release; VEX issuer, document/version, product scope, status, rationale; contradictory evidence; final state; reviewer; assessed time; reassessment triggers. An unsupported comparison or unresolved conflict produces `under_investigation`, not `not_affected`.

## Worked scenarios and counterexamples

1. **Boundary:** imaginary package `widget` has interval `[2.4.0,2.4.3)`. Installed 2.4.2 matches; 2.4.3 does not. Replacing the end event with `last_affected=2.4.3` includes 2.4.3. Never infer a particular next release contains a fix merely from the last observed affected release.
2. **Multiple evidence paths:** imaginary advisory explicitly lists 1.8.0 and includes a 2.x range. A consumer that checks only ranges loses the explicitly listed release. Retain both paths in the explanation.
3. **Backport:** synthetic installed `widget-2.4.1-9.vendor` appears old upstream. A vendor advisory identifies that exact distribution stream and release as fixed. Conclude fixed only after the installed build matches that evidence; `2.4.1-8.vendor` cannot inherit it.
4. **Cross-build VEX:** publisher signs `not_affected` for digest A because vulnerable code was excluded. Deployment is digest B with a different build flag. Do not suppress B. Signature validity establishes neither scope equality nor the correctness of the underlying claim.
5. **Runtime non-observation:** five minutes of tracing do not execute the vulnerable handler. This is sampling evidence, not proof the handler can never execute. Investigate configuration and call paths; preserve unknown status until the claim is supported.
6. **Advisory bundle:** one downstream update addresses three upstream IDs. Do not equate the entire bundle with each upstream vulnerability or propagate one component's clean result to all components.

## Validation scope

Use these cases as review fixtures against the chosen ecosystem implementation. No home-grown comparator is shipped: a small stdlib tuple comparator would misleadingly omit prereleases, epochs, distribution revisions, and Git branching. No scanner was executed and no false-positive/false-negative performance claim is made.
