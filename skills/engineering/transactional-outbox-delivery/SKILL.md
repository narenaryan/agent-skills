---
name: transactional-outbox-delivery
description: Use when choosing polling versus CDC, preserving per-aggregate order, or diagnosing duplicate effects after broker redelivery, lost remote acknowledgments, or expired idempotency keys
---

# Transactional Outbox Delivery

Commit domain state and its event record in one local transaction. The broker and remote API are outside that transaction; replay does not imply one business effect.

## Producer and relay

1. Write domain state and immutable event together; rollback hides both. Keep polling state separate. Keep stable event ID, aggregate type/ID, event type and payload. Allocate any aggregate sequence with the aggregate update, not a timestamp.
2. Polling needs indexed scans, backoff and safe claims. CDC substitutes log retention, snapshots, offsets and connector operations. A Debezium PostgreSQL slot can retain WAL during outages. Test backlog recovery.
3. Advance a polling checkpoint only after broker acknowledgment; a crash after acknowledgment but before checkpoint can duplicate delivery. CDC can replay from offsets. Retain rows and WAL through expected connector recovery.
4. Key Kafka records by aggregate with a stable partitioner and partition count. Partition append order doesn't serialize parallel relays or consumers. Enforce next sequence on publish and apply, or reject gaps.

## Apply local effects atomically

Insert a unique `(consumer_name, event_id)` marker and apply the effect inside one consumer DB transaction. A lost claim does nothing; failed effects roll back markers. Commit before broker acknowledgment. Retain markers through supported replay; specify broker retention and the authoritative historical archive.

## Reconcile remote effects after a lost response

Record operation identity before dispatch: an opaque stable key, provider/account/action scope and frozen request parameters. A DB marker cannot atomically cover the remote mutation. Workflow replay may reuse a recorded result; an unreported activity can retry under its policy.

| Evidence | Decision |
|---|---|
| Outcome unknown, documented receiver dedup still guaranteed at arrival | Retry the identical scoped request with the same key. Start the window at earliest possible acceptance, not the timeout. Include delivery delay, SDK retries and clock uncertainty; stop if unbounded. |
| Expired/unknown key guarantee, no receiver dedup, or parameters changed | Stop automatic writes. Query the authoritative provider operation/resource by stable reference; confirm identity, scope, parameters and final outcome. |
| No match or ambiguous status | Keep unresolved without terminal proof tied to this operation: no effect occurred and no prior attempt can still commit. Absence alone is neither proof. |

Example: a remote fulfillment commits, but the acknowledgment is lost. Replay the recorded intent within its safe window or reconcile without writing. [Offline fixture](examples/test_external_retry.py); [sources and validation limits](SOURCES.md).

## Pitfalls

- Marking an event sent before broker acknowledgment can lose it; marking a remote operation complete before receipt can conceal a failed action.
- Minting a new key on a timeout or reusing an expired key can create another effect.
- Multi-service recovery needs coordination or compensation, not just an outbox.
- A provider may replay a cached error; neither an error nor an empty listing proves no effect. Check the endpoint's version-specific contract.
