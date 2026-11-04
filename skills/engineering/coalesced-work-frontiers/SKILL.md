---
name: coalesced-work-frontiers
description: Use when asynchronous Kafka consumers coalesce keyed rebuilds, finish records out of order, or risk acknowledging work added during an in-flight job
---

# Coalesced Work Frontiers

Coalescing reduces computation, not acknowledgement obligations. Each record stays attached until its rebuild durably covers it. Apply this to replaceable full-state work, not payments, increments, or events whose individual effects matter.

## Freeze the work, then prove completion

1. Track every delivered record by partition and offset, plus key, required revision, and assignment generation. Keep an ordered delivered ledger per partition. Aggregate queued work by key without dropping its member records.
2. At dispatch, freeze the job's exact membership and required revision. Messages arriving for that key enter a later job. Locally serialize jobs for one key; a successful old job must never acknowledge the key's entire current queue.
3. Verify the rebuild reads a snapshot that includes every member's required change. An event can outrun a database replica. Delay alone is not proof: check an authoritative revision or replication barrier. Define how revisions compare; unrelated counters cannot be maximized together.
4. Mark only frozen members complete after the required sink writes are durably acknowledged. On failure, retain/requeue those members with their obligations. Fence completion callbacks by both assignment generation and job attempt so a late retry cannot complete its successor.

## Commit a delivered prefix

For each partition, the safe frontier is the **first unfinished delivered record's offset**. If all delivered records finished, use the next-offset metadata saved for that delivery batch, not an unrelated latest consumer position. In Kafka 4.2, retain the relevant `ConsumerRecords.nextOffsets()` metadata, including leader epoch.

Example: offsets 10, 14, 19 arrive, with saved next offset 23. Completing 14 and 19 leaves the frontier at 10. Completing 10 and 14 leaves it at 19; completing all permits 23. Offsets can be sparse: waiting for integer 11 stalls, while committing `max(completed)+1` can lose unfinished work.

Disable auto-commit for asynchronous processing. Keep consumer API calls on its owning thread; workers return completion messages. Bound queued/in-flight work, pause affected partitions under pressure, and continue polling within the configured interval. Only reclaim ledger entries after the corresponding commit succeeds.

## Ownership and replay

On revocation, commit only safe completed frontiers while ownership permits. On loss, do not assume a final commit is legal. Invalidate affected work generations; stale callbacks cannot advance the new owner's bookkeeping. This is **not sink fencing**: a revoked worker may still write. Use sink-side revision checks or fencing for that separate hazard.

A crash after sink success but before offset commit replays work. Reuse [transactional-outbox-delivery](../transactional-outbox-delivery/SKILL.md) for duplicate-safe effects; stronger atomic result/checkpoint storage requires its own implementation.

## Check and limits

Run `python3 check_frontier.py` for deterministic sparse-offset, coalescing, retry, replay, and stale-callback counterexamples. It is a state model, not a Kafka integration test. See [sources and limits](SOURCES.md).

## Pitfalls

Never equate compute completion with durable output, coalesced keys with frozen members, or callback fencing with external-write fencing. Preserve unfinished records through retries and shutdown.
