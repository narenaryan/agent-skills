---
name: rust-compile-time-invariants
description: Use when designing Rust APIs, structs, or enums to make invalid states unrepresentable and force the compiler to flag missed updates when fields/variants change — covers private-field sealing, #[non_exhaustive], #[must_use], TryFrom over fallible From, slice pattern matching over indexing, explicit destructuring in trait impls, exhaustive enum matches without `_`, parameter structs over boolean flags, and the clippy lints that enforce these
---

# Rust Compile-Time Invariants

Core rule: **put the compiler in charge of enforcing invariants.** Every pattern below converts a runtime check or convention into a compile error when the type evolves.

## Construction & invariants

| Need | Construct |
|---|---|
| Force validation on every instance (intra-crate) | Add `_private: ()` field; only the validating `new()` can fill it |
| Same, but block even same-module bypasses | Nested module + private `Seal` struct; `pub use inner::S` |
| Force callers through constructor at crate boundary | `#[non_exhaustive]` on the struct/enum |
| Mark a value that must be consumed | `#[must_use = "Configuration must be applied to take effect"]` |
| Conversion that can fail | `TryFrom<T>`, never `From<T>` with `unwrap_or_else` |

`_private: ()` enforces intra-crate; `#[non_exhaustive]` enforces cross-crate. Pick by scope.

## Pattern matching that survives refactors

```rust
// Slice patterns — no indexing, length and access in one step
match users.as_slice() {
    []            => /* empty */,
    [only]        => /* exactly one */,
    [first, rest @ ..] => /* head/tail */,
}

// Destructure in trait impls so adding a field is a compile error
impl PartialEq for Order {
    fn eq(&self, other: &Self) -> bool {
        let Self { size, toppings, ordered_at: _ } = self;   // _ is intentional
        let Self { size: s2, toppings: t2, ordered_at: _ } = other;
        size == s2 && toppings == t2
    }
}

// Exhaustive enum match — no `_` arm
match state {
    State::Init | State::Ready => start(),
    State::Running             => tick(),
    State::Done                => cleanup(),
}   // adding State::Failed forces a compile error here

// Default fill that breaks loudly when fields are added
let Foo { a, b, c, d } = Foo::default();
let foo = Foo { a: my_a, b: my_b, c, d };   // not `..Default::default()`
```

## API shape

- **Replace boolean parameters** with enums or a parameter struct. `process(data, true, false, true)` is unreadable; `process(data, Params::production())` is.
- **Scoped temporary mutability** — bind once, mutate inside a block, return immutable:
  ```rust
  let data = { let mut v = fetch(); v.sort(); v };
  ```
- Name ignored fields (`has_fuel: _`, not bare `_`) so reviewers can see what was deliberately skipped.

## Clippy enforcement

Add to `Cargo.toml`:

```toml
[lints.clippy]
indexing_slicing            = "deny"   # forces slice patterns / .get()
fallible_impl_from          = "deny"   # forces TryFrom when conversion can fail
wildcard_enum_match_arm     = "deny"   # bans `_ =>` on enums
wildcard_in_or_patterns     = "deny"
unneeded_field_pattern      = "deny"   # bans `..` when fields could be named
fn_params_excessive_bools   = "deny"
must_use_candidate          = "warn"
```

## Pitfalls

- `#[non_exhaustive]` blocks struct-literal construction **only across crates**. Inside the defining crate, anyone can still build the struct directly — combine with `_private: ()` if you also need intra-crate enforcement.
- `#[must_use]` on a function applies to the return value, not the function. To force callers to use a *type* everywhere it appears, put `#[must_use]` on the type definition.
- `wildcard_enum_match_arm` fires on `_ => unreachable!()` too; use explicit `Variant::A | Variant::B => unreachable!()` so future variants surface.
- `Self { ordered_at: _, .. }` defeats the destructure-forces-update trick — `..` silently absorbs new fields. Use named `_` for each ignored field, never `..`.
- Sealed types via private field break `#[derive(Default)]` and serde's default deserialization — provide an explicit `Default` impl that goes through the constructor, or accept that defaults are unavailable.
- `TryFrom` is auto-implemented for any `From`, so adding `TryFrom` next to an existing `From` causes a conflicting-impl error; remove the `From` first.
