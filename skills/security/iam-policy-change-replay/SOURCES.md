# Provenance and validation

Researched 2026-10-11. Historical backfill, not a new-publication claim. The skill is an original synthesis; Uber's internal simulator is not an AWS API or deployable dependency.

## Source-to-claim map

- [Uber: Adding Determinism and Safety to Uber IAM Policy Changes](https://www.uber.com/blog/adding-determinism-and-safety-to-uber-iam-policy-changes/), Avinash Srivenkatesh, Zi Wen, Zakir Akram, published 2025-09-18. Read the complete article. It replays access requests through current and proposed policy engines, because logged verdicts reflect older policies. Refreshing at review handles intervening policy changes. Runtime ABAC attributes remain a stated coverage limitation. The context-aware corpus binding and separate required/forbidden contracts here are our proposed synthesis, not claims that Uber implemented these exact gates. The canonical article redirects geographically; retain its stable /blog/ URL.
- [AWS CheckNoNewAccess API](https://docs.aws.amazon.com/access-analyzer/latest/APIReference/API_CheckNoNewAccess.html): PASS means the supplied candidate does not add access relative to the supplied reference; FAIL indicates it might. A deny-all candidate illustrates why this property alone cannot establish availability or successful remediation. No AWS call was performed.
- [AWS EvaluationResult](https://docs.aws.amazon.com/IAM/latest/APIReference/API_EvaluationResult.html): current documentation explicitly describes one result per action, top-level aggregation across resources, and per-resource decisions in ResourceSpecificResults. It does not date the semantic transition. Do not infer a historical deployment date or silently reuse a parser written for another response shape. Bind evaluator/schema observations and reject missing per-resource coverage in the illustrative adapter.
- [AWS ResourceSpecificResult](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ResourceSpecificResult.html): EvalResourceName and EvalResourceDecision identify each resource result. MissingContextValues can appear at this level; inspect both levels conservatively.
- [AWS simulator guide](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html): simulation does not execute the service request; production context and supported policy layers constrain conclusions. Current guide says resource control policies are unsupported and flags advanced live-environment differences. This skill deliberately avoids declaring a simulator to be a complete live authorization oracle.
- [AWS CLI simulate-custom-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/simulate-custom-policy.html), reference banner 2.37.9 when read: paginated API/CLI output requires complete collection. The fixture models explicit resource ARNs only, not wildcard resource expansion, cross-account evaluation, SCPs, IAM policy parsing, or provider semantics.
- [AWS custom policy checks guide](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-custom-policy-checks.html): checks for new access incur a charge. No credentials, account changes, billed calls, or cloud provisioning are part of this reproduction.

All AWS pages reviewed 2026-10-11; publication/update dates are unspecified. Documentation/source verification is distinct from runtime AWS verification.

## Failure, remedy, and boundaries

Run `python3 skills/security/iam-policy-change-replay/scripts/check_replay.py` and repeat with `python3 -O`. Standard-library only; no installation, network, credentials, files outside the checkout, or mutating side effects.

The original fixture processes synthetic API-shaped reports for one fixed principal/context bundle. Fifteen unittest methods demonstrate:

- A finite no-new-access comparison accepts deny-all while the independent required-call contract fails.
- Equal aggregate explicit denials conceal a new allowance on another resource; per-resource comparison catches it.
- Existing forbidden access fails without a decision delta; an explicitly expected removal can pass when required access remains.
- Missing runtime context, incomplete or duplicate coverage, malformed decisions, incomplete pagination, stale binding, unavailable baseline, and unsupported layers remain unknown.
- Supported complete evidence and a synthetic two-page topology pass the scoped checks; this is not an observed AWS page split.

The adapter consumes previously collected results and does not collect AWS pages, verify page marker chains, calculate cryptographic bindings, prove corpus representativeness, or detect falsely declared support. Its binding strings are illustrative. A real collector must attest complete input identity and provenance, validate transport/API failures, and obtain independent owner-defined contracts. These tests validate the decision contract only. They do not validate IAM evaluation, live privileges, deployment behavior, or production safety. A pass never grants execution permission.

## Relationship to existing skills

`rbvm-guarded-remediation` controls authorization, identity, retries, and rollout; `rbvm-verified-closure` proves deployed state. This skill fills the intervening policy-diff oracle gap. `ai-bug-patterns` names authorization/state failure classes but does not describe dual-baseline replay or resource-aggregate masking. `minimal-sufficient-evidence` concerns evidence selection rather than this IAM-specific technique.
