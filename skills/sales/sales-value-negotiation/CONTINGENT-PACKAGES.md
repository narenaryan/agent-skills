# Contingent Package Checks

Use this companion when a commercial impasse concerns a future outcome, not merely an unaffordable price. Prepare options for authorized human review; this is neither legal drafting nor permission to send, accept, or settle terms.

## Check the disagreement before pricing it

Write each side's forecast separately, with its evidence and uncertainty. Ask what private data could explain the gap. Do not average their probabilities or infer dishonesty from refusal: risk tolerance, cash constraints, measurement cost, and unwillingness to maintain the relationship can each make fixed terms preferable.

Specify a shared event, observation window, quality criterion, data source, and verification responsibility. Identify who controls timing, inputs, exclusions, or the metric. If a party can improve the measured result while damaging the desired outcome, redesign the proposal before pricing it. Agree how missing evidence, disputed records, buyer-caused delay, and scope changes would be reviewed; do not invent a default settlement.

## Original worked example

All amounts below are **thousands of USD**. A hypothetical fixed project pays 30; a contingent option pays 20 plus 20 for a verified success. Delivery costs the seller 24 in either state. Monitoring/administration adds 2 for each side only under the contingent option. Both states remain possible; scope and outcome values are assumed identical across pricing options. Timing, taxes, financing, overhead, and legal costs are omitted; this is not a proposed real transaction.

| Option/state | Buyer total cost | Seller contribution |
|---|---:|---:|
| Fixed | 30 | 6 |
| Contingent failure, verified | 22 | -6 |
| Contingent success, verified | 42 | 14 |
| Evidence missing or disputed | Unresolved | Unresolved |

Assume, only for illustration, seller success probability 0.8 and buyer probability 0.2. Seller expected contribution is `0.8 × 14 + 0.2 × (-6) = 10`; buyer expected cost is `0.2 × 42 + 0.8 × 22 = 26`. A risk-neutral expected-value comparison favors the candidate for each side before exposure constraints. This does not establish accurate forecasts, willingness to accept risk, or newly created joint economic value.

At a common probability 0.5, seller contribution is 4 and buyer cost 32: both are worse than fixed terms. At any common probability, seller improvement plus buyer savings totals -4, the additional administration cost. With these assumptions, seller indifference occurs at 0.6 and buyer indifference at 0.4; uncertainty crossing those thresholds reverses the respective comparison.

## Rejection and redesign cases

- **Hard exposure:** A buyer cap of 35 rejects the possible 42 cost despite expected cost 26. A seller floor of zero rejects the -6 failure contribution despite expected contribution 10. Renegotiate the package or use a feasible alternative; do not silently substitute an average for a cap.
- **Hidden information:** A capacity audit changes the seller's assumed success probability from 0.8 to 0.3. Expected contribution becomes zero, below the fixed six. Investigate evidence rather than maintaining an optimistic price assumption.
- **Gaming:** A deadline-only bonus rewards a rushed delivery worth 35 to the buyer just like an acceptable delivery worth 50, while charging 40 before administration. Add independently checkable quality criteria; a new label alone does not validate quality.
- **Unknown evidence:** An unavailable report cannot be labeled failure to select the lower payment. Route it to the previously agreed review process; arithmetic cannot settle a factual dispute.

Run `python3 check_contingent.py` for arithmetic and counterexamples. Passing these checks does not validate demand, causal commercial benefits, legal enforceability, or actual measurement quality. See [provenance](SOURCES.md).
