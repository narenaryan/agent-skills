---
name: marketing-funnel-diagnosis
description: Use when conversion falls, acquisition channels disagree, or a funnel dashboard suggests a bottleneck before measurement, cohort maturity, and traffic mix have been checked.
---

# Marketing Funnel Diagnosis

A funnel rate is conditional on entry rules, identity, event order, and observation time. Changing traffic composition can move aggregate rates while segment performance stays constant. Diagnose measurement before changing campaigns or pages.

## Lock the contract

Record counting unit, entry event, ordered milestones, intervening-event rules, deduplication, conversion window, timezone, exclusions, and channel assignment. Each numerator must come from its denominator's cohort. Use equally matured entry cohorts; recent entrants have less opportunity to convert.

## Diagnosis sequence

1. Reconcile event and business totals. Check releases, consent changes, duplicate events, bot filters, identity merges, missing channels, and reporting lag. Preserve unknown attribution rather than silently discarding it.
2. Show counts beside rates: entries, step completions, absolute drop-offs, step conversion, final conversion, and time-to-convert. A denominator surge can lower a rate while completions rise.
3. Compare equivalent cohorts within channel, device, geography, or buyer type. Prespecify plausible segments; report small counts and uncertainty.
4. Separate mix from within-segment change. Use fixed, non-overlapping segments and old denominator shares for the analyzed rate: `standardized_new = sum(old_share * new_rate)`. Compare this with both observed aggregate rates. This is descriptive standardization, not a causal counterfactual.
5. Investigate the localized problem using error logs, customer feedback, and relevant usability evidence. Return competing explanations, counterevidence, and the smallest discriminating check. Confirm business impact through purchases, qualified pipeline, or retention.

## Worked mix example

Channel A converts at 10%; B at 2%. An 80:20 traffic split yields 8.4% overall; 20:80 yields 3.6%. Reweighting the unchanged rates by the old mix returns 8.4%: no within-channel deterioration.

## Sources and scope

- [Amplitude: funnel interpretation](https://amplitude.com/docs/analytics/charts/funnel-analysis/funnel-analysis-interpret): ordering, windows, entry cohorts, and drop-offs; inspect your own tool's counting semantics.
- [Microsoft: metric interpretation pitfalls](https://www.microsoft.com/en-us/research/wp-content/uploads/2020/08/2017-08-KDDMetricInterpretationPitfalls.pdf): ratio decomposition and telemetry bias; observational funnels still cannot establish causation.

## Pitfalls

- Joining monthly signups to monthly purchases mixes cohorts and conversion lags.
- The largest percentage drop may have little recoverable business value.
- Averaging segment percentages without denominator weights distorts totals.
- Optimizing a local step can attract worse-fit buyers or shift failures downstream.
