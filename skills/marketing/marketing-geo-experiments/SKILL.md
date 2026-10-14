---
name: marketing-geo-experiments
description: Use when measuring campaign lift by city, DMA, region, or market because user-level randomization is unavailable or cross-channel sales matter.
---

# Marketing Geo Experiments

A geo is the assignment unit: a million records across 12 geos are 12 clusters. Randomized assignment and synthetic control differ; pre-test fit does not make a match randomized.

## Select a design

| Situation | Path | Gate |
|---|---|---|
| Exposure can be assigned across non-overlapping targetable regions | Randomized holdback (new tactic), go-dark (switch off existing), or heavy-up (increase existing); randomize within pairs | Respect geo/pair assignment in inference |
| Randomization is infeasible but treated geos have a credible donor pool | Pre-specified synthetic control | Label quasi-experimental; check pre-fit, donor contamination, placebos, and sensitivity |
| Few usable geos, no credible controls, or material interference | Redesign or use another measurement approach | Do not launch a test that cannot change the decision; null is not “no effect” |

## Plan before changing spend

1. Specify intervention, eligible geos, comparator, outcome/lag, guardrails, and decision threshold. Distinguish the tested spend change from total channel ROI.
2. Verify targetable geo grain across relevant campaigns. Isolate budgets/bidding; shared portfolios can move spend between cells. Track planned and actual spend by geo.
3. Use geo-by-period history to compare assignments, durations, and power under plausible effects. Reserve a separate pre-period for power after matching to reduce overfit. Require acceptable pre-fit and MDE below the decision effect; otherwise add geos, extend a mature window, or redesign.
4. Predeclare assignment, outcomes, guardrails, window, exclusions, interference checks, inference, and inconclusive action. Keep campaigns stable; log regional shocks and spend deviations before viewing lift.

## Read at the assignment level

- Randomized: estimate by original assignment; inference respects cluster/pair randomization and small cluster count. Purchases/daily rows are not randomized units.
- Synthetic control: require pre-period fit, placebo/sensitivity checks, and named assumptions. Poor fit or contaminated donors means inconclusive, not a post-hoc tuned control.
- Report contrast, actual spend change, lift with uncertainty, conversion maturity, and guardrails. Keep lift and spend change visible separately; near-zero spend denominators cannot support iROAS.
- Apply only predeclared exclusions. Shocks/leakage may invalidate the contrast; do not drop geos after viewing outcomes.

Hypothetical: a 24-DMA video test uses a shared portfolio budget, so treatment spend could reduce control spend. First isolate budgets. Pre-test simulations then show a 16% MDE while finance says an 8% lift would change allocation. Do not run this design as decision-grade; redesign and rerun power, proceeding only if the MDE can resolve that decision. A later +4% estimate with an interval spanning zero remains inconclusive, not proof of no effect.

Primary sources and worked examples: [SOURCES.md](SOURCES.md).

## Pitfalls

- Choosing matched geos after observing test outcomes biases the comparison.
- Neighbor spillover, travel, national promotions, or shared bidding can erase the intended contrast.
- One pre-period fit or synthetic-control specification does not establish robustness.
- User-level sample sizes do not rescue few geo clusters.
