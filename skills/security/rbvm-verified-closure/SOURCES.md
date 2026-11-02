# Source ledger and verification examples

Core reviewed 2026-10-12; key-access extension reviewed 2026-10-30. The closure join and post-close reopen procedure are original implementation patterns. NIST does not require a particular scanner, schema, digest field, finding-ID policy, reopen workflow, monitoring interval, or evidence-retention period.

## Primary evidence

- [NIST SP 800-40 Rev. 4](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-40r4.pdf), Murugiah Souppaya and Karen Scarfone, April 2022. Section 2.2(d) says to continuously monitor the risk response; §2.3.4 says to monitor that deployed patches remain installed, citing patch removal, vulnerable software restored from backup, and factory reset. This supports a post-close drift watch. The local risk-tiered cadence, same-finding reopen, and denominator handling are implementation choices, not NIST requirements.
- [Kubernetes: Images](https://kubernetes.io/docs/concepts/containers/images/), continuously updated documentation, sections “Image names” and “Multi-architecture images with image indexes.” Tags may move; content digests are immutable. An image index can refer to architecture-specific manifests. This motivates identity-aware comparison instead of a raw tag match or an unqualified digest-string comparison.

## Original worked scenarios

1. A clean candidate image has digest B; every live pod still runs digest A. Result: build evidence exists, deployment evidence fails. Do not close.
2. Eleven of twelve affected pods run B. The twelfth is unreachable. Result: eleven verified, one unknown. Report the denominator and keep the remaining finding open.
3. All pods run B, but the second scanner run lost credentials and emitted no findings. Result: verification pending; empty output is not negative evidence.
4. A scanner reports clean after a suppression was added. Result: inspect disposition. Approved acceptance remains accepted-risk, not fixed.
5. A host has the corrected package on disk but still runs the old loaded library pending restart. Result: installation complete, activation unverified.
6. The approved multi-platform index is X and the running platform manifest is Y. Result: require recorded membership Y in X plus platform-specific scan coverage; do not fail or pass based solely on X != Y.
7. A removed asset is absent from the new inventory. Result: require decommission evidence; absence alone cannot distinguish retirement from collection failure.
8. After closure on digest B, a fresh successful runtime observation confirms recovery restored vulnerable digest A to one asset. Result: confirmed regression; reopen the same finding for that asset, retain the original denominator, and re-evaluate priority/exceptions. Old closure evidence does not certify the reverted state.
9. After closure on B, the monitor is stale or missing and reports no current digest. Result: unknown/verification-pending; investigate, but do not infer clean status or call it a regression. If a current successful observation later confirms vulnerable A, classify confirmed regression and reopen; the stale monitor alone supports neither conclusion.

## Local evidence fixture

Run from repository root:

```bash
python3 skills/security/rbvm-verified-closure/scripts/check_closure.py
```

The fixture deliberately exercises only the closure-time post-activation scan path; it does not test recurring post-close drift monitoring, alerting, or reopen delivery. Its timestamp rule is stricter than the skill's alternative immutable-artifact workflow. A valid predeployment artifact scan plus current runtime-digest proof needs a separate adapter with explicit scan/database freshness policy. The stdlib fixture models four independent joins: population coverage, artifact identity, evidence ordering, and successful relevant detection. It exercises one success and counterexamples for each gate, including empty scope. Timestamps and identities are synthetic; no cloud, host, scanner, authentication, concurrency, recurring monitor, or rollout behavior is tested. Production adapters must establish evidence authenticity, freshness policy, manifest relationships, scanner coverage, monitoring delivery, and race resistance themselves.

## Overlap boundary

`container-image-patching` ends with image verification. This skill checks whether that verified artifact actually displaced the vulnerable deployed population. It does not duplicate package-manager commands or general test-minimization guidance.

## Key-access retention extension

Reviewed 2026-10-30. [KEY-ACCESS.md](KEY-ACCESS.md) refines the existing runtime-activation gate rather than introducing a competing closure skill. It distinguishes denying future acquisition from retiring an already-issued capability. Unlike TLS trust-path verification, the object here is locally usable key material or a service-managed data-key holder, not a certificate verifier or session.

### Primary sources and claim boundaries

- [Cloudflare: geographically fenced key management](https://blog.cloudflare.com/post-quantum-geo-key-manager/), published 2026-10-23, first retained as a lead 2026-10-24, reviewed 2026-10-30. The operating section distinguishes provisioning/keyring synchronization from process-memory caching until restart or expiry. Its rotation section distinguishes retained previous epochs from removing old-epoch access. This is a particular closed-beta architecture, not a general revocation guarantee, an alleged vulnerability, a measured delay, or a portability claim. No numeric cache lifetime is given.
- [AWS KMS: How unusable KMS keys affect data keys](https://docs.aws.amazon.com/kms/latest/developerguide/unusable-kms-keys.html), continuously updated documentation, no publication date supplied. KMS operations fail subject to eventual consistency, but already-unwrapped data keys can continue operating. Its EBS example retains a data key in Nitro while a volume is attached; detachment removes that key. This is service-specific behavior, not permission to detach storage or a universal process-restart remedy.
- [AWS Encryption SDK: Data key caching details](https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/data-caching-details.html), continuously updated. Valid matching cache entries can supply cryptographic materials without obtaining them again from the underlying provider. Matching includes algorithm suite, encryption context, partition and, for decryption, encrypted data keys. No cache-key implementation or production adapter is reproduced here.
- [AWS Encryption SDK: cache security thresholds](https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/thresholds.html), continuously updated. Thresholds govern reuse and eviction; they are not evidence that all copies or in-flight operations have disappeared. This recipe deliberately makes no universal expiry scheduler, secure-zeroization or upper-bound claim. Language APIs and cache implementations differ; check the deployed SDK/CMM/version rather than transferring one implementation's behavior.

The per-generation evidence join, permitted-control test and conservative closure oracle are original synthesis, not an AWS or Cloudflare prescribed procedure. Sources were read, not production services exercised. They do not establish a regulatory or cryptographic compliance conclusion.

### Original failure/remedy model

`python3 skills/security/rbvm-verified-closure/scripts/check_key_retention.py` runs nine test methods, including grouped evidence/population counterexamples. A warm toy holder retains an opaque capability after its provider denies acquisition. Evicting its cache prevents new cache hits but does not cancel a previously issued handle. Explicit handle completion plus blocked acquisition and complete per-generation observations passes the conservative fixture oracle. A new process generation cannot certify retirement of the old one. A failed permitted-key control blocks closure.

This stdlib model contains no key bytes or cryptography. Its lookup-driven expiry is an explicit model assumption, not a claim about every AWS/Cloudflare implementation. Passing it proves only the modeled distinction and decision gates. It does not authenticate evidence, discover holders, measure propagation/TTL, verify zeroization, cancel real work, prove race-free production closure, exercise AWS/Cloudflare, or test backups/compromised copies. A production adapter needs authoritative inventory and a stable observation/retirement boundary. The broader closure fixture remains separate and unchanged.

No key disabling, deletion, rotation, service restart, cache eviction, storage detachment, cloud API, credential access, or production remediation was performed or authorized by this fixture.
