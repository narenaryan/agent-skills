---
name: ui-scroll-regions
description: Use when building or debugging horizontally scrollable UI regions — timelines, Gantt/swimlane views, wide tables, frozen first columns, synced rulers/headers — or when scroll "doesn't work", the scrollbar is invisible, or panes drift out of sync.
---

# Scrollable Regions & Frozen Panes

The failure mode to design against: N separate scroll containers held together with JavaScript scroll-sync, each with its scrollbar hidden. It demos fine and ships broken — no visible affordance, sync jitter, and dead zones for wheel/touch input.

## Core rule: one native scroll container

Wrap everything that must pan together (ruler/header, all lanes/rows) in a **single** `overflow-x: auto` element. Freeze non-scrolling parts (actor/label column) either outside the container or inside it with `position: sticky; left: 0`.

| Instead of | Do |
|---|---|
| One scroll container per row + `onScroll` sync | One shared container wrapping all rows |
| Hidden scrollbars + separate 1px "scrollbar strip" | The container's own native scrollbar |
| JS guard flags (`isSyncing` + rAF release) to stop echo loops | No sync code at all |
| Separate grids for header/body that must align | Header and body as children of the same scrolled element |

Scroll-sync JS is a last resort (e.g. two independent virtualized panes). If forced: sync in `onScroll`, guard against echo, and know that programmatic `scrollLeft` fires scroll events before the next rAF — release guards in `requestAnimationFrame`, and accept that per-frame guards can swallow real user deltas (lag/desync under continuous scrolling).

## Scrollbar visibility is the affordance

- macOS/iOS use **overlay scrollbars**: invisible until scrolling starts. A region with no other overflow cue reads as "everything fits". Never rely on the scrollbar alone — clip content at the edge, add a fade/gradient, or show a count ("12 more →").
- `scrollbar-width: none` / `::-webkit-scrollbar { display: none }` on the only scrollable element removes the affordance entirely. Hide scrollbars only when an adjacent visible one scrolls the same content.
- A near-zero-height strip whose only job is "be the scrollbar" is invisible on overlay-scrollbar platforms. Don't build one; use the real container.
- `scrollbar-gutter: stable` reserves the gutter for the **vertical** (inline-end) scrollbar only — it does not help horizontal layouts.

## Sizing the scrolled track

- Give inner tracks `min-width`, not `width`: content stretches to fill wide viewports (bars/labels reach the right edge) and only overflows — and scrolls — when it genuinely exceeds the viewport. A fixed `width` floor (e.g. `max(840, n * 120)`) leaves dead space on wide screens and ignores the actual viewport.
- In CSS grid/flex ancestors, scroll containers need `min-width: 0` (grid/flex items default to `min-width: auto` and refuse to shrink, so overflow never triggers).
- Percent-positioned children with a minimum-width floor can escape the track: `left: 98%` + `min 1.5%` width ⇒ clipped sliver at the boundary. Clamp: `left = min(left, 100 - width)`.

## Input handling

- Desktop mice have no horizontal wheel: users need shift+wheel, trackpad, or a draggable scrollbar. If the region is central to the feature, a visible scrollbar is mandatory, not optional.
- `touch-action: pan-x` on a region blocks **vertical page scrolling** for touches starting there — acceptable for a short strip, hostile on a tall region.
- Test scroll empirically, not by inspection: assert `scrollWidth > clientWidth`, set `scrollLeft` and check content actually moved, dispatch a wheel event with `deltaX` and confirm the same. A container can look scrollable and be inert (e.g. `min-width: auto` trap above).
