# Ratio-metric provenance and validation

Reviewed November 10, 2026. Historical backfill, not a new publication.

- Alex Deng, Ulf Knoblich and Jiannan Lu, [Applying the Delta Method in Metric Analytics](https://alexdeng.github.io/public/files/kdd2018-dm.pdf), KDD 2018, DOI [10.1145/3219819.3219919](https://doi.org/10.1145/3219819.3219919). Sections 2.2 and 3, equations 4 and 6, supply the first-order ratio variance and randomization-unit aggregation. The conference is August 19–23, 2018; [Microsoft's catalog](https://www.microsoft.com/en-us/research/publication/applying-the-delta-method-in-metric-analytics-a-practical-guide-with-novel-ideas/) labels the publication July 2018. These dates are not the November review date.

- Microsoft ExP, [Patterns of Trustworthy Experimentation: Post-Experiment Stage](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-post-experiment-stage/), published December 24, 2021; reviewed November 10, 2026. The metric-observation discussion supports reporting denominator movement and distinguishing telemetry changes from behavior. No significance-dependent metric switching rule is adopted.

The companion retains a narrow iid-pair asymptotic contract. It does not transfer the paper's simulation sample sizes into universal thresholds or generalize its mixed-model comparison to all mixed models. Equal-user and opportunity-weighted calculations are explicitly different targets, not universally biased versus unbiased methods.

## Original evidence

`check_ratio.py` is original standard-library Fraction/unittest arithmetic, not downloaded source code. Eight original methods check an estimand counterexample, covariance/residual identity, an omitted-covariance faulty estimate, equal denominators, pseudoreplication arithmetic, scaling/order, genuine zero activity and invalid denominator/sample inputs. Run from this directory:

```bash
python3 check_ratio.py -v
python3 -O check_ratio.py -v
```

Independent review adds three committed methods: a hand-expanded nonzero variance, genuine zero-activity retention versus removal, and 999 three-unit count combinations checked against a pairwise variance identity. All 11 methods passed in both modes on Python 3.12.14. The faulty estimator has positive variance for proportional totals, while the covariance-preserving expression is zero. Duplicating rows lowers the calculated variance without adding independent units. These are algebraic counterexamples, not measured false-positive rates or confidence-interval coverage.

No campaign, live data pipeline, fitted regression, covariance-adjusted CUPED, robust-design inference, sequential analysis, agent-use experiment, causal business benefit or CI validation. Exact Fraction arithmetic avoids floating-point cancellation in the fixture; no production numerical robustness claim. Small examples demonstrate mechanics, not sufficient sample sizes. Campaign actions remain separately authorized.
