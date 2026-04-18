---
description: Convert a documentation URL into one or more concise global skills covering only advanced / non-obvious knowledge
argument-hint: <url> [scope-hint]
allowed-tools: Bash, Write, Read, Glob, Grep, WebFetch, AskUserQuestion, TaskCreate, TaskUpdate
---

# skill-creator

Input: `$ARGUMENTS` — a URL (optionally followed by a scope hint like "merging, rebase" or "only reset & bisect").

Goal: turn the resource into specialized global skills in `~/.claude/skills/` that empower future agents to reach for **advanced constructs** instead of chaining simple mechanisms, and that avoid re-documenting widely-known basics.

## The filter (most important rule)

For every candidate piece of content, ask: **"Would a competent practitioner already know this without consulting docs?"** If yes, drop it. Keep only:

- **Mental models** that explain why commands behave as they do (e.g. three-trees, promise microtask queue, page cache lifecycle).
- **Non-default flags** and their exact effect (`-X patience`, `--ignore-rev`, `--force-with-lease`, `--prune=now`).
- **Sharp edges / pitfalls** the docs bury in a warning paragraph.
- **Operator / syntax distinctions** people conflate (`^` vs `~`, `..` vs `...`, `-S` vs `-G`).
- **Recovery / undo** paths.
- **Under-the-hood** details that change how you'd reason (storage layout, ordering guarantees, race conditions).
- **Advanced constructs that replace chained simple ones** — this is the core motivation. Surface them explicitly so future agents don't reinvent the chain.

Drop: definitions, hello-world, "what is X", install steps, marketing text, anything obvious from the command name.

## Workflow

1. **Fetch the entry URL** with WebFetch. Ask for: table of contents and which sub-pages cover advanced topics. If the page itself is the content, skip to step 3.

2. **Scope with the user** via `AskUserQuestion` if multiple coherent skill areas exist. Two questions max:
   - which topic groups to cover (multiSelect, ≤4 options)
   - depth (concise <300 words / standard ~500 / deep ~1000+) — default: concise
   Skip this step if the user's scope hint already disambiguates or only one topic exists.

3. **Fetch sub-pages in parallel** (one WebFetch per chapter). In each prompt:
   - Name the specific advanced items to extract.
   - Explicitly say "skip basics, definitions, hello-world."
   - Request tables, exact commands, pitfalls.

4. **Plan skills** — one skill per coherent topic. Create a TaskCreate entry for each. Naming: `<domain>-<topic>` with active/descriptive nouns (`git-advanced-merging`, `postgres-explain-analyze`, `k8s-pod-lifecycle`). Lowercase, hyphens only.

5. **Write each skill** to `~/.claude/skills/<name>/SKILL.md` using the template below. Batch independent Write calls in one message.

6. **Verify word counts**: `for d in ~/.claude/skills/<new-skills>; do wc -w "$d/SKILL.md"; done`. If concise depth was chosen and any skill exceeds target by >30%, trim prose (keep tables and commands).

7. **Report**: list skill names, word counts, and the rationale for any skill that runs long (dense reference tables).

## Skill file template

```markdown
---
name: <lowercase-hyphen-name>
description: Use when <specific triggering conditions and symptoms — NOT a summary of what the skill does>
---

# <Title>

<1–2 sentence mental model or core invariant. Skip if trivially obvious from the name.>

## <Quick-reference section — table preferred>

| <axis> | <effect> | <notes> |

## <Patterns / recipes>

```bash
<exact command>     # <why / when>
```

## Pitfalls

- <sharp edge with concrete consequence>
- <second sharp edge>
```

### Frontmatter rules

- `description` MUST start with "Use when..." and describe triggering conditions, **not** workflow. A description that summarizes the skill's steps causes future Claude to follow the description and skip the body.
- Keep description under 500 chars. Include concrete symptoms/keywords future Claude would search for.
- `name` matches the directory name exactly.

### Content rules

- Lead with the mental model if one exists; otherwise jump to the table.
- Prefer tables over prose for reference material.
- Every command block must be copy-pasteable (exact flags, real paths — not `<placeholder>` when a real example fits).
- Every skill ends with a **Pitfalls** section. If you can't think of three real pitfalls, the topic may not be advanced enough to warrant a skill.
- No narrative ("in this guide we will..."). No marketing. No restatement of what the tool is.
- No emojis.

## Word budgets

| Depth | Target | Hard max |
|-------|--------|----------|
| concise | ~300 | 400 (only if table-heavy reference) |
| standard | ~500 | 650 |
| deep | ~1000 | 1500 |

`wc -w` counts tokens inside tables and code, so dense reference skills naturally run higher than their prose length suggests. Trim prose first; keep commands.

## When NOT to create a skill

- The resource is only basics — tell the user, don't fabricate advanced content.
- The topic is already covered by an existing skill in `~/.claude/skills/` — update that file instead of creating a duplicate. Check with `ls ~/.claude/skills/` before writing.
- The content is project-specific (belongs in CLAUDE.md, not a global skill).
- The "advanced" construct is enforceable with tooling (linter, formatter) — automate it, don't document it.

## Authentication / fetch failures

If WebFetch returns an auth wall or paywall, stop and tell the user which pages are blocked. Don't fabricate content from the URL slug.

## Final report format

```
Created N skills in ~/.claude/skills/:
  - <name>  (<words>w)  — <one-line topic>
  ...

Skipped: <topics that turned out to be basics or already covered>
Source: <url>
```
