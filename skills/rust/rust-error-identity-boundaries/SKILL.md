---
name: rust-error-identity-boundaries
description: Use when adding Rust error context or wrappers changes recovery behavior, or when reviewing anyhow and thiserror boundaries for preserved types, causes, and operation details.
---

# Rust Error Identity Boundaries

Treat diagnostic text, concrete error identity, and the source chain as separate contracts. An informative message does not prove that callers can still classify the failure.

## Preserve the information needed by callers

1. Identify the classification contract before changing an error boundary: a domain variant, a typed operation marker, an underlying source kind, or a combination. Do not branch on formatted messages.
2. Preserve existing errors with `?`, `anyhow::Error::new`, or an explicit domain wrapper.
3. Attach operation information using anyhow context. Typed context can classify the operation while ordinary text explains it. Additional context preserves anyhow's existing downcasts. Context values require `Display + Send + Sync + 'static`; a marker need not implement `std::error::Error`. Use `with_context` for lazily prepared details.
4. Select the traversal the contract requires. Inspect a domain error directly, or use `chain()` and downcast each cause when classification genuinely depends on a lower-level type. Keep operation context as a separate classification condition when necessary.
5. Use explicit `map_err` construction when a thiserror wrapper must retain both operation fields and its original source.

## Regression evidence

Test direct typed-context downcasts, domain-wrapper traversal, and the broken stringification alternative. Add unrelated and different-kind failures as negative controls. Change human-readable context without changing the classification. Assert retained fields and source kinds independently of display text.

The original [fixture](examples/src/lib.rs) uses synthetic errors with no filesystem or network operations. See [provenance and validation limits](SOURCES.md) before running it. Its direct dependencies are version-pinned; compilation and runtime are unverified.

## Pitfalls

- Anyhow context downcasts are not arbitrary source-chain searches. Introducing a domain wrapper changes the concrete underlying error; direct downcasts to its source can fail.
- Stringification destroys original types and causes. Later context cannot reconstruct that information.
- `#[from]` implies `#[source]` but permits only the source field and an optional backtrace, not extra operation fields. `#[error(transparent)]` forwards Display and source behavior rather than adding a diagnostic layer.
