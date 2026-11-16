---
name: cpp-constructor-contracts
description: Use when replacing an empty C++ constructor with = default, moving a defaulted constructor out of class, diagnosing zero-initialization or type-trait regressions, or evaluating a constructor-related optimization across language modes.
---

# Audit constructor refactors as contract changes

An empty body and `= default` can produce similar instructions yet select different initialization semantics. Track **the first declaration**, the caller's initialization form, storage duration, and member initializers before comparing generated code. Scope below: ordinary non-union classes, C++20.

## Distinctions that survive an empty body

For an otherwise simple class containing `int n;`, without a member initializer:

| Constructor | User-provided? | Automatic `T t;` | Automatic `T t{};` |
|---|---|---|---|
| In-class `T() = default;` on first declaration | No | `n` uninitialized | `n` zero-initialized |
| In-class `T() {}` | Yes | `n` uninitialized | `n` uninitialized |
| `T();` then `T::T() = default;` | Yes | `n` uninitialized | `n` uninitialized |

These classes are non-aggregates in C++20 because their constructors are user-declared. Do not generalize the table to aggregate initialization, unions, or constructors that initialize members. A default member initializer such as `int n = 7;` establishes a value in all three cases, but makes the default constructor non-trivial.

## Review recipe

1. Inventory actual callers: automatic declarations, brace construction, arrays, wrapper member initialization, and static/thread-storage objects. A global fixture can conceal a missing initialization through earlier static zero-initialization. An outer user-provided constructor does not imply the inner object is uninitialized: `Outer() : member() {}` value-initializes that member; omission uses its default member initializer if present, otherwise default-initializes it.
2. Record required traits separately. First-declaration defaulting permits trivial default construction only when the remaining class conditions hold. An empty body or later defaulting prevents it. Check aggregate status under the actual language mode: the simple first-defaulted class can be an aggregate in C++17, but not C++20; an existing `T{9}` call may stop compiling.
3. Build positive and negative translation units. Use valid `constexpr`-capable surrogates and inspect rejection reasons; a non-constant constructor rejection alone proves nothing about member initialization. In C++20, avoid non-template, non-defaulted `constexpr` constructors with no valid constant-initialization path. Never execute uninitialized scalar reads.
4. If a defined default state is required, preserve it explicitly rather than removing initialization for a benchmark. Member initializers can change traits, so verify the new contract instead of calling them a cost-free substitute.
5. Only after semantic checks, measure the real workload on pinned compiler, flags and target. An assembly difference is not an end-to-end speedup; retain the baseline without measured benefit.

Run the [isolated checks](check_contracts.py) from this skill directory with `python3 check_contracts.py`. See [sources and limits](SOURCES.md).

## Pitfalls

- “Defaulted” does not mean “not user-provided”; declaration order matters.
- Braces do not universally zero every object, and semantic zero-initialization is not a portable `memset` recipe for pointers.
- Passing UBSan does not establish absence of uninitialized reads. The probes deliberately avoid those reads; they do not certify production constructors or ABI compatibility.
