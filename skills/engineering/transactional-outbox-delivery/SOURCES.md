# Transactional outbox delivery: sources and validation

Reviewed November 19, 2026. Rolling documentation is identified by API/version where possible. These sources explain behavior; no external command, SDK, service or network call is executed by the fixtures.

| Primary source | What it supports |
|---|---|
| [AWS transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html), [saga guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-patterns.html) | Local atomic event/state writes, receiver duplicate handling and explicit coordination/compensation for multi-service recovery. |
| [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html), [Debezium PostgreSQL connector](https://debezium.io/documentation/reference/stable/connectors/postgresql.html), [Kafka 4.2 design docs](https://kafka.apache.org/42/documentation/) | Outbox event and partition-key mapping, WAL/offset retention, and ordered append within partitions; not business-effect atomicity. |
| [Temporal Activity Definition: Idempotency](https://docs.temporal.io/activity-definition#idempotency) | Recorded completions replay without re-execution; failed-to-report activities can retry. This does not turn the external mutation and workflow recording into one transaction. |
| [Amazon Builders’ Library: Making retries safe](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) | Caller-supplied request identity, parameter binding, semantic equivalence and late-arriving operations; retention varies across resources/services. |
| [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests), [Stripe advanced error handling](https://docs.stripe.com/error-low-level) | Concrete API v1 example: after execution starts, the first status/body (including HTTP 500) can be replayed; a pruned key can trigger new execution. Stripe v1 keys are eligible for pruning after at least 24 hours; this isn't a general provider default. API v2 has different semantics. |

The [November 19, 2026 Temporal/Pydantic webinar listing](https://pages.temporal.io/webinar-building-durable-agents-with-pydantic.html) motivated this investigation; it isn't evidence of provider guarantees or a claimed recording review.

From repository root:

```sh
python3 -m unittest discover -s skills/engineering/transactional-outbox-delivery/examples -v
python3 -O -m unittest discover -s skills/engineering/transactional-outbox-delivery/examples -v
```

The original fixture uses separate local SQLite stores and a fake integer clock. It exercises one synthetic receiver with exact request matching and fixed key expiry. It injects the lost response after a committed effect; it also models an already-in-flight attempt becoming visible only after an absent lookup. The goal is to expose incorrect decision contracts, not demonstrate a general exactly-once system. No concurrent SQLite callers, provider integration, network delays, real process kill, Temporal replay execution, CDC, Kafka, live financial/fulfillment actions or distributed timing guarantees are exercised. Model-only delay bounds do not validate any deployment's assumptions.
