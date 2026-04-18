---
name: git-rewriting-history
description: Use when editing past commits — amending, splitting, squashing, reordering, dropping, or bulk-rewriting history with interactive rebase or filter-repo
---

# Rewriting Git History

**Iron rule:** only rewrite commits not yet pushed to a shared branch. Every rewrite changes the SHA of the commit and all descendants.

## Amend

```bash
git commit --amend              # edit message + staged changes
git commit --amend --no-edit    # fold staged changes, keep message
git commit --amend --author="Name <email>"
```

## Interactive Rebase

```bash
git rebase -i HEAD~N
git rebase -i --root
git rebase -i --autosquash      # auto-order fixup!/squash! commits
```

Commits appear **oldest-first** (replay order, opposite of `git log`).

| Verb | Effect |
|------|--------|
| `pick` | use as-is |
| `reword` | keep diff, edit message |
| `edit` | stop to amend diff/message |
| `squash` | fold into previous, combine messages |
| `fixup` | like squash, discard this message |
| `drop` | remove entirely |
| `exec <cmd>` | run cmd between commits (e.g. `exec make test`) |

## Splitting

Mark `edit`, then at the stop:
```bash
git reset HEAD^
git add -p && git commit
git rebase --continue
```

## Bulk Rewrite: filter-repo

Prefer `git-filter-repo` over deprecated `git filter-branch`.

```bash
git filter-repo --path secrets.env --invert-paths   # purge file from all history
git filter-repo --path-rename old/:new/
git filter-repo --mailmap mailmap.txt               # rewrite authors
git filter-repo --subdirectory-filter trunk
```

After rewrite: force-push with `--force-with-lease`.

## Recovery

```bash
git rebase --abort
git reflog && git reset --hard HEAD@{N}
```

## Pitfalls

- `--autosquash` needs commits made via `git commit --fixup=<sha>`.
- `exec make test` between commits pinpoints which rewritten commit breaks the build.
- `filter-branch` silently corrupts edge cases; `filter-repo` refuses unsafe rewrites.
