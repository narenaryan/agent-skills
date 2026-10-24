---
name: sales-pipeline-forecast-calibration
description: Use when assigning B2B opportunity win probabilities or aggregating pipeline forecasts by stage, segment, or close horizon.
---

# Sales Pipeline Forecast Calibration

A win probability is conditional on the snapshot, eligible population, and outcome horizon. A stage percentage from one year's closed deals does not automatically transfer to another selling motion.

## Define one forecast event

1. State the outcome, horizon, event time, and deal identity rule, such as “closed-won within 90 days after the snapshot.” Count a win only by its recorded close-won date. Define how reopened or duplicate opportunities are treated. Require the full 90-day window; exclude snapshots with incomplete follow-up. For this target, open on day 90 means “not won within 90 days,” not “lost”; for eventual-win forecasts, it is unresolved.
2. Rebuild snapshots using only fields known at forecast time. Exclude later stage changes and close notes. Do not randomly split repeated snapshots of one deal across train/test; group by deal for unseen-deal tests or use time cutoffs for ongoing-pipeline updates.
3. Group by decision-relevant stage or sales motion. Show mature counts and uncertainty. If a cell is sparse or the process changed, use a broader baseline only when its outcomes and scope are comparable; otherwise say “insufficient history.”

## Check calibration

Within each probability band and relevant cohort, compare mean predicted probability with observed wins divided by eligible outcomes. At each cutoff, train only on labels fully mature before it, then score later forecasts after their horizons mature. Do not use future fields or the same outcomes to both adjust and evaluate a forecast.

For a binary target, the Brier score is mean((p − y)²), where y=1 for a win within the horizon and 0 otherwise. Lower is better for the same target and population, but the score combines calibration, resolution, and outcome uncertainty. Pair it with a reliability table and a simple base-rate forecast.

## Worked check

Synthetic example: two segments each have 20 mature opportunities and a 40% mean prediction. One wins 4/20 (20%); the other 12/20 (60%). Pooling gives 16/40 = 40%, matching the predicted average while hiding opposite 20-point segment errors. At 20 cases per segment, treat this as an exploratory signal, not a settled rate; collect more evidence. The arithmetic is not performance evidence.

Multiply probability by amount only when both refer to the same scope and horizon. If history is not comparable, keep buyer evidence separate, label a numeric forecast unvalidated, and follow [discovery qualification](../sales-discovery-qualification/SKILL.md) rather than inventing odds.

## Source notes

See [primary sources, scope limits, and validation notes](SOURCES.md).

## Pitfalls

- Stage or horizon changes break historical comparability.
- Open deals are not eventual losses; censor unresolved cases for eventual-win forecasts.
- Brier score alone does not show calibration, and pooled results can hide segment errors.
- Probability × amount is an expectation, not committed revenue; stale deal values distort it.
- Models and salespeople may use different evidence; preserve buyer context and uncertainty.