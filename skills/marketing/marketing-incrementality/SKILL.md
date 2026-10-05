---
name: marketing-incrementality
description: Use when attributed ROAS is driving budget decisions, a channel's causal contribution is disputed, or a marketing holdout experiment needs design or interpretation.
---

# Marketing Incrementality

Attribution allocates touchpoint credit; incrementality estimates effects of changing marketing. Randomize eligibility before exposure; compare assigned groups, including people never exposed.

## Design the decision

1. Specify intervention, eligible population, control, decision, and horizon. “Additional paid-search budget” and “all paid search versus none” estimate different effects.
2. Choose a stable randomization unit. Use users or accounts when exposure can be isolated; use non-overlapping randomized geographies when individual assignment is infeasible. Analyze uncertainty at the assignment level, not as millions of independent visits.
3. Predeclare one business outcome, guardrails, minimum decision-relevant effect, significance/power assumptions, duration, conversion lag, exclusions, and fixed-horizon or valid sequential analysis. Estimate feasibility from baseline variability; insufficient traffic makes the design inconclusive.
4. Verify assignment, outcome coverage, spend separation, and contamination. For user-level tests, check observed assignment counts against the planned split. Diagnose sample-ratio mismatch before interpreting lift.
5. Analyze intention-to-treat. Include outcomes across channels; report absolute difference, relative lift, interval, incremental spend, and economic assumptions. A positive estimate alone does not justify scaling.

Deliver the design and decision rule; executing or changing campaigns requires authorization.

## Arithmetic check

Equal randomized groups of 10,000 produce 600 versus 500 purchasers: estimated lift of 1 percentage point, 20% relative, and 100 incremental treatment purchasers. With $5,000 additional spend, cost per incremental purchaser is $50. These illustrative estimates do not establish significance.

For unequal groups, use rates and population scaling rather than subtracting raw totals. Incremental ROAS uses incremental revenue divided by incremental spend; profitability additionally requires contribution margin and incremental operating costs.

## Sources and scope

- [Chen and Au: geo experiments](https://arxiv.org/abs/1908.02922): randomized regional designs; interference and few heterogeneous regions limit precision.
- [Microsoft: sample-ratio mismatch](https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/): user-level assignment diagnostics, not a universal geo-test threshold.
- [Lewis and Rao](https://doi.org/10.1093/qje/qjv023): advertising effects can be difficult to estimate precisely; no universal sample-size rule.

## Pitfalls

- Comparing exposed users with unexposed users introduces selection bias.
- Repeated fixed-horizon significance checks inflate false positives.
- Non-significance does not prove zero effect; ratios become unstable near zero denominators.
- Spillovers, delayed purchases, and changed promotions can invalidate interpretation or restrict generalization.
