---
name: sapling-stacked-pr-workflow
description: Use when Sapling's `sl` needs an older stacked commit amended, a restack conflicts or orphans children, or GitHub stack PR diffs overlap unexpectedly
---

# Repair and Review Sapling Stacks

Sapling replaces an amended commit with a successor; descendants restack automatically or become orphans on conflicts. Review each edit in Smartlog (`sl`).

## Edit a lower commit

1. Run `sl` and `sl status`. Confirm `@`, target, and pending files. Unlike Git's index, `sl amend` includes all pending changes by default.
2. At stack top, preview routing with `sl absorb --dry-run`. Then run `sl absorb` to inspect its proposed targets and prompt. Accept only unambiguous chunks; unmatched changes stay pending. Absorbing can restack descendants and delete commits left empty.
3. For a new file or ambiguous change, run `sl addremove` if needed, then `sl amend --to REV` with the intended target. Or `sl goto REV` before amending. Confirm only intended files are pending.
4. Inspect `sl` after edit. If children are orphaned, run `sl restack`; resolve conflicts then `sl rebase --continue`, or `sl rebase --abort` if unsafe. Verify graph and tests before publishing.

## Recover a mistaken edit

- `sl undo` restores the graph before the last graph operation; `sl redo` reverses that undo. It does not restore working-copy edits or retract remote publication.
- `sl unamend` returns an amended leaf draft to its predecessor and leaves the delta pending; it works only when the draft has no children and its predecessor has matching parents. `sl uncommit` does the same for a mistaken leaf draft commit when nothing is already pending.
- Inspect an earlier version with `sl log -r "predecessors(REV)"`, replacing `REV` with the target; inspect a candidate via `sl show` before `sl unhide`.

## Choose the GitHub review shape

Provide a GitHub PAT; Sapling recommends `gh auth login --git-protocol https`. Check `sl ssl` for linked-PR status and verify `default` / `default-push` target the intended repos. `sl pr submit --stack` includes draft ancestors. Each PR contains its own commit and all lower commits, so GitHub diffs overlap; use ReviewStack when the team supports it. For one PR per branch, use `sl push --to remote/my-feature`, then create the PR on GitHub. `sl push -f` force-updates that branch; check team policy.

## Pitfalls

- Amend changes commit IDs. Follow Smartlog, not stale hashes.
- `sl unhide` also reveals ancestors. Local undo/hide does not retract a pushed commit or close/update its PR.
- Release 0.2.20260929 asks before `goto` of an obsolete commit or committing atop one; `HGPLAIN=1` retains old script behavior. Don't bypass the interactive prompt.
- For PRs touching `.github/workflows`, default `gh` scopes lack `workflow`; `sl pr submit` may create/update a PR, then abort updating its archive branch. Check GitHub before retry; refresh with `gh auth refresh -s workflow` first.

See [SOURCES.md](SOURCES.md) for official references, version scope, and validation limits.
