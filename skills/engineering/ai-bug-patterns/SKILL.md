---
name: ai-bug-patterns
description: Use when writing or reviewing AI-assisted code, PRs, tests, or QA plans that may fail silently - turns common AI-generated bug clusters into checks for broken auth, race conditions, stale state, validation drift, idempotency, swallowed errors, and incomplete refactors
---

# AI Bug Patterns

Use this skill when AI-assisted code passes happy-path tests but could be
silently wrong. These bugs return clean responses with the wrong access, state,
timing, or data source.

## Working rule

Review the negative space, not just the feature path:

1. Name who must be denied, what state must stay synchronized, and which
   operations must be atomic, cancel-safe, or idempotent.
2. Check whether omission fails closed. Missing auth, scope, config, or
   validation should block work, not allow it.
3. Ask for pre-production evidence: negative, cross-tenant, concurrent, retry,
   cache-invalidation, or startup checks.

## Scan these clusters

| Cluster | Ask |
|---|---|
| Authorization, access control, query scope, credentials, tokens | Can one user, tenant, org, role, or token see or mutate another context's data? Is scope enforced at the backend boundary? |
| TOCTOU, partial updates, async completion, cancellation, non-atomic operations | Can state change between check and use? Can a late response, failed second step, or cancellation leave inconsistent state? |
| Webhook, retry, dedup, and idempotency failures | Can duplicate delivery or retry charge, send, grant, import, or mutate twice? Is uniqueness enforced by storage? |
| Stale derived state, stale cache, unsynced code paths, inconsistent data source | After a mutation, do API, worker, admin, UI, cache, and reporting paths agree on the source of truth? |
| Startup/config validation, input validation, validation drift, fuzzy matching, boundary errors | Can bad config boot? Can one path accept what another rejects? Are limits, rounding, normalization, and matching explicit? |
| Swallowed errors, incomplete refactors, stale constants, null dereferences, UI/accessibility gaps | Does failure become success, empty data, wrong status, unreachable UI, or old behavior that survived a rename? |

## Evidence to request

- Auth: denied-user, cross-tenant, wrong-audience, expired-token, and
  missing-scope tests.
- Races: transaction, rollback, out-of-order completion, and replay-the-same-
  event-twice tests.
- State: mutate, then read through every cache, derived state, and data source.
- Validation/refactor: fails-fast startup, boundary inputs, shared validator,
  and old-name search evidence.

## Make bugs legible

Prefer designs where omission fails loudly:

- Deny by default; require explicit grants.
- Centralize scope filters and validation at trust boundaries.
- Use database constraints, transactions, unique keys, and idempotency keys.
- Treat caches and derived state as dependencies with owners and invalidators.
- Log and propagate unexpected errors; ignore only named, safe cases.

## Pitfalls

- Reviewing only the generated diff; inspect adjacent endpoints, jobs, and
  alternate callers that share the invariant.
- Accepting a passing happy-path test as evidence for authorization, retries,
  concurrency, or cache behavior.
- Treating null dereferences as the main AI risk. They are visible; silent
  access, race, state, and validation bugs are more likely to escape.

Source: Detail blog.
