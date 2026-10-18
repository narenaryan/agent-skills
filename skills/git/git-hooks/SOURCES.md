# Git hooks: sources and validation limits

Reviewed 2026-10-18. This updates the existing git-hooks skill, applying Ned Batchelder's visibility technique while qualifying its clone claim with Git's template and configuration behavior.

## Article

- [Ned Batchelder, “Making git hooks visible” (2026-10-11)](https://nedbatchelder.com/blog/202610/making_git_hooks_visible): uses zsh chpwd functions to list executable, non-sample hooks under git rev-parse --git-path hooks, deduplicates notices, checks for .pre-commit-config.yaml without a recognizable pre-commit/prek installer hook, and calls the checks at shell startup. The post itself warns about prompt noise. These inventory and marker checks are heuristics, not verification of script behavior or enforcement.

## Primary Git documentation

- [githooks](https://git-scm.com/docs/githooks): hooks default to $GIT_DIR/hooks, core.hooksPath changes the location, and files without the executable bit are ignored. Hook working directories differ for worktree and bare repositories, with receive-side hooks running in $GIT_DIR.
- [git-config: core.hooksPath](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corehooksPath): paths may be absolute or relative; relative paths resolve from the hook's working directory. The setting may centralize hooks.
- [git-init: template directory](https://git-scm.com/docs/git-init#_template_directory) and [git-clone: --template](https://git-scm.com/docs/git-clone#Documentation/git-clone.txt---template): initialization or cloning can copy template files into a new repository. A fresh clone normally lacks the source checkout's local .git/hooks, but a configured template can seed hooks.
- [repository layout: hooks](https://git-scm.com/docs/gitrepository-layout#_hooks) and [git-worktree details](https://git-scm.com/docs/git-worktree#_details): linked worktrees use $GIT_COMMON_DIR/hooks rather than a private worktree hooks directory.
- [git rev-parse](https://git-scm.com/docs/git-rev-parse): --git-common-dir and --git-path support locating the shared metadata and effective hooks directory.

## Validation and limits

- Isolated Git 2.52.0 checks confirmed default and configured --git-path hooks, linked worktrees sharing the default and configured hooks path, and executable-hook copying from a local init template. The fixture hook was never executed; no hook was installed, enabled, or run in a user repository.
- Static checks covered frontmatter/name, word budget, source URLs, and relative links. Article zsh functions were read but not executed. No claim is made about arbitrary hook safety, behavior, cross-platform prompts, or GitHub CI.

