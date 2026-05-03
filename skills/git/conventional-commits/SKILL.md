---
name: conventional-commits
description: Use when writing or validating Conventional Commits v1.0.0 messages — choosing between `!` and `BREAKING CHANGE:` footer, formatting git-trailer footers (Token-with-dashes vs `BREAKING CHANGE`), scope syntax, mapping types to SemVer bumps, prepending gender-neutral gitmoji-style icons (feat ⚡ / fix 🐛 / refactor ♻️ / docs 📝), or handling revert/multi-paragraph body rules
---

# Conventional Commits v1.0.0

Header grammar: `<type>[(scope)][!]: <description>`. Body and footers are separated by blank lines. Footers follow the git-trailer convention.

## Type → SemVer → Emoji

All emojis are **object-based and gender-neutral** — no person/profession glyphs that default to a specific presentation in most fonts.

| Type | SemVer bump | Emoji | Shortcode |
|------|-------------|-------|-----------|
| `feat` | MINOR | ⚡ | `:zap:` |
| `fix` | PATCH | 🐛 | `:bug:` |
| `refactor` | — | ♻️ | `:recycle:` |
| `docs` | — | 📝 | `:memo:` |
| `perf` | — | 🚀 | `:rocket:` |
| `test` | — | ✅ | `:white_check_mark:` |
| `build` | — | 📦 | `:package:` |
| `ci` | — | 🤖 | `:robot:` |
| `chore` | — | 🔧 | `:wrench:` |
| `style` | — | 🎨 | `:art:` |
| any with `!` / `BREAKING CHANGE:` | MAJOR | 💥 | `:boom:` |

**Emoji placement:** prepend before the type, then a single space — `⚡ feat(parser): add array support`. Don't replace the type with the emoji; tooling (semantic-release, commitlint) parses the textual type. Some teams prefer the `:zap:` shortcode form for plain-text terminals.

## Breaking changes — two mechanisms

| Mechanism | Form | Footer required? |
|-----------|------|------------------|
| Marker | `feat(api)!: drop v1 endpoints` | No — description carries the explanation |
| Footer | `BREAKING CHANGE: v1 endpoints removed` | Yes; can combine with `!` |

`BREAKING-CHANGE` (hyphen) is a synonym **only** as a footer token. The text `BREAKING CHANGE` MUST be uppercase; everything else is case-insensitive.

## Footer format (git-trailer rules)

```
<Token>: <value>          # standard
<Token> #<value>          # issue-ref form, e.g. Refs #133
```

- Token MUST replace whitespace with `-`: `Reviewed-by`, `Acked-by`, `Signed-off-by`. The lone exception is `BREAKING CHANGE` (space allowed).
- Footer values may span newlines; parsing terminates at the next valid `Token: ` or `Token #` pair.
- Footers begin one blank line after the body.

## Examples

```
⚡ feat(parser): add ability to parse arrays

🐛 fix: prevent racing of requests

Introduce a request id and a reference to latest request.

Reviewed-by: Z
Refs: #123
```

```
💥 chore!: drop Node 6 from CI

BREAKING CHANGE: dropping Node 6 which hits end of life in April
```

```
revert: let us never again speak of the noodle incident

Refs: 676104e, a215868
```

## Pitfalls

- Forgetting the **space after the colon** in the header — `feat:add x` is invalid.
- Writing a footer token with a space (`Reviewed by:`) — only `BREAKING CHANGE` may contain a space; everything else needs `-`.
- Using lowercase `breaking change:` — the token MUST be uppercase, unlike the rest of the spec which is case-insensitive.
- Putting `BREAKING CHANGE` in the body instead of the footer block — tools that parse trailers (and SemVer release tooling) will miss it; the MAJOR bump won't trigger.
- Assuming `!` alone bumps MAJOR but skipping a description that explains the break — when `!` is used without a `BREAKING CHANGE:` footer, the **description** is the break explanation, so it must be self-contained.
- Replacing the textual type with an emoji (`⚡(parser): ...`) — commitlint/semantic-release won't recognize it; always keep `feat`/`fix`/etc. after the emoji.
- Avoid person/profession emoji (👷, 👨‍💻, 💄) for type icons — they default to a specific gender presentation in most fonts and exclude readers; prefer object glyphs (🤖, 🔧, 🎨).
- Multi-codepoint emoji (♻️ uses VS-16, ZWJ sequences) can confuse regex-based hooks counting characters; prefer the `:shortcode:` form if your toolchain is byte-fragile.
- Scope must be a noun in parens (`fix(parser):`), not a verb or sentence; pick one scope or omit.
- `revert` is conventional, not specified — agree on a project convention (most tools expect `revert: <subject>` + `Refs:` footer with reverted SHAs).
