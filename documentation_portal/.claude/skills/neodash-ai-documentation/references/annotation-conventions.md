# Annotation conventions

Capture TWO screenshots per call-out target:

- **Annotated** → `./neodash-docs/<report>/assets/annotated-<report>-<tab>-NN-<slug>.png`
  — referenced in the draft markdown. Shows a red box (and, when helpful, a red
  arrow + label) on the control the reader should interact with.
- **Clean** → `./neodash-docs/<report>/assets/<report>-<tab>-NN-<slug>.png`
  — sidecar. Kept for review and for re-rendering a no-overlay variant. Not
  linked from the markdown by default.

Annotated FIRST, clean SECOND — the target can move after a click, hover, or
scroll.

## When to annotate

- A control the reader must click or select (study/version selector, operator
  toggle, a tab, the Rows-per-page dropdown, a column menu).
- A specific area the surrounding prose calls out by letter, e.g. "(A)", "(B)".

## When NOT to annotate

- A whole-tab overview shot where the point is the layout, not one control.
- A pure result/observation shot (e.g. "the table now lists the studies").
- Anything showing real study data / PII — skip and flag it; redaction is out
  of scope for this MVP.

## Style (matches docs/public/images/user_guides/neodash_elements_overview.png)

- Red `#e01e28`. Box stroke 3px. Arrow 3px with a triangular head.
- Use a **box only** for a single obvious target.
- Add an **arrow + short label** when the target is small or crowded (the
  top-right toolbar icons, a column `⋮`), so the reader can't miss it.
- Use a **letter badge** only when one screenshot has several targets. Always
  **letters** (A, B, C, …), never digits — the published guides refer to call-outs
  as "(A)", "(B)", and a screenshot with digits forces the prose to switch scheme
  mid-report. Digits in a guide mean **ordered steps**, letters mean **places on
  the screenshot**; keeping the two apart is the whole point.
- Letter in reading order: left-to-right, top-to-bottom, as the cards are laid out.
- **Badge style is small red** — a filled `#e01e28` circle of radius 13 anchored on
  the box's top-left corner, white bold 14px Arial letter. This is the house style
  (Activity Library Dashboard, Audit Trail Report). Do **not** use the large blue
  circles found in the older CRF Library Versions and Laboratory Data Specification
  images — those predate the standard and are being migrated. `neodashAnnotate`
  already draws small red; do not override it.
- No translucent fills, no motion paths. Consistency beats cleverness.

## Mechanics (DOM/SVG injection, not Pillow)

Use the helper in `templates/annotation-snippet.js` via Playwright
`browser_evaluate`. It exposes:

```js
neodashAnnotate(targetOrSelector, { arrow?: "auto" | {x,y}, label?: string, mark?: "A" })
neodashAnnotateClear()
```

Per target:

1. `browser_evaluate(<contents of annotation-snippet.js>)` — idempotent inject.
2. `browser_evaluate(() => neodashAnnotate("<selector>", { arrow: "auto", label: "Select study" }))`
3. `browser_take_screenshot` → the **annotated** filename.
4. `browser_evaluate(() => neodashAnnotateClear())`
5. `browser_take_screenshot` → the **clean** filename.
6. Click/act and continue.

Resolve the selector from the page `browser_snapshot` (use the element's
accessible name / role) — the same target you are about to click.

**Match card titles EXACTLY, not by prefix.** NeoDash report cards are best
located by their visible title (the disabled "Report name…" input value), but
several titles share a common prefix — e.g. `Number of Activities and Instances`
is ALSO the start of `Number of Activities and Instances by Group and Subgroup`
and `… by Type and Subtype`. A `startsWith`/`includes`/`querySelector` substring
match returns the wrong (first) card, so one call-out silently lands on another
card and a box goes missing. Use exact string equality on the trimmed title.
When the live title carries a dynamic suffix (e.g. `Activity in Tabular Format
- Pulse Rate`), match the exact stable text up to the ` - ` separator — never an
ambiguous fragment. After annotating, sanity-check that every expected letter
(A, B, C, …) drew a box; a missing badge means a title collision.

## Out of scope (MVP)

Translucent highlights, click-trace overlays, callout legends with paragraphs,
PII blur, vision-model coordinate detection (Playwright already has the bounding
box).
