# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

OpenStudyBuilder / Clinical-MDR — clinical trial metadata management for pharma research. Monorepo of independently-built components sharing one Neo4j graph database as the integration point.

## Nested instructions — read these first

Two components carry their own detailed rule sets. When working in either, read the rule files, not just the index:

- `api/AGENTS.md` → `api/.claude/rules/*.md` (project-overview, project-structure, commands, architecture, database, api-conventions, code-standards, authentication, testing, monitoring)
- `frontend/AGENTS.md` → `frontend/.claude/rules/*.md` (overview, commands, architecture-core, components, patterns, routing-auth, conventions-gotchas)

Those two `.claude/` directories hold **rules only**. Skills and subagents live at the repository root — see below.

## Claude Code layout

Skills and subagents are all at the repository ROOT, so every command is available whichever component you are working in. This is deliberate: a `.claude/skills/` directory *below* the launch directory does not load at startup (it only appears once Claude touches a file in that subdirectory), and a nested `.claude/agents/` is invisible to a session started above it. Do not move either back under a component.

- **`.claude/skills/osb-*/`** — the 11 user-invokable slash commands. For a project skill the DIRECTORY NAME *is* the command, so the `osb-` prefix has to stay on the directory; keep each skill's frontmatter `name` byte-identical to its directory name.
- **`.claude/skills/branch-change-detection/`** and **`.claude/skills/logging-standards-helper/`** — internal helpers, deliberately UNPREFIXED because they are not slash commands (`user-invocable: false`). The missing prefix is the signal. Renaming either breaks references silently: `branch-change-detection` is reached only by a literal `Read` of its path from 5 call sites, and `logging-standards-helper` is preloaded by 4 agents through their `skills:` frontmatter, where a failed lookup is logged to the debug log rather than surfaced.
- **`.claude/agents/`** — 9 subagents, referenced from the skills by their frontmatter `name` as `subagent_type`.

**Path convention inside skills and agents: every file path is repo-root-relative.** Commands that genuinely depend on the working directory carry an explicit "run from `api/`" or "from `frontend/`" note — that is process cwd, not a path. Two files point at root `.claude/` paths from inside a component (`api/.claude/rules/monitoring.md`, `frontend/.claude/rules/patterns.md`); both are correct as written and are annotated as such. Do not "fix" them by prefixing the component.

## Components

| Dir | Purpose | Stack |
|-----|---------|-------|
| `api/` | REST API — four FastAPI apps off one codebase | Python 3.14, FastAPI, neomodel/Neo4j |
| `frontend/` | OpenStudyBuilder web UI | Vue 3, Vite, Vuetify 3, Pinia, **npm** |
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

### The three public API apps

One codebase, three public ASGI apps, shared `common/` (config, auth, database, telemetry, exceptions). Each has its own port, `openapi.json`, tests, and lint target:

| App | Port | poe tasks |
|-----|------|-----------------|
| `clinical_mdr_api/` (main) | 8000 | `dev`, `lint`, `testunit`, `testint`, `openapi` |
| `extensions/` | 8009 | `extensions-*`, `extensions-openapi` |
| `standards_import/` (CDISC ingestion) | 8010 standalone / 8000 merged | `standards-import-*` |

`standards_import/` is the only app that talks to a **second** database: neomodel stays bound to the MDR database via `NEO4J_DSN`, and the CDISC staging database is reached with the raw driver via `STANDARDS_IMPORT_STAGING_DSN`. That staging database is durable and owned by this app — analysing a new package needs the state left by the previous ones. It also deliberately bypasses the main API's library-editability and uniqueness guards, so it carries its own `Library.Import` RBAC role.

When `STANDARDS_IMPORT_ENABLED=true` (the default), the main app on port 8000 also serves `standards_import/`'s routers under `/standards-import`. Running `uvicorn standards_import.main:app` on port 8010 still works as a standalone deployment. The Python package `standards_import` is intentionally kept as its own top-level module tree even in the merged deployment: the import-linter contract (`clinical_mdr_api ↔ standards_import` independence) and the sblint Cypher linter both depend on the two packages remaining disjoint. Collapsing the namespace would collapse the code-level boundary those tools enforce.

Staging and MDR share one Neo4j database, kept apart by:
- **`:CDISCStaging` marker label** — every node the staging side creates carries this second label alongside its real label (e.g. `:RawPackage:CDISCStaging`). The drift check in `verifications/` and the sblint rule in `api/sblint/` both enforce this statically. Keep sblint rule `STAGING_LABELS` up to date when creating new staging-level nodes.
- **Neo4j roles** (`mdr`/`staging`) — provisioned by `db/init_neo4j.py` on Enterprise. The `mdr` role has a DENY on `:CDISCStaging` nodes; the `staging` role is an allowlist of `:CDISCStaging` only. This is defence in depth: the app never relies on the DENY for correctness — it must work on Community too.
- **import-linter** — `pipenv run lint-imports` in `api/` enforces: `standards_import` must not import `clinical_mdr_api`; `clinical_mdr_api` must not *directly* import `standards_import.repositories/.services/.domain` (`.routers` is the intended public mount point); staging repositories must not use neomodel.

The consumer API is internal; the example for external usage is `extensions/consumer_sample/` (see its `README.md`).

The main API follows three-layer DDD — `domains/` (business logic, no outward deps) → `domain_repositories/` (Neo4j persistence, Memento pattern, optimistic locking) → `routers/`+`services/`+`models/`. Build features inside-out in that order; see `api/.claude/rules/architecture.md`.

## Commands

Every Python component is **uv** with its own `pyproject.toml`/`uv.lock`, and tasks live under `[tool.poe.tasks]`, run via `uv run poe <name>` (poethepoet) — **check there rather than guessing**; tasks differ per component and some are pinned to a version number (see migrations below). `load_tests/` was the pilot for this migration to uv/poe, followed by `api/` and then the rest of the Python components.

```bash
# api
cd api && uv sync --group dev
uv run poe dev                                  # :8000
uv run poe testunit                             # unit
uv run poe testint                              # integration — needs Neo4j, runs xdist parallel
uv run poe testauth                             # OAuth/RBAC
uv run poe test -- path/to/test.py::test_name   # single test (plain pytest -s)
uv run poe format && uv run poe lint && uv run poe mypy
uv run poe sblint                               # custom in-repo static analysis (sblint/)
uv run poe openapi                              # regenerate openapi.json after route/model changes
uv run poe schemathesis                         # contract tests against a running :8000

# frontend (npm)
cd frontend && npm install
npm run dev                                     # vite default :5173
npm run lint && npm run format
npm run test:smoke                              # builds demo bundle, then Playwright
npx playwright test --config tests/smoke/playwright.config.js -g "name"   # single smoke test

# db
cd db && ./create_neo4j_local.sh && uv run poe init_neo4j
```

`db_schema_migration` scripts are **pinned per migration number** — `test`/`verify`/`migrate` all point at `*_024` today, corrections at `*_022`. Bump those `pyproject.toml` `[tool.poe.tasks]` entries when starting a new migration.

## Database population order

Order matters — each step depends on the previous:

1. `db/` — init schema
2. `import_standards/` — CDISC controlled terminology
3. `api/` — start API
4. `import_sponsor_data/` — sponsor codelists + mock data (goes through the API, not straight to Neo4j)

Steps 2 and 4 are load-bearing, not just populating: a number of codelists are resolved by submission value to build forms and validate mandatory fields, so a missing or empty one stops a feature rather than degrading it (no `VisitType` terms → no study visit can be created). `import_sponsor_data/SYSTEM_CODELISTS.md` lists which codelists are required, what each is needed for, and how the failures present — the read path is silent, the write path raises a 400 naming the submission value. Consult it before concluding that odd behaviour against a fresh or restored database is a code bug.

## Environment

Each component reads its own `.env` — copy from its `.env.example` (`api/`, `db_schema_migration/`, `frontend/`, `verifications/` ship one; `db/` documents its variables in `db/README.md`). The API is driven by `NEO4J_DSN`; `db/` and the compose files use the split `NEO4J_MDR_*` variables, and the two must agree on host/port/credentials.

Bolt port differs by setup: 7687 for Neo4j Desktop, 5078 for the repo's Docker container (`db/README.md`). OAuth is off by default locally; enable with `OAUTH_ENABLED`, `OAUTH_METADATA_URL`, `OAUTH_API_APP_ID`.

Additional variables introduced during the staging/MDR merge:
- `STANDARDS_IMPORT_ENABLED` (default `true`) — gates the standards-import routers on the main app under `/standards-import`. Set `false` to run the main app without them (e.g. when standards-import is deployed separately).
- `NEO4J_MDR_ROLE_USER` / `NEO4J_MDR_ROLE_PASSWORD` / `NEO4J_STAGING_ROLE_USER` / `NEO4J_STAGING_ROLE_PASSWORD` — provision least-privileged Neo4j users for the two halves of the database (Enterprise only; skipped gracefully on Community). See `db/README.md` for details.

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
