---
name: git-advanced-merging
description: Use when resolving non-trivial merge conflicts, choosing a merge strategy, or undoing a merge — covers -X options, diff3 markers, strategy vs option, reset vs revert -m, and re-merging reverted branches
---

# Advanced Git Merging

## Conflict Marker Style

Default hides the common ancestor. Show it:
```bash
git config --global merge.conflictStyle zdiff3   # git 2.35+; else diff3
git checkout --conflict=diff3 path               # re-render existing conflict
```

Markers become `<<<ours / ||| base / === / theirs >>>` — resolution is far easier.

## Side-Picking

```bash
git checkout --ours path
git checkout --theirs path
git add path
```

During **rebase**, ours/theirs **swap**: "theirs" = the commits being replayed.

## Strategy (`-s`) vs Strategy Option (`-X`)

- **Strategy** (`-s`) picks the algorithm: `ort` (default), `recursive`, `resolve`, `octopus`, `ours`, `subtree`.
- **Option** (`-X`) tunes a strategy. `-X ours` only breaks ties; non-conflicting changes still merge.

```bash
git merge -X ours feature           # merge all, prefer ours on conflict
git merge -s ours feature           # fake-merge: record, keep tree unchanged
git merge -X ignore-all-space feature
git merge -X patience feature       # better diff for reordered blocks
```

`-s ours` says "we abandon their work but don't want future merges replaying it."

## Inspecting

```bash
git ls-files -u                     # stages 1=base, 2=ours, 3=theirs
git show :1:f > base; git show :2:f > ours; git show :3:f > theirs
git merge-file -p ours base theirs > resolved
git log --merge -p path             # commits on either side touching file
git log --left-right HEAD...MERGE_HEAD
```

## Abort

```bash
git merge --abort                   # before committing
git reset --merge                   # equivalent
```

## Undoing a Completed Merge

**Local only:** `git reset --hard ORIG_HEAD`

**Already pushed:** `git revert -m 1 <merge-sha>` (keep mainline, drop feature side).

**Gotcha:** after `revert -m 1`, re-merging the same branch pulls only new commits — Git thinks the rest is already merged. Fix:
```bash
git revert <revert-commit>          # un-revert
git merge feature                   # clean re-merge
```

## Pitfalls

- No `-s theirs` exists; do `-s ours` on the other branch then merge back.
- Octopus strategy refuses to auto-resolve conflicts.
- For recurring conflicts, enable rerere.
