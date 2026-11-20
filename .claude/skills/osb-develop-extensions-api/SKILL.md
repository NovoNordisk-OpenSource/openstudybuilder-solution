---
name: osb-develop-extensions-api
description: "Use when creating a new extension or changing an existing one in the Extensions API (api/extensions/, port 8009). For the main API use /osb-develop-main-api; for api/consumer_api/ use /osb-develop-consumer-api."
---

# Develop Extensions API

I'll help you with Extensions API development by invoking the specialized Extensions API implementation agent. This agent will analyze your request, examine existing patterns, and implement the necessary changes following established conventions.

The user will provide a feature description after the slash command. I'll use that description as the task specification when invoking the extensions-api-implementation-specialist.

`{USER_REQUEST}` = the user's description, verbatim, exactly as they typed it after the slash command. Every agent prompt below ends by substituting it — a prompt that says "the request follows" and then contains nothing leaves the agent with no task at all, so never send one without it. Do not paraphrase, summarise, or "clean up" the request: the agent needs the user's own wording, including any file paths, field names, or extension names they mentioned.

If the user invoked the skill with no description at all, do not guess and do not invoke an agent. Ask them what they want built, then continue.

## What this skill handles:

- Implementing new Extensions API extensions
- Updating or modifying existing Extensions API extensions
- Creating tests for Extensions API functionality
- Following Extensions API patterns and conventions
- Working with files in the `api/extensions/` directory
- Setting up new extension directory structures

## Shared context

Define `{EXTENSIONS_CONTEXT}` once and substitute it verbatim into every agent prompt below:

```
The Extensions API lives in `api/extensions/` and runs on port 8009. Each extension is a self-contained module with its own router, and optionally its own models, database operations, and tests.

`api/extensions/README.md` is the authoritative specification for extension structure: the `{extension_name}_main.py` naming rule, `__init__.py` placement, the shared utilities in `extensions/common.py`, authentication via rbac and security dependencies, and how `extensions_api.py` discovers and mounts extensions. Read it before writing any code and follow it exactly.

This prompt deliberately does not restate those rules. The README is the single source of truth; anything repeated here would drift out of date. If the README and this prompt ever disagree, the README wins.

The README uses `my_extension` as an illustrative placeholder — it is documentation, not an extension on disk. Never assume a directory exists because the README names it. Enumerate the real ones with:

    for d in api/extensions/*/; do n=$(basename "$d"); [ -f "$d${n}_main.py" ] && echo "$n"; done

That mirrors the discovery rule in `extensions_api.py` (a directory counts as an extension only if it contains `{name}_main.py`), so it will not report build-artifact or shared-test directories.

Of what it does report, use `hello` and `system` as reference patterns. Treat anything else it reports as internal and off-limits: do not copy its structure as an example, and do not modify it unless the user names it explicitly.

What the caller needs from you, as the last section of your response:
- **CHANGED FILES**: every file you created or modified, one repo-relative path per line.
- **ROUTES TOUCHED**: whether you added, removed, or changed any route, response model, or endpoint docstring — this decides whether extensions/openapi.json must be regenerated.
```

## After the agent returns

The specialist runs its own fast checks (format, lint, sblint) and reports what it ran. It is explicitly barred from regenerating the OpenAPI spec, because that is not a check — it rewrites the committed `extensions/openapi.json` and bumps `extensions/apiVersion`. That belongs to the user, not to an agent acting on its own initiative.

Use the agent's ROUTES TOUCHED report to decide whether the spec is even affected. If it did not provide one, derive it from CHANGED FILES (or `git status --porcelain` under `api/extensions/`): any `*_main.py`, router, or `models.py` change is route-facing; changes confined to `db.py` or `tests/` are not.

- **No route, response model, or endpoint docstring changed** → do not ask. Say the spec is unaffected and move on.
- **Something route-facing changed** → ask, exactly once:

```
AskUserQuestion({
  questions: [{
    question: "This change touches the API surface, so extensions/openapi.json is now out of date. Regenerate it?",
    header: "OpenAPI",
    options: [
      {
        label: "Yes, regenerate now (Recommended)",
        description: "Regenerates with OAUTH_ENABLED=True. Rewrites extensions/openapi.json and bumps extensions/apiVersion."
      },
      {
        label: "No, leave it for now",
        description: "Source and spec stay out of sync. Fine mid-task, but the PR is incomplete until someone runs `uv run poe extensions-openapi` — the spec is generated and must never be hand-edited."
      }
    ],
    multiSelect: false
  }]
})
```

If they agree, run it from `api/`:

```bash
uv run poe extensions-openapi
```

The poe task pins `OAUTH_ENABLED=True` via its `env` table in `pyproject.toml`, which is load-bearing: that flag gates the OAuth2 security schemes, and generating with it off silently drops `OAuth2AuthorizationCodeBearer` and `BearerJwtAuth` from `components.securitySchemes` — a large unrelated diff and a spec that misdescribes the API's auth. Do not "simplify" the `env` table out of the `[tool.poe.tasks.extensions-openapi]` entry, and do not rely on overriding it from your shell instead: the task's own `env` table is what sets it in the child process, independent of whatever `api/.env` or your shell currently has.

If they decline, say plainly that the spec is now stale and name the command they will need later. Do not ask again in the same run.

Then report what the agent verified and what you did. If the agent's response showed no lint output, or it claimed a pass without showing it, re-run the checks yourself rather than taking its word.

## Invoking the specialist

There is no task-type, extension-type, or feature-scope question. Whether this is a new extension, a modification, or a multi-extension feature is clear from the request, and the specialist reads the README and the existing extensions to settle structure.

**Target.** Discover the extensions (do NOT use a hardcoded list):

```bash
for d in api/extensions/*/; do n=$(basename "$d"); [ -f "$d${n}_main.py" ] && echo "$n"; done
```

- If the request names a discovered extension, or is clearly a new one, state which and proceed.
- Otherwise ask, one option per plausible extension (at most 4; describe each by the first line of its `{name}_main.py` docstring or its router prefix). Say the list is filtered so the user knows to use the built-in "Other".

`{TARGET}` = the extension name(s), or `new: <name>` for a new extension.

**Access level — new extensions only.** If the request creates a new extension and does not state who may call it, ask:

```
AskUserQuestion({
  questions: [{
    question: "What level of access control does this extension need?",
    header: "Authentication",
    options: [
      { label: "Admin access required", description: "Requires rbac.ADMIN_READ or rbac.ADMIN_WRITE - for administrative functions" },
      { label: "Study data access", description: "Requires rbac.STUDY_READ - for accessing study-related data" },
      { label: "Library data access", description: "Requires rbac.LIBRARY_READ - for accessing library/reference data" },
      { label: "Public access", description: "Only requires the basic security dependency - no specific role needed" }
    ],
    multiSelect: false
  }]
})
```

`{AUTH_LEVEL}` = the selected label (or the user's "Other" text); the access level the request states; or, when modifying, `match the extension's existing routes`.

```
Agent({
  description: "Extensions API implementation",
  subagent_type: "extensions-api-implementation-specialist",
  prompt: "Implement the user's request in the Extensions API.

DEVELOPMENT CONTEXT:
- Target: {TARGET}
- Authentication: {AUTH_LEVEL}

{EXTENSIONS_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read the spec first**: Read api/extensions/README.md, then read hello or system end to end as a worked example. When modifying, read the target extension's main file, models, and database operations; if its directory does not exist, stop and report the discovered extension names rather than guessing.
2. **Structure**: For a new extension, set up the directory exactly as the README specifies. For an existing one, match its own layout rather than importing conventions from elsewhere. If the work spans several extensions, make the boundaries between them explicit.
3. **Router and auth**: APIRouter with the security dependency plus the rbac constant matching {AUTH_LEVEL}.
4. **Models and persistence**: Pydantic models in models.py and Neo4j operations in db.py, only where needed.
5. **Create tests**: Add or update tests in each affected extension's tests/ subdirectory.
6. **Document**: OpenAPI documentation and endpoint docstrings. Do not run `uv run poe extensions-openapi` and never hand-edit extensions/openapi.json.
7. **Preserve contracts**: Every new or renamed extension must satisfy the discovery rule in extensions_api.py. Do not break existing endpoints unless the user explicitly asked for a breaking change.
8. **Close with the handoff**: End with CHANGED FILES and ROUTES TOUCHED as described above.

The user's request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** above.
