# Sales pipeline forecast calibration: sources and limits

Reviewed 2026-10-16. This is an original operational synthesis. No CRM records, customer data, forecast model, or sales team were accessed.

## Primary references

- [scikit-learn 1.9.1: probability calibration](https://scikit-learn.org/stable/modules/calibration.html) (reviewed 2026-10-16). Its calibration curve groups predictions and compares mean predicted probability with the observed positive fraction. The guide notes that Brier score reflects calibration, resolution, and outcome uncertainty together, so a Brier score alone does not isolate calibration.
- [scikit-learn 1.9.1: TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) (reviewed 2026-10-16). Time-ordered evaluation avoids training on future observations and evaluating on past ones. The documentation assumes equally spaced samples and notes that its `groups` parameter is ignored; CRM opportunities are irregular and repeated, so this skill does not claim direct `TimeSeriesSplit` use solves the problem. Instead, it calls for date-cutoff evaluation with target-horizon maturity and opportunity grouping matched to the forecast use.
- [Gneiting and Raftery, “Strictly Proper Scoring Rules, Prediction, and Estimation,” JASA 102(477), 2007](https://doi.org/10.1198/016214506000001437). This paper develops proper scoring rules for probabilistic forecasts, including the Brier score. It supports evaluating issued probabilities honestly; it provides no sales-specific win rate.
- [Sormunen et al., “Predicting sales offer success of industrial configure-to-order equipment: evaluating explainable AI approach with B2B sales experts,” Journal of Marketing Analytics, published 2026-08-27](https://link.springer.com/article/10.1057/s41270-026-00518-7). This is direct B2B sales research, but it is narrow context only. The partner data came from one industrial configure-to-order company; the article reports 1,062 cases considered, 615 finished won/lost offers, and a cleaned sample of 439 (including 146 from one country). It evaluates binary classification with a random 90/10 split, not probability calibration. Its expert questionnaire used five reviewers and four selected cases. The reported balanced-accuracy figures are not generalizable forecasts or evidence that this skill improves sales performance. The authors also used a public B2C banking dataset as a separate functionality demonstration; that is not B2B validation.

## Synthesis boundaries

A fixed-horizon “win by date” target differs from eventual win/loss: an opportunity still open at the horizon is not an eventual loss. The skill keeps the event, forecast snapshot, and eligible population explicit; it recommends counts, a time-forward check, and a simple baseline before publishing cohort probabilities. No source specifies a universal minimum cohort size, sales-stage map, forecast horizon, or acceptable score. The worked two-segment example is hypothetical and demonstrates how pooled calibration can mask opposite segment errors. It is not empirical performance proof.

The nearby [sales discovery and qualification skill](../sales-discovery-qualification/SKILL.md) says not to invent win probabilities. This skill adds a check for when a historical probability is comparable enough to use; if not, keep buyer evidence separate and label the numeric probability unvalidated.

## Validation performed and not performed

- The 492-word skill file was statically checked against the creator's 300–500-word budget, exact frontmatter name/path, “Use when” trigger, final Pitfalls section, and relative link to the existing qualification skill.
- The worked example uses synthetic counts. An arithmetic check confirms 4 + 12 = 16 pooled wins, 16/40 = 40% matching the mean prediction, and per-segment rates 4/20 = 20% and 12/20 = 60%. This is an arithmetic check, not a performance test.
- No CRM pipeline, forecast model, random split, probability calibrator, or empirical business outcome was tested. No repository test suite or CI result is claimed.