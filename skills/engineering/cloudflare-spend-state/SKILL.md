---
name: cloudflare-spend-state
description: Use when Cloudflare spend policies appear unchanged after billing rollover, a limit-reached alert is mistaken for an active block, or missing current_state is being interpreted as available budget.
---

# Cloudflare Spend State

Read four separate facts: configured policy, billing-period evaluation, delivery bookkeeping, and observed runtime behavior. A budget threshold is not a synchronous admission reservation.

## Evidence boundaries

| Field | What it establishes |
|---|---|
| `version` / ETag | Configuration revision; rollover need not change it |
| `current_state` | Asynchronous estimate; missing means unavailable |
| `evaluated_at` | Evaluation time, not newest usage-event time |
| `billing_period_start/end` | Subscription cycle, not calendar month |
| `status` | Threshold evaluation, not runtime blocking |
| Enforcement generations + `succeeded` | Delivery completed when generations agree; no runtime readback |

## Read-only diagnosis

1. Identify account, policy, product and action. Workers and Durable Objects balances are separate. `notification` is not `usage_block`.
2. Obtain a fresh GET through an authorized read connection. Preserve capture time and response; do not skip dynamic-state inspection because ETag is unchanged.
3. Keep absent state, `unavailable` and `no_current_period` distinct from `below_limit`. Do not replace them with zero. Check period bounds before comparing snapshots.
4. Report desired state, delivery status, generations and expiry separately. Pending/retry delivery can overlap a new billing period. Even completed delivery does not prove every runtime rejected the intended work.
5. For enforcement claims, request relevant existing runtime evidence with explicit scope. Do not generate chargeable traffic or alter policies merely to test them.

Example: identical version 4 snapshots show an old-period `limit_reached` and new-period `below_limit`. A configuration-only cache misses the transition; fresh state comparison detects it. Neither snapshot establishes a hard spending ceiling.

[Sources and worked checks](SOURCES.md). From this directory: `python3 check_state.py`.

## Pitfalls

- Metering, subscription/pricing joins and runtime propagation are asynchronous; unpriced usage is pending, not free.
- Advertised near-real-time timing is not a worst-case overspend bound. A concurrency cap limits simultaneous work, not lifetime expenditure.
- Raising a threshold or disabling/deleting a policy can restore billable service. Changes require separate approval; this diagnostic grants none.
