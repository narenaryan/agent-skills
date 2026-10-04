---
name: rust-deterministic-concurrency-tests
description: Use when Rust concurrent data structures pass stress tests intermittently, lose updates despite atomics, or need reproducible interleaving tests; applies to Loom or Shuttle instrumentation, sequential-model oracles, replay, and bounded schedule exploration.
---

# Rust Deterministic Concurrency Tests

Treat the schedule as test input. Even sequentially consistent loads and stores do not make a compound read-modify-write atomic. More threads and sleeps increase opportunities for failure without making the failing execution reproducible.

## Choose a scheduler

| Tool | Good fit | Boundary |
|---|---|---|
| Loom 0.7 | Small synchronization algorithms; explore interleavings and modeled memory behaviors | State-space growth and configured bounds limit coverage |
| Shuttle 0.9 | Larger scenarios with randomized/PCT exploration and deterministic replay | Passing sampled schedules does not establish correctness |

Use maintained tooling rather than copying an educational scheduler. Keep production logic shared with the instrumented build.

## Build a meaningful model

1. Route synchronization and thread creation through a small conditional-import module. Replace the primitives used by the implementation itself, not only the test. Reset state inside every scheduler invocation.
2. Start with two actors and few operations. For a counter, compare completed increments with the final value. For queues/maps, specify permitted histories and ordering; final-state equality alone does not prove linearizability.
3. Control other nondeterminism. Mock I/O, clocks, and system calls; use scheduler-supported randomness or fixed inputs. Uncontrolled randomness prevents reliable replay.
4. Capture the failing input and schedule before shrinking. Reduce actors/operations while retaining the same invariant violation, then keep the small regression case.

For a project wired with Loom's documented `cfg(loom)` dependency/import scheme and an integration test named `loom_counter`:

```bash
RUSTFLAGS="${RUSTFLAGS:+$RUSTFLAGS }--cfg loom" cargo test --release --test loom_counter
```

Run the ordinary build separately to catch conditional-import drift. For Shuttle failures, preserve the emitted schedule string and replay it with `shuttle::replay`; record the tool version alongside it.

Sources: [matklad, 2024-07-05](https://matklad.github.io/2024/07/05/properly-testing-concurrent-data-structures.html), [Loom 0.7.2](https://docs.rs/loom/0.7.2/loom/), [Shuttle 0.9.5](https://docs.rs/shuttle/0.9.5/shuttle/).

## Pitfalls

- Any uninstrumented synchronization can hide behaviors from the scheduler.
- A bounded or randomized pass covers the explored model, not every production execution or memory-model behavior.
- Spin loops can exhaust exploration without progress; use the tool's modeled yield where its documented fairness requirements apply.
- Do not replace the implementation with a simplified test-only algorithm; that proves the substitute, not the shipped code.
