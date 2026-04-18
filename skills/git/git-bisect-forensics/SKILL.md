---
name: git-bisect-forensics
description: Use when hunting a regression across many commits or tracing the origin of a line/function/string — covers automated bisect, skip, replay, blame -L/-C/-w, and pickaxe search (-S/-G)
---

# Git Bisect & Forensics

## Bisect: Binary Search

```bash
git bisect start <bad> <good>     # or: start; bad; good <tag>
# git checks out midpoint; you test, then:
git bisect good | bad | skip
git bisect reset                  # finish, back to original HEAD
```

## Automated

Exit codes: `0` good, `1–124,126,127` bad, `125` skip, `≥128` abort.

```bash
git bisect start HEAD v1.4.0
git bisect run ./reproduce.sh
git bisect run sh -c 'cargo build && cargo test --test regression'
```

1000 commits → ~10 test runs.

## Save / Resume

```bash
git bisect log > bisect.log
git bisect reset
# later:
git bisect replay bisect.log
```

## Blame

```bash
git blame -L 40,80 file.py                 # line range
git blame -L :funcName:file.py             # by function
git blame -w file.py                       # ignore whitespace-only
git blame -C file.py                       # detect moves within same-commit diffs
git blame -C -C -C file.py                 # across files in any commit (thorough)
git blame --ignore-rev <sha> file.py       # skip a mass-format commit
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

`-C` bypasses "moved file → blame points at the move commit."

## Pickaxe

```bash
git log -S"token"                  # when token count in file changed
git log -S"pat" --pickaxe-regex
git log -G"regex"                  # any line matching was touched
git log -L :ClassName:src/p.ts     # full evolution of a symbol
git log --follow -p -- path        # history across renames
```

- `-S`: added/removed detection (precise).
- `-G`: any touch of matching lines (broader).

## Combo: Narrow then Bisect

```bash
git log -S"oldLogic" -- src/       # last clean commit
git bisect start HEAD <that-sha>
git bisect run pytest tests/test_regression.py
```

## Pitfalls

- On commits that don't build, return **125** (skip), not 1, from the bisect script.
- `-S` is literal by default; use `--pickaxe-regex`.
- Bisect leaves detached HEAD — always `git bisect reset` before committing.
