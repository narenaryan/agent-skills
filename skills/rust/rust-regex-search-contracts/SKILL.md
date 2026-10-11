---
name: rust-regex-search-contracts
description: Use when Rust regex refactors change match offsets, sliced searches invent word boundaries, a lexer skips invalid input, or multi-pattern searches choose the wrong token after switching engines.
---

# Rust Regex Search Contracts

Search configuration is part of correctness. A faster engine is interchangeable only when its match policy, boundary context, offsets, and failure behavior match the caller's contract.

## Choose the contract first

| Need | Construct | Trap |
|---|---|---|
| Boolean existence | `meta::Regex::is_match` | Computing captures adds unnecessary work |
| Search a region | `Input::new(full).span(start..end)` | Slicing changes boundary context and rebases offsets |
| Match at a lexer cursor | `.anchored(Anchored::Yes)` | Unanchored search silently skips unmatched bytes |
| Token identity plus span | `meta::Regex::new_many` | Pattern order breaks equal-start ties; this is not longest-token selection |
| Specialized engine | Fallible search plus explicit fallback | `MatchError` is indeterminate, not “no match” |

Prefer the meta engine unless measured requirements justify owning lower-level limitations. It composes engines and fallbacks; choosing a standalone DFA also transfers unsupported-input handling to you.

## Preserve context

With `regex-automata = "=0.4.13"`:

```rust
use regex_automata::{meta::Regex, Anchored, Input};
let re = Regex::new(r"\bcat\b")?;
let hay = "bobcat!";
assert!(re.is_match(&hay[3..6])); // Wrong context: invents a word.
assert!(!re.is_match(Input::new(hay).span(3..6)));

let token = Regex::new(r"[a-z]+")?;
let input = Input::new("!cat").span(0..4).anchored(Anchored::Yes);
assert!(token.find(input).is_none()); // Reject the gap; don't skip '!'.
```

`Anchored::Yes` refers to the search start. Default `^` refers to the haystack start; multiline mode changes its meaning again. Validate input ranges before searching. Keep returned offsets in the original byte coordinate system.

Before replacing an engine, compare pattern IDs, spans, captures, empty matches, Unicode cases, and errors, not just match counts. The [fixture](examples/src/lib.rs) provides six failure/remedy cases; [provenance](SOURCES.md) records runtime limits.

## Pitfalls

- Reordering alternatives or patterns changes leftmost-first results. Longest-token lexing needs its own explicit selection policy.
- `earliest(true)` may change the chosen match; it is not a semantics-preserving speed switch.
- `MatchKind::All` is not a drop-in “find every occurrence” mode for ordinary unanchored iteration.
- Handwritten cursor loops can stall on empty matches; use the engine's iterator when its non-overlapping semantics fit.
