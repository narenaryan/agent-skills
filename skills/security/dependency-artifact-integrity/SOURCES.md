# Dependency artifact integrity: provenance and validation

Reviewed 2026-10-20. This is original synthesis, not a reproduction of a vendor benchmark or a universal package-manager ranking.

## Sources and claim boundaries

- Keegan Ryan, [Package managers have an integrity problem](https://blog.trailofbits.com/2026/10/14/package-managers-have-an-integrity-problem/), published 2026-10-14. Previously identified as a lead in the October 18 scan; deep-reviewed October 20. The experiment considers a compromised package-serving endpoint, not compromised signing secrets. Each tested manager used a particular version/package/platform/configuration. We retain the distinction between resolution, archive checks, and independent trust, not its comparative rankings. We did not run its Docker/mitmproxy harness or install a CA.
- [pip secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/), documentation observed as 26.2.1, publication/update date not stated. Local expected hashes, graph-wide hash mode, binary-only restriction, multiple allowed artifacts, and index hashes' weaker trust boundary. pip 26.2 adds `--no-require-hashes`; the recipe explicitly requests enforcement rather than relying on implicit activation.
- [pip download](https://pip.pypa.io/en/stable/cli/pip_download/), documentation observed as 26.2.1, date not stated. Collects distributions without installation; `--no-index`, local `--find-links`, and binary-only selection bound the fixture. The command is not generally safe from build hooks when source distributions are allowed.
- [pip configuration](https://pip.pypa.io/en/stable/topics/configuration/), documentation observed as 26.2.1, date not stated. The fixture removes inherited `PIP_*` variables and sets `PIP_CONFIG_FILE` to the platform null device so external configuration cannot change the local-only experiment. It does not modify configuration files or credentials.
- [Dart pub get](https://dart.dev/tools/pub/cmd/pub-get#enforce-lockfile), docs state Dart 3.13.3 and page update 2026-05-15. Supports the hosted-package mismatch/invalid-resolution rejection claim only. Dart execution was not tested.
- [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/), observed v11.21.0 documentation, date not stated. Requires a lock, rejects manifest disagreement, does not rewrite lockfiles, and removes existing node_modules. It is not offered here as a read-only test command.
- [npm registry signature verification](https://docs.npmjs.com/verifying-registry-signatures/), page last edited 2023-10-23, reviewed 2026-10-20. Documents `npm audit signatures` as a separate step for downloaded dependencies; registry support and verification coverage matter. Neither npm signature verification nor attestation policy was runtime-tested.

The step requiring a reviewed baseline and the stop/investigate workflow are conservative operational design recommendations, not a guarantee or authority to alter security controls. Hashes show equality to approved bytes, not publisher honesty, absence of malware, or vulnerability remediation. Use existing RBVM applicability and priority skills for that separate decision.

## Reproduction

Run `python3 skills/security/dependency-artifact-integrity/reproduce.py` with an already available pip. Observed on Python 3.12.14 / pip 26.2.1 on 2026-10-20:

| Case | Observed |
|---|---|
| Original wheel, trusted hash | Accepted exact bytes |
| Parent plus transitive wheel, complete hashes | Accepted |
| Parent hashed, transitive wheel unhashed | Rejected for missing hash |
| Direct requirement without hash, explicit enforcement | Rejected for missing hash |
| Changed inert payload, same name/version, no expected hash | Accepted changed bytes (weak baseline) |
| Same changed payload with original trusted hash | Rejected for mismatch |

Every case checks that its requirements file is unchanged. Rejected cases must save no wheels; accepted cases must save the expected leaf bytes. Wheels contain inert text and distribution metadata only; their internal RECORD hashes are consistent in both original and changed variants. This isolates the external trusted-hash check rather than relying on malformed packages. All files are temporary and cleaned up. No network requests, package installation, package import, fetched software execution, source build, trust-store modification, or repository CI was needed.

Exploratory limit: in the local `--find-links` setup, pip accepted `fixture_leaf>=1.0` when its sole matching wheel had the supplied hash, despite the secure-installs page describing pinning as required. This branch does not claim to have demonstrated rejection of unpinned specifications. Pinning remains the recipe's reproducibility requirement; validate actual resolver behavior for the deployed version/source type.

This is a six-case pip download integration fixture, not validation of all package managers, caches, signatures, installed environments, registry compromise, platform variants, or build reproducibility. README references `test.sh`, but it is absent from the inspected base. No full repository suite or CI result is claimed.
