# Measurement epochs: worked decision checks

These original synthetic scenarios extend the asset-evidence join contract into aggregate reporting. They do not estimate scanner recall, enterprise risk, or remediation effectiveness.

## Contract and bridge

Record an epoch ID with the counting unit (instance/finding/event), identity/deduplication version, population eligibility, numerator predicate, denominator predicate, observation window, collector/scanner and advisory database versions, configuration/exclusions, and classifier version. Preserve raw observation references and policy-owned freshness criteria.

A **same-record bridge** applies both classification rules to exactly the same immutable observations, retaining failures/unknowns in a transition table. It measures label movement on that snapshot, not changes in the underlying systems. Do not imply counterfactual comparability when the old record lacks a new required field. Detector behavior, certificate chains, authentication, exclusions, and sampling changes may alter what was observed; a classification bridge alone cannot repair those changes.

Only replay already-authorized retained data. New collection or production changes need separate authority. Preserve original published values and identify any retrospectively restated series, its rule version, eligible records, and omissions.

## 1. A classifier makes the headline improve

One hundred observed clients: 40 accept a weak-key probe and 60 reject it. The old classifier calls all 100 “browser.” A revised classifier moves 30 accepting clients into “bot,” without any new observations.

| Same records | Old browser | New browser | New bot |
|---|---:|---:|---:|
| Accept | 40 | 10 | 30 |
| Reject | 60 | 60 | 0 |
| Total | 100 | 70 | 30 |

Naive baseline: browser acceptance fell from 40% to about 14.29%, therefore patching improved.

Bridge: all-client acceptance remains 40/100. Thirty accepting records changed segment, not behavior. Report a classifier-induced discontinuity; do not count 30 remediations. If no raw inputs remain, the bridge is unavailable and the trend stays incomparable.

## 2. The denominator silently loses failures

A fixed inventory has 100 eligible asset incarnations. Initially all are observed: 40 affected, 60 unaffected. Later collection observes 70: 10 affected and 60 unaffected; 30 previously affected assets are unreachable.

Naive baseline: 10/70 = 14.29%, a 25.71 percentage-point improvement.

Contract result: 10 observed affected, 60 observed unaffected, 30 unknown; coverage 70/100. The population affected fraction is bounded by 10/100 and 40/100 **only assuming correct observed classifications, binary status, and complete inventory**. No particular unknown asset is proven fixed. In real inventories, undiscovered assets invalidate that population bound. Reuse verified closure for per-asset decisions; no-telemetry is not retirement.

## 3. A valid bridge still does not prove causation

Same 100 asset incarnations, complete observations, unchanged definitions and collection conditions: 40 were affected, now 25 are affected. Per-ID reconciliation shows 15 affected→fixed transitions with fresh fixed-state evidence, 25 affected→affected, and 60 unaffected→unaffected.

Report 15 verified affected-to-fixed transitions and 25 still affected. This supports the observed cohort result, not a causal claim that a campaign caused it or a numerical reduction in organizational risk. New entrants and retired instances belong in separate reconciliation rows, not silently substituted into the fixed cohort.

## 4. A changed control defeats replay

A probe’s control certificate chain changes while the collector is rolled back for three days. Reapplying a bot classifier to old logs does not recover the missing probes or the counterfactual responses to the new chain. Start a new collection epoch and expose the gap; do not interpolate it into successful patching. A stable or validly harmonized classifier is necessary for this comparison but not sufficient.

## Validation and limits

Reviewed 2026-11-01 against the primary references in [SOURCES.md](SOURCES.md). Arithmetic and transition conservation were checked with original JavaScript in the tool sandbox: 100 = 70 + 30; 40 = 10 + 30; 40/100 = 0.4; 10/70 ≈ 0.142857; coverage 0.7; the synthetic missingness interval [0.1, 0.4]; and 40 − 15 = 25. These are worked decision checks, not production measurements. No local shell, Python freshness fixture, scanner, TLS probe, or monitoring pipeline was run in this cycle.
