# rust skills

Advanced Rust reliability skills focused on invariants and runtime correctness: compile-time API safety, bug classes that survive memory safety, and deterministic concurrency testing.

## Skills

- **[rust-deterministic-concurrency-tests](rust-deterministic-concurrency-tests/SKILL.md)** - reproducible interleaving tests with Loom or Shuttle, instrumented synchronization, model oracles, bounded exploration, and schedule replay.
- **[rust-runtime-bug-classes](rust-runtime-bug-classes/SKILL.md)** - writing or reviewing Rust code that touches filesystem paths, untrusted input, Unix CLI compatibility, chroot/sandbox boundaries, and non-UTF-8 bytes.
- **[rust-compile-time-invariants](rust-compile-time-invariants/SKILL.md)** - designing structs/enums/APIs so invalid states are unrepresentable and refactors fail fast at compile time.

## Install

```bash
./install.sh rust                      # install all
./install.sh rust-runtime-bug-classes  # install one
```
