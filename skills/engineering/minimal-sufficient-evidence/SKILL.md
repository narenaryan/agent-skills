---
name: minimal-sufficient-evidence
description: Use when designing or reviewing tests, debugging plans, regression suites, process metrics, documentation templates, predictive models, or root-cause analyses to remove redundancy and keep only the smallest evidence set that still supports the decision
---

# Minimal Sufficient Evidence

Use this skill when a workflow is growing by accumulation: more tests, more metrics,
more bug hypotheses, more template fields, more model variables, or more root-cause
factors. The goal is not minimalism for its own sake; it is the smallest set that
still distinguishes the important cases and supports the next decision.

## Working rule

For every proposed artifact, ask:

1. What hypothesis, decision, or failure mode does this cover?
2. Is that already covered by something else with the same signal?
3. What breaks if we remove it?

Keep the item only when it adds independent signal, catches a distinct risk, or
materially improves reproducibility.

## Regression tests

Do not add tests that assert the same behavior through cosmetic variations.
Before writing a new regression test:

- Name the exact bug or invariant being protected.
- Identify the smallest fixture that reproduces it.
- Check nearby tests for the same hypothesis, not just the same code path.
- Prefer one table-driven test with meaningful cases over many copied tests.
- Keep duplicates only when they exercise different layers, encodings,
  concurrency shapes, trust boundaries, or platform behaviors.

When pruning a suite, remove or merge tests that fail and pass together for the
same reason. Preserve one canonical test with the clearest failure message.

## Bug search

Use the scientific method. Treat each step as an experiment:

- State one hypothesis.
- Change one variable.
- Run the smallest reliable reproduction.
- Record the result.
- Narrow the search space.

Use delta debugging when the input, patch, configuration, or environment is too
large: repeatedly split it, test each half, and keep the smallest subset that
still fails. Stop when further reduction would remove the failure or make the
case unrealistic.

## Metrics

Use a small metric set that covers the process characteristics you actually need
to manage. Each metric must have an owner, a decision it informs, and a known
failure mode. Drop vanity metrics and highly correlated metrics unless they catch
different risks.

Good metric sets usually include one measure of volume, one of quality, one of
speed or latency, and one of risk when those dimensions matter. Do not measure
because measurement is possible.

## Documentation templates

Template fields must earn their place. For bug reports, keep fields that help
someone reproduce and diagnose the failure:

- observed behavior
- expected behavior
- exact reproduction steps
- minimal input or fixture
- environment/version
- relevant logs, screenshots, or traces
- first known bad and last known good, when available

Remove fields that people routinely leave blank, invent, or cannot use in a
later workflow.

## Predictive models

Prefer the fewest variables that provide stable predictive power. Start with a
simple baseline and add variables only when they improve out-of-sample behavior
or explain a known mechanism. Watch for proxies, leakage, multicollinearity, and
variables that make the model harder to maintain without improving decisions.

Use as few variables as possible, but not fewer: keep variables required for
fairness, calibration, known causal structure, or important segment performance.

## Root cause

End with the crucial factors, not the whole investigation history. Usually there
is one cause, or a small interacting set. Separate:

- root cause: the condition that made the failure possible
- trigger: the event that exposed it
- contributing factors: conditions that made it worse
- non-causes: plausible hypotheses ruled out by evidence

The final analysis should explain why the selected cause is sufficient and why
discarded explanations are not needed.

## Pitfalls

- Deleting tests only because they look similar; compare the hypothesis they
  protect.
- Keeping tests only because they touch different lines; line coverage is not
  independent evidence.
- Adding metrics without naming the decision they change.
- Letting templates become questionnaires instead of workflow tools.
- Treating correlation-heavy model features as independent signal.
- Publishing root-cause writeups that list every observation instead of the
  decisive factors.
