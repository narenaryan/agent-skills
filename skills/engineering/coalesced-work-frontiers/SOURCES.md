# Sources and validation

Reviewed November 4, 2026. Original synthesis; the executable fixture is original code, not fetched third-party software.

## Primary sources

- [Cloudflare: DNS targeted zone builds](https://blog.cloudflare.com/dns-targeted-zone-builds/), Alex Fattouche, published November 2, 2026. First discovered November 2; deeply reviewed November 4. The unified scheduler retains all Kafka messages attached to merged work through retries, separates later same-zone changes, checks replica freshness, and soft-commits only after earlier work finishes. These mechanisms motivate the membership/frontier model. DNS-specific performance measurements are not transferred to other workloads. Coalescing arbitrary business events is not supported by this source.
- [Apache Kafka 4.2 KafkaConsumer API](https://kafka.apache.org/42/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html), versioned reference documentation; publication/update date not asserted. Documents sparse offsets, position versus committed position, manual commits with asynchronous processing, the next record's offset or `ConsumerRecords.nextOffsets()` after exhaustion, leader-epoch metadata, consumer thread confinement, and replay between external writes and commits. This is reference documentation, not a monitored blog.
- [Apache Kafka 4.2 ConsumerRecords API](https://kafka.apache.org/42/javadoc/org/apache/kafka/clients/consumer/ConsumerRecords.html), versioned reference documentation; publication/update date not asserted. `nextOffsets()` contains offsets and metadata for partitions whose position advanced in that poll; it is not restricted to partitions returning data records. Preserve this batch association rather than reconstructing positions from integer adjacency.
- [Apache Kafka 4.2 ConsumerRebalanceListener API](https://kafka.apache.org/42/javadoc/org/apache/kafka/clients/consumer/ConsumerRebalanceListener.html), versioned reference documentation; publication/update date not asserted. Revocation and ownership loss differ: lost partitions may already belong to another consumer. Cooperative rebalances can affect only a subset of partitions. Callbacks notify ownership changes rather than granting a veto.

## What the fixture establishes

Run from this directory:

```sh
python3 check_frontier.py
python3 -O check_frontier.py
```

The standard-library unittest model freezes job membership, retains sparse ordered delivered records, gates completion on a declared durable write and sufficient revision, and rejects stale assignment/attempt callbacks. Thirteen tests cover all six completion orders for three jobs, an unsafe maximum-completed offset baseline, sparse offsets, coalescing, arrivals during work, retries, non-durable results, independent partitions, cross-partition key membership, assignment reset, write-before-commit replay, malformed poll input, and duplicate callbacks. Both normal and optimized Python 3.12.14 runs passed on November 4, 2026; unittest checks remain active under optimization. Independent review additionally passed four edge cases and detected three deliberate faulty-policy mutations, in both interpreter modes; those review-only artifacts remain in the research record.

The incorrect baseline can skip unfinished offset 10 after later offsets finish. The remedy retains the unfinished delivered prefix. Waiting for every integer offset incorrectly stalls at 11 after sparse delivery. These are deterministic counterexamples and model invariants, not measured production reliability improvements.

## Limits and integration obligations

No broker, consumer library, database, replica, or real sink was run. `durable=True` and `built_revision` are trusted inputs, not verified persistence or replication barriers. Revisions must share a valid comparison domain; the toy model assumes integer revisions per key. The model uses a whole-consumer generation reset, not production cooperative-partition fencing. It does not implement leader epochs, commits/commit failures, worker cancellation, queue bounds, ledger reclamation, pause/poll scheduling, sink-side fencing, or idempotent writes. Duplicate processing after a crash is demonstrated, not eliminated. A production integration must validate all of these, including failure during partial sink writes and ownership transfer. Local serialization does not prevent revoked or remote workers from writing stale state. No exactly-once, throughput, memory-bound, or deployment-safety claim follows from these tests.
