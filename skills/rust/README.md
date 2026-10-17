# rust skills

Advanced Rust reliability skills focused on invariants and runtime correctness: compile-time API safety, bug classes that survive memory safety, deterministic concurrency tests, regex semantics, actor delivery, async cancellation, and typed error identity.

## Skills

- **[rust-deterministic-concurrency-tests](rust-deterministic-concurrency-tests/SKILL.md)** - reproducible interleaving tests with Loom or Shuttle, instrumented synchronization, model oracles, bounded exploration, and schedule replay.
- **[rust-runtime-bug-classes](rust-runtime-bug-classes/SKILL.md)** - writing or reviewing Rust code that touches filesystem paths, untrusted input, Unix CLI compatibility, chroot/sandbox boundaries, and non-UTF-8 bytes.
- **[rust-compile-time-invariants](rust-compile-time-invariants/SKILL.md)** - designing structs/enums/APIs so invalid states are unrepresentable and refactors fail fast at compile time.

- **[rust-regex-search-contracts](rust-regex-search-contracts/SKILL.md)** - context-preserving search spans, lexer anchoring, pattern priority, and engine failure contracts.
- **[rust-tokio-cancellation-safety](rust-tokio-cancellation-safety/SKILL.md)** - audit `select!` branch futures and preserve partial I/O progress across cancellation and shutdown.
- **[rust-tokio-actor-delivery](rust-tokio-actor-delivery/SKILL.md)** - cancellation-safe admission, request/reply guarantees, and outstanding-permit shutdown.
- **[rust-error-identity-boundaries](rust-error-identity-boundaries/SKILL.md)** - typed context, wrapper causes, downcasting, and explicit conversion boundaries.

## Validation

Rust example crates are source-reviewed but compiler/runtime tests have not run: the research executor has no Rust toolchain. Direct dependencies are pinned; transitive lockfiles are not resolved. The Tokio cancellation-safety skill is documentation-only with no fixture. See each skill's SOURCES.md before running.

## Install

```bash
./install.sh rust                          # install all
./install.sh rust-runtime-bug-classes      # install one
./install.sh rust-tokio-cancellation-safety # install one
```
