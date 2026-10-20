---
name: git-hooks
description: Use when hooks are unexpected, missing, or misconfigured; covers effective paths, visibility, lifecycle, bypasses, and checkout scope
---

# Git Hooks

Hooks run on named Git events from the effective path. Git ignores non-executable files; failed pre-hooks abort, post-hooks do not.

## Locate the effective hooks

~~~bash
git rev-parse --git-path hooks
git rev-parse --git-common-dir
git config --show-origin --get core.hooksPath
~~~

--git-path hooks resolves the path: $GIT_DIR/hooks normally, $GIT_COMMON_DIR/hooks in linked worktrees. Relative core.hooksPath follows hook cwd (non-bare clients: worktree root; bare/receive: $GIT_DIR).

## Distribution

Clones omit source `.git/hooks`; templates can seed hooks and `core.hooksPath` can redirect to shared/global hooks. After reviewing and trusting the scripts, use a tracked directory:
```bash
git config core.hooksPath .githooks
git commit --no-verify          # bypass pre-commit + commit-msg
git push --no-verify            # bypass pre-push
```

## Visibility and checkout scope

- A custom zsh chpwd function can list executable non-.sample hooks once per path; call it at shell startup too, and avoid alert fatigue.
- A .pre-commit-config.yaml declares checks, not an installed hook. Installer-marker checks miss custom wrappers.
- Sharing a working copy can bring active .git metadata. Linked worktrees share common-dir hooks; see [Git worktrees](../git-worktrees/SKILL.md).

## Client-Side

Commit flow: `pre-commit` → `prepare-commit-msg` → editor → `commit-msg` → `post-commit`.

| Hook | Args | Abort? | Use |
|------|------|--------|-----|
| `pre-commit` | — | yes | lint, format, fast tests |
| `prepare-commit-msg` | msg-file, source, sha | yes | inject ticket ID, templates |
| `commit-msg` | msg-file | yes | validate message format |
| `post-commit` | — | no | notifications |
| `pre-rebase` | upstream [branch] | yes | block rebasing published commits |
| `post-rewrite` | `amend`\|`rebase`; stdin: old→new sha | no | re-run artifact gen after amend |
| `post-checkout` | prev, new, branch-flag | no | LFS smudge, regenerate artifacts |
| `post-merge` | squash-flag | no | restore untracked state |
| `pre-push` | remote, url; stdin: `local-ref local-sha remote-ref remote-sha` | yes | full tests, block force-push to main |
| `pre-auto-gc` | — | yes | defer gc when busy |

Patch flow (`git am`): `applypatch-msg` → `pre-applypatch` → `post-applypatch`.

## Server-Side (on bare repo)

| Hook | Args | Scope | Abort? |
|------|------|-------|--------|
| `pre-receive` | stdin `old new ref` per updated ref | once per push | yes (rejects all) |
| `update` | ref, old, new | **per ref** | yes (that ref only) |
| `post-receive` | stdin like pre-receive | once | no — CI triggers |

`update` is the granular gatekeeper: protect branches, reject non-FF on main, require signed commits.

`pre-push` and `pre-receive` receive ref-update records on stdin; read them when validating refs.

## Pitfalls

- For Bash hooks, use `set -euo pipefail`; POSIX sh lacks `pipefail`.
- `core.hooksPath` **replaces** the default dir; copy any needed defaults in.
- Client hooks are advisory; enforce security server-side or in CI.
- Prompt listings are visibility aids, not hook validation or enforcement.

See [source and validation notes](SOURCES.md).

