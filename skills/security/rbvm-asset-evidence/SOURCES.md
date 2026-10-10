# Asset evidence: sources and validation

Reviewed 2026-10-10. This is an original operational synthesis, not a claim that either source mandates an RBVM data model or a particular scan interval.

## Primary evidence

- [Kubernetes: Object Names and IDs](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/), live documentation, page last-modified 2026-01-27. Sections **Names** and **UIDs**: names can recur after deletion; UIDs distinguish historical object occurrences. This supports separating resource incarnation from familiar labels.
- [OCI Image Specification: descriptor, v1.1.1](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md), sections **Properties**, **Digests**, and **Verification**. Descriptors identify content and carry media type, digest, and size. Verification concerns bytes, not runtime deployment identity. The specification distinguishes descriptors targeting manifests and other content; do not treat all digests as interchangeable.

The freshness budget, source precedence, clock tolerance, unknown queue, and reversible-merge rules are proposed local policy. Obtain organizational approval before adopting them. No unsupported claim about a scanner's completeness or performance is made.

## Worked scenarios (original, synthetic)

1. **IP reuse:** scanner observation at 09:00 concerns provider instance `i-A`; inventory at 11:00 shows `i-B` at the same IP. Expected: retain two instances and attach the finding to A. B requires evidence. Counterexample: merging on IP falsely attributes A's patch to B.
2. **Late delivery:** observation collected Monday arrives Thursday. With a locally chosen 24-hour budget, it is stale on Thursday even if ingested seconds ago. Counterexample: using ingestion time converts pipeline delay into artificial freshness.
3. **Image fan-out:** two workload UIDs reference the same verified platform manifest. Expected: one artifact, two deployment relationships and potentially different exposure/owners. Counterexample: digest deduplication that collapses both workloads loses blast radius.
4. **Clock error:** collection timestamp is one hour in the future; clock tolerance is five minutes. Expected: invalid-time queue, not a fresh result. Fix the clock or recover trustworthy source timing.
5. **Partial success:** a collector lists packages but cannot inspect a mounted application directory. Expected: qualified package coverage and unknown application coverage. A process exit code of zero is insufficient evidence of complete coverage.
6. **Retirement:** agent disappears for three days. Expected: unknown/stale lifecycle state unless authoritative termination evidence exists. Do not lower the denominator merely because a source stopped reporting.

## Executable scope

From the repository root:

```bash
python3 skills/security/rbvm-asset-evidence/fixture.py
```

The stdlib fixture tests an explicitly synthetic freshness/coverage contract: exact boundary, late ingestion, future clock skew, partial collection, missing observation, and naive timestamps. It does not discover assets, implement a provider identity system, test scanner recall, or measure operational coverage.
