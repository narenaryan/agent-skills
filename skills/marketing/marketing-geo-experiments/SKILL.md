---
name: marketing-geo-experiments
description: Use when measuring campaign lift by city, DMA, region, or market because user-level randomization is unavailable or cross-channel sales matter.
---

# Marketing Geo Experiments

Geo is the assignment unit: a million rows across 12 geos still gives 12 clusters. Choose assignment and estimator separately: synthetic control can estimate randomized tests; without random assignment, the result is quasi-experimental.

## Select a design

| Situation | Path | Gate |
|---|---|---|
| Exposure can be assigned across non-overlapping targetable regions | Holdback (new), go-dark (existing off), or heavy-up (existing increase); randomize within pairs | Respect geo/pair assignment in inference |
| Randomization is infeasible but treated geos have a credible donor pool | Pre-specified synthetic control | Label quasi-experimental; check pre-fit, donor contamination, placebos, and sensitivity |
| Few usable geos, no credible controls, or material interference | Redesign or use another method | Do not launch a test that cannot change the decision; null is not “no effect” |

## Plan before changing spend

1. Specify intervention, eligible geos, comparator, one primary KPI and conversion lag, guardrails, and decision threshold. Separate tested spend change from total-channel ROI.
2. Verify targetable geo grain across relevant campaigns. Isolate budgets/bidding; shared portfolios can move spend between cells. Track planned and actual spend by geo.
3. Use geo-by-period history to compare assignments and duration. Predeclare alpha/power and report them with MDE. For pairs, reserve separate pre-periods for matching and power to limit overfit. If MDE exceeds the decision effect, redesign. In randomized tests, pre-fit affects precision/power, not validity; synthetic control requires credible pre-fit.
4. Predeclare assignment, KPI, guardrails, window, exclusions, interference checks, inference, and inconclusive action. Keep campaigns stable; log regional shocks and spend deviations before viewing lift.

## Read at the assignment level

- Randomized: use original assignment in inference; respect cluster/pair design and small geo count. Purchases/daily rows are not randomized units.
- Synthetic control: require credible pre-fit, placebo/sensitivity checks, and named assumptions. Poor fit or contaminated donors means inconclusive, not a post-hoc tuned control.
- Report contrast, actual spend change, lift with uncertainty, conversion maturity, and guardrails. Keep lift and spend change visible separately; near-zero spend denominators cannot support iROAS.
- Apply only predeclared exclusions. Shocks/leakage may invalidate the contrast; do not drop geos after viewing outcomes.

Hypothetical: a 24-DMA video test shares one portfolio budget, so treatment spend may reduce control spend. Isolate budgets first. Pre-test power gives a 16% MDE; finance would act on an 8% lift. Do not launch. Add geos or extend a mature window, then rerun power; proceed only if the MDE can resolve the decision. A later +4% estimate with an interval spanning zero remains inconclusive.

Primary sources and worked examples: [SOURCES.md](SOURCES.md).

## Pitfalls

- Choosing matched geos after observing test outcomes biases the comparison.
- Neighbor spillover, travel, national promotions, or shared bidding can erase the intended contrast.
- One pre-period fit or synthetic-control specification does not establish robustness.
