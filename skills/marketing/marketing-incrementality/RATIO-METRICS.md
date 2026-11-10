# Ratio metrics without changing the question

Use for user-randomized experiments reporting events per opportunity. Define the metric before choosing its standard error. This companion does not cover incremental ROAS, a ratio of treatment-control differences.

## Choose the target

Store one row per assigned unit with numerator total `S` and denominator total `N`. Preserve zero-activity units as `(0,0)` where that is their genuine observed outcome; missing logs are not zeros. Predeclare windows, attribution rules and eligible population. Treatment can change both totals: report each alongside the ratio.

Original counterexample: four units have `(S,N) = (1,1), (0,1), (0,9), (0,9)`. Aggregate events/opportunities is `1/20 = 5%`; averaging the four personal rates gives `25%`. Neither arithmetic operation fixes a mismatched business question. Equal unit weighting and opportunity weighting answer different questions; equal denominators are one case where they coincide.

## Preserve the covariance

For one arm with `k` independent, identically distributed unit-level pairs, finite second moments and a denominator mean separated from zero:

```text
r = sum(S) / sum(N)
u_i = S_i - r*N_i
estimated_variance(r) = sample_variance(u) / (k * mean(N)^2)
```

This first-order delta estimate equals `(var(S) + r*r*var(N) - 2*r*cov(S,N)) / (k*mean(N)^2)`, using sample moments with divisor `k-1`. Independent-arm absolute contrasts add arm variances. Do not apply that shortcut to paired, stratified, adaptive or dependent designs without their design-specific inference.

Read [sources and limits](RATIO-SOURCES.md). From this document's directory, run `python3 check_ratio.py` for original arithmetic checks.

## Pitfalls

- Repeated events are not independent randomized units. Duplicating unit rows leaves the rate unchanged but falsely shrinks this variance estimate.
- Dropping numerator-denominator covariance can create uncertainty even when every unit has exactly the same ratio.
- Few units, dominant units, heavy tails or a weak denominator can defeat the approximation. These checks do not validate interval coverage or a universal sample-size cutoff.
- An undefined personal rate for `N=0` is not a reason to discard an assigned unit from the aggregate estimand. Zero total denominator is undefined.
- A rate change is not automatically additional customers, profit or permission to change spend.
