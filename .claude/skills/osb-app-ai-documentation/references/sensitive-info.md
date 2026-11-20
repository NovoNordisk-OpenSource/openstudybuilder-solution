# Covering sensitive information in screenshots

The guideline requires that screenshots cover employee names and roles, study numbers/IDs,
drug names, doses and the sponsor (company) logo. The OpenStudyBuilder product logo is never masked. NeoDash captures had no such step; the main
application always shows some of it (user menu, **Author** columns, study banner).

**Mask first, annotate second, clean third.** Masks are painted into the page as
opaque rectangles, so they appear in BOTH the annotated and the clean sidecar image.
Never take a screenshot, then mask afterwards.

## Per page, before the first screenshot

Inject `templates/annotation-snippet.js`, then run (adjust selectors from a
`browser_snapshot`; check each count):

```js
() => ({
  emails:  osbMaskMatching(/[\w.+-]+@[\w-]+\.[\w.-]+/),
  studyIds: osbMaskMatching(/\b[A-Z]{2,}[-_ ]?\d{3,}\b/),   // tune to the local ID pattern
  logo:    osbMask('img[src*="company_logo"]', { all: true }),   // sponsor logo ONLY
  user:    osbMask('[data-cy="topbar-user-name"]', { all: true }),
})
```

Rules:

- **Do not mask the OpenStudyBuilder logo** (`study_builder_homepage_logo.png`, top-left). Only the
  sponsor/company logo (`company_logo_*`, top-right) is covered. Never use a blanket
  `header img` selector — it hits both.
- **Log the counts.** A pattern that matches 0 where something is visible is a miss.
  Look at the screenshot, not just the numbers.
- Masks are lost on navigation and often on re-render (route change, dialog open,
  table paging). Re-apply before every screenshot.
- Table columns (**Author**, **Modified by**): mask the column cells with
  `osbMask('<td selector>', { all: true })` or by email pattern.
- `<input>` values and chips with names are not text nodes — mask them by selector.
- **Always review the final PNG visually** (Read tool). If anything sensitive is
  still readable, delete the image and redo it; do not ship it with a note.
- Masks take the colour of the background behind them (`fill: "auto"`, the default), so they
  blend in instead of showing as grey boxes. Do not use blur (reversible-looking, inconsistent).

### Gotchas learned on the Vue/Vuetify app

- **Dialogs dim the header.** Under a Vuetify dialog scrim the header is darker than its CSS
  colour, so `fill: "auto"` paints a visibly lighter box. Open the dialog, take a probe shot,
  read the dimmed header pixel (stdlib PNG reader) and pass it explicitly, e.g.
  `osbMask('img[src*="company_logo"]', { all: true, fill: 'rgb(11,22,53)' })`. The value
  depends on dialog size (small vs tall dialogs gave different scrims). Masks sit above the
  scrim, so clear and re-apply with the explicit fill after the dialog opens.
- **No header, no logo mask.** Full-screen wizards (Add activity instance) hide the app header;
  there is no logo to cover, so do not apply the logo mask there.
- **Scope text masks to the overlay.** With a dialog or wizard open, the table underneath is
  still in the DOM, so `osbMaskMatching(emailRegex)` over the body paints stray boxes. Pass
  `{ within: '.v-overlay--active' }` and log the count.
- **Hidden duplicates.** Vuetify keeps other tabs' content mounted. Queries such as
  `.v-btn-toggle`, `button:has(.mdi-plus)` or `.v-list-item` also return hidden elements
  (rect 0×0 at the top-left), and an annotation on one lands at (0,0). Filter by a non-zero
  bounding rect. Stale zero-height `tbody` rows can look like data but are not.

## When masking is not enough

Drug names inside long free text, or a whole table of real study data: prefer
switching to a demo dataset, or skip the screenshot and flag it in the draft
summary. Do not guess.
