---
name: git-worktrees
description: Use when needing multiple checked-out branches simultaneously without re-cloning — review a PR while keeping WIP, per-branch build caches, or hotfix alongside feature work
---

# Git Worktrees

Second (and third, …) working directories linked to the same `.git` object store. One repo, many checkouts. Shared history, objects, refs, hooks, LFS — no re-clone.

## Commands

```bash
git worktree add ../hotfix hotfix-branch        # existing branch
git worktree add -b new-branch ../new main      # create from main
git worktree add --detach ../inspect <sha>      # for read-only review
git worktree list [--porcelain]
git worktree lock ../critical                   # prevent prune
git worktree move ../old ../new
git worktree remove ../hotfix                   # after cd out
git worktree prune                              # clean stale metadata
git worktree repair                             # fix links after moves
```

## Rules

- Same branch can't be checked out in two worktrees (use `--detach` or `--force`).
- Main worktree can't be `remove`d — it owns `.git`.
- `rm -rf` on a worktree dir leaves `.git/worktrees/<name>/` — run `prune`.

## Workflows

**Review a PR without losing WIP:**
```bash
git worktree add ../review-1234 --detach origin/pr/1234
```

**Hotfix during a long build:**
```bash
git worktree add -b hotfix/urgent ../hotfix origin/main
```

**Per-branch dedicated build caches:** each worktree has its own `node_modules`, `target/`, etc. — no cross-branch invalidation.

**Parallel bisect:** keep main worktree for editing, run `git bisect run` in a second.

## Per-Worktree Config

```bash
git config extensions.worktreeConfig true
git config --worktree user.email alt@example.com
```

`core.bare`, `core.worktree` are always worktree-scoped.

## Pitfalls

- Hooks run for **every** worktree — `post-checkout` firing `yarn install` per-worktree is correct but noisy.
- Stashes are **shared** across worktrees (single `refs/stash`). Label them.
- IDE indexers can follow `.git` in a linked worktree back to the main repo — point the IDE at the worktree root.
- Worktree on removable media that disappears → `git worktree prune`.
