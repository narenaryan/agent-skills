# Publish closure against the evidence you reviewed

A valid review can go stale while it waits for approval or a worker. Close against the recorded evidence revision, not simply the latest ticket state. Closure at that revision is historical proof, not a guarantee about the live fleet.

| At review | At publication |
|---|---|
| Bind finding identity, expected disposition/revision, and exact evidence references. | Recheck expected finding revision and eligible disposition. Do not overwrite a later risk decision, reopen, or reviewer update. |
| Bind a manifest revision for the reviewed scope, including membership and evidence dependencies. | Compare the same nonreused manifest token, or all dependency revisions plus a membership token. A per-known-asset check misses newly added assets. |
| Record the evidence freshness deadline, if applicable. | Recheck age even if no revision changed. Evaluate freshness at the decision, not when approval was queued. |

1. Perform the slow evidence join outside the write transaction. Include asset incarnations, effective runtime and policy/coverage inputs. Scope revisions to their authority and epoch; after restore or rebootstrap, invalidate old tokens or include a new epoch. For a single manifest token, every relevant recorded change must update it in the same commit.
2. In one authoritative store, compare the reviewed dependencies and write the closure proof as one conditional transaction. Do not refresh a token and retry with the old review. A mismatch, absent dependency, or failed transaction leaves verification pending, not proof of regression. After a lost response, look up the exact proof operation; an inconclusive read does not establish no commit.
3. Preserve the disposition and its evidence as an as-of record. Current reporting must stop showing it as verified when a relied-on input changes, goes missing, or expires. Only newly confirmed affected evidence justifies a regression finding. A CAS in a local evidence store cannot fence independent deployments or prove unobserved runtime state.

Example: a rollout is verified on digest B, then the observer records a rollback to A before the close write. A blind write still records fixed. The guarded write rejects the stale review. Even B → A → B cannot reuse the old activation review solely because the digest came back.

## Evidence and local probes

- [SQLite isolation](https://www.sqlite.org/isolation.html) documents serialized writes and WAL snapshot behavior. [etcd v3.6 transactions](https://etcd.io/docs/v3.6/learning/api/#transaction) show atomic comparisons within one store; [etcd recovery](https://etcd.io/docs/v3.6/op-guide/recovery/#revision-difference) explains why revisions may go backward after a restore. The fixture does not run etcd.
- [NIST SP 800-40 Rev. 4, §§2.2(d), 2.3.3–2.3.4](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-40r4.pdf) supports verification and ongoing monitoring of effective patching. Tokens, conditional publication and conflict handling are implementation choices, not NIST requirements.

```bash
python3 skills/security/rbvm-verified-closure/scripts/check_publish.py
python3 skills/security/rbvm-verified-closure/scripts/check_publish_independent.py
```

The offline SQLite fixture compares an unconditional write with a guarded update using two connections and explicitly interleaved writes. Revisions, evidence, and findings are synthetic. Tokens are supplied by test writers; token generation, freshness-at-commit, immutable audit storage, monitoring delivery and external systems are not tested. The current-view check covers recorded revision drift only. Nothing here authorizes a ticket change or production action.

## Pitfalls

- Digest equality does not detect an intervening restart or rollback; do not use a reusable value as a revision token.
- A second read before an unconditional write leaves the same race.
- Compare tokens within their authority and incarnation. Do not sort tokens or use a ticket version as proof that a separate inventory stayed unchanged.
