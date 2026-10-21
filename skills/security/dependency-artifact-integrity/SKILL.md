---
name: dependency-artifact-integrity
description: Use when a lockfile, checksum, or package signature is treated as proof of trustworthy dependencies, a hash mismatch tempts automatic lock regeneration, or CI must reject substituted package bytes before execution.
---

# Dependency Artifact Integrity

Resolution, byte integrity, signer identity, and vulnerability status are separate contracts. A checksum from the same compromised endpoint cannot independently authenticate an artifact.

## Verification questions

| Claim | Evidence needed |
|---|---|
| Same dependency resolution | Frozen manifest/lock agreement, including transitive dependencies |
| Same artifact bytes | Trusted expected archive digest, enforced on mismatch |
| Expected publisher/build | Verified signature/attestation bound to expected identity and artifact |
| Acceptable vulnerability risk | Separate applicability/risk decision; authentic packages can be vulnerable |

## Recipe

1. Record manager version, platform, source types, configuration, and execution paths. Identify checksum scope: archive, manifest, tree, or metadata. A “checksum” field need not authenticate downloaded bytes.
2. Separate controlled dependency updates from consumption. Review expected hashes/trust metadata before consumption; regeneration after a mismatch merely blesses new bytes. Initial acquisition remains a trust decision.
3. Choose documented enforcement, not a similarly named option. For pip, explicitly require hashes and pin the complete graph, including approved wheel variants. Dart's `--enforce-lockfile` rejects changed hosted-package hashes. npm's `ci` freezes lock resolution, while registry-signature verification is a separate operation. Do not extrapolate across managers.
4. Prove the gate in a disposable workspace: approved bytes pass; changed bytes at the same name/version fail; missing direct/transitive evidence fails; trust files remain unchanged. Use inert local artifacts and existing tools. Disable source builds/lifecycle execution; never install interception CAs or weaken transport verification.
5. On mismatch, retain hashes/source context, stop promotion, and investigate corruption, repackaging, or compromise. Do not auto-refresh hashes, suppress verification, or declare remediation. Rollout and exceptions require approval; reuse [security-gate-rollout](../security-gate-rollout/SKILL.md).

Offline demonstration from repository root:

```bash
python3 skills/security/dependency-artifact-integrity/reproduce.py
```

It uses local inert wheels and pip download: unhashed acquisition accepts substituted bytes; hash enforcement rejects them. No package is installed/executed. This tests neither signatures nor other managers.

Sources: [Trail of Bits](https://blog.trailofbits.com/2026/10/14/package-managers-have-an-integrity-problem/) and official manager documentation; versions, validation, and limits in [SOURCES.md](SOURCES.md).

## Pitfalls

- Zero verified packages establishes no coverage.
- Caches can hide a broken gate; test with fresh destinations and controlled caches.
- Hashes cannot prevent malicious content already accepted into the baseline.
- An application lockfile does not automatically constrain its library's downstream consumers.
