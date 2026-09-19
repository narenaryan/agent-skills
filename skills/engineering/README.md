# engineering skills

General engineering judgment for testing, debugging, metrics, documentation, modeling, root-cause analysis, AI-generated bug patterns, and practical system maintenance.

## Skills

- **[minimal-sufficient-evidence](minimal-sufficient-evidence/SKILL.md)** - remove redundant tests and artifacts while preserving the smallest evidence set needed for debugging, regression coverage, metrics, templates, models, and root-cause analysis.
- **[ai-bug-patterns](ai-bug-patterns/SKILL.md)** - review AI-assisted code for silent production failures: broken auth, missing query scope, TOCTOU, idempotency bugs, stale state, validation drift, swallowed errors, and incomplete refactors.
- **[macos-disk-space-recovery](macos-disk-space-recovery/SKILL.md)** - diagnose low disk space on macOS with APFS-aware measurement, rank real offenders, and remove caches or app data safely while reporting reclaimed space.
- **[modularize-large-files](modularize-large-files/SKILL.md)** - find files past ~2k lines and split god modules along cohesion seams, preserving the public API with re-exports and verifying tests between each behavior-preserving extraction.

## Install

```bash
./install.sh engineering                  # install all
./install.sh minimal-sufficient-evidence  # install one
./install.sh ai-bug-patterns              # install one
./install.sh macos-disk-space-recovery    # install one
./install.sh modularize-large-files       # install one
```
