# agent-skills: A curated list of skills & commands which stays low on tokens

## Goal

Turn `~/.claude/skills` and `~/.claude/commands` content into an open-source
repository that users can clone and install from with a single shell command.
The repo organizes skills into categories for browsing; the installer flattens
them into the layout Claude Code expects at install time.

## Background

Claude Code discovers skills at `~/.claude/skills/<skill-name>/SKILL.md` and
commands at `~/.claude/commands/<name>.md`. Both locations are flat — there is
no native concept of categories or grouping. Users who want to share or
selectively install skills need tooling that reconciles a grouped repo layout
with the flat install target.

Initial content to port from the author's machine:
- 10 `git-*` skills under `~/.claude/skills/`
- 1 command, `skill-creator.md`, under `~/.claude/commands/`

The repo is intended to grow (e.g., `go`, more categories), so layout and
install behavior must scale without reshuffling.

## Repository Layout

```
agent-skills/
├── README.md                      # pitch + quick start + category table
├── install.sh                     # the installer (this spec's main artifact)
├── test.sh                        # smoke tests for install.sh
├── docs/superpowers/specs/        # design docs (this file lives here)
├── skills/
│   ├── git/
│   │   ├── README.md              # category TOC
│   │   ├── git-advanced-merging/SKILL.md
│   │   ├── git-bisect-forensics/SKILL.md
│   │   ├── git-data-recovery/SKILL.md
│   │   ├── git-hooks/SKILL.md
│   │   ├── git-rerere/SKILL.md
│   │   ├── git-reset-mechanics/SKILL.md
│   │   ├── git-revisions-syntax/SKILL.md
│   │   ├── git-rewriting-history/SKILL.md
│   │   ├── git-submodules/SKILL.md
│   │   └── git-worktrees/SKILL.md
│   └── skill-creator/             # (placeholder — no skill folder yet)
│       └── README.md              # category TOC
└── commands/
    └── skill-creator/
        ├── README.md              # category TOC
        └── skill-creator.md
```

Rules:
- **Skill folder names keep their full names** (e.g. `git-hooks`, not `hooks`).
  They land in `~/.claude/skills/git-hooks/` on install, avoiding cross-category
  collisions.
- **Categories are directory-level only.** Claude Code never sees them.
- **Commands mirror the category structure** so a category groups both skills
  and commands that belong together.
- **Per-category `README.md`** is the only added doc — it is a 1-liner summary
  plus a bulleted list of the category's skills/commands with their
  one-line descriptions. No per-skill README.

## Installer: `install.sh`

### Interface

```
Usage: ./install.sh [options] <target>...

Targets:
  <category>   Install all skills+commands in that category (e.g. git)
  <name>       Install a single skill or command by name (e.g. git-hooks)
  --all        Install everything under skills/ and commands/

Options:
  --link       Symlink instead of copy (updates flow from repo)
  --force      Overwrite existing files in ~/.claude/
  --dry-run    Print planned actions, don't touch filesystem
  -h, --help   Show usage
```

### Target resolution

For a bare positional arg `foo`, in order:
1. If `skills/foo/` exists → **category install**: every
   `skills/foo/*/SKILL.md` folder, plus every file under `commands/foo/` if
   that directory exists.
2. Else if exactly one `skills/*/foo/` exists → **single skill install**.
3. Else if exactly one `commands/*/foo.md` exists → **single command
   install**.
4. Else → error with a suggestion (`did you mean "git"?`).

If step 2 or 3 is ambiguous (same name in two categories) the script errors and
asks the user to disambiguate with the category prefix (`git/foo`).

### Install targets on disk

- Skills → `~/.claude/skills/<skill-name>/` (directory copied/linked flat)
- Commands → `~/.claude/commands/<command-name>.md` (single file copied/linked)

### Conflict handling

Per item, checked independently:
- **Default (no `--force`)**: if the target path exists, log
  `skipped: <name> (already installed, use --force to overwrite)` and continue.
- **`--force`**: overwrite. For existing symlinks, replace the link. For
  existing directories/files, `rm -rf` (directory) or `rm` (file) the target
  and then install.
- **`--dry-run`**: print every planned action as `would install: ...` / `would
  skip: ...` / `would overwrite: ...`. No filesystem writes.

### Copy vs symlink

- **Copy (default)**: `cp -R` for skill directories; `cp` for command files.
- **`--link`**: `ln -s <absolute-repo-path> <target>`. Absolute paths ensure
  the link still resolves if the user's shell cwd changes.

### Safety rails

- Verify `~/.claude/` exists before doing anything; if not, exit 2 with a
  message directing the user to install Claude Code first.
- The script only writes to `~/.claude/skills/` and `~/.claude/commands/`.
  Never anywhere else.
- Before any `rm -rf` under `--force`, the script asserts the target path
  resolves under `~/.claude/skills/` or `~/.claude/commands/`. If not, abort
  without touching anything (paranoia check against path bugs).
- All operations run as the invoking user; no `sudo`.

### Output style

One line per item, no color (CI/pipe-friendly):
```
installed: git-hooks
installed: git-worktrees
skipped: git-rerere (already installed, use --force to overwrite)
linked: skill-creator (command)
```

Summary line at the end: `done: <installed_count> installed, <skipped_count>
skipped, <failed_count> failed`.

### Exit codes

- `0` — every requested item was installed or cleanly skipped.
- `1` — one or more items failed (missing source in repo, permission error,
  safety-rail trip).
- `2` — usage error (unknown flag, missing `~/.claude/`, ambiguous target,
  unresolvable target name).

## README Strategy

### Root `README.md`

Replaces the current 2-sentence placeholder. Contains:
- One-paragraph pitch: a curated list of skills & commands that stays low on
  tokens through knowledge distillation and straightforward prose.
- Quick start block:
  ```bash
  git clone https://github.com/<user>/agent-skills.git
  cd agent-skills
  ./install.sh git
  ```
- Category table with column headers `Category | Skills | Description`.
- Short `--link` note for contributors who want repo edits to flow to their
  live `~/.claude/` without reinstalling.
- Link to per-category READMEs.

### Per-category `README.md`

One-line category description plus a bulleted list of skills/commands in the
category, each with its `description:` line from its `SKILL.md` frontmatter.
Intentionally short — serves as a TOC, not as documentation. The `SKILL.md`
itself remains the source of truth for each skill.

## Testing

No unit test framework. `test.sh` drives end-to-end smoke tests against an
ephemeral `$HOME`:

- Point `$HOME` at a fresh `/tmp/fake-claude-$$/`.
- Seed `$HOME/.claude/` so the pre-flight check passes.
- Run each of these and assert the resulting tree:
  - `./install.sh git` — all 10 skills land in `.claude/skills/`.
  - `./install.sh git-hooks` — only `git-hooks/` lands.
  - `./install.sh skill-creator` — the command file lands in
    `.claude/commands/skill-creator.md`.
  - `./install.sh --all` — skills + commands both populated.
  - `./install.sh --link git` — `.claude/skills/git-hooks` is a symlink
    pointing back into the repo's absolute path.
  - `./install.sh git` (second run, no `--force`) — skips all items.
  - `./install.sh --force git` — overwrites.
  - `./install.sh --dry-run git` — no filesystem writes; output lists
    planned actions.
  - `./install.sh doesnotexist` — exits 2, prints suggestion or "unknown
    target".

Each scenario is a bash function asserting expected paths via `[[ -d ... ]]` /
`[[ -L ... ]]` / `[[ -f ... ]]` and expected stdout via string match. The
script reports `ok:`/`fail:` per scenario and exits non-zero on any failure.

## Out of Scope

- Uninstall command (future work; `rm -rf` of specific paths is low-stakes
  enough that users can do it manually for now).
- A Makefile or package-manager wrapper. The shell script stays the single
  entry point.
- Windows support. Script targets mac/linux bash.
- Category metadata files (YAML manifest, etc.). Directory structure is the
  source of truth.
- Publishing to a plugin marketplace or Claude Code's plugin system. This
  repo is intentionally just "drop files into `~/.claude/`."

## Open Questions

None at spec time. Decisions locked with user:
- Layout: categorized repo, flat install target.
- Installer: single shell script.
- Copy default, `--link` opt-in.
- Default skip on conflict, `--force` opt-in.
- Script accepts both category names and individual skill/command names.
- Install script handles both skills and commands within a given target.
