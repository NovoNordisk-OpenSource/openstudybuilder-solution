---
name: osb-develop-consumer-api
description: "Use when adding or changing endpoints in the Consumer API (api/consumer_api/, port 8008), including changes that may break external consumers. For the main API use /osb-develop-main-api; for api/extensions/ use /osb-develop-extensions-api."
---

# Develop Consumer API

I'll help you with Consumer API development by invoking the specialized Consumer API implementation agent. This agent will analyze your request, examine existing patterns, and implement the necessary changes following established conventions.

The user will provide a feature description after the slash command. I'll use that description as the task specification when invoking the consumer-api-implementation-specialist.

`{USER_REQUEST}` = the user's description, verbatim, exactly as they typed it after the slash command. Every agent prompt below ends by substituting it — a prompt that says "the request follows" and then contains nothing leaves the agent with no task at all, so never send one without it. Do not paraphrase, summarise, or "clean up" the request: the agent needs the user's own wording, including any file paths, field names, or endpoint paths they mentioned.

If the user invoked the skill with no description at all, do not guess and do not invoke an agent. Ask them what they want built, then continue.

## What this skill handles:

- Implementing new Consumer API endpoints
- Updating or modifying existing Consumer API endpoints
- Creating tests for Consumer API functionality
- Following Consumer API patterns and conventions
- Working with files in the `api/consumer_api/` directory
- Updating requirements and traceability documentation

## Shared context

Define `{CONSUMER_CONTEXT}` once and substitute it verbatim into every agent prompt below:

```
The Consumer API lives in `api/consumer_api/` and runs on port 8008. It is read-heavy but NOT read-only — it exposes write endpoints too, so do not infer its constraints from an HTTP verb. What distinguishes it is that its consumers are external: a change to an existing response is visible to them the moment it ships.

There is no README for this component. The authoritative sources are the code and the traceability docs — read them rather than relying on this prompt:

- `api/consumer_api/v1/main.py` — every mounted route, with its auth dependency, pagination, and response model. This is the pattern to match.
- `api/consumer_api/v1/db.py` and `v1/models.py` — query and Pydantic model conventions.
- `api/consumer_api/shared/` — exactly two modules. `responses.py` holds the response models (`PaginatedResponse`, `PaginatedResponseWithStudyVersion`, `StudyVersionSimple`); `common.py` holds shared query/pagination/sort helpers (`query`, `db_pagination_clause`, `db_sort_clause`, `SortByType`, `get_api_version`). It holds **no config and no exceptions** — configuration comes from `common.config.settings` and exceptions from `common/exceptions.py`, both shared across all three apps. Do not add a Consumer-API-specific config or exceptions module.
- `api/consumer_api/requirements/fs/` and `requirements/urs/` — functional and user requirement specs that must be updated alongside behaviour changes.
- `api/consumer_api/tests/v1/` — the expected shape of test coverage.

This prompt deliberately does not restate the conventions those files encode; they are the single source of truth and anything duplicated here would drift.

VERSIONING POLICY — read before changing any existing endpoint. Breaking changes ARE permitted in the Consumer API; backward compatibility is a strong default, not a hard rule. What is not permitted is introducing one *silently*.

A breaking change is anything that removes or renames an existing response field, changes its type, or changes the meaning of its value. Adding a new field to a response is non-breaking. Changing an existing endpoint's status codes, required parameters, or auth requirements is breaking.

If the change you are asked to make is breaking: implement it, then report it. Do not stop, do not refuse, and do not silently reshape the request into a non-breaking one. Cutting a new API version is one option the user may choose — it is not a required consequence, and you should not create one on your own initiative.

What the caller needs from you, as the last section of your response:
- **BREAKING CHANGES**: every breaking change this work introduces, one per line, as `METHOD /path — what changed, and what an existing consumer would see`. Write `None` when there are none. Never omit this section: a breaking change the user learns about from a consumer bug report rather than from you is the one outcome this policy exists to prevent.

Note that v2 is NOT currently available as a target. `api/consumer_api/v2/main.py` is entirely commented out, its router is not mounted (see the commented `include_router` call in `api/consumer_api/consumer_api.py`), and its package file is misnamed `__int__.py` rather than `__init__.py`. Activating v2 is real work in its own right. If the task requires v2, stop and tell the user what activating it involves instead of silently writing code into a module that serves no traffic.

Never assume an endpoint, path, or version exists because this prompt or a document mentions it. Enumerate what is actually served:

    grep -E -A1 '@router\.(get|post|put|patch|delete)\(' api/consumer_api/v1/main.py | grep -oE '"/[^"]+"' | tr -d '"' | sort -u
```

## After the agent returns

The specialist runs its own fast checks (format, lint, sblint) and reports what it ran. It is explicitly barred from regenerating the OpenAPI spec, because that is not a check — it rewrites the committed `consumer_api/openapi.json` and bumps `consumer_api/apiVersion`. That belongs to the user, not to an agent acting on its own initiative.

**Surface the BREAKING CHANGES section first, before anything else you report.** Breaking changes are allowed here, so the agent will have implemented them rather than stopping — which means this report is the only place the user finds out. Do not bury it under the check results, do not summarize it as "some response fields changed", and do not drop it because the change was small.

- **Agent reported `None`** → say in one line that nothing breaking was introduced, and move on.
- **Agent listed one or more** → repeat the list verbatim, then tell the user plainly that existing consumers of those endpoints will be affected on deploy. Mention that cutting a new API version is available if they want to avoid that, but do not cut one and do not press the point — they may well have intended the break.
- **Agent omitted the section entirely** → do not assume it means `None`. Say the agent failed to report, and derive it yourself by diffing the response models it changed.

Then use the agent's report to decide whether the spec is even affected:

- **No route, response model, or endpoint docstring changed** → do not ask. Say the spec is unaffected and move on.
- **Something route-facing changed** → ask, exactly once:

```
AskUserQuestion({
  questions: [{
    question: "This change touches the API surface, so consumer_api/openapi.json is now out of date. Regenerate it?",
    header: "OpenAPI",
    options: [
      {
        label: "Yes, regenerate now (Recommended)",
        description: "Regenerates with OAUTH_ENABLED=True. Rewrites consumer_api/openapi.json and bumps consumer_api/apiVersion."
      },
      {
        label: "No, leave it for now",
        description: "Source and spec stay out of sync. Fine mid-task, but the PR is incomplete until someone runs `uv run poe consumer-openapi` — the spec is generated and must never be hand-edited."
      }
    ],
    multiSelect: false
  }]
})
```

If they agree, run it from `api/`:

```bash
uv run poe consumer-openapi
```

The poe task pins `OAUTH_ENABLED=True` via its `env` table in `pyproject.toml`, which is load-bearing: that flag gates the OAuth2 security schemes, and generating with it off silently drops `OAuth2AuthorizationCodeBearer` and `BearerJwtAuth` from `components.securitySchemes` — a large unrelated diff and a spec that misdescribes the API's auth. Do not "simplify" the `env` table out of the `[tool.poe.tasks.consumer-openapi]` entry, and do not rely on overriding it from your shell instead: the task's own `env` table is what sets it in the child process, independent of whatever `api/.env` or your shell currently has.

If they decline, say plainly that the spec is now stale and name the command they will need later. Do not ask again in the same run.

Then report what the agent verified and what you did. If the agent's response showed no lint output, or it claimed a pass without showing it, re-run the checks yourself rather than taking its word.

## Invoking the specialist

There is no task-type, version, or data-type question. The task type is clear from the request; v1 is the only mounted version (see the v2 note in the shared context); and the rbac dependency comes from the nearest comparable route, not from a data category.

If the request is to modify an existing endpoint, find it before invoking the agent. Do NOT use a hardcoded list of endpoints; enumerate what is served:

```bash
grep -E -A1 '@router\.(get|post|put|patch|delete)\(' api/consumer_api/v1/main.py | grep -oE '"/[^"]+"' | tr -d '"' | sort -u
```

- If the request names an endpoint in the enumeration, state which one you matched and proceed.
- Otherwise ask, deriving at most 4 options from the enumeration (group routes by first path segment and list a few real paths per group). Say the list is filtered so the user knows to use the built-in "Other".

`{TARGET}` = the matched endpoint path or group, or `none` for new work.

```
Agent({
  description: "Consumer API implementation",
  subagent_type: "consumer-api-implementation-specialist",
  prompt: "Implement the user's request in the Consumer API.

DEVELOPMENT CONTEXT:
- Target endpoint (when modifying): {TARGET}

{CONSUMER_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read before writing**: Enumerate the served routes, then read the nearest comparable endpoint in v1/main.py end to end — handler, models, and database operations — as a worked example. When modifying, locate the target route first; if it is not served, stop and report the routes that are rather than guessing.
2. **Classify against the versioning policy FIRST**: Before you edit, decide whether each part of the change is breaking, per the definition above — classifying afterwards means reconstructing the old response from memory. If it is breaking, implement it anyway and record it for the BREAKING CHANGES section; do not stop, and do not quietly substitute a non-breaking alternative for what was asked.
3. **Implement in v1**: Routes in v1/main.py with the auth dependency of the nearest comparable route, Pydantic models in v1/models.py, queries in v1/db.py, all following the existing patterns. List endpoints use the shared PaginatedResponse types rather than hand-rolled pagination.
4. **Create tests**: Add or update tests under consumer_api/tests/v1/ for every new or changed endpoint.
5. **Document**: Docstrings and OpenAPI documentation. Do NOT run `uv run poe consumer-openapi` yourself — it rewrites the committed openapi.json and bumps apiVersion, so the caller asks the user before regenerating. Say whether the spec needs regenerating; never hand-edit openapi.json.
6. **Update traceability**: Update the requirements documentation under consumer_api/requirements/.
7. **Close with the handoff**: End with the BREAKING CHANGES section described above.

The user's request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** above.
