---
name: osb-develop-main-api
description: "Use when adding or changing endpoints, services, repositories, or domain logic in the main Clinical MDR API (api/clinical_mdr_api/, port 8000). For api/consumer_api/ use /osb-develop-consumer-api; for api/extensions/ use /osb-develop-extensions-api."
---

# Develop Main API

I'll help you with main API development by invoking the specialized endpoint implementation agent. This agent will analyze your request, examine existing patterns, and implement the necessary changes following the project's three-layer DDD architecture.

The user will provide a feature description after the slash command. I'll use that description as the task specification when invoking the endpoint-implementation-specialist.

`{USER_REQUEST}` = the user's description, verbatim, exactly as they typed it after the slash command. Every agent prompt below ends by substituting it — a prompt that says "the request follows" and then contains nothing leaves the agent with no task at all, so never send one without it. Do not paraphrase, summarise, or "clean up" the request: the agent needs the user's own wording, including any file paths, field names, or endpoint paths they mentioned.

If the user invoked the skill with no description at all, do not guess and do not invoke an agent. Ask them what they want built, then continue.

## What this skill handles:

- Implementing new main API endpoints
- Updating or modifying existing main API endpoints
- Domain logic, repository persistence, and service orchestration
- Creating unit and integration tests for main API functionality
- Working with files in the `api/clinical_mdr_api/` directory

This skill does NOT cover the Consumer API (`api/consumer_api/`) or the Extensions API (`api/extensions/`) — use `/osb-develop-consumer-api` or `/osb-develop-extensions-api` for those. If the user's request turns out to target one of them, say so and stop rather than writing into `clinical_mdr_api/`.

## Shared context

Define `{MAIN_API_CONTEXT}` once and substitute it verbatim into every agent prompt below:

```
The main API lives in `api/clinical_mdr_api/` and runs on port 8000. It is the primary read/write API for clinical metadata, and it is by far the largest of the three apps in `api/`.

Its defining constraint is the three-layer DDD architecture. Business logic lives ONLY in `domains/`; Neo4j access lives ONLY in `domain_repositories/`; `routers/`, `services/`, and `models/` handle HTTP and serialization concerns. New features are built inside-out: domain → repository → service.

The authoritative sources are the rule files and the code — read them rather than relying on this prompt:

- `api/.claude/rules/architecture.md` — the three layers, their dependency direction, and the inside-out workflow.
- `api/.claude/rules/database.md` — neomodel, optimistic locking, and the versioning graph model.
- `api/.claude/rules/api-conventions.md` — Zalando REST naming, HTTP verb/status pairs, and the full exception-to-status-code table. The exceptions live in `common/exceptions.py`; there is no `clinical_mdr_api/exceptions/` module.
- `api/.claude/rules/code-standards.md` — Black/isort at 88 chars (NOT 200; that is Ruff's separate limit), imports at top of file, type hints on public methods.
- `api/.claude/rules/testing.md` — where unit vs integration tests belong.

This prompt deliberately does not restate what those files encode; they are the single source of truth and anything duplicated here would drift.

The main API has NO component README, and — unlike `consumer_api/`, which carries `requirements/fs/` and `requirements/urs/` — NO `requirements/` traceability directory. Do not go looking for either, and do not invent traceability updates as a step.

ROUTER WIRING — the most commonly missed step. Mounting a new route takes three edits, not one:
1. The route module itself under `clinical_mdr_api/routers/<area>/`.
2. An export in `clinical_mdr_api/routers/__init__.py` (`from ... import router as <name>_router`).
3. An `app.include_router(...)` call in `clinical_mdr_api/main.py` with its `prefix` and `tags`.
A router that is written but not exported and mounted serves no traffic and will not appear in the OpenAPI spec.

VERSIONING GRAPH MODEL — read `api/.claude/rules/database.md` before touching any repository code that writes version pointers. `LATEST_DRAFT` / `LATEST_FINAL` / `LATEST_RETIRED` are historical pointers, NOT current-status flags. They may coexist on the same Root and may point at the same value node. Never delete one when setting another — doing so has caused real regressions. Current status derives from the open `HAS_VERSION` (`end_date IS NULL`).

Never assume a route, service, or aggregate exists because this prompt or a document mentions it. Enumerate what is actually mounted — this path is relative to the REPO ROOT, not to `api/`:

    grep -oE 'prefix="[^"]*"' api/clinical_mdr_api/main.py | sed 's/prefix="//;s/"$//' | sort -u

For a narrower search, grep that output — the list is long enough that reading it end to end is rarely the right move.

VERIFICATION IS SPLIT BETWEEN YOU AND THE CALLER. You have Bash for the fast checks — run `uv run poe format`, then `uv run ruff check` and `uv run python -m sblint.main` scoped to the files you changed, and converge before returning. Your agent definition has the full rules and the invocation traps; follow them. Do not run the test suites, do not run `uv run poe openapi`, and never claim a check passed that you did not run.

The caller then runs the slow remainder — unscoped mypy and the tests — and asks the user before regenerating the OpenAPI spec.

What the caller needs from you, as the last section of your response:
- **CHANGED FILES**: every file you created or modified, one repo-relative path per line. The caller scopes the linter to exactly this list, so a path you omit goes unchecked.
- **ROUTES TOUCHED**: whether you added, removed, or changed any route, response model, or endpoint docstring — this decides whether the OpenAPI spec must be regenerated.
- **LAYERS TOUCHED**: which of domain / repository / service you edited — this decides whether unit tests, integration tests, or both need to run.
```

## Verification

The agent runs the fast scoped checks itself (format, ruff, sblint) and converges before returning. You run what it deliberately cannot: the unscoped type-check and the tests. The OpenAPI spec is a separate case — it is not a check, it mutates committed files, so you ASK before regenerating it and never do so on your own initiative. The invocation below ends by referring back here.

**Working directory: every command in this section runs from `api/`**, because they are all `uv run poe` tasks and `pyproject.toml` lives there. Note this differs from the enumeration command, whose path is written relative to the repo root — check where you are before pasting either.

Work from the agent's CHANGED FILES list; if it did not produce one, recover it with `git status --porcelain` and `git diff --name-only`, filtered to `api/**/*.py`. If that comes back empty, the agent changed nothing: say so and stop rather than running linters against an empty file list.

**1. Confirm the agent's checks actually ran.**

The agent reports what it ran. If its response shows no format/lint output — or claims a pass without showing it — do not take its word. Run them yourself before going further:

```bash
uv run poe format                                      # isort + black, ~6s
uv run ruff check <changed .py files>                  # fast, scoped or whole-codebase
uv run python -m sblint.main <changed .py files>       # ~0.5s scoped, vs ~14s whole-codebase
```

`uv run poe format` is whole-codebase but the tree is black-clean at baseline, so it only touches the new code. If it reformats a file the agent never touched, stop and say so — the baseline drifted and this change is now entangled with someone else's.

`uv run poe lint` runs ruff over the whole codebase and is fast and sandbox-safe; scoping with `ruff check <changed files>` is still faster for a small diff. The tree is ruff-clean at baseline ("All checks passed!"), so any finding is attributable to this change; the rule config comes from `[tool.ruff]` in `pyproject.toml`.

**2. Type-check — deliberately NOT scoped.**

```bash
uv run poe mypy    # whole codebase; tens of seconds
```

Run mypy over the whole codebase even though scoping it to the changed files is far faster. The extra seconds buy something scoping cannot: mypy follows imports *downward*, so a scoped run checks the changed file and what it imports — but never its **callers**. Change a function signature and a scoped run passes clean while every call site elsewhere is now wrong. That is precisely the breakage a signature change causes, so pay the cost.

These checks were clean across the whole codebase when this skill was written, so in the normal case anything they report is attributable to this change. Do not treat that as guaranteed — if a reported error sits in a file the agent never touched, it is pre-existing or someone else's in-flight work. Confirm against the CHANGED FILES list before you attribute anything, and report unrelated failures separately rather than fixing them here.

Two invocation traps, both verified the hard way:
- `uv run poe mypy` and `uv run poe sblint` are poe tasks with their target paths **baked in**. Appending file paths duplicates them — mypy then fails with `Duplicate module named "clinical_mdr_api"` and checks nothing, while appearing to have run. To scope either one you must bypass the task: `uv run python -m mypy <files>` / `uv run python -m sblint.main <files>`.
- A scoped run that reports `no issues found in 2 source files` has checked two files, not the codebase. Do not read that as a clean bill of health for the change.

**3. Tests — by layer touched.**

```bash
uv run poe testunit   # domain-layer logic; no database needed
uv run poe testint    # anything touching Neo4j — REQUIRES a running database
```

`testint` needs Neo4j on the bolt port from `.env` (7687 for Neo4j Desktop, 5078 for the repo's Docker container). Check reachability before running it; if the database is down, say so and skip it rather than reporting a connection error as a test failure.

**4. OpenAPI — ASK, never regenerate on your own initiative.**

Never regenerate the spec without asking first — not via `uv run poe openapi`, not by calling `generate_openapi_json.py` directly. It is not a check: it rewrites the committed `openapi.json`, bumps the `apiVersion` file, and that diff triggers the frontend CI job. Regenerating it uninvited puts a large generated diff and a version bump into the user's working tree as a side effect of a question they did not ask.

First decide whether it is even relevant, using the agent's ROUTES TOUCHED report. If the agent did not provide one, derive it from CHANGED FILES: anything under `routers/` or `models/` is route-facing; changes confined to `domains/`, `domain_repositories/`, or `tests/` are not.

- **No route, response model, or endpoint docstring changed** → do not ask. Say the spec is unaffected and move on.
- **Something route-facing changed** → ask, exactly once:

```
AskUserQuestion({
  questions: [{
    question: "This change touches the API surface, so api/openapi.json is now out of date. Regenerate it?",
    header: "OpenAPI",
    options: [
      {
        label: "Yes, regenerate now (Recommended)",
        description: "Regenerates with OAUTH_ENABLED=True. Rewrites openapi.json and bumps the apiVersion file. That diff triggers the frontend CI job, so a matching frontend change belongs in the SAME pull request."
      },
      {
        label: "No, leave it for now",
        description: "Source and spec stay out of sync. Fine mid-task, but the PR is incomplete until someone runs `uv run poe openapi` — the spec is generated and must never be hand-edited."
      }
    ],
    multiSelect: false
  }]
})
```

If they choose to regenerate, run it from `api/`:

```bash
uv run poe openapi
```

The poe task pins `OAUTH_ENABLED=True` via its `env` table in `pyproject.toml`, which is load-bearing: that flag gates the OAuth2 security schemes, and generating with it off silently drops `OAuth2AuthorizationCodeBearer` and `BearerJwtAuth` from `components.securitySchemes` — a large unrelated diff and a spec that misdescribes the API's auth. Do not "simplify" the `env` table out of the `[tool.poe.tasks.openapi]` entry, and do not rely on overriding it from your shell instead: the task's own `env` table is what sets it in the child process, independent of whatever `api/.env` or your shell currently has.

Generation does NOT need a running Neo4j — `configure_database` builds a lazy driver and never connects at import — but it does need a valid `NEO4J_DSN` in `.env` or it raises on the scheme.

If they decline, say plainly that the spec is now stale and name the command they will need later. Do not ask again in the same run.

**Fixing what the checks find.** Fix failures the change caused, then re-run the check that failed. Give up after two rounds on the same failure and report it rather than thrashing. Never "fix" a pre-existing failure in code the change did not touch — report it separately so it does not get silently folded into this PR.

**Reporting.** State plainly what ran, what passed, and what did not. If you skipped a step — integration tests with no database, OpenAPI on a change that touched no routes — say which and why. Do not report a check as passing unless you saw it pass.

## Invoking the specialist

**Area guard first.** Re-read the user's request against the scope stated at the top of this file. If it targets `api/consumer_api/` or `api/extensions/` — it names one of those apps, a route only they serve, or port 8008/8009 — stop and point the user at `/osb-develop-consumer-api` or `/osb-develop-extensions-api` instead of invoking the specialist.

There is no task-type question. Whether this is a new endpoint, a modification, or a full feature is clear from the request, and the specialist settles layer depth and scope by reading the code.

If the request is to modify an existing endpoint, find it before invoking the agent. Do NOT use a hardcoded list of endpoints; enumerate what is mounted (from the REPO ROOT):

```bash
grep -oE 'prefix="[^"]*"' api/clinical_mdr_api/main.py | sed 's/prefix="//;s/"$//' | sort -u
```

- If the request names a path, resource, or area that matches, state which endpoint you matched and proceed.
- If it is ambiguous, grep the enumeration for the nouns in the request and `clinical_mdr_api/routers/` for the operation described. Only if that still leaves genuine ambiguity, ask with at most 4 concrete candidate paths, and say the list is filtered so the user knows to use the built-in "Other".
- If nothing matches, do not guess. Report what you searched for and ask the user to name the endpoint.

`{TARGET}` = the matched endpoint path, or `none` for new work.

```
Agent({
  description: "Main API implementation",
  subagent_type: "endpoint-implementation-specialist",
  prompt: "Implement the user's request in the main Clinical MDR API.

DEVELOPMENT CONTEXT:
- Target endpoint (when modifying): {TARGET}

{MAIN_API_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read before writing**: Enumerate the mounted prefixes, then read the nearest comparable endpoint or feature end to end — its router, service, repository, and domain aggregate — as a worked example. When modifying, locate the target route and follow it down through every layer before changing anything; if it is not mounted, stop and report what is rather than guessing.
2. **State the scope before writing**: Decide from the request and the existing code whether this is (a) service-layer only, reusing an existing aggregate and repository, (b) an existing aggregate needing a new repository query or persistence method, (c) a new domain aggregate, or (d) a cross-cutting feature spanning several domains. Say which layer owns each part of the change — a validation rule belongs in the domain, a query change in the repository. For (c) or (d), also state the aggregate boundaries and the interfaces between layers. Give this BEFORE you start writing, so the user can correct you early. If the request is genuinely ambiguous between these, ask the user rather than guessing.
3. **Build inside-out**: domain → repository → service → router, to whatever depth you determined. Services orchestrate and translate; they do not decide business rules. Repositories persist; they do not validate. domains/ must not import from domain_repositories/ or services/.
4. **Match the conventions**: Derive the HTTP verb and status from what the endpoint does, per api/.claude/rules/api-conventions.md — GET/200, POST/201, PATCH/200, DELETE/204. A paginated listing follows the existing pagination, filtering, and sorting conventions. Take the rbac dependency from the nearest comparable route in clinical_mdr_api/routers/, not from the verb. Use the most specific type from `common.exceptions`, never generic exceptions.
5. **Define models**: Pydantic request/response models under clinical_mdr_api/models/, matching the naming of the surrounding area. If an existing response shape changes, call that out explicitly — the frontend consumes this spec.
6. **Respect the versioning model**: If the work touches version pointers, status transitions, or versioned entities, follow api/.claude/rules/database.md exactly, including optimistic locking, and preserve every LATEST_DRAFT / LATEST_FINAL / LATEST_RETIRED pointer.
7. **Wire every new router**: All three edits described under ROUTER WIRING above.
8. **Create tests**: Unit tests under clinical_mdr_api/tests/unit/ for domain logic, integration tests under clinical_mdr_api/tests/integration/ for anything hitting Neo4j. Reuse fixtures from tests/fixtures/.
9. **Close with the handoff**: End with CHANGED FILES, ROUTES TOUCHED, and LAYERS TOUCHED as described above.

The user's request follows:

{USER_REQUEST}"
})
```

When the agent returns, run the checks in **## Verification** above.
