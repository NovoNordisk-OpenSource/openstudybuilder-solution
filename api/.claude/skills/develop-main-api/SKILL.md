---
name: develop-main-api
description: "Implement new or update existing API endpoints in the main Clinical MDR API by leveraging the specialized endpoint implementation agent. Scopes strictly to api/clinical_mdr_api/ and its three-layer DDD architecture."
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

This skill does NOT cover the Consumer API (`api/consumer_api/`) or the Extensions API (`api/extensions/`) — use `/develop-consumer-api` or `/develop-extensions-api` for those. If the user's request turns out to target one of them, say so and stop rather than writing into `clinical_mdr_api/`.

## Shared context

Define `{MAIN_API_CONTEXT}` once and substitute it verbatim into every agent prompt below:

```
The main API lives in `api/clinical_mdr_api/` and runs on port 8000. It is the primary read/write API for clinical metadata, and it is by far the largest of the three apps in `api/`.

Its defining constraint is the three-layer DDD architecture. Business logic lives ONLY in `domains/`; Neo4j access lives ONLY in `domain_repositories/`; `routers/`, `services/`, and `models/` handle HTTP and serialization concerns. New features are built inside-out: domain → repository → service.

The authoritative sources are the rule files and the code — read them rather than relying on this prompt:

- `api/.claude/rules/architecture.md` — the three layers, their dependency direction, and the inside-out workflow.
- `api/.claude/rules/database.md` — neomodel, optimistic locking, and the versioning graph model.
- `api/.claude/rules/api-conventions.md` — Zalando REST naming, HTTP verb/status pairs, and the full exception-to-status-code table. The exceptions live in `common/exceptions.py`; there is no `clinical_mdr_api/exceptions/` module.
- `api/.claude/rules/code-standards.md` — Black/isort at 88 chars (NOT 200; that is Pylint's separate limit), imports at top of file, type hints on public methods.
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

VERIFICATION IS SPLIT BETWEEN YOU AND THE CALLER. You have Bash for the fast checks — run `pipenv run format`, then `pipenv run pylint -j 1` and `pipenv run python -m sblint.main` scoped to the files you changed, and converge before returning. Your agent definition has the full rules and the invocation traps; follow them. Do not run the test suites, do not run `pipenv run openapi`, and never claim a check passed that you did not run.

The caller then runs the slow remainder — unscoped mypy and the tests — and asks the user before regenerating the OpenAPI spec.

What the caller needs from you, as the last section of your response:
- **CHANGED FILES**: every file you created or modified, one repo-relative path per line. The caller scopes the linter to exactly this list, so a path you omit goes unchecked.
- **ROUTES TOUCHED**: whether you added, removed, or changed any route, response model, or endpoint docstring — this decides whether the OpenAPI spec must be regenerated.
- **LAYERS TOUCHED**: which of domain / repository / service you edited — this decides whether unit tests, integration tests, or both need to run.
```

## Verification

The agent runs the fast scoped checks itself (format, pylint, sblint) and converges before returning. You run what it deliberately cannot: the unscoped type-check and the tests. The OpenAPI spec is a separate case — it is not a check, it mutates committed files, so you ASK before regenerating it and never do so on your own initiative. Every branch below ends by referring back here.

**Working directory: every command in this section runs from `api/`**, because they are all `pipenv` scripts and the Pipfile lives there. Note this differs from the enumeration command in the branches below, whose path is written relative to the repo root — check where you are before pasting either.

Work from the agent's CHANGED FILES list; if it did not produce one, recover it with `git status --porcelain` and `git diff --name-only`, filtered to `api/**/*.py`. If that comes back empty, the agent changed nothing: say so and stop rather than running linters against an empty file list.

**1. Confirm the agent's checks actually ran.**

The agent reports what it ran. If its response shows no format/lint output — or claims a pass without showing it — do not take its word. Run them yourself before going further:

```bash
pipenv run format                                      # isort + black, ~6s
pipenv run pylint -j 1 <changed .py files>             # never `pipenv run lint`; see below
pipenv run python -m sblint.main <changed .py files>   # ~0.5s scoped, vs ~14s whole-codebase
```

`pipenv run format` is whole-codebase but the tree is black-clean at baseline, so it only touches the new code. If it reformats a file the agent never touched, stop and say so — the baseline drifted and this change is now entangled with someone else's.

Never use `pipenv run lint`: the Pipfile hardcodes `-j 0`, whose process pool dies under the sandbox with `PermissionError` on `os.sysconf("SC_SEM_NSEMS_MAX")`, and it lints every file in all four packages — minutes rather than seconds — reporting pre-existing issues in untouched code. Aim for a clean score on the changed files; the exact threshold comes from the pylint config in `pyproject.toml`, not from this file. A `Unable to create file .../pylint/*.stats` warning is the sandbox blocking pylint's cache — harmless.

**2. Type-check — deliberately NOT scoped.**

```bash
pipenv run mypy    # whole codebase; tens of seconds
```

Run mypy over the whole codebase even though scoping it to the changed files is far faster. The extra seconds buy something scoping cannot: mypy follows imports *downward*, so a scoped run checks the changed file and what it imports — but never its **callers**. Change a function signature and a scoped run passes clean while every call site elsewhere is now wrong. That is precisely the breakage a signature change causes, so pay the cost.

These checks were clean across the whole codebase when this skill was written, so in the normal case anything they report is attributable to this change. Do not treat that as guaranteed — if a reported error sits in a file the agent never touched, it is pre-existing or someone else's in-flight work. Confirm against the CHANGED FILES list before you attribute anything, and report unrelated failures separately rather than fixing them here.

Two invocation traps, both verified the hard way:
- `pipenv run mypy` and `pipenv run sblint` are Pipfile scripts with their target paths **baked in**. Appending file paths duplicates them — mypy then fails with `Duplicate module named "clinical_mdr_api"` and checks nothing, while appearing to have run. To scope either one you must bypass the script: `pipenv run python -m mypy <files>` / `pipenv run python -m sblint.main <files>`.
- A scoped run that reports `no issues found in 2 source files` has checked two files, not the codebase. Do not read that as a clean bill of health for the change.

**3. Tests — by layer touched.**

```bash
pipenv run testunit   # domain-layer logic; no database needed
pipenv run testint    # anything touching Neo4j — REQUIRES a running database
```

`testint` needs Neo4j on the bolt port from `.env` (7687 for Neo4j Desktop, 5078 for the repo's Docker container). Check reachability before running it; if the database is down, say so and skip it rather than reporting a connection error as a test failure.

**4. OpenAPI — ASK, never regenerate on your own initiative.**

Never regenerate the spec without asking first — not via `pipenv run openapi`, not by calling `generate_openapi_json.py` directly. It is not a check: it rewrites the committed `openapi.json`, bumps the `apiVersion` file, and that diff triggers the frontend CI job. Regenerating it uninvited puts a large generated diff and a version bump into the user's working tree as a side effect of a question they did not ask.

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
        description: "Source and spec stay out of sync. Fine mid-task, but the PR is incomplete until someone runs `pipenv run openapi` — the spec is generated and must never be hand-edited."
      }
    ],
    multiSelect: false
  }]
})
```

If they choose to regenerate, run it from `api/`:

```bash
pipenv run openapi
```

The Pipfile script pins `OAUTH_ENABLED=True`, which is load-bearing: that flag gates the OAuth2 security schemes, and generating with it off silently drops `OAuth2AuthorizationCodeBearer` and `BearerJwtAuth` from `components.securitySchemes` — a large unrelated diff and a spec that misdescribes the API's auth. Do not "simplify" the `env` prefix out of the Pipfile, and do not try to override it from your shell: pipenv loads `api/.env` over the inherited environment, so a shell assignment is silently discarded.

Generation does NOT need a running Neo4j — `configure_database` builds a lazy driver and never connects at import — but it does need a valid `NEO4J_DSN` in `.env` or it raises on the scheme.

If they decline, say plainly that the spec is now stale and name the command they will need later. Do not ask again in the same run.

**Fixing what the checks find.** Fix failures the change caused, then re-run the check that failed. Give up after two rounds on the same failure and report it rather than thrashing. Never "fix" a pre-existing failure in code the change did not touch — report it separately so it does not get silently folded into this PR.

**Reporting.** State plainly what ran, what passed, and what did not. If you skipped a step — integration tests with no database, OpenAPI on a change that touched no routes — say which and why. Do not report a check as passing unless you saw it pass.

## Task type

AskUserQuestion({
  questions: [{
    question: "What type of main API development do you need?",
    header: "Task Type",
    options: [
      {
        label: "New endpoint implementation (Recommended)",
        description: "Create a new endpoint following the three-layer DDD architecture - the agent determines the layer depth and operation type from your description and the existing code"
      },
      {
        label: "Modify existing endpoint",
        description: "Update or enhance an existing main API endpoint - I'll locate the endpoint and gather the modification details"
      },
      {
        label: "Full feature implementation",
        description: "Complete feature spanning domain aggregates, repositories, services, routers, and tests - the agent scopes it from your description and the existing aggregates"
      },
      {
        label: "Custom implementation",
        description: "Work directly with your provided task description for specific main API requirements"
      }
    ],
    multiSelect: false
  }]
})

Match on the label PREFIX in every mapping below — the "(Recommended)" suffix may or may not be present.

**Before invoking any agent, apply the area guard.** Re-read the user's request against the scope stated at the top of this file. If it targets `api/consumer_api/` or `api/extensions/` — it names one of those apps, a route only they serve, or port 8008/8009 — stop and point the user at `/develop-consumer-api` or `/develop-extensions-api` instead of invoking the specialist. This is the only place that guard is enforced; past this point every branch writes into `clinical_mdr_api/`.

Note on options: `AskUserQuestion` accepts a maximum of 4 options per question and always offers an "Other" free-text choice automatically. The task-type question above is the only one this skill asks up front — every branch below proceeds without a follow-up. If a branch does end up needing to ask (the modify branch, when the target is genuinely ambiguous), keep it to 4 real candidates and do not add an "Other …" option of your own; the built-in one already covers it.

"Custom implementation" above is deliberately a real option rather than a duplicate of that escape hatch: it selects a distinct agent prompt, not just free text.

---

**If "New endpoint implementation" is selected:**

Do not ask a follow-up question. How far down the DDD layers the endpoint reaches, and which HTTP operation it is, are determinations to be made by reading the request against the existing code — the specialist agent is better placed to make them than the user is, and asking would force the user to guess at an architecture decision before anyone has looked at the relevant aggregate.

Invoke the endpoint implementation specialist directly:

```
Agent({
  description: "New main API endpoint implementation",
  subagent_type: "endpoint-implementation-specialist",
  prompt: "I need help implementing a new endpoint in the main Clinical MDR API. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: New endpoint implementation

{MAIN_API_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read before writing**: Enumerate the mounted prefixes, then read the nearest comparable endpoint end to end — its router, service, repository, and domain aggregate — as a worked example.
2. **Determine the layer depth yourself, then state it**: Decide from the request and the existing code whether this is (a) service-layer only, reusing an existing aggregate and repository, (b) an existing aggregate needing a new repository query or persistence method, or (c) a new domain aggregate built from scratch. State which one you concluded and why BEFORE you start writing, so the user can correct you early. If the request is genuinely ambiguous between these, ask the user rather than guessing.
3. **Build inside-out**: Implement in domain → repository → service order, to whatever depth you determined. Do not start at the router.
4. **Match the operation to the conventions**: Derive the HTTP verb and status from what the endpoint does, per api/.claude/rules/api-conventions.md — GET/200 for reads, POST/201, PATCH/200, DELETE/204. A paginated listing must follow the existing pagination, filtering, and sorting conventions rather than a hand-rolled scheme; a write operation engages versioning, optimistic locking, and domain validation.
5. **Confirm the auth dependency against a neighbour**: Do not infer the rbac dependency from the verb. Use the dependency on the nearest comparable route in clinical_mdr_api/routers/.
6. **Keep business logic in the domain layer**: Services orchestrate and translate; they do not decide business rules. Repositories persist; they do not validate.
7. **Define models**: Add Pydantic request/response models under clinical_mdr_api/models/, matching the naming of the surrounding area.
8. **Wire the router**: Perform all three wiring edits described under ROUTER WIRING above. A router missing any of the three serves no traffic.
9. **Use the project's exception types**: `from common.exceptions import NotFoundException, ValidationException` and friends, picking the most specific type per the table in api-conventions.md — never generic exceptions.
10. **Create tests**: Unit tests under clinical_mdr_api/tests/unit/ for domain logic, integration tests under clinical_mdr_api/tests/integration/ for anything hitting Neo4j. Reuse fixtures from tests/fixtures/.
11. **Close with the handoff**: End with CHANGED FILES, ROUTES TOUCHED, and LAYERS TOUCHED as described above. Do not run or claim to run any verification.

The user's main API endpoint request follows:

{USER_REQUEST}"
})
```

When the agent returns, run the checks in **## Verification** above.

---

**If "Modify existing endpoint" is selected:**

Do NOT use a hardcoded list of endpoints — it goes stale, and the main API mounts far too many routers for such a list to be usable anyway. Enumerate what is actually served first:

```bash
# from the REPO ROOT — not from api/, where this relative path does not resolve
grep -oE 'prefix="[^"]*"' api/clinical_mdr_api/main.py | sed 's/prefix="//;s/"$//' | sort -u
```

That returns many dozens of distinct prefixes — vastly more than the four options `AskUserQuestion` allows, so a picker is not an option. The default is therefore to infer, not to ask:

- If the user's task description names a path, resource, or area that matches the enumeration, skip the question entirely. State which endpoint you matched and proceed.
- If the description is ambiguous, narrow it yourself first — grep the enumeration for the nouns in the user's description, and grep `clinical_mdr_api/routers/` for the operation they described.
- Only ask if that still leaves genuine ambiguity, and then offer at most the 4 most plausible candidates as concrete paths. Say in the question text that the list is filtered to the closest matches so the user knows to use the built-in "Other" choice.
- If nothing matches, do not guess. Report what you searched for and ask the user to name the endpoint.

`{TARGET_ENDPOINT}` = the matched or selected endpoint path.

Then invoke the endpoint implementation specialist:

```
Agent({
  description: "Modify existing main API endpoint",
  subagent_type: "endpoint-implementation-specialist",
  prompt: "I need help modifying an existing endpoint in the main Clinical MDR API. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Modify existing endpoint
- Target: {TARGET_ENDPOINT}
- Modification Type: Enhancement or bug fix to existing functionality

{MAIN_API_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Locate the target**: Find the mounted route, then follow it down through its service, repository, and domain aggregate before changing anything. If the route is not in the enumeration, stop and report what is actually mounted rather than guessing.
2. **Place the change in the right layer FIRST**: Decide which layer actually owns the behaviour being changed. A validation rule belongs in the domain, not the service; a query change belongs in the repository, not the service. Getting this wrong is the most common way these changes go bad.
3. **Follow existing patterns**: Match the surrounding code's style and structure rather than importing conventions from another area of the codebase.
4. **Respect the versioning model**: If the change touches version pointers or status transitions, re-read api/.claude/rules/database.md and preserve every LATEST_DRAFT / LATEST_FINAL / LATEST_RETIRED pointer.
5. **Check the response contract**: If the change alters an existing response shape, call that out explicitly to the user — the frontend consumes this spec.
6. **Update tests**: Modify or add unit and integration tests covering the changed behaviour.
7. **Close with the handoff**: End with CHANGED FILES, ROUTES TOUCHED, and LAYERS TOUCHED as described above. Do not run or claim to run any verification.

The user's endpoint modification request follows:

{USER_REQUEST}"
})
```

When the agent returns, run the checks in **## Verification** above.

---

**If "Full feature implementation" is selected:**

Do not ask a follow-up question. Whether the feature is a new domain aggregate, an extension of an existing one, or cross-cutting is a conclusion drawn from reading the request against the existing aggregates — the specialist agent is better placed to reach it than the user is, and it is the first thing the agent does anyway when it designs the domain.

Invoke the endpoint implementation specialist directly:

```
Agent({
  description: "Full main API feature implementation",
  subagent_type: "endpoint-implementation-specialist",
  prompt: "I need help implementing a complete feature in the main Clinical MDR API. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Full feature implementation
- Implementation Type: Complete feature spanning multiple DDD layers

{MAIN_API_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read before writing**: Enumerate the mounted prefixes, then read the closest existing feature end to end across all three layers as a worked example.
2. **Determine the feature's scope yourself, then state it**: Decide from the request and the existing aggregates whether this is (a) a new domain aggregate with its own root, repository, services, and routers, (b) an extension of an existing area such as studies, concepts, controlled terminologies, syntax templates, or ODMs, or (c) a cross-cutting feature spanning several domains, such as a new filter, export format, audit trail, or listing. State which one you concluded and why. If the request is genuinely ambiguous between these, ask the user rather than guessing — the answer changes how much gets built.
3. **Design the domain first**: Identify the aggregate roots and their boundaries, and define the public interfaces between layers, BEFORE writing any code. Present that design in your summary alongside the scope conclusion, so the user can correct both before implementation goes far.
4. **Implement inside-out**: domain → repository → service → router, with tests at each layer. Do not write the router first and back-fill the domain.
5. **Keep the dependency direction clean**: domains/ must not import from domain_repositories/ or services/. Verify this before finishing.
6. **Respect the versioning model**: If the feature introduces versioned entities, follow the Root/Value + HAS_VERSION model in api/.claude/rules/database.md exactly, including optimistic locking in the repository.
7. **Wire every router**: Apply all three edits from ROUTER WIRING above to each new router, not just the first.
8. **Create a comprehensive test suite**: Unit tests for domain logic, integration tests for persistence and endpoints, covering happy paths and error cases.
9. **Close with the handoff**: End with CHANGED FILES, ROUTES TOUCHED, and LAYERS TOUCHED as described above. Do not run or claim to run any verification.

The user's full feature request follows:

{USER_REQUEST}"
})
```

When the agent returns, run the checks in **## Verification** above.

---

**If "Custom implementation" is selected:**

Invoke the endpoint implementation specialist directly:

```
Agent({
  description: "Custom main API implementation",
  subagent_type: "endpoint-implementation-specialist",
  prompt: "I need help with a custom implementation in the main Clinical MDR API. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Custom implementation based on user's specific requirements
- Implementation Type: User-defined main API task

{MAIN_API_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read before writing**: Enumerate the mounted prefixes and read the relevant parts of clinical_mdr_api/ before deciding on an approach.
2. **Identify the owning layer**: Work out which layer each part of the change belongs in before editing, and keep business logic in the domain layer.
3. **Follow conventions**: Match existing code style, naming conventions, and architectural patterns.
4. **Respect the versioning model**: If the work touches version pointers or status transitions, re-read api/.claude/rules/database.md first.
5. **Implement changes**: Create or modify domain logic, repositories, services, models, and routers as needed, applying all three ROUTER WIRING edits to any new router.
6. **Create tests**: Add unit and/or integration tests appropriate to the layers touched.
7. **Close with the handoff**: End with CHANGED FILES, ROUTES TOUCHED, and LAYERS TOUCHED as described above. Do not run or claim to run any verification.

The user's custom main API development request follows:

{USER_REQUEST}"
})
```

When the agent returns, run the checks in **## Verification** above.
