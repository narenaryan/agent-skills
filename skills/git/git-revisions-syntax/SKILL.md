---
name: git-revisions-syntax
description: Use when selecting commits, ranges, or historical refs in git — covers ^, ~, .., ..., @{N}, @{time}, --not, and pickaxe content selectors
---

# Git Revision Syntax

## Single Commits

| Syntax | Meaning |
|--------|---------|
| `abc123` | SHA prefix (≥4, unambiguous) |
| `HEAD` / `@` | current commit |
| `HEAD^` | first parent |
| `HEAD^2` | **second** parent (merge's other side) |
| `HEAD~N` | walk N steps along first parent |
| `HEAD~3^2` | chained: grandparent's merge sibling |
| `HEAD@{2}` | 2 reflog entries ago |
| `HEAD@{yesterday}` / `@{2.weeks.ago}` | reflog by time |
| `@{-1}` | previously checked-out branch |
| `@{u}` / `@{push}` | upstream / push target |
| `tag^{}` | deref annotated tag to commit |
| `:/fix typo` | newest commit whose msg matches regex |

`^N` picks parent **N** of one commit (merge-aware). `~N` walks N first-parent steps. Different.

## Ranges

| Syntax | Meaning |
|--------|---------|
| `A..B` | in B, not A |
| `A...B` | symmetric diff (either but not both) |
| `^A B` / `B --not A` | same as `A..B` |
| `A B ^C` | in A or B, not C |

```bash
git log origin/main..HEAD              # unpushed
git log --left-right main...feature    # side-marked
git log HEAD --not release/*
```

## Content-Based Selectors

```bash
git log -S"token"                  # commits where literal token count changed
git log -S"pat" --pickaxe-regex
git log -G"regex"                  # commits touching any matching line
git log -L :funcName:file.js       # evolution of a function
git log -L 10,20:file.js           # evolution of line range
```

`-S` = added/removed detection; `-G` = any line touching pattern.

## Plumbing

```bash
git rev-parse HEAD~3               # resolve to full SHA
git merge-base A B                 # nearest common ancestor
git name-rev <sha>                 # which branch/tag contains it
```

## Pitfalls

- Reflog selectors (`@{N}`, `@{time}`) are **local**, expire (~90 days).
- `HEAD^` in zsh/PowerShell needs quoting.
- `A..B` is empty if B is an ancestor of A — probably want `B..A`.
