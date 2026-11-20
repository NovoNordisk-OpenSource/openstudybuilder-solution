# Fail loud — never substitute, never approximate

A guide that documents the wrong control ships and gets read. "Substituting the
closest analogue" is the natural failure of a helpful agent; these rules override it.

## Before every click

1. **Literal-label check.** The exact label from the source guide/plan must be in the
   current `browser_snapshot` (`osbFind` also throws on no match or ambiguity). If it is
   absent, **STOP** — no near match ("Add activity" is not "Add activity instance").
   If the live label differs from the source guide, record the difference; the
   draft uses the live UI wording and the summary flags the guide for correction.
2. **Name the gate.** A missing control is usually a prerequisite: wrong database
   (empty data), missing role/permission, a parent item not selected, the item is in
   the wrong status (e.g. **Approve** only on Draft), or a library not populated (see
   `import_sponsor_data/SYSTEM_CODELISTS.md`). Say which in the failure message.
3. **Duplicate-screenshot tripwire.** Two consecutive screenshots that are
   byte-identical mean the previous click was a no-op. Stop and report.

## Read-only by default — the app writes to a real database

NeoDash only reads. The main application **writes**. Unless the dev explicitly
approved a specific write flow in this run:

- **Open** forms and dialogs, fill nothing that persists, **never click** **SAVE**,
  **Approve**, **New version**, **Delete**, **Inactivate**, **Reactivate**,
  **CONTINUE** on the last step, or any confirm button of a destructive dialog.
  Close with **CANCEL** / the close icon and confirm the dialog is gone.
- Typing example values into form fields to show a filled form is fine ONLY if the
  form is cancelled afterwards, and the values are neutral placeholders (no real drug,
  study or person names).
- Check which backend the page talks to (`browser_network_requests` filter `/api` or
  `config.json`) before the first form open, and tell the dev if it is a shared
  database. A shared/preview database means read-only, no exceptions.
- If a write flow is approved, say in the draft summary which records were created
  so the dev can remove them.

## Stop conditions

- **Login / SSO page** → stop; the dev signs in (`app-navigation.md`). Never automate.
- **Blank page, spinner that never ends, `Network Error` toast** → API unreachable or
  CORS/config problem. Check `config.json` `API_BASE_URL`; stop and report.
- **Table shows "No data available"** where the guide implies data → wrong/empty
  database. Capture, flag low confidence, do not invent rows in the prose.
- **Expected button/tab is missing** → role/permission or status gate. Stop; do not
  document a different control.
- **Sensitive content still visible after masking** → redo; never ship (see
  `sensitive-info.md`).
- **Action the guide describes would write and was not approved** → document from
  the form alone and flag "not exercised".

## Failure message shape

> Expected control/label "<name>" not found on <url> (<page>) at step <n>.
> Most likely cause: <gate>. Stopping. Partial screenshots saved to
> documentation_portal/osb-app-docs/<slug>/assets/.

Also write `documentation_portal/osb-app-docs/<slug>-FAILED.md` (what was tried, where
it stopped) so the next run has context.

## Why non-negotiable

Halting before a redundant, wrong or **destructive** click is the rule working
preventively. A skipped screenshot costs minutes; a wrong guide or an accidental save
to a shared database costs far more.
