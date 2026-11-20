# Annotation conventions (OSB application)

Same visual house style as the NeoDash guides, so both kinds of guide look alike.
Mechanics: `templates/annotation-snippet.js` (`osbAnnotate`, `osbFind`, masks).

## Files per target

- **Annotated** → `documentation_portal/osb-app-docs/<slug>/assets/annotated-<slug>-NN-<step>.png`
  — referenced in the draft. Red box, plus arrow + label when the target is small.
- **Clean** → `documentation_portal/osb-app-docs/<slug>/assets/<slug>-NN-<step>.png`
  — sidecar for review / re-rendering. Both are masked (sensitive info covered).

Order: **mask → annotated → clear annotations → clean → act**. The target can move
after a click, so the annotated shot always comes first.

## Style

- Red `#e01e28`, box stroke 3px, arrow 3px with triangular head, white label chip with
  red 2px border and bold red 15px Arial text.
- **Letter badges** (A, B, C…) only when one screenshot has several targets; letters
  in reading order (left→right, top→bottom). Never digits — digits are ordered
  steps in the prose, letters are places on the screenshot. Badge: filled red circle,
  radius 13, on the box's top-left corner, white bold 14px letter.
- Box only for one obvious target; add arrow + short label for small or crowded
  targets (icon buttons, row action menus, filter chips).
- Label wording = the UI wording ("Add activity"), not a paraphrase.
- No translucent fills, no click traces, no blur. Consistency beats cleverness.

## When to annotate

- A control the reader must click, select or fill (**Add activity** icon, a mandatory
  field, a dropdown, **SAVE**).
- An area the prose calls out as "(A)", "(B)".

## When not to annotate

- A pure overview shot where the point is the layout (a whole page or tab).
- A result shot ("the table now lists…").

## Matching targets exactly

Never box by substring. `osbFind('Activities')` matches only a control whose whole
text is `Activities`, not `Activity Instances`; it throws on zero or multiple
matches. For fields, find by the visible label inside the form dialog:
`osbFind('Activity name', { within: '.v-dialog' })`, or use a selector taken from
`browser_snapshot`. After annotating, check every expected letter drew a box
(a missing badge means the selector hit another element) by looking at the image.

Icon-only buttons (table header, row menu) have no text for `osbFind`: hover for the
tooltip wording, then pass the element itself (see `app-navigation.md`).

## Manual path (no browser)

When screenshots are supplied by hand, draw the same boxes with
`.claude/skills/osb-neodash-ai-documentation/templates/annotate-manual.py` (JSON spec
of pixel boxes; identical style). Mask sensitive areas by adding filled rectangles
with Pillow or by re-taking the shot.
