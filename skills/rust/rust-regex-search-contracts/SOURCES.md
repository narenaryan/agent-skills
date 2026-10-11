# Provenance and validation

Reviewed 2026-10-11. Original synthesis and small authored regression fixtures; no article code was downloaded or executed.

## Sources

- Andrew Gallant, [Regex engine internals as a library](https://burntsushi.net/regex-internals/), published 2023-07-05. Historical motivation: composable engines, first-class multi-pattern results, fallible low-level searches, and meta-engine fallbacks. Its examples target regex-automata 0.3 and are not copied as current APIs.
- [regex-automata 0.4.13 Input](https://docs.rs/regex-automata/0.4.13/regex_automata/struct.Input.html): region context, original offsets, search anchoring versus pattern anchors, earliest matching, and invalid bounds.
- [regex-automata 0.4.13 meta::Regex](https://docs.rs/regex-automata/0.4.13/regex_automata/meta/struct.Regex.html): multi-pattern IDs, boolean queries, UTF-8 empty matches, and iterator contracts.
- [regex-automata 0.4.13 MatchKind](https://docs.rs/regex-automata/0.4.13/regex_automata/enum.MatchKind.html): preference ordering and why All is unsuitable as a general unanchored find-all switch.

The version pin is a documentation/fixture compatibility target, not a claim that this is the newest release. Do not mechanically port the historical post's 0.3 examples.

## Coverage and limits

Six authored Rust tests reproduce slicing false positives, offset rebasing, lexer gaps/caret confusion, short-first token selection, Unicode empty-match iteration, and boolean versus greedy-span distinctions. Each asserts the problematic behavior and/or the intended remedy using fixed inputs. They do not benchmark speed, certify arbitrary patterns, or exercise low-level MatchError fallback. That fallback advice is documentation-verified only.

Rust runtime tests were **not run**: neither rustc nor cargo is available on the research executor's PATH. No dependencies or toolchains were installed. Review and Markdown/TOML/structure checks do not establish compilation or test success. The fixtures intentionally contain test-only unwraps on fixed patterns; these are not recommendations for untrusted patterns.

From the repository root, on an already provisioned toolchain and dependency cache:

```sh
cargo test --offline --manifest-path skills/rust/rust-regex-search-contracts/examples/Cargo.toml
```

No Cargo.lock was generated because dependency resolution was not run. The direct crate is exact-pinned; transitive versions remain unresolved until validation. Record the Rust version and resolved lockfile when running. An offline cache miss is a blocker, not permission to fetch or install software.

## Deduplication

The existing Rust runtime-bug skill discusses byte preservation and syscall boundaries, compile-time-invariants covers API shape, and deterministic-concurrency-tests covers schedule exploration. None specifies regex match policy, context-preserving region searches, or pattern priority. The new skill owns only that contract.
