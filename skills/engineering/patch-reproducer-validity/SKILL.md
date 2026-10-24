---
name: patch-reproducer-validity
description: Use when a bug fix passes its reproducer, a patch may break working behavior, or a review must distinguish introduced regressions from incomplete fixes, pre-existing defects, and incomparable runs.
---

# Validate Patch Reproducers

Fix efficacy and regression freedom are separate claims. A test that changes from red to green can prove a particular repair while another supported behavior changes from green to red.

## Paired evidence

Interpret each case against an independent contract, not merely differences in output. Hold fixture, assertion, entrypoint, and unrelated configuration/dependencies constant; record intentional dependency/configuration changes as part of the patch.

| Baseline | Candidate | Bounded conclusion |
|---|---|---|
| Fails contract | Passes | This case is repaired |
| Passes | Fails contract | Introduced-regression candidate; verify reachability and attribution |
| Fails contract | Fails contract | Compare failure identity/impact: incomplete repair or pre-existing defect can coexist with a new or worsened failure |
| Passes | Passes | No failure observed in this case, not proof of regression freedom |
| Either arm: setup failure, unstable results, or incomparable context | — | Inconclusive; preserve the claim and missing evidence |

## Recipe

1. State the observable contract and trust boundary: input/state, expected result, and wrong result. Derive the oracle from a specification, invariant, or hand-checked example. Confirm supported configuration and a real caller path; private-helper misuse alone proves no user-visible regression. Attacker-controlled malformed input still matters when a security invariant promises safe rejection. Check whether an intentional contract change was actually approved.
2. Run the unchanged reproducer on the pre-change revision and candidate. Capture revision IDs, invocation, raw output, fixture/environment fingerprints, and assertion reached. A build error is not a functional reproduction. Build compatibility itself can be the contract, but requires matched supported toolchains and the relevant build diagnostic.
3. For the reported defect, require intended baseline failure and candidate success. If the historical revision cannot run, use a narrow reversion or mutant in a disposable copy and label it substitute evidence, not historical reproduction. Never ship the deliberate fault. A hang needs a bounded, contract-specific timeout assertion.
4. Separately probe behaviors affected by the diff: boundary inputs, error handling, callers, and security protections. For a new-regression claim, show baseline success and candidate failure through the same meaningful interface. Where practical, revert the implicated change in isolation and replay; unrelated dependency or fixture changes otherwise confound attribution.
5. Challenge the repaired condition with a narrow mutant; a survivor may expose a weak oracle, but equivalent or unobservable mutants are not automatically missing tests. For concurrent/timing failures, control schedule or clock where supported; a seed alone does not fix interleavings. Mixed outcomes remain inconclusive, not “retry until green.”
6. Retain regression tests and run relevant surrounding tests; report repaired cases, introduced regressions, unresolved defects, and verification gaps separately. Keep pre-existing defects visible without blaming this patch. Evidence does not authorize rollout or close an RBVM finding; those require their own gates.

## Worked example

Synthetic positional pagination promises `[11, 12]` for offset 10, limit 2, and `[]` for limit 0. A patch repairs `[11]` to `[11, 12]` but removes the zero-limit guard and returns `[11]`. The target fix passes while a distinct regression is proven. `bool(result)` misses the original defect.

Run the original isolated cases: `python3 skills/engineering/patch-reproducer-validity/reproduce.py`. [Sources and limits](SOURCES.md) distinguish local model evidence from project validation.

## Pitfalls

- Treating setup failure, a changed oracle, or weaker assertions as red/green proof.
- Requiring production deployment for a library test, or claiming a mocked helper proves an end-to-end path.
- Calling an unchanged defect newly introduced, or dismissing attacker-reachable failures as unsupported input.
- Treating coverage, mutation score, or one repaired case as permission to ship.
