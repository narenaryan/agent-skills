# Sources and validation

Reviewed November 16, 2026. This is historical-backlog research, not a new-article alert.

## Primary evidence

- Daniel Lemire, [In C++, = default and {} are not the same constructor](https://lemire.me/blog/2026/11/02/default-and-braces-are-not-the-same-constructor/), November 2, 2026. Motivation: compiler-dependent constructor performance. The article's timing and GCC 15/16 behavior were **not** reproduced. No upstream benchmark code was executed.
- C++ working-draft N4861 [initialization](https://timsong-cpp.github.io/cppwp/n4861/dcl.init): default/value initialization and zero-initialization of scalar/class subobjects. The draft mirror is a historical C++20 reference, not the current published ISO document.
- N4861 [explicitly-defaulted functions](https://timsong-cpp.github.io/cppwp/n4861/dcl.fct.def.default): first-declaration defaulting versus user-provided later definitions, and constexpr compatibility.
- N4861 [aggregates](https://timsong-cpp.github.io/cppwp/n4861/dcl.init.aggr): user-declared constructor exclusion and omitted element initialization.
- N4659 [aggregates](https://timsong-cpp.github.io/cppwp/n4659/dcl.init.aggr): historical C++17 user-provided/explicit/inherited constructor exclusion, contrasted with C++20 user-declared exclusion.
- N4861 [member initialization](https://timsong-cpp.github.io/cppwp/n4861/class.base.init), paragraphs 9–10: omitted members use their default member initializer when available; an explicit mem-initializer overrides it.
- N4861 [constexpr rules](https://timsong-cpp.github.io/cppwp/n4861/dcl.constexpr), paragraphs 6–7: a non-template, non-defaulted constexpr constructor must have some valid constant-initialization path; otherwise the program is ill-formed, no diagnostic required. Template specialization has a separate rule.
- N4861 [static initialization](https://timsong-cpp.github.io/cppwp/n4861/basic.start.static): separate static/thread-storage initialization phase.
- Current working draft [default constructors](https://eel.is/c++draft/class.default.ctor) and [defaulted definitions](https://eel.is/c++draft/dcl.fct.def.default), read November 16: corroborate triviality conditions and user-provided distinction. These are rolling draft pages; current draft wording/features are not treated as C++20 compiler support.

## Original experiment

`check_contracts.py` generates isolated translation units in a temporary directory using already installed GCC. Its C++20 cases distinguish first-defaulted, empty, and late-defaulted constructors; default member initializers; triviality; array initialization; and wrapper member omission versus explicit value-initialization. Separate C++17/C++20 probes exercise changed aggregate eligibility and a previously viable brace call.

Negative probes are compiled only and require a specific GCC diagnostic fragment. The first- and late-defaulted constructors are explicitly constexpr. The empty-body constructor uses a class-template surrogate with a demonstrated valid specialization, avoiding both a non-constexpr-call confound and C++20 ill-formed-no-diagnostic-required definitions. The omitted-wrapper probe uses the same template technique. Two deliberately incorrect trait assertions are rejected. These are semantic counterexamples, not a mutation-coverage metric or a proof that an arbitrary production change is wrong.

Independent review found and repaired the original non-template empty constexpr surrogate and omitted-wrapper definition; pre-review pass results are superseded. Seventeen compile accept/reject cases and three valid-runtime configurations (debug, release with NDEBUG, and UBSan) passed on installed GCC 14.2.0, Debian x86_64. The runtime checks use only initialized values, including a static object whose zero-initialization masks an empty constructor. No negative executable is produced or run. Assertions are compile-time or explicit return checks, not removable runtime `assert` calls.

Run from this directory:

```sh
python3 check_contracts.py
python3 check_review_contracts.py
```

Python uses only the standard library. `CXX` may name another compiler executable, but diagnostic matching is GCC-oriented; other compilers are not validated. Temporary files are owned and cleaned by the harness. No installation or fetched third-party code execution.

## Independent review

All seven linked initial sources plus N4861 member-initialization/constexpr rules and N4659 aggregates were read. The corrected primary harness passed normally and under Python `-O`. Six additional compile accept/reject probes and three initialized-runtime configurations passed in both interpreter modes on the same GCC 14.2.0. They cover late-defaulted member initializers, member-initializer override, null-pointer initialization, ordinary non-constexpr traits, rejected empty-body array constant initialization, a deliberately wrong DMI/triviality assertion, and static/thread/function-static storage. Final parent review also caught an impossible non-template constexpr function in the independent array probe; it now uses a function template with a demonstrated valid specialization. The stated independent passes are the reruns after that correction. Diagnostic assertions are GCC-specific. No uninitialized runtime read was added.

An exploratory nested non-trivial case remains unresolved, **not a passing validation**: GCC 14.2.0 rejected the following as an incompletely initialized constant in both C++20 and C++23 modes:

```cpp
struct Ready { int n = 7; };
struct Outer { int count; Ready member; constexpr Outer() = default; };
constexpr Outer a{};
static_assert(a.count == 0 && a.member.n == 7);
```

The reviewer expected value-initialization's initial zero phase to preserve `count`; no second compiler or implementation root-cause analysis was available. This observation is not asserted to establish a language rule or compiler defect. It prevents extrapolating the passing simple-class probes to all nested non-trivial cases; the table's explicitly simple scope is unchanged. The exploratory program was compile-only, never executed, and is outside the six passing review cases.

## Limits

Not an exhaustive language conformance suite, production lifetime/ABI audit, allocation/container matrix, sanitizer proof of initializedness, timing benchmark, or agent-effectiveness experiment. No claim about every combination of bases, access controls, unions, reference members, allocator hooks, exceptions, padding or C++26 rules. Existing repository `test.sh` is absent; these focused checks are not a repository-wide test pass. No security settings, host skills, registry, CI, or production changes.
