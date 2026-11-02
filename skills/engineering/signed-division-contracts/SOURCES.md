# Sources and validation

Reviewed 2026-11-02; source publication dates are not discovery dates.

## Primary sources

- [Daniel Lemire, Beating the compiler at signed 32-bit division](https://lemire.me/blog/2026/10/31/beating-the-compiler-at-signed-32-bit-division/), published 2026-10-31, first seen 2026-10-31. Research lead, not a universal performance guarantee. Its constant-divisor investigation motivated widening the product and using a non-improving divisor as a control. The runtime-divisor library discussion is outside this skill.
- [Lemire, Bartlett and Kaser, Integer Division by Constants: Optimal Bounds, v3](https://arxiv.org/html/2012.12369v3), revised 2021-06-29; historical reference backfill. Theorem 1 supplies reciprocal-approximation conditions; its following discussion establishes a sufficient scale bound. No paper implementation was downloaded or executed.
- C++20 working draft N4861, [shift operators](https://timsong-cpp.github.io/cppwp/n4861/expr.shift) and [multiplicative operators](https://timsong-cpp.github.io/cppwp/n4861/expr.mul), frozen language reference mirrored from the standard draft: signed right shift rounds down; integer division truncates; invalid shift counts and unrepresentable division results are undefined. Current draft [shift](https://eel.is/c++draft/expr.shift) and [division](https://eel.is/c++draft/expr.mul) wording was also checked. The official N4861 PDF retrieval failed to parse; the frozen HTML sections were read instead.

## Original derivation

Let `N=2^31`, `k=ceil(log2 d)`, `m=2^(31+k)`, `c=ceil(m/d)` and `delta=cd-m`. For positive non-power-of-two `d`, `0<delta<d` and `m>=Nd`. For `0<n<=N`,

`cn/m = n/d + n*delta/(m*d)`, with `0<n*delta/(m*d)<1/d`.

Since the fractional steps of `n/d` are multiples of `1/d`, the perturbed value has the same floor and is never integral. Consequently `floor(-cn/m)+1=-floor(n/d)`, including when `n` is divisible by `d`. Zero needs no correction. This proves the rounding identity over the stated domain independently of the sampled tests.

As `d>=2^(k-1)+1` and `d<2^31`, `c<2^32`. Therefore `|x*c|<2^63`; the product fits `int64_t`. The recipe never computes `abs(INT32_MIN)` and narrows only the representable quotient. None of this establishes performance.

## Reproduce isolated checks

From this directory, with an existing GCC installation:

```sh
g++ -std=c++20 -Wall -Wextra -Wconversion -Werror -O0 test_division.cpp -o /tmp/division-debug
/tmp/division-debug
g++ -std=c++20 -Wall -Wextra -Wconversion -Werror -O3 -DNDEBUG test_division.cpp -o /tmp/division-release
/tmp/division-release
g++ -std=c++20 -Wall -Wextra -Wconversion -Werror -O2 -fsanitize=undefined -fno-sanitize-recover=all test_division.cpp -o /tmp/division-ubsan
/tmp/division-ubsan
g++ -std=c++20 -O3 -fno-tree-vectorize -DASSEMBLY_ONLY -S -masm=intel test_division.cpp -o /tmp/division-assembly.s
```

Actual environment: x86_64, Debian GCC 14.2.0-19. Each executable passed 10,487,820 oracle comparisons across 32,928 divisor trials (trials may repeat divisors), ten runtime-domain rejections and two rounding-mutant detections. The cases include all signed 16-bit numerators for eight divisors, endpoint/multiple neighborhoods, and a deterministic generated sample. Template-specialized 7 and 1000 paths are also compared. No `assert` dependency. The literal C++ block extracted from `SKILL.md` additionally passed 1,324,320 oracle comparisons in both optimized and UBSan builds; constrained instantiations for 0, -7 and 8 failed compilation as expected. These extraction/negative-compile harnesses remain task evidence, not a repository test runner.

Observed scalar assembly: for 7, the widened candidate removed the baseline's post-multiply add-back sequence. For 1000, the baseline already lacked that sequence and the candidate required a separately loaded wider multiplier. This is code-generation evidence, not a measured performance improvement.

Limits: no exhaustive full int32 input/divisor Cartesian test, other compiler/architecture execution, timing benchmark, vectorized/application benchmark, downloaded library execution, or production validation. Clang was unavailable. GCC compile-time rejection checks for 0, -7 and 8 are recorded in task evidence; normal division is not invoked on invalid domains. No repository-wide test suite is implied.
