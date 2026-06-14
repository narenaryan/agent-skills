---
name: ui-form-design
description: Use when designing or reviewing forms and inputs — text fields, dropdowns/selects, password fields, autocomplete, defaults/pre-fills, or form-level validation and error messaging.
---

# Form Design

Forms are where users do the most work for the least reward — every field, choice, and error message either reduces or adds to that cost.

## Input field choices

| Input type | Guidance |
|---|---|
| Text field | Use a **hint** (placeholder-style example/format) inside or below the field instead of relying only on an external label, when space is tight |
| Dropdown (limited, known options) | Prefer **select** over free text — eliminates invalid input and typos |
| Dropdown (large or fuzzy option set) | Use **type-or-enter** (combobox) so users can filter by typing |
| Free text | Only when choices are unbounded or not enumerable |

**Rule of thumb**: if the valid values are a finite, enumerable set, use a select/dropdown — don't make users type something you could've offered as a choice.

## Defaults and pre-fills

- Pick the **most common** value as the default, not a neutral/empty one — most users should be able to accept defaults and move on.
- Pre-fill from known context (previous entries, account info, geolocation) but make it visibly editable.
- Minimize total field count: every field is a decision point and a place to fail validation. Combine fields where possible (e.g. single "full name" vs. first/last when no real need to split).

## Autocomplete

Use autocomplete/typeahead on any search or lookup field to cut typing and reduce zero-result searches. Show enough of each suggestion (icon, secondary text) to disambiguate similar matches.

## Rich preview dropdowns

For settings that visibly change the UI (themes, fonts, layouts), use a dropdown/chooser that **previews the result before applying** — don't make users apply-and-check repeatedly.

## Password fields

- Show password **policy as a checklist** below the field: each requirement gets a checkmark (met) or cross/neutral icon (unmet), updating live as the user types.
- Add a **strength meter** alongside the checklist: red/short for weak, green/full for strong. The checklist tells *what's* wrong; the meter gives an at-a-glance summary.

## Errors and validation

- Show a **summary of errors at the top of the form** — don't rely on users scrolling to find inline messages.
- Additionally **mark each offending field** (border color, icon, inline message) so the summary and the field are both discoverable.
- Validate as early as is useful (on blur for format errors) but don't error on a field the user hasn't finished typing into yet.

## Pitfalls

- Free-text fields for things like "Country" or "State" — typos and inconsistent casing break downstream filtering/search.
- Defaulting to blank/"Select one" when one option is overwhelmingly common — adds a click for nearly everyone.
- Showing only a strength meter without the checklist — users don't know *which* rule they're failing.
- Listing errors only inline, scattered through a long form — users miss how many things are wrong and where.
