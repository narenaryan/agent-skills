---
name: rbvm-applicability
description: Use when package-version matches conflict with vendor backports, OSV ranges, VEX assertions, runtime reachability, or vulnerability aliases and a finding may be suppressed incorrectly.
---

# RBVM Applicability

Applicability is a scoped claim about a particular build and configuration. Separate upstream advisory matching, downstream patch state, and deployer evidence; uncertainty remains actionable uncertainty.

## Interpret without flattening

| Evidence | Semantics |
|---|---|
| OSV ranges | `introduced` inclusive; `fixed` exclusive; `last_affected` inclusive |
| OSV `limit` | Exclusive scope boundary, not proof of a fix |
| OSV identity | `aliases` means equivalent vulnerability; `upstream` and `related` are different relationships |
| Vendor backport | Compare full distribution package release and advisory, not upstream version alone |
| VEX | Status applies only to identified product/component scope |

## Recipe

1. Resolve ecosystem, package, installed version, distribution/release, architecture, build digest, and configuration. Preserve advisory IDs, revisions, withdrawal state, and provenance.
2. Evaluate OSV explicit versions OR applicable ranges with the ecosystem comparator. Git ranges require repository/commit ancestry; never compare commit hashes lexically. Unsupported ordering yields unknown.
3. Check the distribution vendor's advisory or machine-readable patch evidence. A lower upstream version may include the fix; a newer-looking custom build may not.
4. Validate VEX publisher authority, product/build match, revision, and supporting rationale. OpenVEX `not_affected` requires justification or impact statement; require review for free-text-only reasoning. `under_investigation` must not suppress.
5. Record affected, not affected, fixed, or under investigation with evidence, reviewer, and reassessment triggers. Runtime non-observation alone cannot establish unreachable code. Reassess when build, configuration, advisory, or assertion changes.

Example: synthetic advisory affects `[2.4.0,2.4.3)`. Version 2.4.3 is outside that range. A distro's 2.4.1 release can also be fixed, but only matching vendor patch evidence supports that conclusion. A VEX statement for another digest does not.

Sources: [OSV v1.9.1](https://ossf.github.io/osv-schema/), [OpenVEX v0.2.0](https://github.com/openvex/spec/blob/v0.2.0/OPENVEX-SPEC.md), [Red Hat backporting](https://access.redhat.com/security/updates/backporting), reviewed 2026-10-10. Trust/review gates are local policy; see [SOURCES.md](SOURCES.md).

## Pitfalls

- SemVer ordering is invalid for arbitrary RPM/Debian versions.
- A backport possibility is not evidence that this installed build is patched.
- Alias deduplication must not erase per-package applicability or bundle unrelated fixes.
- A suppression is conditional evidence, never permanent immunity for a CVE.
