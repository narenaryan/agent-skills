---
name: prompt-cache-boundaries
description: Use when Claude API agents repeatedly rewrite shared context, first requests miss the prompt cache, or high cache-hit rates coexist with rising per-task cost.
---

# Audit Prompt Cache Boundaries

A stable template need not produce a stable provider-bound prefix. A matching prefix is not an observed cache hit; a hit is not evidence of lower task cost or preserved task quality.

## Separate the evidence

| Question | Evidence |
|---|---|
| What changed? | Final request structure, ordered tools, system blocks, history, model, and prompt-affecting settings |
| What was reused? | Actual response `usage.cache_read_input_tokens`, not a local hash |
| Did optimization help? | Comparable completed tasks: total usage, latency, failures, and independently checked outcomes |

## Repair the boundary

1. Inspect authorized synthetic requests after harness/SDK transformations. Record model, platform, workspace, feature configuration, and breakpoint positions. Keep prompt bodies, credentials, and customer data out of telemetry.
2. Claude prefixes follow `tools → system → messages`. Keep tool order and schema serialization deterministic. Changed tool definitions invalidate later prefixes; hashing only the system prompt misses this. Do not erase required instructions or tools merely to make requests match.
3. Separate stable instructions from changing repository/date/context blocks, preserving their roles, content, and ordering. Mark the last stable block with `"cache_control": {"type": "ephemeral"}`. A marker after volatile content writes that volatile prefix; lookback cannot recover a shorter entry that was never written. Automatic caching alone does not fix that layout.
4. Verify the chosen model/platform's minimum cacheable length, isolation scope, TTL, and breakpoint limits. Concurrent readers cannot use a new entry before its writer's response starts. A local byte comparison establishes neither token eligibility nor cache availability.

`[shared policy + cwd/date]◀cache` differs between jobs. `[shared policy]◀cache [cwd/date]` exposes a reusable boundary without deleting context. Changing an earlier tool description still breaks that prefix. Reordering/splitting content needs task-quality checks; preserved concatenated text alone is insufficient.

## Diagnose without inventing certainty

For authorized Claude API calls, opt into `diagnostics` each turn and chain the previous response ID. This feature is not available on Bedrock or Google Cloud. Read diagnostics alongside usage:

| Result | Interpretation |
|---|---|
| `diagnostics: null` | Ambiguous without opt-in and prior-ID context; never independently proves a hit |
| `cache_miss_reason: null` | Comparison pending |
| `previous_message_not_found` / `unavailable` | No usable comparison |
| `*_changed` | First divergence only; an earlier prefix may still hit |

Compare write/read/uncached/output tokens and calls per completed task, not only hit percentage. Keep model/effort and task mix comparable; any intentional changes need separate quality evaluation. Vendor savings do not transfer automatically.

Run offline counterexamples from repository root:

```bash
python3 skills/engineering/prompt-cache-boundaries/fixture.py
```

[Primary sources and validation limits](SOURCES.md).

## Pitfalls

- Treating a null diagnostic or local fingerprint as a hit, or a first-call miss as proof of a broken boundary.
- Sharing private context beyond its authorized audience to improve reuse.
- Claiming savings or quality parity from serialization tests; they exercise neither inference nor billing.
