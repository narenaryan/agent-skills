# engineering skills

General engineering judgment for testing, debugging, metrics, documentation, modeling, root-cause analysis, AI-generated bug patterns, and practical system maintenance.

## Skills

- **[minimal-sufficient-evidence](minimal-sufficient-evidence/SKILL.md)** - remove redundant tests and artifacts while preserving the smallest evidence set needed for debugging, regression coverage, metrics, templates, models, and root-cause analysis.
- **[patch-reproducer-validity](patch-reproducer-validity/SKILL.md)** - prove repaired cases separately from introduced regressions; distinguish pre-existing defects, weak oracles, and incomparable replay evidence. See [sources and validation limits](patch-reproducer-validity/SOURCES.md).
- **[prompt-cache-boundaries](prompt-cache-boundaries/SKILL.md)** - audit provider-bound Claude prompt prefixes, separate cache diagnostics from actual reuse, and preserve task-quality evidence. See [sources and offline validation limits](prompt-cache-boundaries/SOURCES.md).
- **[ai-bug-patterns](ai-bug-patterns/SKILL.md)** - review AI-assisted code for silent production failures: broken auth, missing query scope, TOCTOU, idempotency bugs, stale state, validation drift, swallowed errors, and incomplete refactors.
- **[macos-disk-space-recovery](macos-disk-space-recovery/SKILL.md)** - diagnose low disk space on macOS with APFS-aware measurement, rank real offenders, and remove caches or app data safely while reporting reclaimed space.
- **[modularize-large-files](modularize-large-files/SKILL.md)** - find files past ~2k lines and split god modules along cohesion seams, preserving the public API with re-exports and verifying tests between each behavior-preserving extraction.

- **[compressed-ndjson-boundaries](compressed-ndjson-boundaries/SKILL.md)** - preserve record boundaries through zstd decompression, cap memory growth, reject truncated streams, and respect simdjson lifetimes.

- **[transactional-outbox-delivery](transactional-outbox-delivery/SKILL.md)** - keep domain writes and event rows atomic, make relay retries safe, and preserve aggregate order with idempotent consumers.

- **[linux-io-latency-triage](linux-io-latency-triage/SKILL.md)** - distinguish OS queueing from issued-request latency, check trace coverage, and avoid false NVMe saturation or writeback attribution. See [sources and scenario-test limits](linux-io-latency-triage/SOURCES.md).

## Install

```bash
./install.sh engineering                  # install all
./install.sh minimal-sufficient-evidence  # install one
./install.sh ai-bug-patterns              # install one
./install.sh macos-disk-space-recovery    # install one
./install.sh modularize-large-files       # install one
./install.sh compressed-ndjson-boundaries # install one
./install.sh transactional-outbox-delivery # install one
./install.sh patch-reproducer-validity     # install one
./install.sh prompt-cache-boundaries       # install one
```
