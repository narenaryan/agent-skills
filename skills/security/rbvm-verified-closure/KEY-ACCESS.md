# Key-access closure: acquisition is not use

Use this recipe when the approved remediation requires specified holders to stop using a key, not merely to stop fetching it. A KMS denial, provisioning update, or cache-age setting proves only its own boundary.

## Separate the claims

| Observation | What remains unproven |
|---|---|
| KMS key unusable / new unwrap denied | Already-unwrapped data keys may still operate locally |
| Provisioning or kernel keyring updated | Existing process copies may not have reloaded |
| Cache entry exceeds reuse threshold | In-flight holders, copied material, and memory erasure are separate |
| One restarted process rejects access | Other replicas and older process generations remain untested |

AWS documents an attached EBS volume continuing I/O after its KMS key becomes unusable: its data key is already in Nitro hardware. This is an architectural example, not a recommendation to detach a volume. AWS Encryption SDK caching similarly avoids service calls on valid hits. Its reuse thresholds do not establish global revocation or secure erasure.

## Verification recipe

1. State the exact revoked capability, affected key/version, caller population, operations, and deadline. Distinguish future acquisition, continued use, and destruction of copies. These are different acceptance criteria.
2. Inventory each retention layer: provider authorization, provisioned keyring, process cache, outstanding operation handles, and service-managed holders. Bind observations to asset and process generation; preserve unreachable holders as unknown.
3. On a controlled non-production fixture, warm the old path before the change. Compare a new acquisition with that already-warm caller after the change. Require the expected denial and a permitted-key control; a timeout or dead service is not successful revocation evidence.
4. Determine the documented refresh/retirement event for each holder. Verify the authorized change actually reached that generation. Elapsed TTL alone does not prove eviction, completion of in-flight work, or erasure. Do not invent a revocation bound from an unspecified cache lifetime.
5. Join blocked acquisition, retired usable holders, successful controls, and complete population evidence before closing the **continued-use** claim. Record separately what is still unknown about copies, backups, previous epochs, or service-specific behavior. A local restart cannot prove compromised copies were destroyed.

Example: fresh unwrap fails, but a previously acquired handle still works. Report acquisition blocked / continued use not closed. In the toy fixture, cache retirement plus handle release permits closure only after every scoped runtime is accounted for.

```bash
python3 skills/security/rbvm-verified-closure/scripts/check_key_retention.py
```

This is an original capability-lifetime model, not cryptography, AWS, Cloudflare, erasure, timing, or production validation. See [source/version limits](SOURCES.md#key-access-retention-extension).

## Pitfalls

- Rotation can preserve older epochs; it does not automatically revoke them.
- A cached-use path may emit no new KMS request; quiet service logs do not prove non-use.
- Evidence collection grants no permission to disable/delete keys, evict caches, restart services, detach storage, or accept residual risk.
