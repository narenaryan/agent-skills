# Container patch evidence: provenance and validation

Reviewed 2026-10-21. This is an in-place refinement of the existing patching skill,
not a new scanner, risk model, or production authorization. The original skill's
20% size-increase ceiling and `-cve-patched` suffix are retained as repository-local policy,
not attributed to a security standard. No source registry expansion is included.

## Primary references

| Source | Publication/version information | Supports; limits |
|---|---|---|
| [Trivy vulnerability detection](https://trivy.dev/docs/latest/scanner/vulnerability/) | Rolling documentation; no publication/update date asserted | Package installation provenance selects vendor versus ecosystem advisories; distro backports differ from upstream versions. Vendor-advisory delays and unsupported software limit detection. |
| [Trivy filtering](https://trivy.dev/docs/latest/configuration/filtering/) | Rolling documentation | Severity, status, ignore and VEX filters affect visibility. `--ignore-unfixed` also hides statuses such as deferred fixes or end-of-life. A filtered result is not a complete vulnerability inventory. |
| [Trivy configuration](https://trivy.dev/docs/latest/configuration/) | Rolling documentation | Flags, environment variables and configuration files affect effective options; JSON output does not neutralize inherited filters. Inspect the actual run context. |
| [Trivy reporting](https://trivy.dev/docs/latest/configuration/reporting/) | Rolling documentation; JSON example uses schema 2 | JSON retains structured artifact/component data; `trivy convert` makes presentation views from collected JSON. Report schemas and optional fields must be validated for the actual installed version. |
| [Trivy image CLI](https://trivy.dev/docs/latest/references/configuration/cli/trivy_image/) and [image target](https://trivy.dev/docs/latest/target/container_image/) | Rolling documentation; [v0.76.0 release](https://github.com/aquasecurity/trivy/releases/tag/v0.76.0) published 2026-10-14 | Documents `--scanners`, `--pkg-types`, `--list-all-pkgs`, `--platform`, JSON output and explicit image selection. The release was observed, not installed; rolling docs are not an immutable v0.76 contract. Check provisioned-tool help before use. |
| [Trivy exit behavior](https://trivy.dev/docs/latest/configuration/others/) | Rolling documentation | Default zero exit code permits findings. EOL OS detection has separate handling; EOL can make vulnerability detection insufficient. Successful execution is not complete coverage. |
| [Trivy database handling](https://trivy.dev/docs/latest/configuration/db/) | Rolling documentation | Vulnerability and Java databases update separately. Controlled snapshots support comparison; do not freeze an old database indefinitely or claim freshness from cache access time. |
| [Docker build best practices](https://docs.docker.com/build/building/best-practices/) | Rolling documentation; no publication/update date asserted | Tags are mutable; digest pinning makes base selection explicit but requires deliberate updates. Combine APT update/install and list cleanup in a layer. Rebuilding from a new base is a candidate change, not proof of remediation. |
| [Debian trixie apt-get manual](https://manpages.debian.org/trixie/apt/apt-get.8.en.html) | APT 3.0.3; manual date 2024-11-18; source updated 2025-06-24 (HTML conversion date is not source publication) | Named installation can bring dependency changes; explicit version selection may downgrade. `--only-upgrade` is not a promise that the whole solver transaction changes only requested names. Simulation disables locking; non-root access/configuration can affect fidelity. |

## Original decision contract

The skill synthesizes a conservative comparison rule: use equivalent detector,
database, platform, coverage and policy evidence, and separately demonstrate the
reviewed component transition. These are local evidence requirements, not a
claim that Trivy emits a complete, trusted comparison envelope automatically.
If detection conditions change, rescan both preserved artifacts under the new
conditions rather than interpreting an incomparable pair as a patch result.
Freshness and applicability remain separate questions; an old but identical
snapshot does not satisfy a current release gate by itself.

Run from the repository root:

```bash
python3 skills/security/container-image-patching/fixture.py
```

The standard-library fixture uses invented normalized records, not real Trivy
JSON. Fourteen cases contrast a weak empty-findings oracle with artifact,
platform, detector/configuration, completion, coverage and component checks.
They cover a reviewed vendor-release transition without an upstream-version
change, hidden findings, changed database/scanner/platform, wrong image, failed
scan, unreviewed coverage, unchanged or missing package, residual finding,
duplicate identity, missing baseline finding, and an independently vulnerable
bundled copy. `approved_release` is supplied as previously reviewed evidence;
the fixture does not discover fixes, compare versions, or verify that authority.
Removal requires separate evidence and is deliberately not accepted by this
upgrade-only fixture. Candidate upgrade evidence is not whole-image safety,
compatibility, deployed-state verification, or permission to close a ticket.

## Validation limits

Executed on Python 3.12.14: all 14 synthetic cases pass, including the deliberate
false-confidence baseline. No external dependencies, network, subprocesses,
package installation, container execution, image build, or scanner invocation
is involved in the fixture.

Docker and Trivy were unavailable. The CLI recipe was source-reviewed and shell
syntax-checked, not runtime-tested. APT simulation/solver behavior, live
registries, scanner JSON parsing, package remediation, application health,
multi-platform builds and deployment/rollback were not tested. The repository
README mentions `test.sh`, but that file is absent from base main; no full-suite
or CI pass is claimed.
