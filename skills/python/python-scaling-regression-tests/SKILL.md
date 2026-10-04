---
name: python-scaling-regression-tests
description: Use when Python code remains fast on small fixtures but slows disproportionately with input size, or a refactor may turn a linear algorithm quadratic; applies to empirical complexity regression tests, size-function design, and bigO measurement isolation.
---

# Python Scaling Regression Tests

Test how cost grows, separately from how many milliseconds one execution takes. A faster implementation can still have a worse growth curve. An empirical fit is evidence over sampled inputs, not an asymptotic proof.

## Choose the experiment

| Decision | Constraint |
|---|---|
| Size function | Represent the work-driving dimension; use constant-time metadata such as `len(a) + len(b)`, not a traversal |
| Input family | Exercise meaningful sizes and distributions; separate early-exit, worst-case, and duplicate-heavy cases |
| Timing boundary | Construct fixtures outside the measured function; include copying only when copying is part of its contract |
| Claim | Pair growth checks with output assertions; keep absolute-latency budgets separate |

## Isolated bound check

Use a dedicated performance-test process. The upstream `plasma-umass/bigO` API checked on 2026-10-04 exposes `assert_bounds` and `disable_persistence`; verify the project's pinned dependency.

```python
from bigO import assert_bounds, disable_persistence

disable_persistence()  # Dedicated test process: suppress exit-time JSON writes.

def unique_count(values):
    seen = set()
    for value in values:
        seen.add(value)
    return len(seen)

def test_unique_count_scaling():
    samples = [(list(range(n)),) for n in range(2_000, 82_000, 2_000)]
    assert unique_count([2, 2, 5]) == 2
    assert_bounds(unique_count, lambda values: len(values), samples,
                  time="O(n)")
```

`assert_bounds` clears prior in-memory measurements. A short `no_persistence()` block restores the save flag afterward, so it does not prevent later exit-time writes. For exploratory `track` runs, use a fresh directory so accumulated `bigO_data.json` cannot mix experiments.

Before trusting the gate, temporarily substitute a behavior-equivalent quadratic implementation and confirm rejection. Repeat the unchanged baseline to check noise sensitivity; restore the real implementation afterward. Record the dependency version and input family with the result.

Sources: [Python⇒Speed, 2026-01-07](https://pythonspeed.com/articles/big-o-tests/), [upstream API and caveats](https://github.com/plasma-umass/bigO#using-bigo-in-unit-tests), [checked implementation](https://github.com/plasma-umass/bigO/blob/a8533ee35b8fd3b0d52aa77915a073400cece817/bigO/bigO.py).

## Pitfalls

- One size or tiny inputs can hide a growth change beneath call overhead.
- A passing bound misses constant-factor slowdowns and untested input distributions.
- Concurrent calls are outside bigO's supported measurement model; isolate the benchmark.
- Do not fix flaky results by silently weakening the bound. Inspect samples, environment noise, and the chosen size metric first.
