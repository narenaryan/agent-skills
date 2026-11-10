# Covariate adjustment: evidence and limits

Historical research reviewed November 3, 2026. The Microsoft explainer entered the backlog November 2; this is not a new-publication alert. No campaign or customer data was used.

## Primary sources and boundaries

- [Deng, Xu, Kohavi and Walker, WSDM 2013](https://exp-platform.com/Documents/2013-02-CUPED-ImprovingSensitivityOfControlledExperiments.pdf), conference February 4–8, 2013: §§3.2, 4.2–4.4 support common control-variate contrasts, treatment-unaffected covariates, missing-history indicators, and separate treatment of non-user metrics. Its observed Bing gains are not promised here.
- [Alex Deng, Chapter 10](https://alexdeng.github.io/causal/sensitivity.html), publication/update date not independently established; read November 3: §§10.2.1–10.2.2 distinguish fixed common coefficients from fitted regression and explain why the unknown covariate mean cancels in the two-arm contrast.
- [Winston Lin, 2013](https://arxiv.org/html/1208.2301v2), first submitted August 11, 2012; v2 April 19, 2013; journal volume 7(1), pp. 295–318: interaction adjustment and sandwich uncertainty have asymptotic guarantees under the stated finite-population regularity conditions. This does not imply unbiased finite-sample fitted regression or valid ordinary homoskedastic errors. Unequal allocation and heterogeneous slopes can hurt pooled adjustment. Full HTML §§4–6 read.
- [Microsoft ExP, November 15, 2022](https://www.microsoft.com/en-us/research/articles/deep-dive-into-variance-reduction/): estimator variance differs from changing/trimming the outcome; precision gains vary by metric and surface. This is a historical research reference, not a newly monitored source. The rendered comparison table contains a treatment-minus-treatment typo; this recipe uses the treatment-minus-control contrast independently established above.

The frozen-coefficient recipe is a deliberately narrow teaching baseline, not a claim to implement Microsoft's CUPED-VR. Neither fitting a coefficient on the present outcomes nor using a separate coefficient for each arm is equivalent to this fixture. No new source registry or monitoring scope is added.

## Original finite-population experiment

Twelve units have X values −5, −3, −1, 1, 3, 5, each twice, with E values −1 and +1 per X. All 924 balanced assignments are enumerated; a second design enumerates all 495 assignments with four treated units. The illustrative coefficient 2 is fixed before assignment, not learned from these randomized outcomes. The potential outcomes are constructed, not empirical.

The script checks unbiased average contrast and variance reduction for this population, the exact finite-population variance relation under heterogeneous effects, null effect, unequal allocation, a non-predictive covariate, treatment contamination, common centering, and three faulty analysis variants: wrong correction sign, arm-specific centering, and reusing raw variance. All arithmetic uses standard-library rational numbers; no Monte Carlo noise or fitted model is involved. Mutant counterexamples are explicit comparisons, not a mutation-testing framework.

For fixed transformed potential outcomes Z, complete randomization gives Var(delta)=S²(Z1)/n1+S²(Z0)/n0−S²(tau)/N. Averaging the fixture's sample-variance estimate over every assignment equals the first two terms. Constant effects make the omitted term zero; heterogeneous effects make the estimate conservative on average. This checks variance arithmetic, not guaranteed confidence-interval coverage.

## Limits

No fitted regression, cross-fitting, empirical A/A calibration, hypothesis-test coverage, real campaign, telemetry pipeline, power forecast, causal business benefit, ratio metric, clustered assignment, sequential inference, third-party code, or production integration was tested. Coefficient drift can erase or reverse precision gains even while a fixed unaffected adjustment remains unbiased over randomization. Retain raw estimates and validate the chosen production estimator separately. Existing SRM diagnostics remain prerequisites.
