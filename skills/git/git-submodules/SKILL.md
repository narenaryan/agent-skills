---
name: git-submodules
description: Use when working with git submodules — cloning, updating, pinning a branch, pushing safely, branch switching that adds/removes submodules, or resolving submodule conflicts
---

# Git Submodules

A submodule pins a **specific commit** of an external repo. `.gitmodules` stores URL+path; the super tree records the SHA as a gitlink.

## Cloning

```bash
git clone --recurse-submodules <url>       # preferred
git submodule update --init --recursive    # after a plain clone
```

Plain clone creates empty dirs. `update` without `--init` silently skips new ones.

## Default Update = Detached HEAD

`git submodule update` checks out the pinned SHA **detached**. Work there is lost on next update unless committed to a branch.

Proper edit flow:
```bash
cd sub && git checkout main
# edit, commit, push from inside sub first
cd .. && git add sub && git commit         # bump super pin
```

## Track a Branch

```bash
git config -f .gitmodules submodule.sub.branch main
git submodule update --remote --merge      # fetch + merge
git submodule update --remote --rebase     # fetch + rebase
```

`--remote` alone drops to detached HEAD — loses local work.

## Global Defaults

```bash
git config --global submodule.recurse true         # applies to pull/checkout/reset (NOT clone)
git config --global push.recurseSubmodules check
git config --global status.submodulesummary 1
```

## Push Safety

```bash
git push --recurse-submodules=check        # fail if sub commits unpushed
git push --recurse-submodules=on-demand    # push subs first
```

Without this you push a super pointing to a SHA that doesn't exist remotely.

## Batch

```bash
git submodule foreach 'git fetch --all'
git submodule foreach --recursive 'git status -sb'
```

## Conflicts & URL Moves

Both sides bumped pin:
```bash
cd sub && git merge <their-sha>
cd .. && git add sub && git commit
```

`.gitmodules` URL changed upstream:
```bash
git submodule sync --recursive
git submodule update --init --recursive
```

## Removing

```bash
git submodule deinit -f path/sub
git rm -f path/sub
rm -rf .git/modules/path/sub
```

## Pitfalls

- Forgetting to push the sub before the super — the #1 submodule bug.
- `submodule.recurse=true` does **not** affect `git clone`.
- Converting a subdir to a submodule: `git rm -r dir` then `git submodule add` (not `rm -rf`).
