---
name: iam-policy-change-replay
description: Use when tightening IAM permissions or reviewing generated infrastructure policies where a passing no-new-access check, aggregate denial, or historical access replay could hide an outage, new resource access, or missing runtime context.
---

# IAM Policy Change Replay

Permission reduction and service continuity are separate claims. Compare identical requests against current and proposed policies; historical logged decisions belong to an older policy state.

## Three independent checks

| Check | Proves within its scope | Does not prove |
|---|---|---|
| No-new-access comparison | Candidate adds no permission relative to reference | Required callers still work; existing excess access disappeared |
| Required-access replay | Named principal/action/resource/context cases still succeed | Unobserved workflows work |
| Forbidden-access cases | Specified attack-path requests are denied | Every possible attack path is blocked |

## Recipe

1. Freeze current/candidate policy hashes, evaluator version, resource identities, runtime attributes, and request corpus. Refresh at review if any input changes. Replay both policies now; never substitute logged historical verdicts.
2. Add owner-specified required and forbidden requests before inspecting candidate results. Include rare recovery jobs, resource boundaries, and relevant attribute variants. Deduplicating only principal/action/resource loses ABAC distinctions.
3. For AWS simulation, compare per-action/per-resource decisions from `ResourceSpecificResults`. Current documentation describes a top-level aggregate across resources: one explicit denial can hide another resource's allowance. Check pagination and exact expected coverage; missing/duplicate results or `MissingContextValues` require investigation, not a pass.
4. Report unexpected allow→deny and deny→allow transitions separately. A known forbidden request still allowed fails even without a delta. Keep incomplete context or unsupported policy layers unknown.
5. After authorized rollout, verify effective policy identity and representative behavior through `rbvm-verified-closure`; simulated authorization neither executes the service operation nor validates its parameters.

Counterexample: denying every action satisfies no-new-access but breaks the deployment caller. Conversely, an aggregate denial can coexist with newly allowed access to another resource. The offline fixture catches both:

```bash
python3 skills/security/iam-policy-change-replay/scripts/check_replay.py
```

Sources: [Uber policy replay](https://www.uber.com/blog/adding-determinism-and-safety-to-uber-iam-policy-changes/) (2025-09-18); [AWS result semantics](https://docs.aws.amazon.com/IAM/latest/APIReference/API_EvaluationResult.html), reviewed 2026-10-11. [Sources, versions, limits](SOURCES.md).

## Pitfalls

- Equal unknown outcomes are not evidence of equivalence.
- Historical traffic omits future callers; preserve explicit contract cases.
- AWS simulator coverage differs from live enforcement; unsupported layers remain a gap.
- Access Analyzer custom checks can incur charges. This skill grants no API-spending or deployment permission.
