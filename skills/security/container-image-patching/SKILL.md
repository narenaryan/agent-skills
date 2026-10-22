---
name: container-image-patching
description: Use when patching a Docker or OCI image, a Trivy finding disappears after rebuilding, or before/after scan results disagree about whether a package was fixed.
---

# Container Image Patching

A disappearing finding is not a demonstrated patch. Compare immutable artifacts under equivalent detection conditions, then prove the installed component changed.

## Evidence contract

| Preserve | Why |
|---|---|
| Manifest digests and platform | Tags and other architectures are not the tested artifact |
| Scanner version, database identity/time, effective configuration | Detector changes can create an apparent fix |
| Target/path, package source, installed release, advisory | One CVE can affect multiple independently installed copies |
| Logs, inventory, exclusions and suppressions | Empty findings do not establish complete coverage |

## Recipe

1. Confirm owner, approved image/build environment, scan/build permissions, and rollback. Use provisioned tooling; missing tools require approval, not automatic installation. Builds execute Dockerfile instructions; image scanning may retrieve images/databases. Publishing or deploying needs separate authority.
2. Resolve the source digest and platform; preserve index-to-platform-manifest mapping for multi-platform images. For local builds, retain the immutable local image ID and build provenance until a manifest exists. Record size using the same measurement method before/after.
3. Audit configuration, environment, ignore files, VEX and exclusions before collection; JSON still honors filters. Retain these identities and package inventory, then create presentation views. In an approved environment with exported digest reference and platform:

```bash
: "${IMAGE_REF:?Set the approved digest reference}"
: "${PLATFORM:?Set the approved OS/architecture}"
trivy image --scanners vuln --pkg-types os,library --list-all-pkgs \
  --platform "$PLATFORM" --format json --output before.json \
  "$IMAGE_REF" 2>before.log && \
trivy convert --format table --severity HIGH,CRITICAL before.json
```

4. Route each component by installation provenance: distro-managed packages use matching vendor releases/backports; language dependencies need their dependency/build workflow. Preserve unfixed findings. HIGH/CRITICAL is a view, not prioritization policy; use [RBVM decisions](../rbvm-priority-decisions/SKILL.md).
5. Select reviewed fixed releases. For Debian/Ubuntu, `apt-get install --only-upgrade` targets installed packages, but dependency resolution still needs inspection. Simulate in the equivalent build context; reject unapproved removals, downgrades, or collateral changes. Version selection can downgrade. Revalidate before applying; simulation is not a locked transaction. Keep update/install/list-cleanup in one Dockerfile layer; a supported base-image refresh is an alternative requiring its own review.
6. Scan the candidate with equivalent coverage/configuration and database snapshot; if these changed, rescan both immutable artifacts. Match component instances, not CVE totals. Verify the installed release or verified removal, remaining/new findings, and runtime compatibility tests. Missing/unsupported/EOL coverage or scan failure stays unknown. Route deployment evidence through [verified closure](../rbvm-verified-closure/SKILL.md).
7. Retain the existing ≤20% size-increase ceiling and `-cve-patched` naming unless the owner approves different policy; neither proves safety. Report digests, package changes, evidence differences, residual findings, tests, and limits.

[Sources and synthetic counterexamples](SOURCES.md); documentation reviewed 2026-10-21. Trivy/Docker commands were not runtime-tested.

## Pitfalls

- Trivy normally exits zero even with findings; process success is not a clean verdict.
- Severity/unfixed/suppression filters can erase evidence without changing installed bytes.
- Digest pinning prevents silent drift but also requires deliberate security updates.
