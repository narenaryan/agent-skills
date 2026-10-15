---
name: transactional-outbox-delivery
description: Use when a database-backed service needs polling-versus-CDC choices, duplicate-safe consumers, or per-aggregate delivery order
---

# Transactional Outbox Delivery

Commit domain state and its event record in one local database transaction. The broker is outside; expect replay. Transport “exactly once” does not ensure one business effect.

## Producer and relay

1. In one transaction, update the domain row and insert an immutable event row; rollback must leave neither visible. Include stable event ID, aggregate type/ID, event type, and payload. If order matters, allocate the per-aggregate sequence with the aggregate update, not a timestamp.
2. Polling needs indexed scans, backoff, and safe claims. After its initial snapshot, CDC avoids repeated scans but adds log retention, offsets, snapshots, and connector operations. Debezium PostgreSQL slots retain WAL during outages and can consume disk. Test restart and backlog recovery.
3. Keep event fields immutable; polling state is separate. A poller advances or deletes only after broker acknowledgement; a crash before checkpoint duplicates. CDC replays from offsets; retain rows and WAL through connector capture and recovery.
4. If order matters, use aggregate ID as Kafka key with a stable key-based partitioner and unchanged partition count. Matching keys share a partition; Kafka preserves its append order, not end-to-end order across parallel relays or consumer effects. Enforce next sequence and serialize per aggregate on publish and apply, or reject/retry gaps. IDs and timestamps do not prove commit order.

Example: order 781 emits `OrderPlaced` as `E`/sequence 14; every retry keeps both values.

## Make consumer dedup atomic

Use a durable unique `(consumer_name, event_id)` key. In one consumer DB transaction, insert the key and apply the effect only if the claim wins; a duplicate is a no-op. Commit DB before Kafka offset commit or other broker ack. If the effect fails, roll back the marker; redelivery after commit is safe. For external effects, an outbox makes dispatch durable; the receiver still needs idempotency or reconciliation.

Retain source outbox/WAL through connector recovery. Set broker-topic retention separately for consumer replay/audit; archive IDs and sequences if older replay is promised. Deleting delivered rows removes that replay source; name the authoritative archive and expiry.

Sources: [AWS transactional-outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html); [AWS saga guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-patterns.html); [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html); [Debezium PostgreSQL connector](https://debezium.io/documentation/reference/stable/connectors/postgresql.html); [Kafka 4.2 design docs](https://kafka.apache.org/42/documentation/).

## Pitfalls

- A polling relay that marks or deletes before broker acknowledgement can lose an event on crash.
- A dedup marker committed apart from the business effect still permits a duplicate effect after a crash.
- Kafka partition order is not end-to-end order if relay or consumer work is parallelized.
- Purging rows before the supported recovery horizon makes older events unreplayable.
- The outbox covers one service’s state and event record, not a multi-service transaction; if coordinated recovery is required, model a saga with explicit retries and compensation.
