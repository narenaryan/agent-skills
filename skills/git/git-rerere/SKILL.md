---
name: git-rerere
description: Use when the same merge conflicts keep recurring across rebases or long-running integration branches — enables automatic replay of previously-recorded resolutions
---

# Git Rerere (Reuse Recorded Resolution)

Rerere fingerprints conflict hunks + resolutions. On any later merge/rebase/cherry-pick producing the **same** conflict, Git auto-applies the stored fix.

## Enable

```bash
git config --global rerere.enabled true
git config --global rerere.autoupdate true   # also stage auto-resolved files
```

Storage: `.git/rr-cache/<hash>/{preimage,postimage}`. Local, not pushed.

## Commands

```bash
git rerere status         # files with recorded preimages
git rerere diff           # current vs recorded resolution
git rerere remaining      # unresolved files
git rerere forget <file>  # discard a recorded resolution
git rerere gc             # prune old entries
```

## Flow

1. First conflict: `Recorded preimage for 'file'`.
2. Resolve + commit: `Recorded resolution for 'file'`.
3. Next time the same conflict appears: `Resolved 'file' using previous resolution.` — with `autoupdate`, already staged.

## Canonical Uses

- Long-running topic branch rebased onto main repeatedly.
- Nightly integration branches that merge many topics, reset, re-merge.
- **Test-merge-and-reset** to pre-record resolutions:
  ```bash
  git merge feature && git reset --hard HEAD~
  # resolution is recorded; next merge applies it automatically
  ```

## Sharing

rr-cache isn't pushed. Copy between checkouts:
```bash
rsync -a .git/rr-cache/ other-repo/.git/rr-cache/
```

## Pitfalls

- Matches exact conflict content — whitespace/ordering drift breaks the match. Check `git rerere diff` before trusting auto-resolution.
- With `autoupdate=true`, a bad past resolution silently re-applies. Spot-check.
- Auto-resolved files show no conflict markers; use `git rerere forget <file>` to re-surface for manual redo.
