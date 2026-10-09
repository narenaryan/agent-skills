---
name: marketing-incrementality
description: Use when attributed ROAS drives budget decisions, campaign holdout lift is disputed, or experiment groups diverge after logging, joins, filters, or exposure-based segmentation.
---

# Marketing Incrementality

Attribution allocates touchpoint credit; incrementality estimates effects of changing marketing. Randomize eligibility before exposure; compare assigned groups, including people never exposed. Valid assignment does not guarantee valid analyzed cohorts.

## Design the decision

1. Specify intervention, eligible population, control, decision, and horizon. Additional spend and channel shutdown estimate different effects.
2. Randomize stable users/accounts where isolation is feasible; otherwise consider randomized non-overlapping geographies. Analyze uncertainty at the assignment level, not as independent visits.
3. Predeclare outcome, guardrails, decision-relevant effect, power assumptions, duration, conversion lag, exclusions, and fixed-horizon or valid sequential analysis. Check feasibility against baseline variability.
4. Verify outcome coverage, spend separation, contamination, and cohort integrity below before interpreting lift.
5. Analyze intention-to-treat across channels. Report absolute/relative lift, interval, incremental spend, and margin/operating-cost assumptions. Positive estimates alone do not justify scaling.

Campaign execution or changes require authorization.

## Diagnose cohort integrity

For user-level tests, compare distinct assignment-unit counts with the configured allocation using the design-appropriate SRM test. Trace counts through processing stages. Allocation ramps require design-specific analysis.

| First divergence | Investigate |
|---|---|
| Assignment | Bucketing, unstable IDs, ramp timing |
| Logging/joins | Variant-dependent loss, duplicate/drop joins |
| Filter/trigger | Treatment-dependent inclusion, absent control counterfactual logging |

Localize by time and pre-treatment segment. An exposure/click filter can select on treatment effects. Recover retained raw outcomes and reprocess; if missing outcomes prevent valid target-population estimation, fix collection and rerun. Matching counts through arbitrary deletion/reweighting does not recover missing outcomes.

## Arithmetic check

600 versus 500 purchasers in groups of 10,000 imply +1 percentage point, +20% relative, and 100 incremental treatment purchasers; $5,000 additional spend implies $50 each. Unequal groups require rates and population scaling. Estimates alone establish neither significance nor profitability.

Incremental ROAS = incremental revenue / incremental spend; near-zero denominators make ratios unstable.

[Sources, worked counterexample, and validation](SOURCES.md).

## Pitfalls

- No detected SRM does not prove unbiased outcome coverage; balanced losses can still distort lift.
- An SRM alert identifies a symptom, not its cause; user-count thresholds do not transfer to few-cluster geo designs.
- Repeated fixed-horizon peeking inflates false positives; safety monitoring is not permission to declare an early winner.
- Non-significance is not zero effect; spillovers and delayed conversions limit interpretation.
