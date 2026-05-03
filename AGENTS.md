# AGENTS.md

## Purpose

This repository stores reusable agent skills. When working in this repo, prefer the skill definitions in `skills/` as the source of truth for workflow-specific guidance.

## Git Skill Policy

For any Git-related task in this repository, load and follow the relevant skill under `skills/git/` before making changes.

Examples:

- Commit message creation or review: `skills/git/conventional-commits/SKILL.md`
- History rewriting: `skills/git/git-rewriting-history/SKILL.md`
- Reset, restore, or undo flows: `skills/git/git-reset-mechanics/SKILL.md`
- Merge conflict resolution: `skills/git/git-advanced-merging/SKILL.md`
- Lost commit or branch recovery: `skills/git/git-data-recovery/SKILL.md`

## Commit Messages

When creating or rewriting commit messages for this repository, follow `skills/git/conventional-commits/SKILL.md`.

Current repository convention:

- Use Conventional Commits header syntax.
- Prefix the textual type with the mapped emoji from the skill.
- Keep the textual type present for tooling compatibility.

Example:

`⚡ feat(scope): add example`
