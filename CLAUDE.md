# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

OpenStudyBuilder / Clinical-MDR — clinical trial metadata management for pharma research. Monorepo of independently-built components sharing one Neo4j graph database as the integration point.

## Nested instructions — read these first

Two components carry their own detailed rule sets. When working in either, read the rule files, not just the index:

- `api/CLAUDE.md` → `api/.claude/rules/*.md` (project-overview, project-structure, commands, architecture, database, api-conventions, code-standards, authentication, testing, monitoring)
- `frontend/CLAUDE.md` → `frontend/.claude/rules/*.md` (overview, commands, architecture-core, components, patterns, routing-auth, conventions-gotchas)

## Components

| Dir | Purpose | Stack |
|-----|---------|-------|
| `api/` | REST API — three FastAPI apps off one codebase | Python 3.14, FastAPI, neomodel/Neo4j |
| `frontend/` | OpenStudyBuilder web UI | Vue 3, Vite, Vuetify 4, Pinia, **npm** |
| `db/` | Neo4j schema init, NeoDash reports | Docker, Python |
| `db_schema_migration/` | Numbered schema migrations + data corrections | Python |
| `import_standards/` | CDISC controlled terminology + data models import | Python |
| `import_sponsor_data/` | Sponsor codelists and mock data (via API) | Python |
| `export/` | Study export | Python |
| `verifications/` | Data-quality checks against a live DB/API | pytest-bdd |
| `system_tests/` | End-to-end UI tests | Cypress |
| `load_tests/` | Load tests | Locust |
| `documentation_portal/` | Docs site | VitePress |
| `_tools/build_sbom.py` | Shared SBOM generator every component's `build-sbom` script calls | Python |

### The three API apps

One codebase, three ASGI apps, shared `common/` (config, auth, database, telemetry, exceptions). Each has its own port, `openapi.json`, tests, and lint target:

| App | Port | Pipfile scripts |
|-----|------|-----------------|
| `clinical_mdr_api/` (main) | 8000 | `dev`, `lint`, `testunit`, `testint`, `openapi` |
| `consumer_api/` (read-only) | 8008 | `consumer-api-*`, `consumer-openapi` |
| `extensions/` | 8009 | `extensions-*`, `extensions-openapi` |

The main API follows three-layer DDD — `domains/` (business logic, no outward deps) → `domain_repositories/` (Neo4j persistence, Memento pattern, optimistic locking) → `routers/`+`services/`+`models/`. Build features inside-out in that order; see `api/.claude/rules/architecture.md`.

## Commands

Every Python component is pipenv with its own `[scripts]` block in its `Pipfile` — **check there rather than guessing**; scripts differ per component and some are pinned to a version number (see migrations below).

```bash
# api
cd api && pipenv sync --dev
pipenv run dev                                  # :8000
pipenv run testunit                             # unit
pipenv run testint                              # integration — needs Neo4j, runs xdist parallel
pipenv run testauth                             # OAuth/RBAC
pipenv run test -- path/to/test.py::test_name   # single test (plain pytest -s)
pipenv run format && pipenv run lint && pipenv run mypy
pipenv run sblint                               # custom in-repo static analysis (sblint/)
pipenv run openapi                              # regenerate openapi.json after route/model changes
pipenv run schemathesis                         # contract tests against a running :8000

# frontend (npm)
cd frontend && npm install
npm run dev                                     # vite default :5173
npm run lint && npm run format
npm run test:smoke                              # builds demo bundle, then Playwright
npx playwright test --config tests/smoke/playwright.config.js -g "name"   # single smoke test

# db
cd db && ./create_neo4j_local.sh && pipenv run init_neo4j
```

`db_schema_migration` scripts are **pinned per migration number** — `test`/`verify`/`migrate` all point at `*_024` today, corrections at `*_022`. Bump those Pipfile entries when starting a new migration.

## Database population order

Order matters — each step depends on the previous:

1. `db/` — init schema
2. `import_standards/` — CDISC controlled terminology
3. `api/` — start API
4. `import_sponsor_data/` — sponsor codelists + mock data (goes through the API, not straight to Neo4j)

## Environment

Each component reads its own `.env` — copy from its `.env.example` (`api/`, `db_schema_migration/`, `frontend/`, `verifications/` ship one; `db/` documents its variables in `db/README.md`). The API is driven by `NEO4J_DSN`; `db/` and the compose files use the split `NEO4J_MDR_*` variables, and the two must agree on host/port/credentials.

Bolt port differs by setup: 7687 for Neo4j Desktop, 5078 for the repo's Docker container (`db/README.md`). OAuth is off by default locally; enable with `OAUTH_ENABLED`, `OAUTH_METADATA_URL`, `OAUTH_API_APP_ID`.

Frontend config is **runtime**, not bundled — `frontend/public/config.json`, loaded by `src/main.js`. That is where `API_BASE_URL` / `EXTENSIONS_API_BASE_URL` point the UI at a backend; the `.env.*` files only carry build-mode settings.

The Docker compose stack that runs every component together is maintained outside this repository. This repo is developed component-by-component against a local Neo4j.

## Neo4j versioning model — easy to get wrong

Each versioned entity has a `Root` node linked to `Value` nodes by `HAS_VERSION` rels carrying `version`/`status`/`start_date`/`end_date`. Current status derives from the **open** `HAS_VERSION` (`end_date IS NULL`).

`LATEST_DRAFT` / `LATEST_FINAL` / `LATEST_RETIRED` are **historical pointers, not current-status flags**. They coexist on the same Root and may point at the same value node. Never delete one when setting another — that has caused real regressions. Full detail in `api/.claude/rules/database.md`.

## CI

`.github/workflows/pr-required-checks.yml` is a coordinator: it git-diffs the PR against its base, dispatches only the per-project build workflows whose paths changed, and aggregates into ONE required status check named `required`. Consequences when editing workflows:

- Adding a component = three edits in that file: a filter entry, a dispatch block, and the job key in `required`'s `needs:` list. Branch protection never changes.
- A change under `_tools/` triggers nearly every project (shared SBOM step).
- A change under `api/` also triggers `verifications` and `db_schema_migration` — both build against the in-tree api.
- A change to `api/openapi.json` triggers `frontend` — the demo build generates mocks from the spec.
- Editing the coordinator itself deliberately triggers nothing; verify with a follow-up PR that touches a real project.

## Conventions

- Present tense imperative commit subjects ("Add feature").
- Run the component's `format` + `lint` before committing.
- `openapi.json` files are generated — never hand-edit; run the app's `*-openapi` script.
- A small change spanning `api/` and `frontend/` belongs in **one** PR, not two. The CI coordinator dispatches per-directory, so a cross-component PR simply runs both jobs — and an `api/openapi.json` change re-runs the frontend job against the new spec, which is exactly the pairing you want validated. Split across two PRs, the frontend half builds against the old spec still on `main`.
