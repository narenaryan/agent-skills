# Sources and validation

Status: **source-reviewed; compilation and runtime tests unrun**. No Rust
toolchain or fetched dependency was installed or executed. These are original
fixtures, not copied author examples. Documentation was checked on 2026-10-11.

## Why this is a distinct skill

The existing repository skills were read through the GitHub connector:

- [rust-compile-time-invariants](https://github.com/narenaryan/agent-skills/blob/main/skills/rust/rust-compile-time-invariants/SKILL.md), blob `b2ed6be991a29b6a343d839dca33ab07986154af`: API construction and compile-time change detection.
- [rust-runtime-bug-classes](https://github.com/narenaryan/agent-skills/blob/main/skills/rust/rust-runtime-bug-classes/SKILL.md), blob `fd7683be98512bba22d5d971f8d9988251513455`: syscall identity, byte handling, errors, and trust boundaries.
- [rust-deterministic-concurrency-tests](https://github.com/narenaryan/agent-skills/blob/main/skills/rust/rust-deterministic-concurrency-tests/SKILL.md), blob `e39ff1d9120f29e7f3da64c5fa921fc1e92e6ed9`: Loom/Shuttle model instrumentation and bounded exploration.

None specifies Tokio request-admission, reply-abandonment, or permit-aware
shutdown contracts. This fixture is a protocol/API regression test, not another
schedule-exploration framework. Blocking-pool lifecycle is deferred to a separate
candidate and is not part of this skill.

## Primary evidence

1. Alice Ryhl, [Actors with Tokio](https://ryhl.io/blog/actors-with-tokio/),
   published **2021-02-13**. Supports task/handle separation, resource ownership,
   bounded backpressure, expected abandoned replies, sender-cycle shutdown
   hazards, and bounded-send deadlock cycles. The skill's explicit admission
   states and test design are our synthesis, not claims of quoted author text.
2. Tokio **1.48.0**, [Sender source and cancellation contract](https://github.com/tokio-rs/tokio/blob/tokio-1.48.0/tokio/src/sync/mpsc/bounded.rs#L756-L788).
   A losing `send` branch drops its payload; `reserve` separates capacity waiting
   from payload transfer. Cancellation loses queue position. Verified through
   GitHub because the initial rustdoc Sender page fetch failed.
3. Tokio **1.48.0**, [select! cancellation and fairness](https://docs.rs/tokio/1.48.0/tokio/macro.select.html#cancellation-safety).
   Default randomized polling and ordered `biased;` polling are distinct policies.
   These tests use explicit bias and channel state to force the intended branch.
4. Tokio **1.48.0**, [Receiver::close](https://docs.rs/tokio/1.48.0/tokio/sync/mpsc/struct.Receiver.html#method.close),
   [recv](https://docs.rs/tokio/1.48.0/tokio/sync/mpsc/struct.Receiver.html#method.recv),
   and [try_recv](https://docs.rs/tokio/1.48.0/tokio/sync/mpsc/struct.Receiver.html#method.try_recv).
   Existing permits can send after closure, and termination waits for permits to
   be consumed or released. `try_recv` distinguishes empty from disconnected.
5. Tokio **1.48.0**, [mpsc clean shutdown](https://docs.rs/tokio/1.48.0/tokio/sync/mpsc/index.html#clean-shutdown).
   Close then drain; dropping the receiver discards unread queued messages.
6. Tokio [1.48.0 package manifest](https://github.com/tokio-rs/tokio/blob/tokio-1.48.0/tokio/Cargo.toml).
   Declares Rust **1.71** for Tokio itself. The rustdoc release date is
   **2025-10-14**. The fixture uses Rust edition 2021 and exactly Tokio
   `=1.48.0`, with `rt`, `macros`, and `sync`. It does not assert a minimum
   toolchain for the complete dependency graph, which is not locked or compiled.

## Test inventory

| Test | Observable contract |
| --- | --- |
| `cancelled_direct_send_drops_its_unsent_payload` | A full queue forces pending send; a ready cancellation wins and increments the payload's drop counter. |
| `cancelled_reservation_returns_payload_for_one_later_delivery` | The same full-queue cancellation returns ownership; a later retry produces exactly one receive and one eventual drop. |
| `closed_admission_returns_the_original_payload` | Closed-channel admission retains payload identity and ownership. |
| `dropping_reply_receiver_does_not_retract_an_enqueued_request` | A queued mock addition executes even when its reply receiver was dropped before the actor started. |
| `outstanding_permit_can_send_after_close_and_delays_termination` | New sends are rejected while an old permit keeps the receiver nonterminal and can deliver one value. |
| `dropping_outstanding_permit_also_allows_clean_termination` | Releasing the last outstanding permit lets the closed receiver finish. |
| `ready_admission_wins_the_documented_ready_cancellation_tie` | The helper's explicit admission-first bias is covered. |

No sleeps, timer advancement, wall-clock thresholds, network, unsafe code, or
third-party actor framework are used. All tests select the current-thread Tokio
runtime. Tests containing awaits rely on the documented ready/closed channel
states; a regression could hang, so a future CI runner should apply its ordinary
outer job timeout, without treating timing as a correctness assertion.

## Reproduce later

From the examples/ directory, in an authorized environment with a Rust toolchain and an
already-provisioned dependency cache:

```sh
cargo test --offline
cargo fmt --check
```

These commands were **not run** here. An offline cache miss is a verification
blocker, not authorization to fetch dependencies or install software. The first
successful Cargo run will generate `Cargo.lock`; preserve that lockfile and
record `rustc --version` before claiming reproducibility of the complete
dependency graph. The exact Tokio pin freezes the APIs under examination, not
all transitive dependencies.

## Limits

These are finite behavioral regressions for a deliberately small in-memory
actor. They do not prove starvation freedom, absence of production deadlocks,
exactly-once side effects, fairness under repeated cancellation, persistence,
distributed delivery, or application-level rollback. The helper returns a
payload only when its own cancellation branch wins; dropping the entire helper
future also drops its owned payload. A caller needing ownership across task
abortion must keep that state outside the aborted future or choose another
explicit ownership protocol. Queue closure and request/reply channels do not
replace such a protocol.
