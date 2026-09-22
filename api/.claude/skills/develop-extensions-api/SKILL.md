---
name: develop-extensions-api
description: "Implement new or update existing API endpoints in the Extensions API by leveraging the specialized Extensions API implementation agent."
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
```

## After the agent returns

The specialist runs its own fast checks (format, lint, sblint) and reports what it ran. It is explicitly barred from regenerating the OpenAPI spec, because that is not a check — it rewrites the committed `extensions/openapi.json` and bumps `extensions/apiVersion`. That belongs to the user, not to an agent acting on its own initiative.

Use the agent's report to decide whether the spec is even affected:

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
        description: "Source and spec stay out of sync. Fine mid-task, but the PR is incomplete until someone runs `pipenv run extensions-openapi` — the spec is generated and must never be hand-edited."
      }
    ],
    multiSelect: false
  }]
})
```

If they agree, run it from `api/`:

```bash
pipenv run extensions-openapi
```

The Pipfile script pins `OAUTH_ENABLED=True`, which is load-bearing: that flag gates the OAuth2 security schemes, and generating with it off silently drops `OAuth2AuthorizationCodeBearer` and `BearerJwtAuth` from `components.securitySchemes` — a large unrelated diff and a spec that misdescribes the API's auth. Do not "simplify" the `env` prefix out of the Pipfile, and do not try to override it from your shell: pipenv loads `api/.env` over the inherited environment, so a shell assignment is silently discarded.

If they decline, say plainly that the spec is now stale and name the command they will need later. Do not ask again in the same run.

Then report what the agent verified and what you did. If the agent's response showed no lint output, or it claimed a pass without showing it, re-run the checks yourself rather than taking its word.

## Task type

AskUserQuestion({
  questions: [{
    question: "What type of Extensions API development do you need?",
    header: "Task Type",
    options: [
      {
        label: "New extension implementation (Recommended)",
        description: "Create a complete new extension following Extensions API patterns - I'll gather extension details, functionality requirements, and authentication needs"
      },
      {
        label: "Modify existing extension",
        description: "Update or enhance an existing extension - I'll identify the target extension and modification details"
      },
      {
        label: "Full feature implementation",
        description: "Complex feature spanning multiple extensions or significant extension enhancements"
      },
      {
        label: "Custom implementation",
        description: "Work directly with your provided task description for specific Extensions API requirements"
      }
    ],
    multiSelect: false
  }]
})

Match on the label PREFIX in every mapping below — the "(Recommended)" suffix may or may not be present.

Note on options: `AskUserQuestion` accepts a maximum of 4 options per question, and always offers the user an "Other" free-text choice automatically. Do not add an explicit "Custom …" option to any question below; it would waste a slot and duplicate the built-in escape hatch.

---

**If "New extension implementation" is selected:**

AskUserQuestion({
  questions: [{
    question: "What type of functionality will this extension provide?",
    header: "Extension Type",
    options: [
      {
        label: "Data processing",
        description: "Process, transform, or analyze data - typically includes Neo4j database operations and business logic"
      },
      {
        label: "Integration",
        description: "Connect with external APIs or services - includes an external client and its configuration"
      },
      {
        label: "Reporting or export",
        description: "Generate reports, exports, or data visualizations - may include file generation"
      },
      {
        label: "System utility",
        description: "System monitoring, health checks, or administrative functions"
      }
    ],
    multiSelect: false
  }, {
    question: "What level of access control does this extension need?",
    header: "Authentication",
    options: [
      {
        label: "Admin access required",
        description: "Requires rbac.ADMIN_READ or rbac.ADMIN_WRITE - for administrative functions"
      },
      {
        label: "Study data access",
        description: "Requires rbac.STUDY_READ - for accessing study-related data"
      },
      {
        label: "Library data access",
        description: "Requires rbac.LIBRARY_READ - for accessing library/reference data"
      },
      {
        label: "Public access",
        description: "Only requires the basic security dependency - no specific role needed"
      }
    ],
    multiSelect: false
  }]
})

`{EXTENSION_TYPE}` = the selected functionality label (or the user's "Other" text).
`{AUTH_LEVEL}` = the selected access-control label (or the user's "Other" text).

Then invoke the Extensions API implementation specialist:

```
Agent({
  description: "New Extensions API extension implementation",
  subagent_type: "extensions-api-implementation-specialist",
  prompt: "I need help implementing a new Extensions API extension. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: New extension implementation
- Extension Type: {EXTENSION_TYPE}
- Authentication: {AUTH_LEVEL}
- Implementation Pattern: Complete new extension with proper structure

{EXTENSIONS_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read the spec first**: Read api/extensions/README.md, then read one existing extension end to end as a worked example.
2. **Create extension structure**: Set up the directory exactly as the README specifies.
3. **Implement router**: Create the APIRouter with authentication dependencies matching {AUTH_LEVEL}.
4. **Add models**: Define Pydantic request/response models in models.py if needed.
5. **Add database operations**: Implement db.py for Neo4j operations if the extension needs persistence.
6. **Create comprehensive tests**: Generate a test suite in the extension's tests/ subdirectory.
7. **Document extension**: Ensure proper OpenAPI documentation and endpoint docstrings.
8. **Verify discoverability**: Confirm the new extension satisfies the discovery rule in extensions_api.py.

The user's new extension request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** above.

---

**If "Modify existing extension" is selected:**

Do NOT use a hardcoded list of extensions — it goes stale. Discover them first:

```bash
for d in api/extensions/*/; do n=$(basename "$d"); [ -f "$d${n}_main.py" ] && echo "$n"; done
```

Then decide whether to ask at all:

- If the user's task description already names one of the discovered extensions unambiguously, skip the question. State which extension you inferred and proceed.
- Otherwise ask, building the options from the command's output — one option per discovered extension, labelled with its name. For each description, read the first line of that extension's `{name}_main.py` docstring, or its router prefix if there is no docstring.
- `AskUserQuestion` caps options at 4. If more than 4 extensions are discovered, offer the 4 most plausible given the user's description; the built-in "Other" choice covers the rest. Say in the question text that the list is filtered so the user knows to use "Other".

`{TARGET_EXTENSION}` = the inferred or selected extension name.

Then invoke the Extensions API implementation specialist:

```
Agent({
  description: "Modify existing Extensions API extension",
  subagent_type: "extensions-api-implementation-specialist",
  prompt: "I need help modifying an existing Extensions API extension. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Modify existing extension
- Target Extension: {TARGET_EXTENSION}
- Modification Type: Enhancement or update to existing functionality

{EXTENSIONS_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Locate the target**: Find api/extensions/{TARGET_EXTENSION}/ and read its main file, models, and database operations. If that directory does not exist, stop and report the discovered extension names rather than guessing.
2. **Follow existing patterns**: Match the surrounding code's style and structure rather than importing conventions from elsewhere.
3. **Implement changes**: Modify router endpoints, models, and/or database operations as needed.
4. **Update tests**: Modify or add test files in the extension's tests/ subdirectory.
5. **Document changes**: Update OpenAPI documentation and docstrings.
6. **Preserve contracts**: Keep the extension discoverable and do not break its existing endpoints unless the user explicitly asked for a breaking change.

The user's extension modification request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** above.

---

**If "Full feature implementation" is selected:**

AskUserQuestion({
  questions: [{
    question: "What is the scope of this Extensions API feature?",
    header: "Feature Scope",
    options: [
      {
        label: "Multi-extension feature",
        description: "Feature that requires multiple coordinated extensions working together"
      },
      {
        label: "Major extension enhancement",
        description: "Significant expansion of an existing extension with multiple new capabilities"
      },
      {
        label: "Cross-cutting functionality",
        description: "Feature that adds capabilities across multiple existing extensions"
      }
    ],
    multiSelect: false
  }]
})

`{FEATURE_SCOPE}` = the selected scope label (or the user's "Other" text).

Then invoke the Extensions API implementation specialist:

```
Agent({
  description: "Full Extensions API feature implementation",
  subagent_type: "extensions-api-implementation-specialist",
  prompt: "I need help implementing a complete Extensions API feature. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Full feature implementation
- Feature Scope: {FEATURE_SCOPE}
- Implementation Type: Comprehensive feature with multiple components

{EXTENSIONS_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Design feature architecture**: Plan the complete feature structure within Extensions API patterns before writing code.
2. **Read the spec and survey what exists**: Read api/extensions/README.md, then enumerate and read the extensions this feature will touch.
3. **Implement extensions**: Create or modify extensions as needed for the feature.
4. **Ensure coordination**: If the feature spans multiple extensions, make the boundaries between them explicit rather than implicit.
5. **Create comprehensive tests**: Generate a test suite covering the whole feature, including interactions between extensions.
6. **Document feature**: Ensure proper OpenAPI documentation for all new endpoints.
7. **Verify discoverability**: Confirm every new or renamed extension still satisfies the discovery rule in extensions_api.py.

The user's full feature request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** above.

---

**If "Custom implementation" is selected:**

Invoke the Extensions API implementation specialist directly:

```
Agent({
  description: "Custom Extensions API implementation",
  subagent_type: "extensions-api-implementation-specialist",
  prompt: "I need help with a custom Extensions API implementation. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Custom implementation based on user's specific requirements
- Implementation Type: User-defined Extensions API task

{EXTENSIONS_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read the spec first**: Read api/extensions/README.md and enumerate the existing extensions before deciding on an approach.
2. **Follow conventions**: Match existing code style, naming conventions, and architectural patterns.
3. **Implement changes**: Create or modify extensions, routers, and related code as needed.
4. **Create tests**: Generate appropriate test files in each affected extension's tests/ subdirectory.
5. **Document changes**: Ensure proper OpenAPI documentation and comments where needed.
6. **Verify discoverability**: Confirm anything created or renamed still satisfies the discovery rule in extensions_api.py.

The user's custom Extensions API development request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** above.
