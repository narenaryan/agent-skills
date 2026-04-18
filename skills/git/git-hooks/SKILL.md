---
name: git-hooks
description: Use when writing, debugging, or configuring git hooks (pre-commit, commit-msg, pre-push, pre-receive, etc.) — covers firing order, arguments, exit-code effects, and core.hooksPath for team distribution
---

# Git Hooks

Executables in `.git/hooks/` (or `core.hooksPath`) named for the event. Non-zero exit **aborts** (except `post-*`). Any language; must be `+x`, no extension.

## Distribution

`.git/hooks/*` is **not** cloned. Use a tracked dir:
```bash
git config core.hooksPath .githooks
git commit --no-verify          # bypass pre-commit + commit-msg
git push --no-verify            # bypass pre-push
```

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

## Debugging

```bash
GIT_TRACE=1 git commit
bash -x .git/hooks/pre-commit
```

Hooks reading stdin (`pre-push`, `pre-receive`) **must consume it** — forgetting silently deadlocks on large pushes.

## Pitfalls

- Use `set -euo pipefail` in shell hooks; otherwise silent pass on pipeline failure.
- `core.hooksPath` **replaces** the default dir; copy any needed defaults in.
- Client hooks are advisory — never rely on them for security. Enforce server-side or in CI.
