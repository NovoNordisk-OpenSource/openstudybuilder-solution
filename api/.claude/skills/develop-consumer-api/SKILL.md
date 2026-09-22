---
name: develop-consumer-api
description: "Implement new or update existing API endpoints in the Consumer API by leveraging the specialized Consumer API implementation agent."
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
- `api/consumer_api/shared/` — shared config and response types, including `PaginatedResponse` used by list endpoints.
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
        description: "Source and spec stay out of sync. Fine mid-task, but the PR is incomplete until someone runs `pipenv run consumer-openapi` — the spec is generated and must never be hand-edited."
      }
    ],
    multiSelect: false
  }]
})
```

If they agree, run it from `api/`:

```bash
pipenv run consumer-openapi
```

The Pipfile script pins `OAUTH_ENABLED=True`, which is load-bearing: that flag gates the OAuth2 security schemes, and generating with it off silently drops `OAuth2AuthorizationCodeBearer` and `BearerJwtAuth` from `components.securitySchemes` — a large unrelated diff and a spec that misdescribes the API's auth. Do not "simplify" the `env` prefix out of the Pipfile, and do not try to override it from your shell: pipenv loads `api/.env` over the inherited environment, so a shell assignment is silently discarded.

If they decline, say plainly that the spec is now stale and name the command they will need later. Do not ask again in the same run.

Then report what the agent verified and what you did. If the agent's response showed no lint output, or it claimed a pass without showing it, re-run the checks yourself rather than taking its word.

## Task type

AskUserQuestion({
  questions: [{
    question: "What type of Consumer API development do you need?",
    header: "Task Type",
    options: [
      {
        label: "New endpoint implementation (Recommended)",
        description: "Create a new API endpoint following Consumer API patterns - I'll gather endpoint details, authentication requirements, and response format"
      },
      {
        label: "Modify existing endpoint",
        description: "Update or enhance an existing Consumer API endpoint - I'll identify the endpoint and modification details"
      },
      {
        label: "Full feature implementation",
        description: "Complete feature with multiple endpoints, models, database operations, and tests"
      },
      {
        label: "Custom implementation",
        description: "Work directly with your provided task description for specific Consumer API requirements"
      }
    ],
    multiSelect: false
  }]
})

Match on the label PREFIX in every mapping below — the "(Recommended)" suffix may or may not be present.

Note on options: `AskUserQuestion` accepts a maximum of 4 options per question, and always offers the user an "Other" free-text choice automatically. Do not add an explicit "Other …" or "Custom …" option to any question below; it would waste a slot and duplicate the built-in escape hatch.

---

**If "New endpoint implementation" is selected:**

AskUserQuestion({
  questions: [{
    question: "Which Consumer API version should this endpoint be added to?",
    header: "API Version",
    options: [
      {
        label: "v1 (Recommended)",
        description: "Add to Consumer API v1 - the only version currently mounted and serving traffic. A brand-new endpoint path is additive, so it belongs here."
      },
      {
        label: "v2 (requires activation first)",
        description: "v2 is an inactive placeholder - main.py is fully commented out and its router is not mounted. Choosing this means activating v2 before any endpoint work can begin."
      }
    ],
    multiSelect: false
  }, {
    question: "What type of data will this endpoint provide?",
    header: "Data Type",
    options: [
      {
        label: "Study data",
        description: "Study-related information (visits, activities, SoA, versions) - requires rbac.STUDY_READ"
      },
      {
        label: "Library data",
        description: "Library activities, codelists, projects, unit definitions - requires rbac.LIBRARY_READ"
      },
      {
        label: "Papillons data",
        description: "Papillons SoA and study metadata endpoints"
      },
      {
        label: "Audit data",
        description: "Audit trail or tracking information - typically requires rbac.STUDY_READ"
      }
    ],
    multiSelect: false
  }]
})

`{API_VERSION}` = `v1`, or `v2` if the user selected the activation option (or their "Other" text).
`{DATA_TYPE}` = the selected data-type label (or the user's "Other" text).

Do not infer the rbac dependency from `{DATA_TYPE}` alone. Confirm it against the auth dependency used by the nearest comparable route in `v1/main.py`.

Then invoke the Consumer API implementation specialist:

```
Agent({
  description: "New Consumer API endpoint implementation",
  subagent_type: "consumer-api-implementation-specialist",
  prompt: "I need help implementing a new Consumer API endpoint. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: New endpoint implementation
- API Version: {API_VERSION}
- Data Type: {DATA_TYPE}

{CONSUMER_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read before writing**: Enumerate the served routes, then read the nearest comparable endpoint in v1/main.py end to end as a worked example.
2. **Implement endpoint**: Create the new endpoint in the {API_VERSION} directory, matching the surrounding route's structure and auth dependency.
3. **Create models**: Define Pydantic request/response models in that version's models.py.
4. **Add database operations**: Implement queries in that version's db.py following existing patterns.
5. **Paginate list endpoints**: Use the shared PaginatedResponse type rather than hand-rolling pagination.
6. **Create tests**: Generate test files under consumer_api/tests/{API_VERSION}/.
7. **Document endpoint**: Ensure proper OpenAPI documentation and docstrings. Do NOT run `pipenv run consumer-openapi` yourself — it rewrites the committed openapi.json and bumps apiVersion, so the caller asks the user before regenerating. Just say whether the spec needs regenerating; never hand-edit openapi.json.
8. **Update traceability**: Update the requirements documentation under consumer_api/requirements/.

The user's Consumer API endpoint request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** above.

---

**If "Modify existing endpoint" is selected:**

Do NOT use a hardcoded list of endpoints — it goes stale. Enumerate what is actually served first:

```bash
grep -E -A1 '@router\.(get|post|put|patch|delete)\(' api/consumer_api/v1/main.py | grep -oE '"/[^"]+"' | tr -d '"' | sort -u
```

Then decide whether to ask at all:

- If the user's task description already names an endpoint that appears in the enumeration, skip the question. State which endpoint you matched and proceed.
- Otherwise ask, deriving the options from the enumeration — group the routes by their first path segment and offer one option per group, listing a few real paths from that group in the description.
- `AskUserQuestion` caps options at 4. If more than 4 groups are found, offer the 4 most plausible given the user's description; the built-in "Other" choice covers the rest. Say in the question text that the list is filtered so the user knows to use "Other".

`{TARGET_ENDPOINT}` = the matched or selected endpoint path, or the group name if the user picked a group.

Then invoke the Consumer API implementation specialist:

```
Agent({
  description: "Modify existing Consumer API endpoint",
  subagent_type: "consumer-api-implementation-specialist",
  prompt: "I need help modifying an existing Consumer API endpoint. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Modify existing endpoint
- Target: {TARGET_ENDPOINT}
- Modification Type: Enhancement or bug fix to existing functionality

{CONSUMER_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Locate the target**: Find the route in v1/main.py and read its handler, models, and database operations. If it is not in the enumeration, stop and report the routes that are actually served rather than guessing.
2. **Classify the change against the versioning policy FIRST**: Decide whether the requested change is breaking, per the definition above. Do this before you edit, not after — classifying it afterwards means reconstructing what the old response looked like from memory. If it is breaking, implement it anyway and record it for the BREAKING CHANGES section; do not stop, and do not quietly substitute a non-breaking alternative for what was asked.
3. **Follow existing patterns**: Match the surrounding code's style and structure.
4. **Implement changes**: Modify the endpoint, models, and/or database operations as needed.
5. **Update tests**: Modify or add test files under consumer_api/tests/ for the changed functionality.
6. **Document changes**: Update OpenAPI documentation and docstrings. Do NOT run `pipenv run consumer-openapi` yourself — it rewrites the committed openapi.json and bumps apiVersion, so the caller asks the user before regenerating. Just say whether the spec needs regenerating; never hand-edit openapi.json.
7. **Update traceability**: Update the requirements documentation under consumer_api/requirements/.

The user's endpoint modification request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** above.

---

**If "Full feature implementation" is selected:**

AskUserQuestion({
  questions: [{
    question: "What is the scope of this Consumer API feature?",
    header: "Feature Scope",
    options: [
      {
        label: "Complete new domain",
        description: "New subject area with multiple related endpoints, models, and database operations"
      },
      {
        label: "Extension of existing domain",
        description: "Add capabilities to existing Consumer API areas (studies, library, papillons)"
      },
      {
        label: "Cross-cutting feature",
        description: "Feature that spans multiple domains (e.g., new filtering, export formats)"
      }
    ],
    multiSelect: false
  }]
})

`{FEATURE_SCOPE}` = the selected scope label (or the user's "Other" text).

Then invoke the Consumer API implementation specialist:

```
Agent({
  description: "Full Consumer API feature implementation",
  subagent_type: "consumer-api-implementation-specialist",
  prompt: "I need help implementing a complete Consumer API feature. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Full feature implementation
- Feature Scope: {FEATURE_SCOPE}
- Implementation Type: Complete feature with multiple components

{CONSUMER_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Design feature architecture**: Plan the complete feature structure within Consumer API patterns before writing code.
2. **Read before writing**: Enumerate the served routes, then read the closest existing feature end to end as a worked example.
3. **Check the versioning policy**: Identify any part of the feature that breaks an existing endpoint, per the definition above. Breaking parts are allowed — implement them, and record each one for the BREAKING CHANGES section rather than halting.
4. **Implement endpoints**: Create the related endpoints in the appropriate version directory.
5. **Create comprehensive models and queries**: Define all necessary Pydantic models and database operations following existing patterns.
6. **Paginate list endpoints**: Use the shared PaginatedResponse type consistently.
7. **Create comprehensive tests**: Generate a test suite covering every new endpoint.
8. **Document feature**: Ensure proper OpenAPI documentation. Do NOT run `pipenv run consumer-openapi` yourself — just report that the spec needs regenerating; the caller asks the user before doing it.
9. **Update traceability**: Create or update requirements documentation for the complete feature.

The user's full feature request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** above.

---

**If "Custom implementation" is selected:**

Invoke the Consumer API implementation specialist directly:

```
Agent({
  description: "Custom Consumer API implementation",
  subagent_type: "consumer-api-implementation-specialist",
  prompt: "I need help with a custom Consumer API implementation. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Custom implementation based on user's specific requirements
- Implementation Type: User-defined Consumer API task

{CONSUMER_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read before writing**: Enumerate the served routes and read the relevant parts of consumer_api/ before deciding on an approach.
2. **Check the versioning policy**: Determine whether the work breaks an existing endpoint, per the definition above. If it does, implement it and record it for the BREAKING CHANGES section rather than halting.
3. **Follow conventions**: Match existing code style, naming conventions, and architectural patterns.
4. **Implement changes**: Create or modify endpoints, models, and database operations as needed.
5. **Create tests**: Generate appropriate test files under consumer_api/tests/.
6. **Document changes**: Ensure proper OpenAPI documentation and comments. Do NOT run `pipenv run consumer-openapi` yourself — if any route changed, just report that the spec needs regenerating; the caller asks the user before doing it.
7. **Update traceability**: Update requirements and traceability matrices under consumer_api/requirements/ to reflect the changes.

The user's custom Consumer API development request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** above.
