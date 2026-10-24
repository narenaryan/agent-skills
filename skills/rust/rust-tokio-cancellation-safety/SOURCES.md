# Sources and validation

Status: **primary-source reviewed; Rust code compilation and runtime tests unrun**.
Reviewed 2026-10-14. This skill is an original synthesis of current Tokio API
contracts. No fetched code was copied, and no software or dependencies were
installed.

## Why this is separate

At base commit
[`6650244`](https://github.com/narenaryan/agent-skills/blob/6650244eac96352a7371415efb5ce9cf6770364e/skills/rust/README.md),
the Rust index covers compile-time invariants, runtime bug classes, Loom/Shuttle
schedule exploration, and Tokio actor admission/reply/shutdown. The actor skill
documents `reserve`, dropped reply receivers, and permit-aware shutdown; it does
not cover losing partial I/O progress when a `select!` branch is dropped. The
engineering [AI bug-patterns skill](https://github.com/narenaryan/agent-skills/blob/6650244eac96352a7371415efb5ce9cf6770364e/skills/engineering/ai-bug-patterns/SKILL.md)
mentions cancellation and partial updates generically. This skill is limited to
the per-operation progress contract, especially framed reads and stream writes.

Alice Ryhl's [Actors with Tokio](https://ryhl.io/blog/actors-with-tokio/),
published 2021-02-13, motivates isolating connection I/O in an owning task. It
is architecture context, not evidence for the method-by-method cancellation
table.

## Primary references

- [Tokio `select!` documentation](https://docs.rs/tokio/1.53.3/tokio/macro.select.html),
  Tokio 1.53.3, checked on 2026-10-14. Defines cancellation safety as
  dropping an unfinished future and recreating it without losing progress;
  lists safe receives/reads/writes, non-safe `read_exact`/`write_all`, queued
  lock/semaphore waits, and randomized versus `biased;` polling.
- [Tokio `AsyncReadExt`](https://docs.rs/tokio/1.53.3/tokio/io/trait.AsyncReadExt.html),
  Tokio 1.53.3, checked on 2026-10-14. `read` and `read_buf` are cancel-safe;
  `read_exact` may consume data into its buffer before cancellation without
  returning the consumed count. The persistent framing buffer is the skill's
  synthesis, not a Tokio-provided frame parser.
- [Tokio `AsyncWriteExt`](https://docs.rs/tokio/1.53.3/tokio/io/trait.AsyncWriteExt.html),
  Tokio 1.53.3, checked on 2026-10-14. `write` and `write_buf` are cancel-safe
  single attempts; `write_all` can partially write and a later call restarts
  at the beginning. `write_all_buf` may partially write but advances its
  supplied `Buf` by the written count, so retaining that same buffer preserves
  progress. `flush` is cancel-safe but may partially flush and advances the
  writer's internal buffer. The worked `write_frame_until_shutdown` example
  retains an offset in the owner and is an original pattern; its `true` result
  means all bytes were accepted by `AsyncWrite`, not flushed or delivered. The
  caller must resume with the same frame and an offset in `[0, frame.len()]`.

Version-pinned links preserve the documentation target. No claim is made about
older Tokio releases beyond the separately documented API version being
reviewed.

## Validation limits

- `command -v rustc` and `command -v cargo` returned no paths. No Rust compiler,
  Cargo, or Tokio runtime test was available; none was installed or fetched.
- The repository README mentions `./test.sh`, but the current main tree does
  not contain it; no repository-wide test command was run.
- The table and worked example were checked manually against Tokio's 1.53.3
  method contracts. This is documentation validation, not a compiled fixture.
- A future provisioned Rust run should test cancellation after a deterministic
  partial header read and partial frame write, then verify that resume neither
  loses input nor duplicates output. Use scripted I/O gates, not sleeps as
  correctness assertions. Record `rustc --version` and resolved dependency
  versions; no lockfile or runtime result is claimed here.
- These contracts do not provide atomic network messages, remote delivery,
  exactly-once effects, fairness under `biased;`, or recovery if the enclosing
  owner task itself is aborted. Whether shutdown may abandon partial protocol
  state remains application policy.
