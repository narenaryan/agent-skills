# agent-skills

A curated list of skills & commands which stays low on tokens. Each skill is distilled to the non-obvious knowledge — what a senior engineer would want surfaced, not what a reference manual would say — so Claude spends its context budget on your problem, not on rehashing fundamentals.

> Your agent already knows basic things, let's make it more senior.

## Quick start

Install skills quickly via NPX:

```bash
npx skills add narenaryan/agent-skills -y
```

Or install specific skills:

```bash
git clone https://github.com/N3N/agent-skills.git
cd agent-skills
./install.sh git                 # install all git skills
./install.sh python              # install all python skills
./install.sh github              # install all github skills
./install.sh git-hooks           # or just one skill
./install.sh --all               # or everything
```

Installed items land under `~/.claude/skills/` and `~/.claude/commands/`, where Claude Code discovers them.

## Agent install

Copy this into an agent chat to install these skills:

```markdown
Install skills from this Git repository:
https://github.com/narenaryan/agent-skills
```

## Categories

| Category        | Skills | Commands | Description                            |
|-----------------|--------|----------|----------------------------------------|
| [git](skills/git/)                     | 10 | 0 | Advanced git workflows                 |
| [github](skills/github/)               | 1  | 0 | GitHub operational workflows           |
| [go](skills/go/)                       | 5  | 0 | Practical Go engineering patterns      |
| [python](skills/python/)               | 3  | 0 | Advanced Python runtime semantics      |
| [skill-creator](commands/skill-creator/) | 0  | 1 | Turn docs into concise global skills   |

## Installer options

```
./install.sh [options] <target>...

Targets:
  <category>   Install all skills+commands in that category (e.g. git)
  <name>       Install a single skill or command by name (e.g. git-hooks)
  --all        Install everything

Options:
  --link       Symlink instead of copy — edits in this repo flow to ~/.claude/
  --force      Overwrite existing items
  --dry-run    Print planned actions, don't touch filesystem
  -h, --help   Show usage
```

Default is copy; use `--link` if you're contributing or want `git pull` on this repo to update your installed skills. Second run without `--force` skips anything already installed.

## Contributing

1. Add a skill under `skills/<category>/<skill-name>/SKILL.md` with `name` and `description` frontmatter.
2. Add the skill to the category's `README.md`.
3. Run `./test.sh` to make sure the installer still works.

Skills should be 300–500 words. If you need more, you probably need to split the skill.
