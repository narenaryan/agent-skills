# Sources and validation limits

Reviewed 2026-10-31. The recipe and fixtures are original synthesis, not a port or execution of the linked library.

## Primary sources

- [Daniel Lemire: Billion-query-per-second lookup tables in C++](https://lemire.me/blog/2026/10/26/billion-query-per-second-lookup-tables-in-c/), published 2026-10-26, retained from the October 30 backlog. The article separates candidate hashing from final key comparison. Its vector comparison discussion motivates reviewing page checks against language-level storage requirements. Reported Apple hardware performance is not reproduced or generalized. Comments are leads, not normative language authority.
- [C++ working draft: additive operators](https://eel.is/c++draft/expr.add) and [compound types](https://eel.is/c++draft/basic.compound), continuously maintained draft, reviewed 2026-10-31. Pointer arithmetic is bounded by the array object, including a non-dereferenceable past-the-end position; an adjacent address does not grant ownership of another object. Mapped-page continuity is not a substitute for object bounds. Draft wording is current, not a claim that C++17 has newer hardening facilities.
- [C++ working draft: string-view element access](https://eel.is/c++draft/string.view.access), reviewed 2026-10-31. Indexed access requires an in-range position; the exposed buffer need not be NUL-terminated. The fixture uses C++17-compatible interfaces, without relying on the current draft's hardened-precondition machinery.
- [GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html) and [Clang AddressSanitizer documentation](https://clang.llvm.org/docs/AddressSanitizer.html), reviewed 2026-10-31. ASan instruments memory accesses and can detect allocation overflows. The executable evidence here is GCC, not Clang. No sanitizer suppressions are added. Leak checking is disabled for the subprocess because LeakSanitizer cannot operate under this environment's ptrace; leaks are outside the experiment.

GNU gperf's main manual and output-format page timed out during review; no claim depends on their unavailable text.

## Original experiment

Run from repository root:

```bash
python3 skills/engineering/fixed-key-lookup-contracts/scripts/check_lookup.py
```

Existing GCC 14.2.0 on Linux compiles the same original four-key C++17 lookup at `-O0`, `-O2 -DNDEBUG`, and `-O1 -fsanitize=address -fno-omit-frame-pointer -no-pie`. Each configuration checks 5,147 exact-sized inputs against an independent linear oracle: all keys, every one-byte replacement, suffix-byte additions, prefixes, empty and selected misses. Checks use explicit failure exits, not removable assertions. Two compile-time mutations remove membership verification or truncate byte comparison; both must fail the oracle.

A separate subprocess deliberately copies 16 bytes from a three-byte allocation. It first checks an assumed 4-KiB-page boundary predicate; if the control cannot be established, the harness reports inconclusive. ASan must report heap-buffer-overflow. The corrected lookup copies only logical bytes into initialized storage and passes the same input corpus. This demonstrates that the page predicate is insufficient for the allocation case; it is not an audit of a production SIMD implementation.

No throughput benchmark, vector-instruction inspection, third-party perfect-hash execution, guard-page experiment, exhaustive arbitrary-input proof, other compiler/architecture validation, or CI run is claimed. The harness uses GNU `noinline` and Linux-oriented `-no-pie`; port the test deliberately elsewhere. Production callers must separately prove lifetimes, padding, normalization and concurrency constraints. A successful ASan run can miss untested paths and some subobject violations.

## Overlap

`ai-bug-patterns` provides general negative-case guidance; this skill supplies a concrete fixed-vocabulary membership oracle and object-boundary remedy. Open decoder-contract PR #34 concerns decoding semantics rather than key membership or C++ loads. Existing scaling tests cover complexity, not these validity conditions.
