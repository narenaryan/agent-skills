# Sapling stacked PR workflow: sources and validation

Reviewed 2026-10-17. This skill is an original synthesis of Sapling's official public documentation and release notes. It documents the Git CLI / GitHub workflow only; it does not assume Meta's non-public Sapling server or virtual filesystem.

## Primary sources

- [Introduction](https://sapling-scm.com/docs/introduction/) and [Smartlog](https://sapling-scm.com/docs/overview/smartlog/): public Git support, working-copy markers, graph context, and caveats that Git support may still have rough edges.
- [Stacks of commits](https://sapling-scm.com/docs/overview/stacks/), [absorb](https://sapling-scm.com/docs/commands/absorb/), and [amend](https://sapling-scm.com/docs/commands/amend/): editing lower stack commits, previewing absorb targets, working-copy scope, empty-commit removal, `--to`, and automatic descendant rebasing.
- [restack](https://sapling-scm.com/docs/commands/restack/) and [rebase](https://sapling-scm.com/docs/commands/rebase/): orphaned descendant recovery and conflict continuation/abort.
- [Undo](https://sapling-scm.com/docs/overview/undo/), [Hide/Unhide](https://sapling-scm.com/docs/overview/hide-unhide/), [unamend](https://sapling-scm.com/docs/commands/unamend/), and [uncommit](https://sapling-scm.com/docs/commands/uncommit/): graph history, predecessor lookup, leaf/parent restrictions, and the distinction between graph state and pending working-copy changes.
- [Sapling stack](https://sapling-scm.com/docs/git/sapling-stack/), [Using Sapling with GitHub](https://sapling-scm.com/docs/git/github/), [`pr`](https://sapling-scm.com/docs/commands/pr/), and [`ssl`](https://sapling-scm.com/docs/commands/ssl/): overlapping PR diffs, ReviewStack, branch-per-PR alternative, PAT requirement, GitHub CLI auth, workflow OAuth scope, and linked-PR status.
- [Release 0.2.20260929-102736+288e0c2d](https://github.com/facebook/sapling/releases/tag/0.2.20260929-102736%2B288e0c2d): as of this review, the latest public release dated 2026-09-29; confirms `goto` of an obsolete commit and committing on one prompt for confirmation, and `HGPLAIN=1` keeps earlier script behavior. Check `sl --version`, help, and current release notes before relying on version-specific behavior.

## Validation boundaries

The command claims were checked against the linked official references on 2026-10-17. The authoring environment has no `sl` executable, so no Sapling command was run against a repository. GitHub authentication, PR submission/update behavior, conflict handling, and GitHub rendering were not runtime-tested. No software was installed. The workflow is guidance, not a guarantee that Git support or each hosting configuration has no rough edges.
