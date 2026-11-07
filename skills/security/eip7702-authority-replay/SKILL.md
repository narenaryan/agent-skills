---
name: eip7702-authority-replay
description: Use when reviewing EIP-7702 wallet delegation evidence, especially when a reverted transaction, zero-value transfer, or mixed authorization list is being treated as proof that account authority did not change.
---

# EIP-7702 Authority Replay

Transaction execution and delegation updates have different rollback boundaries. A failed receipt can coexist with a persistent change in who controls future account execution.

## Evidence contract

| Preserve | Why |
|---|---|
| Chain, block hash, transaction position, protocol rules | Ordered state, not latest-state guesses |
| Complete authorization list and verified recovered authorities | Outer sender is not necessarily each authorizer |
| Account nonce/code immediately before authorization processing | Sender nonce has already incremented |
| Applied/skipped tuples and resulting delegation | Receipt status alone misses authority changes |

## Recipe

1. Confirm the chain implements the reviewed EIP-7702 rules. Ethereum mainnet activated Pectra May 7, 2025; other chains need separate verification.
2. Obtain trusted decoding, signature validation and ordered pre-state. Missing accounts, tuple coverage or state make replay **unknown**, not unchanged. Do not substitute caller-supplied authority labels for signature recovery.
3. Reject structurally invalid envelopes first; malformed tuple field bounds invalidate the transaction. Then process tuples in order: chain must be current or zero, nonce must match and be below `2**64 - 1`, and authority code must be empty or delegated. Failed checks skip that tuple; successful changes increment its nonce. Later valid tuples can replace earlier delegation. Zero address clears code.
4. Keep applied delegation changes even if subsequent execution reverts. Report intermediate changes and authorization-stage state. Reconcile later execution effects, including further nonce increments, before comparing observed transaction post-state.
5. Separately assess approval and impact: include privileged contracts controlled by empty-balance accounts. Bind approval to account, delegate/code, chain and nonce. Generic digest-signing access must not evade a dedicated delegation policy. Chain-zero acceptance by protocol is not organizational approval.

Run the bounded offline model:

```bash
python3 skills/security/eip7702-authority-replay/check_replay.py
```

[Sources and validation limits](SOURCES.md). Reuse [guarded remediation](../rbvm-guarded-remediation/SKILL.md) and [verified closure](../rbvm-verified-closure/SKILL.md) for separately authorized actions. This recipe grants no signing, scanning, transaction or production-change permission.

## Pitfalls

- A receipt failure is not delegation rollback.
- A zero immediate balance delta can conceal future authority.
- Deduplicating by account loses ordering and nonce transitions.
- Clearing delegation does not demonstrate storage cleanup or complete incident containment.
