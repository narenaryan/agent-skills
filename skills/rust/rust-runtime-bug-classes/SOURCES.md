# Panic-boundary correction, 2026-10-11

This note documents only the changed panic/lint paragraph. The other pre-existing filesystem, byte, CLI, and sandbox guidance was preserved; this pass does not certify every historical claim in the skill.

- Andrew Gallant, [Using unwrap() in Rust is Okay](https://burntsushi.net/unwrap/), published 2022-08-08, read 2026-10-11: expected failures and broken programmer-maintained invariants need different handling. A justified expect is not automatically an input-handling vulnerability.
- [Rust Reference: overflow](https://doc.rust-lang.org/stable/reference/expressions/operator-expr.html#overflow), read 2026-10-11: arithmetic behavior depends on operation and overflow-check settings. The previous statement that addition/subtraction always panic on attacker-controlled input was too broad.
- [Cargo manifest lints](https://doc.rust-lang.org/cargo/reference/manifest.html#the-lints-section), read 2026-10-11: lint levels belong under [lints.clippy] in Cargo.toml, not as bare lint-name entries in clippy.toml. Cargo's lints table requires Rust/Cargo 1.74 or later.

Validation: the revised TOML block is parsed as data; no Clippy, compiler, input-attack test, or production program was run. Toolchain unavailable. This is a source-grounded documentation correction, not a new skill or a claim that lints prevent every panic.
