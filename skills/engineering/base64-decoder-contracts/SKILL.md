---
name: base64-decoder-contracts
description: Use when replacing or benchmarking Base64 decoders, a faster implementation changes malformed-input behavior, or strict validation is being mistaken for canonical encoding.
---

# Base64 Decoder Contracts

Equal decoded bytes on clean inputs do not imply interchangeable decoders. Acceptance language, padding, alphabet, and rejection behavior are part of the workload; a fast path plus compatibility fallback must be measured together.

## Separate the contracts

| Contract axis | Discriminating input |
|---|---|
| Ignored characters | CR/LF, spaces, tabs, punctuation inside data |
| Padding | Missing, surplus, leading padding; data after padding |
| Alphabet | Standard `+/`, URL-safe `-_`, mixed forms |
| Canonical form | `Zg==` versus `Zh==`: both decode to `f` on CPython 3.12, even with `validate=True` |
| API | Bytes versus ASCII text, return type, exception class; message only if callers depend on it |

Python 3.12's default decoder discards non-alphabet characters. `validate=True` rejects them, but does not guarantee zero pad bits. RFC 4648 separates non-alphabet handling from canonical encoding; the enclosing protocol decides permitted exceptions. Do not silently tighten a legacy contract while calling a replacement compatible.

## Gate timing on semantics

1. Write the application profile first: permitted alphabet, padding, ignored characters, output ownership, rejection behavior. Pin interpreter/library versions; names such as “strict” or “URL-safe” are not specifications.
2. Build a small independently expected corpus covering the axes above and realistic sizes. Compare complete bytes and expected failures, not just lengths or successful clean round trips. Keep malformed-input correctness separate from its timing.
3. For a canonical, padded, standard-alphabet **bytes-only** profile, decode then require exact re-encoding:

```python
import base64
import binascii

def decode_canonical(data):
    if not isinstance(data, bytes):
        raise TypeError("bytes required")
    decoded = base64.b64decode(data, validate=True)
    if base64.b64encode(decoded) != data:
        raise binascii.Error("noncanonical Base64")
    return decoded
```

This intentionally rejects whitespace and alternate spellings. If the application allows CR/LF, remove exactly those bytes before this check; do not broaden permission with generic whitespace stripping. This is a local profile, not a complete MIME parser.

4. Time the complete compatible operation, including necessary normalization, fallback, validation and allocation. A pre-normalized kernel benchmark is a separate claim. Keep fixture generation outside timing; declare whether cache warmup and GC are included. Python `timeit` excludes setup and disables GC by default.
5. Report encoded-input versus decoded-output byte counts explicitly, decimal GB/s versus GiB/s, input distributions, CPU/kernel selection, and versions. A minimum repeat is a microbenchmark lower bound, not tail latency or end-to-end capacity.

Run `python3 skills/engineering/base64-decoder-contracts/reproduce.py`. [Sources and validation limits](SOURCES.md). Use [scaling regression tests](../../python/python-scaling-regression-tests/SKILL.md) separately for growth curves.

## Pitfalls

- Treating stricter rejection as a compatible optimization when callers accept wrapped input.
- Assuming `validate=True` establishes canonical pad bits across versions.
- Timing only the accelerated path while excluding required compatibility work.
- Turning a workload-specific throughput result into a universal speedup claim.
