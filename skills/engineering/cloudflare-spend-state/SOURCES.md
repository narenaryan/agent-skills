# Sources and validation

Reviewed November 14, 2026. The initiating article was published November 13, 2026; API documentation publication/update dates were not observed. Recheck these beta API semantics before integration.

- [Cloudflare spend-management architecture](https://blog.cloudflare.com/spend-management/): technical sections explain staged aggregation, pending usage awaiting pricing inputs, cumulative rating and asynchronous runtime propagation. The article's timing claims were not measured here and do not provide a worst-case cost guarantee.
- [Spend Policies API models](https://developers.cloudflare.com/api/resources/billing/subresources/spend_policies/): separate configuration revision, period evaluation, delivery generations and runtime evidence. The original model index was read directly. Its account/product scope does not cover an entire application's unrelated services.
- [Get Spend Policy](https://developers.cloudflare.com/api/resources/billing/subresources/spend_policies/methods/get/): read endpoint and ETag context. The reader labeled this endpoint page a rewritten summary; substantive state-field claims were also checked in the original model index above. No live API call was made.

## Worked counterexamples

The original standard-library fixture uses trusted, normalized dictionaries, not a production parser. The researcher reported eight original methods passing normally and with `-O` on Python 3.12.14. They show:

- A version-only cache retains an old-period conclusion across rollover; comparing newly obtained state detects the change.
- Missing state cannot supply a below-limit conclusion. Distinct evaluation statuses remain distinct.
- Equal generations with completed delivery still leave runtime behavior unverified. Retry and mismatched-generation cases do not confirm delivery.
- A later evaluation timestamp does not establish usage-event freshness; notification remains distinct from blocking.
- Ten hypothetical serial jobs costing two units each exceed a ten-unit budget despite concurrency one. This arithmetic is not Cloudflare's price, workload, lag or overspend behavior.

From this directory:

```bash
python3 check_state.py -v
python3 -O check_state.py -v
```

The fixture does not decide whether spending is permitted, parse arbitrary responses, validate clocks/IDs/schema, contact a provider, establish billing accuracy, measure enforcement, prove agent benefit, or test a reservation implementation. Runtime verification must use separately authorized evidence and scope. No software installed, credentials accessed, chargeable traffic generated or billing policies changed.

## Scope and alternatives

Existing security-gate-rollout and rbvm-verified-closure teach general evidence boundaries. This skill adds a concrete spend-policy failure: configuration freshness is independent of billing-cycle state, and delivery status is not runtime readback. No new RBVM lifecycle or generic distributed-counter mechanism is claimed.

For a strict application budget, concurrency alone is insufficient. A separate reservation design would need atomic admission, conservative bounded cost per operation, reconciliation and bypass coverage. None is implemented or established by this skill. Do not invent a monetary headroom figure from advertised latency.

Independent review added three committed boundary methods: completed inactive delivery, preserved expiry without runtime proof, and null state versus no owned effect. The normal-mode log confirms all 11 methods passed. An optimized run was invoked, but its redirected log was not inspected before the executor disconnected; optimized success for the final fixture is unconfirmed. The fixture now retains desired state and expiry as reported fields; it does not validate timestamps or infer present activation.
