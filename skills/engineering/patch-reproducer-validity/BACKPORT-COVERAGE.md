# Backport Coverage Across Changed Code

A fix follows an invariant, not a line number or commit hash. An upstream helper can represent several implementations in an older branch. Replaying only the upstream test or repairing one target path leaves the other paths unverified.

## Build a target-specific obligation map

Record the upstream fix and parent, exact target revision/configuration, and invariant being repaired. For each upstream change, map target callers and implementation sites, relevant state assumptions, dependency evidence, and paired tests. Mark unknown mappings explicitly. A missing or renamed helper is not evidence that the target is unaffected; follow history and callers to distinguish duplication, removed behavior and equivalent fixes already present.

| Obligation | Evidence to collect |
|---|---|
| Every affected target site | Caller/path inventory and targeted baseline/candidate probes |
| Necessary prerequisites | History showing the required API, state or lifetime assumption; ordered dependencies or justified adaptation |
| Incidental differences | Why a rename/refactoring need not be imported to preserve the invariant |
| Error exits | Acquisition/release order, cleanup target and side effects, including unchanged surrounding code |
| Supported behavior | Valid/boundary cases under the target's supported configurations |

Do not import every intervening refactor just to make a patch apply. Choose necessary prerequisites within approved scope, adapt the invariant, or stop with the missing evidence. Search results and a manually completed table cannot certify that all sites or dependencies were found.

Inspect full functions and callers, not just conflict markers. Same-named parameters, labels or helpers can have different meanings across branches. A clean application or successful build establishes neither complete coverage nor correct cleanup. Reuse [paired evidence](SKILL.md) to separate repaired cases, new regressions and inconclusive runs.

## Original counterexample

The isolated model's contract rejects payloads longer than eight bytes with no effects or retained lease. Supported target entrypoints `upload` and `restore` contain duplicate implementations; upstream consolidates both into one helper.

| Candidate | Nine-byte upload | Nine-byte restore | Cleanup |
|---|---|---|---|
| Target baseline | Accepted | Accepted | Released |
| One-site backport | Rejected | Accepted | Released |
| Both checks, copied early return | Rejected | Rejected | Lease retained |
| Complete target adaptation | Rejected | Rejected | Released |

Upstream validates before acquisition, so its early return needs no release. The target acquires first. An oracle checking only rejection misses the copied return's resource defect. The complete adaptation covers both sites and balances acquisition/release; valid payloads remain unchanged. These variants demonstrate separate obligations, not a real parser vulnerability or actual kernel backport.

From the directory containing this document (repository or copied package), run:

```sh
python3 check_backport.py
python3 -O check_backport.py
```

## Review packet and authority

Keep the site map, dependency dispositions, adaptations, target build/configuration, paired outputs and remaining unknowns together. For Linux stable work, consult its submission rules for upstream provenance, prerequisites, adaptations and newer supported branches. This does not authorize submission or disclosure.

Use [applicability](https://github.com/narenaryan/agent-skills/blob/main/skills/security/rbvm-applicability/SKILL.md) for whether the deployed vendor artifact is affected, [guarded remediation](https://github.com/narenaryan/agent-skills/blob/main/skills/security/rbvm-guarded-remediation/SKILL.md) for execution approval, and [verified closure](https://github.com/narenaryan/agent-skills/blob/main/skills/security/rbvm-verified-closure/SKILL.md) for fresh deployed evidence. Local validation closes none of those gates. See [sources and limits](SOURCES.md).


Cross-skill links open repository sources; those skills need not be installed beside this package. Local companion links stay within this directory.
