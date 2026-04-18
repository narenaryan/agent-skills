# git skills

Advanced git workflows distilled into small, focused skills. Each one targets a specific scenario — conflicts, recovery, history rewrites — so Claude pulls in only the relevant knowledge.

## Skills

- **[git-advanced-merging](git-advanced-merging/SKILL.md)** — resolving non-trivial merge conflicts, choosing a merge strategy, or undoing a merge. Covers `-X` options, diff3 markers, strategy vs option, `reset` vs `revert -m`, and re-merging reverted branches.
- **[git-bisect-forensics](git-bisect-forensics/SKILL.md)** — hunting a regression across many commits or tracing the origin of a line/function/string. Covers automated bisect, skip, replay, `blame -L/-C/-w`, and pickaxe search (`-S/-G`).
- **[git-data-recovery](git-data-recovery/SKILL.md)** — recovering commits or branches that seem lost after hard reset, force-push, branch delete, or botched rebase. Locate dangling objects via reflog and fsck before gc prunes them.
- **[git-hooks](git-hooks/SKILL.md)** — writing, debugging, or configuring git hooks (pre-commit, commit-msg, pre-push, pre-receive, etc.). Covers firing order, arguments, exit-code effects, and `core.hooksPath` for team distribution.
- **[git-rerere](git-rerere/SKILL.md)** — automatic replay of previously-recorded conflict resolutions. Use when the same merge conflicts keep recurring across rebases or long-running integration branches.
- **[git-reset-mechanics](git-reset-mechanics/SKILL.md)** — undoing commits, unstaging files, or choosing between reset/checkout/restore. Clarifies which tree each variant touches and when `--hard` is unsafe.
- **[git-revisions-syntax](git-revisions-syntax/SKILL.md)** — selecting commits, ranges, or historical refs. Covers `^`, `~`, `..`, `...`, `@{N}`, `@{time}`, `--not`, and pickaxe content selectors.
- **[git-rewriting-history](git-rewriting-history/SKILL.md)** — editing past commits: amending, splitting, squashing, reordering, dropping, or bulk-rewriting history with interactive rebase or filter-repo.
- **[git-submodules](git-submodules/SKILL.md)** — cloning, updating, pinning a branch, pushing safely, branch switching that adds/removes submodules, or resolving submodule conflicts.
- **[git-worktrees](git-worktrees/SKILL.md)** — multiple checked-out branches simultaneously without re-cloning. Review a PR while keeping WIP, per-branch build caches, hotfix alongside feature work.

## Install

```bash
./install.sh git                 # install all
./install.sh git-hooks           # install one
```
