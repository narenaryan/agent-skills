---
name: signed-division-contracts
description: Use when a profiled C++ integer hot path divides signed 32-bit values by compile-time constants, reciprocal multiplication changes negative results, or a hand-written division optimization must be checked against compiler-generated code.
---

# Signed Division Contracts

A reciprocal identity is not yet a valid machine optimization: the input domain, intermediate width, rounding rule, and generated dependency chain must all agree. Keep ordinary division as the baseline until correctness **and target-workload benefit** are established.

## Narrow the contract

| Boundary | Required decision |
|---|---|
| Numerator | Exactly `std::int32_t`, including `INT32_MIN`; never take its 32-bit absolute value |
| Divisor | Positive compile-time constant, not a power of two; reject unsupported inputs |
| Language | C++20 or later; signed right shift rounds downward, integer division truncates toward zero |
| Intermediate | Multiply in signed 64 bits, not unsigned or 32 bits |
| Adoption | Inspect optimized assembly, then measure actual application behavior; fewer source operations prove neither latency nor throughput |

## A constrained candidate

This candidate explicitly constrains its domain:

```cpp
#include <bit>
#include <cstdint>

template<std::int32_t D>
  requires (D > 0 && !std::has_single_bit(std::uint32_t(D)))
constexpr std::int32_t divide_candidate(std::int32_t x) {
  constexpr int shift = 31 + std::bit_width(std::uint32_t(D) - 1u);
  constexpr std::uint64_t scale = std::uint64_t{1} << shift;
  constexpr auto multiplier = scale / D + (scale % D != 0);
  static_assert(multiplier < (std::uint64_t{1} << 32));
  const auto product = std::int64_t(x) * std::int64_t(multiplier);
  return std::int32_t((product >> shift) + (x < 0));
}
```

For this domain, `shift` is at most 62 and the multiplier is below `2^32`, bounding the product within signed 64 bits. The upward reciprocal approximation makes every nonzero scaled magnitude nonintegral; the negative correction is required **even for exact multiples**, not merely when `x % D != 0`. See the [derivation and evidence](SOURCES.md).

## Verify before adopting

1. Compare against `int64_t(x) / int64_t(D)` at both signed endpoints, zero, negative values, and either side of quotient boundaries. Include divisors near powers of two and near `INT32_MAX`.
2. Reject unsupported constants at compilation. Kill mutants that omit the negative correction or replace the arithmetic shift with truncating division while retaining that correction.
3. Build optimized and sanitizer configurations. The [original fixture](test_division.cpp) uses explicit failures, so `NDEBUG` does not disable checks.
4. Compare constant-specialized assembly with plain `x / D`. Test an add-back case (7) and a control (1000). Separate dependency-chain latency, independent throughput, vectorization, and whole-application measurements; retain `/` unless the relevant workload improves.

## Pitfalls

- Widening after multiplication is too late: overflow has already occurred.
- Reusing this formula for powers of two breaks its nonintegrality argument and negative exact multiples.
- C and pre-C++20 signed-shift rules require a separate portability analysis.
- A runtime divisor, unsigned numerator, or 64-bit numerator needs a different derivation, not relaxed guards.
- Reject zero divisors and `INT32_MIN / -1`: ordinary division is not a safe fallback for undefined inputs.
- Sampled tests do not prove speed or exhaustive coverage.
