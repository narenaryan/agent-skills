---
name: modularize-large-files
description: Use when a source file has grown past ~2k lines or a "god module" is hard to navigate - finds the largest files, splits them along cohesion seams (not arbitrary line counts), preserves the public API with re-exports, and moves in behavior-preserving steps verified by tests between each extraction
---

# Modularize Large Files

Line count is a symptom, not the disease. A 2k-line file is a prompt to look for
seams, not a mandate to chop it into ten 200-line files that all import each
other. Split along cohesion boundaries so each new module has one reason to
change; if the pieces still need each other's internals, you have moved the mess,
not fixed it.

## Find the offenders

Rank by size, then read before cutting:

```bash
# Largest tracked source files by line count (skip vendored/generated)
git ls-files '*.ts' '*.tsx' '*.js' '*.py' '*.go' '*.rs' \
  | grep -Ev '(dist|build|vendor|node_modules|\.min\.)' \
  | xargs wc -l | sort -rn | head -20
```

Treat anything over ~2k lines as a candidate. Do not auto-split: a large file
that is genuinely one cohesive thing (a generated parser, a single state machine)
can be fine.

## Find the seams

Inside the file, look for clusters that move together:

- **Types/domain** — interfaces, enums, schemas with no runtime behavior. These
  become a leaf module everything else imports; extract them first.
- **Pure vs I/O** — pull pure helpers away from DB/network/filesystem code.
- **Distinct responsibilities** — a group of functions sharing a prefix, a
  concern (auth, formatting, validation), or the same private state.

The best cut is the one that produces the fewest cross-imports between the new
modules. If two candidate modules would import each other's internals, the seam
is wrong — merge them or lift the shared piece into a third leaf module.

## Move without breaking callers

1. Extract one seam into a new file; keep names identical.
2. In the original file, **re-export** what you moved (`export * from './x'` or a
   barrel `index`) so external callers keep working unchanged.
3. Run typecheck + tests. Green before the next extraction.
4. Commit per extraction — small, revertable, reviewable diffs.

Only after all seams are out and green, migrate callers off the barrel to direct
imports if the project prefers that, as a separate commit.

## Guardrails

- Never mix a refactor with a behavior change in the same commit.
- Watch for circular imports the split introduces — the shared piece belongs in a
  leaf, not in either sibling.
- Preserve test file structure: split the test file along the same seams.
- If a function needs private module state to move, extract the state too or pass
  it explicitly; don't reach across module boundaries with globals.
