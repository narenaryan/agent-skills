---
name: git-reset-mechanics
description: Use when undoing commits, unstaging files, or choosing between reset/checkout/restore — clarifies which tree each variant touches and when --hard is unsafe
---

# Git Reset Mechanics

Three trees: **HEAD** (last commit), **Index** (staged), **Working** (disk). `reset` walks them in order and stops by flag.

| Flag | HEAD ref | Index | Workdir | WD-safe |
|------|----------|-------|---------|---------|
| `--soft` | moves | — | — | yes |
| `--mixed` (default) | moves | resets | — | yes |
| `--hard` | moves | resets | resets | **NO** |

## Reset vs Checkout (no path)

- `git reset --hard <ref>` moves the **branch** HEAD points to; overwrites workdir without checking.
- `git checkout <ref>` moves **HEAD** (detaches if a commit); refuses if unsaved changes conflict.

## With a Path

`git reset <commit> -- <path>` copies commit→index, **skips HEAD move** (can't partially move a pointer). `--hard` with a path is rejected.

`git checkout <commit> -- <path>` copies commit→index **and workdir** — destructive. Prefer modern `restore`:

- `git restore --staged <path>` — unstage
- `git restore <path>` — discard workdir change
- `git restore --source=<ref> -SW <path>` — both

## Patterns

```bash
git reset --soft HEAD~            # undo commit, keep staging
git reset HEAD~                   # undo commit + unstage
git reset --hard HEAD~            # undo + discard (destructive)
git reset --soft HEAD~3 && git commit   # squash last 3
git reset --patch                 # unstage hunks
```

## Pitfalls

- `--hard` is the only destructive common flag — no prompt. Recovery: `git reflog` → `git reset --hard HEAD@{1}`.
- Reset on a pushed branch rewrites history others have. Use `revert` instead.
