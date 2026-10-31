---
name: fixed-key-lookup-contracts
description: Use when replacing a string map with perfect hashing or SIMD comparisons, accepting unknown parser tokens, or reviewing short-buffer loads justified only by page-boundary checks.
---

# Fixed-Key Lookup Contracts

A perfect hash chooses a candidate for a fixed key set; it does not establish membership for arbitrary input. Separately, a readable memory page does not establish permission to read beyond a C++ object.

## Two independent gates

| Gate | Required evidence | Insufficient evidence |
|---|---|---|
| Membership | Candidate length and every logical byte match | Slot exists; known keys have distinct hashes |
| Memory validity | Every loaded byte belongs to valid live storage under the API contract | Load stays on one mapped page; later mask discards excess bytes |

## Recipe

1. Freeze the vocabulary and matching semantics: exact bytes, case folding, embedded NULs, and normalization. Reject unsupported lengths before reading selected character positions. Cast character indices to `unsigned char` before indexing a 256-entry association table.
2. Keep an independent scalar oracle: linear exact comparison over the known keys. Test the optimized candidate selection against it, especially unknown strings sharing known slots, empty input, prefixes, suffixes, same-length one-byte mutations, high-bit bytes, and embedded NULs.
3. Verify length **and** bytes after candidate selection. A prefix comparison or comparison of only a reduced hash is not an exact dictionary lookup.
4. For short inputs, use a length-bounded comparison or copy exactly the logical length into a zero-initialized local block before a full-width comparison. A separate padded-input API may permit wide loads only when callers guarantee sufficient live, readable, initialized storage; `string_view` alone supplies no such padding promise. Include logical length even when stored keys are padded.
5. Test exact-sized allocations under AddressSanitizer, then test ordinary optimized builds. Exercise offsets, short tails and externally supplied views, not only string literals or overallocated strings. ASan passing is evidence for executed cases, not a proof of all object/provenance rules.
6. Benchmark only after correctness: pin compiler, architecture, flags, dependency versions, vocabulary, hit/miss mix and length distribution. Compare equivalent validation, inspect generated code, and keep throughput separate from dependent-query latency. Do not transfer published hardware-specific speedups to your workload.

## Local check

From the repository root, run `python3 skills/engineering/fixed-key-lookup-contracts/scripts/check_lookup.py`. It compiles original C++17 fixtures with an existing `g++`; no downloads. The harness separately expects an intentionally invalid wide read to trigger ASan and checks the corrected lookup against the scalar oracle. It is not a test of a third-party perfect-hash library. See [sources and exact limits](SOURCES.md).

## Pitfalls

- Perfectness applies to the construction set; an unknown key can map to a populated slot.
- Zero-padding can make `GET` and `GET\0` look identical unless length participates.
- Checking page boundaries addresses a hardware fault condition, not C++ allocation bounds; masking afterward cannot undo an invalid read.
- `string_view::data()` need not point to a NUL-terminated string; `strcmp` changes the input contract.
- A deliberately generous test allocation can conceal an overread from ASan.
