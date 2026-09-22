# NeoDash navigation (for Playwright)

How to get from a fresh browser to a captured tab. Use element accessible
names from `browser_snapshot` to resolve targets; don't hard-code CSS unless
nothing else works.

## Environments

- **Local (Docker)** — `http://localhost:5005/`. NeoDash runs as a Docker image
  talking to a local Neo4j at `bolt://127.0.0.1:7687`. If it doesn't respond,
  start it with `docker compose up -d` (the NeoDash docker stack), then re-run.
- **Deployed** — the sponsor's neodash URL (e.g. `…/neodash/`). SSO applies.

## Connect (interactive — the user does this)

NeoDash does **not** auto-connect. After `browser_navigate`:

- **Local:** the connection is **remembered**, so the user just clicks
  **Connect** in the dialog (`bolt://127.0.0.1:7687`).
- **Deployed:** the user completes SSO.

Then `browser_wait_for` until the **Report navigation panel** (left drawer,
titled "Dashboards") with the report list is visible. Do not proceed until a
report list is on screen. Auth is never automated.

## Capture in reader mode

End-user guides must show what a reader sees. In reader mode these are hidden:
report-title rename pencil, card drag handle, add-page `+`, per-card edit menu;
the header toolbar collapses to just the settings gear. If you see those
editor-only controls, you're in editor mode — switch before capturing (see
fail-loud.md).

## Open a report and walk its tabs

1. In the **Report navigation panel**, click the report by its exact name
   (e.g. "Activity Library Dashboard"). Confirm the **Report title** matches.
2. The views are **Page tabs** across the top (ReadMe first). Click a tab to
   switch; `browser_wait_for` the cards to finish loading before screenshotting.
3. Content lives in **report cards** (white panels). A table card has a
   **Rows per page** dropdown (default 5) + pagination, and a column **⋮** menu
   (Sort ASC/DESC, Filter, Hide column, Manage columns); a card can be
   **Maximized** and **Refreshed** from its top-right icons; tables can be
   downloaded via the cloud-download icon. See the README "General features" and
   "NeoDash interface elements" sections for the canonical names to use in prose.

## Element-naming for prose

Use the repo's established names (from `docs/guides/userguide/reports/README.md`):
Report navigation panel, Page tabs, Report card, Maximize button, Refresh button,
Report settings, Rows per page. Keep the source guide's lettered (A)(B)…
call-outs aligned with the matching annotated screenshot.
