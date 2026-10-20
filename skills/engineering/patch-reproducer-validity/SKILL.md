---
name: patch-reproducer-validity
description: Use when a bug fix passes a new regression test but you need evidence the test detects the original defect and checks intended behavior
---

# Validate Patch Reproducers

A green run shows that the current code satisfies the test. It does not show the test would notice the bug. Validate the test oracle against both a known-bad behavior and the candidate fix.

## Prove the regression test

1. State the contract and symptom in observable terms: input or state, expected result, and the wrong result. Derive the expected value from a specification, invariant, or hand-checked example, not from the buggy output.
2. Run the unchanged test on the pre-fix revision with the same fixture, configuration, and dependencies. It should fail at the intended assertion. A build/setup error or unrelated timeout is not reproduction; a hang needs a bounded, contract-specific timeout assertion.
3. Run that same test against the candidate. It should pass without weakening its assertion. If the old revision cannot run, make one controlled copy of the defect: revert the relevant change or inject a narrow mutant. Do not alter production state or commit the deliberate fault.
4. Assert the externally meaningful result, state transition, or side effect. Avoid pinning private call order or helper details unless they are part of the contract. For an unknown expected result, ask for an independent oracle before claiming verification.
5. Challenge the fix with the smallest plausible reversal of its changed condition, boundary, or state update. The regression test should fail. Inspect survivors: a weak assertion may miss a real defect, but an equivalent or unobservable mutant is not proof of a missing test.
6. For timing or concurrency bugs, preserve the fixture and environment; control the schedule or clock where supported. A seed alone may not reproduce thread interleavings. Repeat baseline and candidate; if identical code flips outcomes, diagnose flakiness before treating red/green as evidence.

Then run the focused regression and the relevant surrounding suite. Record which revision and environment each result came from, and disclose tests that could not run. Keep the regression test after the fix so later changes retain the evidence.

## Example

For a page request after item 10 with limit 2, the contract returns IDs `[11, 12]`. The regression assertion `ids == [11, 12]` fails on the old `[11]` result and passes after the boundary fix. Weak `bool(ids)` passes on both, giving false confidence. If the historical revision cannot build, inject the old boundary in a disposable copy and label it a controlled mutant, not baseline evidence.

## Pitfalls

- Counting setup or infrastructure failure as the expected red result.
- Copying expected output from the buggy implementation or changing assertions until both revisions pass.
- Treating a mutation score, coverage number, or surviving mutant as a correctness verdict; mutants are probes, may be equivalent, and do not represent every real defect.
- Rerunning a flaky failure until it passes and calling the result reproducible.
