# Running the application locally for capture

Use when no deployed environment is signed in and reachable from Playwright (typical
reasons: SSO that needs a passkey/device the automation browser cannot use, an
internal certificate authority the automation browser does not trust). **The dev runs
these steps; the skill never edits `.env` files, never starts the API against a
database the dev has not named, and never switches authentication off by itself.**

## Choose the data first

| Option | When | Consequence |
|---|---|---|
| Local Neo4j seeded per the repo (`db/` → `import_standards/` → API → `import_sponsor_data/`, see `CLAUDE.md`) | **Preferred.** Disposable, demo data, no sensitive content | Writes are harmless; still default to read-only |
| A shared/preview database the dev has access to | Only if no seeded local DB exists | **Strictly read-only.** With authentication off the API writes a dummy user node on every request. Mask all names/IDs (`sensitive-info.md`) |

## Steps (dev runs them)

1. **API** — from `api/`: `uv sync --group dev`, copy `.env.example` to `.env` and set
   `NEO4J_DSN` (`bolt://user:password@host:port/<database>`; keep the **database name
   in the DSN path and `NEO4J_DATABASE` identical** — a DSN ending in the default
   `neo4j` database is the usual cause of an empty app). Then `uv run uvicorn clinical_mdr_api.main:app --host 127.0.0.1 --port 8000`.
2. **Authentication** — the local frontend is configured with `OAUTH_ENABLED: "0"`
   (`frontend/public/config.json`), so the API must run with `OAUTH_ENABLED=false` in
   `api/.env`, otherwise every request is rejected. This is the dev's decision. If
   the API terminal prints that it is bound to `0.0.0.0` with authentication disabled,
   restart it bound to `127.0.0.1` only (e.g. `uv run uvicorn clinical_mdr_api.main:app --host 127.0.0.1 --port 8000`),
   so nothing else on the network can reach an unauthenticated API. Never leave it
   running unattended.
3. **Frontend** — from `frontend/`: `npm install`, `npm run dev -- --port 5174 --strictPort`.
   Use `http://localhost:5174` for the skill's Local environment; if the port is occupied, resolve the conflict before continuing.
   `frontend/public/config.json` → `API_BASE_URL` must be `http://127.0.0.1:8000`.
4. **Check** — `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/system/information`
   returns 200 and the app shows data (not an endless skeleton) before capturing.

## Playwright MCP notes

- Two Playwright MCP tool families may exist (`mcp__playwright__*` and
  `mcp__plugin_playwright_playwright__*`). They behave differently for internal
  hosts: if one fails with a certificate error, try the other. `localhost` needs
  neither.
- Screenshot paths must be inside the working directory (use
  `documentation_portal/.playwright-mcp/` for scratch, the draft folder for output).
- `browser_run_code_unsafe` with `page.addScriptTag({ path: … })` is the quickest way to
  inject `templates/annotation-snippet.js` (a full navigation removes it again).

## After capture

Tell the dev to stop the API (and the frontend) and, if a shared database was used,
that the dummy user node may have been written. The `.env` holds credentials and is
git-ignored; do not paste it into drafts or the chat.
