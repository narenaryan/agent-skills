---
name: git-data-recovery
description: Use when commits or branches seem lost — after hard reset, force-push, branch delete, or botched rebase — to locate dangling objects via reflog and fsck before gc prunes them
---

# Git Data Recovery

Lost commits survive until `gc` prunes (default: 14 days dangling, 90 days reflog-reachable). Recovery is a race against `gc`.

## Path 1: Reflog (for commits you were on)

```bash
git reflog                     # HEAD history
git reflog show <branch>       # per-branch
git log -g --oneline           # same as log

git branch rescue <sha>
git reset --hard HEAD@{5}
git cherry-pick HEAD@{1}
```

Reflog is **local**, **per-ref**. A fresh clone has none.

## Path 2: fsck (when reflog is gone)

```bash
git fsck --full --no-reflogs --unreachable --lost-found
# dangling commit abc...
```

`--lost-found` writes objects to `.git/lost-found/{commit,other}/`.

Inspect candidates:
```bash
for sha in $(git fsck --no-reflog --unreachable | awk '/commit/ {print $3}'); do
  git log -1 --format='%h %ci %s' "$sha"
done
git branch rescue <sha>
```

## Path 3: One File from a Commit

```bash
git show <sha>:path > recovered
git checkout <sha> -- path
```

## Protect Before Risky Ops

```bash
git tag rescue/$(date +%s) HEAD
git update-ref refs/rescue/before-rebase HEAD
```

Any ref under `refs/` keeps objects reachable indefinitely.

## gc / Prune

- Auto-triggers at ~7,000 loose objects or 50+ packfiles.
- `git gc --prune=now` **immediately** deletes unreachable objects — do not run during recovery.
- `git reflog expire --expire-unreachable=now --all && git gc --prune=now` destroys recovery paths.

## Find Large Objects

```bash
git rev-list --objects --all \
  | git cat-file --batch-check='%(objectname) %(objecttype) %(objectsize) %(rest)' \
  | awk '$2=="blob"{print $3,$4}' | sort -n | tail -20
```

Purge: `git filter-repo --path <file> --invert-paths`.

## Pitfalls

- Debug on the original working copy; a fresh clone has no reflog.
- Don't "clean up" before verifying recovery — many one-liners silently destroy it.
