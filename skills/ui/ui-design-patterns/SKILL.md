---
name: ui-design-patterns
description: Use when designing or reviewing a UI/UX flow — choosing navigation structure, organizing content/menus, deciding which controls to surface first, adding a wizard/settings page/help system, structuring multi-step or parallel tasks, or picking page transitions/animations.
---

# UI Design Patterns

Good design is invisible: the user accomplishes the goal without noticing the interface. Every choice below should reduce friction, not add decoration.

## Core interaction principles

| Principle | Application |
|---|---|
| Keyboard parity | Every mouse-accessible action needs a keyboard path (tab order, shortcuts, focus rings) |
| Streamline repetition | Batch repeated actions (Find & Replace All, bulk edit, multi-select actions) |
| Spatial/prospective memory | Keep item positions and "things to do later" stable across sessions (don't reflow menus, keep a persistent "later" list/badge) |
| Habituated behaviors | Reuse platform conventions (Ctrl+C/X/V, swipe-to-delete) — don't remap without strong reason |
| Incremental gratification | Show partial results/progress immediately, don't make users wait for a final reveal |
| Surface immediate-need controls | The control matching the user's most likely first action should be visually dominant on landing |
| Defer deferrable choices | Push optional config (sleep timer, advanced settings) to a secondary screen so the primary path stays short |
| Incremental construction | Let users build up a result step by step with visible intermediate state (playlist building, query builders) |
| Frequent items visible | Promote most-used items into primary view; bury rare ones in overflow/"more" |

## Organizing content

Pick one primary scheme, offer a secondary as a filter/sort: **Alphabetical, Numerical, Time, Location, Hierarchy, Category, Facet**.

## Site/app archetypes

| Type | Examples | Core features |
|---|---|---|
| Content-centric | blogs, docs, news | Feature (editorial picks), Search, Browse |
| Commerce-centric | storefronts | Feature (promotions), Search, Browse |
| Task-centric | dashboards, tools, forms | Goal completion flows (wizards, editors) |

## Navigation models

| Model | Shape | Use when |
|---|---|---|
| Hub & Spoke | One home, many leaves, back-to-hub | Simple apps, mobile, single-purpose tools |
| Fully connected | Everything links to everything | Small sites, utility nav |
| Multilevel (tree) | Hierarchical drill-down | Large catalogs, docs, file systems |
| Step-by-step | Linear sequence | Checkout, onboarding, wizards |
| Pyramid scheme | Step-by-step with an integration/overview point | Multi-part setup that ends in a combined review screen |

**Navigation cost**: every jump between views has a cost. Keep distances short — put high-frequency destinations in global nav, and merge adjacent steps into one screen using **module tabs** or **accordions** rather than separate pages.

## UI structure patterns

| Pattern | When to use |
|---|---|
| Clear entry points | Landing/home should make 2-3 primary actions obvious |
| Menu page | Index of sections when no single page dominates |
| Pyramid | Drill-in then summarize (see navigation models) |
| Modal panel | Focused sub-task that blocks the main flow until resolved |
| Deep links | Direct URLs into nested states (shareable, bookmarkable) |
| Escape hatch | Always-available "cancel/home" so users feel safe exploring |
| Fat menus | Mega-menus that expose hierarchy instead of hiding it |
| Sitemap footer | Catch-all for SEO and users who scroll to bottom for structure |
| Sign-in tools | Persistent, small, top-right; don't block content for guests |
| Progress indicator | Multi-step flows — show step N of M, not just a spinner |
| Breadcrumbs | Deep hierarchies — show path back to root |
| Annotated scrollbar | Long lists/timelines where position has meaning (e.g. media seek bar with chapter marks) |

## Wizards and settings pages

- **Wizard**: chunk a big task into steps with Back/Next/Cancel/Finish. For short side-tasks, a single modal with Ok/Cancel/Properties is enough — don't wizard-ify a 2-field form.
- **Settings page**: desktop — three columns (setting name, current value, Edit button opening a modal). Mobile — row with setting name + `>` chevron drilling into an edit screen.

## Multiple views and workspaces

- **Alternative views**: same data, different lens (table vs. calendar vs. kanban) — let users switch, don't force one.
- **Multiple workspaces**: tabs, split screens, separate windows for genuinely parallel tasks — don't force serial navigation for work that's conceptually parallel.

## Help systems

Layer help by intent: **inline hints/tooltips** (in-context, low friction) → **guided tour** (lightbox + instructional panel highlighting one element at a time, for first-run) → **full help docs** → **community/forum** for edge cases. Don't default to a full help doc for a one-line affordance question.

## Animated transitions

| Transition | Use for |
|---|---|
| Brighten/dim | Focus shift, modal open/close backdrop |
| Expand/collapse | Accordions, tree nodes, disclosure widgets |
| Fade in/out, cross-fade | Content swap without spatial relationship |
| Slide | Spatial relationship between views (next/prev, drawer) |
| Spotlight | Drawing attention to one element (tours, onboarding) |

**Pitfall**: stacking multiple transition types on one interaction (slide + fade + scale) reads as motion sickness, not polish. Pick one.

## Visual hierarchy & gestalt

Visual hierarchy communicates: what's most important, how things relate, what to do next. Build it with **size, color, background, position, density, rhythm** — not just font-weight.

Four gestalt principles to lean on:
- **Proximity** — items close together are read as related
- **Similarity** — same style implies same function/category
- **Continuity** — aligned edges/lines imply a sequence or group
- **Closure** — partial shapes get mentally completed (use sparingly, can hide affordances)

## Pitfalls

- Adding a wizard to a task that's actually a single short form — adds clicks without reducing cognitive load.
- Choosing "fully connected" nav for a large site — link count explodes and users lose the hierarchy.
- Using closure/overlap effects on interactive elements — users may not perceive them as clickable.
