# Source ledger and verification examples

Reviewed 2026-10-10. The closure join is an original implementation pattern. It is not a claim that NIST requires a particular scanner, schema, digest field, or evidence-retention period.

## Primary evidence

- [NIST SP 800-40 Rev. 4](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-40r4.pdf), Murugiah Souppaya and Karen Scarfone, April 2022. Sections 2.2 and 2.3 distinguish implementing a risk response, verifying that it took effect, and monitoring its continued presence. Sections 2.3.2–2.3.4 discuss activation, verification, and later change. This supports treating patch installation and ticket completion as insufficient by themselves.
- [Kubernetes: Images](https://kubernetes.io/docs/concepts/containers/images/), continuously updated documentation, sections “Image names” and “Multi-architecture images with image indexes.” Tags may move; content digests are immutable. An image index can refer to architecture-specific manifests. This motivates identity-aware comparison instead of a raw tag match or an unqualified digest-string comparison.

## Original worked scenarios

1. A clean candidate image has digest B; every live pod still runs digest A. Result: build evidence exists, deployment evidence fails. Do not close.
2. Eleven of twelve affected pods run B. The twelfth is unreachable. Result: eleven verified, one unknown. Report the denominator and keep the remaining finding open.
3. All pods run B, but the second scanner run lost credentials and emitted no findings. Result: verification pending; empty output is not negative evidence.
4. A scanner reports clean after a suppression was added. Result: inspect disposition. Approved acceptance remains accepted-risk, not fixed.
5. A host has the corrected package on disk but still runs the old loaded library pending restart. Result: installation complete, activation unverified.
6. The approved multi-platform index is X and the running platform manifest is Y. Result: require recorded membership Y in X plus platform-specific scan coverage; do not fail or pass based solely on X != Y.
7. A removed asset is absent from the new inventory. Result: require decommission evidence; absence alone cannot distinguish retirement from collection failure.

## Local evidence fixture

Run from repository root:

```bash
python3 skills/security/rbvm-verified-closure/scripts/check_closure.py
```

The fixture deliberately exercises only the post-activation scan path; its timestamp rule is stricter than the skill's alternative immutable-artifact workflow. A valid predeployment artifact scan plus current runtime-digest proof needs a separate adapter with explicit scan/database freshness policy. The stdlib fixture models four independent joins: population coverage, artifact identity, evidence ordering, and successful relevant detection. It exercises one success and counterexamples for each gate, including empty scope. Timestamps and identities are synthetic; no cloud, host, scanner, authentication, concurrency, or rollout behavior is tested. Production adapters must establish evidence authenticity, freshness policy, manifest relationships, scanner coverage, and race resistance themselves.

## Overlap boundary

`container-image-patching` ends with image verification. This skill checks whether that verified artifact actually displaced the vulnerable deployed population. It does not duplicate package-manager commands or general test-minimization guidance.
