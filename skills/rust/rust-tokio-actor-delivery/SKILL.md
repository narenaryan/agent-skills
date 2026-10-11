---
name: rust-tokio-actor-delivery
description: Use when building Tokio request/reply actors or reviewing bounded-channel admission, canceled requests, overload behavior, and graceful shutdown.
---

# Tokio Actor Delivery Contracts

Separate capacity reservation, enqueue, execution, and reply receipt. A successful enqueue does not prove processing; a missing reply does not prove the operation never ran.

## Admission and cancellation

- Give the actor exclusive ownership of its resource; expose a clonable sender handle. Prefer bounded mpsc when producers need backpressure and oneshot for individual replies.
- If cancellation must return an unsent payload, race cancellation against `Sender::reserve()`, keeping the payload outside the competing futures. On success, use `Permit::send(payload)` without an intervening await. Directly racing `send(payload)` can drop the payload when another branch wins.
- Decide which outcome wins when admission and cancellation are both ready. Default `select!` polling is randomized; `biased;` makes branch order significant and requires a fairness review.
- Dropping a oneshot reply receiver does not retract an enqueued request. Specify whether admitted work finishes, is skipped before execution, or follows an explicit cancellation protocol. Treat failure to send a reply as expected when callers have lost interest.

## Backpressure and shutdown

- Review cycles of awaited bounded sends for deadlock. Separately review strong sender-handle cycles that prevent natural shutdown. Define overload behavior for `try_send` failures; an unbounded queue merely moves the risk to memory growth.
- For graceful shutdown, close the receiver, drain until `None`, and await the actor's task. Existing permits may still enqueue after `close()` and delay termination; ensure they are sent or dropped. Dropping the receiver instead discards unread messages.

## Verify the contract

Use explicit ready/pending states and gates, not sleeps. Test full-queue cancellation, payload recovery, dropped replies, and shutdown with an outstanding permit. The original [fixture](examples/src/lib.rs) covers these cases with Tokio `=1.48.0`; it is source-reviewed but runtime-unrun. Read [SOURCES.md](SOURCES.md) for evidence, version constraints, test instructions, and limits. Keep these protocol tests distinct from generic Loom/Shuttle schedule exploration.

## Pitfalls

- Canceling `reserve()` preserves an externally held payload, but loses queue position. Retrying reservation is not fairness-preserving.
- A helper preserves payload only through its cancellation branch. Aborting the whole helper drops its owned state; keep recoverable state outside a future that may itself be dropped.
- Do not describe a caller timeout as rollback or infer exactly-once execution from request/reply channels. Side-effecting retries need an application-level policy.
