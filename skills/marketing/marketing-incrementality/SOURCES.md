# Marketing incrementality: provenance and validation

Reviewed 2026-10-09. This is historical-source backfill improving an existing skill, not a claim of newly published research. No campaign was run or changed.

## Primary sources

- [Fabijan et al., SRM taxonomy](https://doi.org/10.1145/3292500.3330722), KDD 2019. [Author manuscript](https://exp-platform.com/Documents/2019_KDDFabijanGupchupFuptaOmhoverVermeerDmitriev.pdf), sections 5–6: distinct failure stages and recoverable processing loss versus missing collection. Microsoft catalogs July 2019; the paper specifies the August 4–8 conference, not a day-level publication date. Full manuscript read; ACM download returned 403.
- [Microsoft, diagnosing SRM](https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/), 2020-09-14: compare configured allocation with observed cohorts and investigate triggers/segments. Its p < 0.0005 alert threshold is platform-specific, not prescribed here.
- [Microsoft, during-experiment patterns](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-during-experiment-stage/), 2021-01-25: pre-treatment segmentation, guardrails, and multiplicity/peeking controls.
- [Microsoft, post-experiment patterns](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-post-experiment-stage/), 2021-12-24: counterfactual control logging for triggered analyses. A trigger must capture potentially affected users; logging alone does not make a treatment-dependent filter valid.
- [Chen and Au, randomized paired geo experiments](https://arxiv.org/abs/1908.02922), first submitted 2019-08-08; reviewed v3, revised 2021-06-06: geo assignment and uncertainty differ from independent-user designs. This revision does not implement their estimator.
- [Lewis and Rao, advertising measurement uncertainty](https://doi.org/10.1093/qje/qjv023), published online 2015-07-06, November 2015 issue: retained basis for feasibility/uncertainty caveats. Journal abstract was indexed; full article was inaccessible during this review. No new quantitative claim relies on its unavailable text.

SRM and geo sources were already cited in the repository before this review. First discovery of those sources is therefore no later than 2026-10-05; the deeper manuscript and 2021 articles were first reviewed for this revision on 2026-10-09. These are method constraints, not API-version guarantees.

## Original worked failure and remedy

Hypothetical fixed 50:50 user assignment; counts below are constructed, not customer data. Outcomes are equally matured and all assigned users initially have observed purchase status.

| Cohort | Treatment purchasers/users | Control purchasers/users | Treatment minus control |
|---|---:|---:|---:|
| Complete assignment cohort | 600/10,000 | 500/10,000 | +1 percentage point |
| Faulty treatment filter | 400/9,000 | 500/10,000 | −0.556 percentage points |
| Corrected filter, replayed raw data | 600/10,000 | 500/10,000 | +1 percentage point |
| Equal counts but biased losses | 400/9,000 | 500/9,000 | −1.111 percentage points |

The faulty filter removes 1,000 treatment users including 200 purchasers. Checking only assignment counts misses the failure. For retained counts, expected counts are 9,500 each: Pearson χ² = 52.631579, one degree of freedom, approximate p = 4.024×10⁻¹³. This is an imbalance diagnostic, not a significance test of conversion lift or proof of the particular filter bug.

With intact raw outcomes, correct the filter and reconstruct the originally assigned cohort. Denominator restoration or zero imputation cannot recreate never-collected outcomes. If that loss prevents valid target-population estimation, fix collection and rerun. This does not rule out a justified missing-data method or an unaffected-population analysis with explicitly narrower scope. The last row additionally removes 1,000 non-purchasing controls, proving that equal retained counts alone cannot establish integrity.

A planned 80:20 split is not SRM merely because counts differ. Likewise, a genuinely treatment-independent filter can preserve valid sampling. The ramp warning is design-dependent synthesis: do not average configured splits or treat outcome-adaptive allocation as a fixed multinomial design. Do not infer causality from diagnostic segment hunting or transplant this user-count calculation to a few randomized geographies.

## Validation boundaries

Original arithmetic checks use Python 3.12 standard-library fractions and math; normal and optimized runs verify sign reversal, recovery, balanced-loss counterexample, planned unequal allocation, sample-size sensitivity, original lift/cost arithmetic, and unequal-arm population scaling. They validate constructed arithmetic, not production telemetry, experiment power, statistical calibration, or business performance. No simulator establishes that a particular campaign is effective.

The concise skill remains the operative recipe; this file documents evidence and the worked counterexample. No software installation, campaign mutation, or repository CI was introduced. The repository's referenced test.sh is absent.
