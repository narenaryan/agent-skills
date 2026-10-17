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
./install.sh engineering         # install all engineering skills
./install.sh security            # install all security skills
./install.sh python              # install all python skills
./install.sh rust                # install all rust skills
./install.sh github              # install all github skills
./install.sh ui                  # install all UI skills
./install.sh conventional-commits # or just one skill
./install.sh minimal-sufficient-evidence # or just one skill
./install.sh container-image-patching     # or just one skill
./install.sh git-hooks           # or just one skill
./install.sh ui-form-design      # or just one skill
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
| [database](skills/database/)           | 1  | 0 | PostgreSQL locking joins, statement snapshots, and concurrency-safe reads |
| [marketing](skills/marketing/)         | 3  | 0 | Evidence-led positioning, causal campaign measurement, sample-ratio diagnostics, and cohort-aware funnel diagnosis |
| [engineering](skills/engineering/)       | 6  | 0 | Minimal evidence for tests, debugging, AI bug patterns, metrics, docs, root cause, macOS disk recovery, splitting large files into modules, bounded compressed NDJSON ingestion, and transactional outbox delivery |
| [security](skills/security/)           | 11 | 0 | Risk-based vulnerability evidence, triage, guarded remediation, IAM policy replay, governance, AI evaluation, security gates, container patching and DNSSEC diagnostics |
| [git](skills/git/)                     | 12 | 0 | Advanced Git and Sapling workflows: history, recovery, stacked PRs, and commit conventions |
| [github](skills/github/)               | 2  | 0 | GitHub operational workflows and npm publishing |
| [go](skills/go/)                       | 5  | 0 | Practical Go engineering patterns      |
| [python](skills/python/)               | 4  | 0 | Advanced Python runtime semantics and scaling regression tests |
| [sales](skills/sales/)                 | 4  | 0 | B2B qualification, buyer-owned decision plans, commercial negotiation, and pipeline probability calibration |
| [rust](skills/rust/)                   | 6  | 0 | Compile-time invariants, runtime safety, deterministic concurrency tests, regex contracts, actor delivery, and typed error identity |
| [ui](skills/ui/)                       | 3  | 0 | UI flows, navigation, forms, validation, scroll regions, and interaction patterns |
| [skill-creator](commands/skill-creator/) | 0  | 1 | Turn docs into concise global skills   |

## Engineering blog sources

[The source registry](sources/engineering-blogs.json) records 15 selected engineering blogs, Hacker News discovery links, feed verification status, editorial filters, and historical example articles. The examples establish source quality; they are not announcements of newly published content. Two examples link to the initial proposed skills.

Before converting another article, inspect existing skills and open pull requests for overlap, read the original source, and verify version-sensitive claims. Use the [skill-creator command](commands/skill-creator/skill-creator.md) with repository paths under `skills/`; publication through a pull request does not install skills locally.

## Security research sources

[The security research companion](sources/security-research.json) adds three vetted technical sources: Uber Engineering Security, Google Security, and GitHub Security Lab. Six historical articles establish quality; primary standards and schema references are listed separately. Use both registries, respect feed verification and index fallbacks, and deduplicate articles and techniques across them.

The [security collection](skills/security/README.md) follows the evidence-to-decision-to-remediation lifecycle. Its synthetic fixtures check decision contracts, not live infrastructure or model performance.

## Rust author sources

[The Rust research companion](sources/rust-research.json) distinguishes Andrew Gallant's and Alice Ryhl's technical blogs from David Tolnay's project documentation. Historical articles establish provenance; they are not new-publication alerts. Use the verified feed or documented index fallback and deduplicate against the other registries. This registry addition does not change any scheduled job.

The new Rust fixtures are source-reviewed examples with exact direct dependency pins. Their compiler/runtime validation remains unrun until an already-provisioned Rust environment is available; see each skill's provenance for limits.

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
