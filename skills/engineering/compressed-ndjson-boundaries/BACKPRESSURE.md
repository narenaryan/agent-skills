# Admission before asynchronous work

A bounded queue limits **enqueued** items, not tasks waiting to enqueue. `create_task(queue.put(record))` can retain the entire input behind a queue whose reported size never exceeds eight. A worker-count limit has the same blind spot when submitted work accumulates elsewhere.

## Capacity and failure contracts

| Boundary | Required distinction |
|---|---|
| Admission | Await `queue.put(record)` before pulling another record; with multiple producers, budget one in-flight record per producer. Acquire permits before spawning tasks, not inside already-created tasks. |
| Bytes | Queue capacity is an item count. Combine it with maximum record size and include producer/sink items, parser objects, decoder window and transient buffers. |
| Completion | A queue becoming empty is not proof of clean compressed EOF or completed sink writes. |
| Failure | A sink can fail while a producer waits for capacity. Cancel and await siblings, close generators/decoder/source, and discard staging. |

## Recipe

1. Start from the existing decoder/framer caps. Do not let a list-returning parser API, result collector or pending-future list silently reintroduce whole-input retention.
2. Couple producer and sink lifetimes. The Python fixture uses `asyncio.TaskGroup` (Python 3.11+): non-cancellation failure cancels siblings and awaits them. A canceled child alone need not make group exit fail: inspect both task results before commit. Cleanup must preserve cancellation, not swallow it. Synchronous decoder or filesystem calls still run cooperatively, not preemptively.
3. Send the success sentinel only after decoder **and** framer EOF checks. Never put it unconditionally in `finally`: a failed sink may never drain a full queue.
4. Stage output privately with a separate storage/output quota. Publish only after producer validation and sink completion. Same-directory rename gives a visibility boundary, not crash durability; remote sinks need their own transaction or reconciliation protocol.

From this skill directory:

```bash
python3 scripts/slow_sink.py
python3 scripts/test_slow_sink_review.py
python3 scripts/slow_sink.py measure 16384 8  # Linux memory observation
```

The original fixture uses installed libzstd and Python JSON, not simdjson. It demonstrates pending-enqueue bypass, corrupted-tail leakage, and blocked-producer cleanup. [Sources and measured limits](SOURCES.md) separate queued payload, Python-traced allocations and whole-process peak RSS.

## Pitfalls

- A low `qsize()` can hide many pending enqueue tasks.
- Backpressure cannot cap a single unbounded record or application-retained output.
- Successful queue draining does not certify input integrity, crash recovery or durable publication.
