# Error identity boundaries: provenance and validation

Reviewed October 11, 2026. This is an original synthesis of project documentation
and source code, not a claim of a newly published blog article. No personal blog
for David Tolnay was verified. His [GitHub profile](https://github.com/dtolnay)
identifies the account as David Tolnay; the project manifests below independently
name him as author. The attempted dtolnay.github.io page did not load.

## Primary evidence

- [Anyhow 1.0.104 Context](https://docs.rs/anyhow/1.0.104/anyhow/trait.Context.html),
  particularly **Effect on downcasting** and **with_context**. Readable at review.
  Supports retained downcasts across anyhow context, typed operation context,
  marker trait bounds, and lazy construction.
- [Anyhow 1.0.104 Error](https://docs.rs/anyhow/1.0.104/anyhow/struct.Error.html),
  sections **new**, **msg**, **chain**, and **downcast_ref**. Readable at review.
  Supports preserving error objects and independently inspecting their causes.
- [Anyhow 1.0.104 implementation](https://docs.rs/anyhow/1.0.104/src/anyhow/error.rs.html),
  `construct_from_std`, `object_downcast`, `context_downcast`, and
  `context_chain_downcast`. Readable at review. The ordinary-object downcast checks
  the stored concrete type, whereas anyhow's context-specific implementation
  traverses its context representation. This source review supports the explicit
  distinction from recursively inspecting an arbitrary `source()` chain.
- [Thiserror 2.0.21](https://docs.rs/thiserror/2.0.21/thiserror/), **Details**.
  Readable at review. Documents the restrictions on `#[from]`, source handling,
  and transparent forwarding. Supplying operation fields through `map_err` is
  this fixture's original application of those constraints.
- [Anyhow manifest](https://github.com/dtolnay/anyhow/blob/master/Cargo.toml)
  and [Thiserror manifest](https://github.com/dtolnay/thiserror/blob/master/Cargo.toml)
  were read through the GitHub connector. At review they declare versions
  1.0.104 and 2.0.21, respectively, David Tolnay as author, and minimum Rust
  versions 1.68 and 1.77. These manifest links are moving references; use the
  version-specific documentation above for the reviewed API contracts.

## Existing-skill boundary

All three existing files were read through the GitHub connector on the review date:

- [Compile-time invariants](https://github.com/narenaryan/agent-skills/blob/main/skills/rust/rust-compile-time-invariants/SKILL.md)
- [Runtime bug classes](https://github.com/narenaryan/agent-skills/blob/main/skills/rust/rust-runtime-bug-classes/SKILL.md)
- [Deterministic concurrency tests](https://github.com/narenaryan/agent-skills/blob/main/skills/rust/rust-deterministic-concurrency-tests/SKILL.md)

The new skill addresses information lost or hidden at error-representation
boundaries. It does not repeat their construction invariants, filesystem/input
hazards, or schedule-testing guidance. General advice to propagate errors does
not distinguish typed context from ordinary source chains.

## Original fixture and expected observations

`examples/src/lib.rs` is original safe Rust, using synthetic `std::io::Error` values and
in-memory `Result` arguments. It performs no filesystem, network, process,
environment-mutation, or unsafe operations. Seven tests cover:

1. Downcasting both typed context and the original error after adding text.
2. A deliberately insufficient direct-only classifier and its source-chain remedy.
3. Stringification losing the original wrapper and cause, followed by a
   value-preserving alternative with the same outer display text.
4. Explicit `map_err` retaining the policy field and the source kind.
5. Negative controls for an unrelated missing input and a permission failure.
6. Classification remaining stable when human-readable context changes.
7. Lazy context preparation on failure and no preparation on success.

The classification rule is deliberately local to the example: a missing policy
requires both its operation marker and a NotFound cause. It does not prescribe
application recovery decisions or authorize retries.

## Validation limits and reproduction

The preparation environment has neither `rustc` nor `cargo` on PATH. The fixture
has been source-reviewed but **has not been compiled or run**. No dependencies
were downloaded, no software was installed, and no upstream code was executed.

`Cargo.toml` pins direct dependencies to `anyhow = "=1.0.104"` and
`thiserror = "=2.0.21"` and uses edition 2021. No fixture MSRV is declared or
verified; the dependency MSRVs quoted above are their own declarations.
Transitive dependencies are not locked, so these pins are not a fully reproducible
dependency graph. No Cargo.lock was fabricated. Default std features are used;
nightly backtrace-provider features are outside this fixture.

In an authorized Rust environment, review the manifest, resolve dependencies,
record the toolchain and lockfile, and run the following command only when the
required dependency cache is already provisioned:

```bash
cargo test --offline --manifest-path examples/Cargo.toml
```

Run it from the skill directory containing this SOURCES.md. This command does not authorize dependency
downloads or installation. Treat the seven expected observations as
unverified until that test run succeeds. Dependency retrieval and build activity
are separate from the fixture's lack of external I/O.
