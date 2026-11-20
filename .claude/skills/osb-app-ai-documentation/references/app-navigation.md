# OpenStudyBuilder application — navigation notes for capture

The frontend is a Vue 3 + Vuetify 4 single-page app. Routes and menu structure are
defined in `frontend/src/router/` and `frontend/src/` (check there before guessing
a label); the labels visible in the running app are authoritative for the guide.

## Environments

| Environment | URL | Notes |
|---|---|---|
| Local frontend | `http://localhost:5174` (Vite; 5173 may be taken, check the terminal) | Needs a reachable API. `frontend/public/config.json` sets `API_BASE_URL` (typically `http://127.0.0.1:8000`) and `OAUTH_ENABLED` |
| Deployed | exact URL from the dev | Requires login — see below |

Do not confuse the app with the VitePress documentation site (often on `:5173`, base
path `/doc/`) — if the page is a docs page, the port is wrong.

## Authentication — never automated, never bypassed

- If the app shows a login / SSO page, **stop** and ask the dev to sign in in the
  Playwright browser, or to use a local frontend + API setup they have already
  prepared. Do not click through SSO, do not enter credentials, do not try to switch
  authentication off, and do not suggest ways of working around it.
- A local API with `OAUTH_ENABLED=false` is the dev's choice and the dev's job to
  start (bind to `127.0.0.1`). It may point at a shared database: such a setup writes
  a dummy user on every request. Treat it as **read-only** (see `fail-loud.md`).
- Playwright MCP tool families differ in what they can reach (one may reject an
  internal certificate authority). If navigation fails with a certificate error, report
  it and try the other family only if the dev has not objected; never set
  `ignoreHTTPSErrors`.

## Layout vocabulary (use these names in the draft; verify against the live UI)

- **Top bar** — OpenStudyBuilder logo (never masked), company logo, current study banner, user menu (company logo, banner and menu are sensitive
  info: mask).
- **Left navigation** — top-level areas such as **Library**, **Studies**,
  **Administration**; items nest (**Library** → **Concepts** → **Activities**).
- **Page tabs** — e.g. **Activities**, **Activity Groups**, **Activity Subgroups**, **Activities by Grouping**,
  **Activity Instances**, **Requested Activities**, **Activity Instance Classes**,
  **Activity Item Classes**; sibling labels share prefixes, so match exactly.
- **Data table** — search box, filter chips, column picker, rows-per-page, row action
  menu (three-dot icon), round icon buttons in the table header (add, filter, column
  picker, download, history).
- **Form dialog / stepper** — fields with asterisks are mandatory; action buttons at
  the bottom (**CANCEL**, **SAVE**, **CONTINUE**/**NEXT**).
- **Overview page** — reached by clicking a row's name; shows definition, status,
  version, history.

## Status and versioning words

Draft / Final / Retired, version numbers (0.1, 1.0), and actions **Approve**,
**New version**, **Inactivate**, **Reactivate**, **Delete**. Document what the UI
shows; never explain behaviour from the backend that the UI does not expose.

## Waiting and stability

- After a click, `browser_wait_for` the next expected text (a dialog title, a tab
  name) rather than sleeping.
- Tables render rows asynchronously — wait for a row or the "No data available" text.
- Vuetify menus and dialogs animate for ~300 ms: wait for the final text before
  injecting masks/annotations, otherwise boxes land on moving elements.
- Prefer **viewport** screenshots when a dialog or menu is open (fixed positioning).
  Use `fullPage` only for plain pages and long overview pages.

## Icon-only buttons have no accessible name

The table-header buttons (add, filter, columns, download, history) and the row action
menu carry no text, `aria-label` or `title`, so `osbFind('Add activity')` cannot find
them and `browser_snapshot` lists them as unnamed buttons. To locate one: hover it
(`browser_hover`) and read the tooltip text — that tooltip is the UI wording to use in
the guide ("Add activity") — then select it by its stable `data-cy` hook and pass the
element to `osbAnnotate`: `add-activity`, `filters-button`, `columns-layout-button`,
`table-export-button`, `table-item-action-button` (grep `frontend/src` for others).
Always use `[data-cy="…"] >> visible=true`. **Tabs on a page stay mounted** (kept
alive) after a switch, so positional selectors such as `.v-main .v-btn--icon` can hit
a hidden button from another tab and time out. Record the tooltip text, not the icon
name.

## Feature flags

Some forms are gated by feature flags served by the API (`/feature-flags`, read by the
frontend store `stores/feature-flags.js`). With a flag off, the button opens a
"Feature is disabled" dialog, or the tab is missing (e.g. `nsvs_library` for
**Non-Standard Variables**, `new_activity_instance_wizard_stepper` for **Add activity
instance**). A database without flags returns `[]`. That is a gate, not a UI bug: name
it, stop for that target, and let the dev decide how to enable it (flags are stored in
the database, so enabling one on a shared database is a write).
