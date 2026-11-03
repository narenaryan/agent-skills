# Covariate adjustment without adjusting away lift

Use this recipe when valid randomized holdouts are too noisy and prior user-level outcomes are available. Adjustment changes the effect estimator, not the campaign outcome or target population. It cannot repair biased assignment, missing outcomes, spillovers, or post-exposure selection.

## Freeze the analysis contract

Keep one row per randomized unit and the original intention-to-treat population. Specify the outcome window, unit weights, covariate cutoff, missing-history handling, coefficient strategy, uncertainty estimator, and stopping rule before inspecting treatment results. A timestamp alone is insufficient: identity joins and feature construction must not depend on treatment.

Do not drop new users merely because they lack history. A predeclared constant fill plus a pre-treatment missingness indicator can retain them in a multivariable adjustment. Missing **outcomes** require a separate identification argument; covariate imputation does not recover them.

## Two coefficient strategies

| Strategy | Contract |
|---|---|
| Frozen common coefficient | Learn on separate historical/calibration data; freeze before assignment. Transparent baseline below; precision may worsen if relationships drift. |
| Estimated on this experiment | Use a validated regression-adjustment implementation. Include treatment-by-centered-covariate interactions and design-appropriate robust uncertainty; do not borrow the fixed-coefficient calculation blindly. |

For a fixed common coefficient `theta`, compute `z_i = y_i - theta*x_i`, then:

```text
delta_adjusted = mean(z_treatment) - mean(z_control)
variance_estimate = sample_variance(z_treatment)/n_treatment
                  + sample_variance(z_control)/n_control
```

This variance expression is for complete randomization of equally weighted individual units, not correlated visits or few-cluster geo designs. It is conservative in expectation under heterogeneous finite-population effects; it does not guarantee a finite-sample normal confidence interval. For fitted coefficients, small samples, ratios, clusters, or adaptive assignment, use the corresponding estimator and inference procedure.

A shared centering constant cancels from the contrast. Centering separately within each arm cancels the correction itself. Report the unadjusted effect alongside the adjusted effect, their uncertainty, and exactly which estimator produced each.

## Failure and remedy

In the original fixture, `Y(0)=20+2X+E`, `Y(1)=Y(0)+3`; frozen `theta=2` removes baseline imbalance while retaining effect 3 averaged over all balanced assignments. Replace history with treatment-contaminated `X+T`: the estimate averages 1, with equally small variance. The attractive precision hides bias. Restore the unaffected covariate; a narrower interval cannot rescue an invalid control variable.

```bash
python3 skills/marketing/marketing-incrementality/check_cuped.py
```

These are synthetic fixed-coefficient checks, not campaign-effect or fitted-regression validation. See [provenance](CUPED-SOURCES.md).

## Pitfalls

- Choosing features or estimators because they produce significance creates specification-search bias.
- High predictive fit is not proof that a covariate is unaffected by treatment.
- Copying the raw standard error onto an adjusted contrast misstates its uncertainty.
- Variance reduction does not authorize early stopping, spend changes, or shortening conversion maturation.
