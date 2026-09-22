---
name: develop-frontend
description: "Implement new or modify existing UI in the StudyBuilder frontend by leveraging the specialized Vue UI development agent. Scopes strictly to the frontend/ directory. Covers components, routed views, Pinia stores, routing, i18n, and frontend extensions."
---

# Develop Frontend

I'll help you with StudyBuilder frontend development by invoking the specialized Vue UI development agent. This agent will analyze your request, examine existing patterns, and implement the necessary changes following established conventions.

The user will provide a feature description after the slash command. I'll use that description as the task specification when invoking the vue-ui-developer.

`{USER_REQUEST}` = the user's description, verbatim, exactly as they typed it after the slash command. Every agent prompt below ends by substituting it — a prompt that says "the request follows" and then contains nothing leaves the agent with no task at all, so never send one without it. Do not paraphrase, summarise, or "clean up" the request: the agent needs the user's own wording, including any component names, route paths, or i18n keys they mentioned.

If the user invoked the skill with no description at all, do not guess and do not invoke an agent. Ask them what they want built, then continue.

## What this skill handles:

- Creating new Vue 3 components and routed views
- Modifying existing components, views, stores, and routes
- Pinia store work and reactivity fixes
- Routing, route metadata, and auth/feature-flag gating
- i18n translation keys
- Frontend extensions under `src/extensions/`
- Working with files in the `frontend/` directory

## Shared context

Define `{FRONTEND_CONTEXT}` once and substitute it verbatim into every agent prompt below:

```
The StudyBuilder frontend lives in `frontend/` — Vue 3 (Composition API), Vite, Vuetify 4, Pinia, npm. All paths below are relative to `frontend/` unless stated otherwise.

The authoritative conventions are in `frontend/CLAUDE.md` and the rule files it indexes, all under `frontend/.claude/rules/`:
`overview.md`, `architecture-core.md`, `commands.md`, `routing-auth.md`, `components.md`, `patterns.md`, `conventions-gotchas.md`.

Read the relevant ones before writing code. This prompt deliberately does not restate what they encode; they are the single source of truth and anything duplicated here would drift. If a rule file and this prompt disagree, the rule file wins.

In particular, do not carry in assumptions from other Vue projects about the i18n layout, the test setup, or how configuration reaches the running app. All three are documented and all three are easy to get wrong from habit — `components.md` for locale file layout, `commands.md` for what test runners actually exist, and `architecture-core.md` plus `conventions-gotchas.md` for runtime `public/config.json` versus build-time `.env.*`.

YOU CANNOT RUN COMMANDS. Your tool allowlist is Glob, Grep, Read, Write, Edit, WebFetch, WebSearch — there is no Bash. Do not claim to have run lint, formatting, a build, or tests. Instead, end your response with a short "Commands to run" section listing exactly what the caller should execute (normally `npm run format` and `npm run lint` from `frontend/`, plus a test command only if you added coverage).

Never assume a store, view, component, route, or extension exists because this prompt or a document mentions it. Enumerate before you rely on it — with the `Glob` tool, since you have no shell:

    Glob("frontend/src/views/**/*.vue")               # views, by section
    Glob("frontend/src/components/**/*.vue")          # components, by section
    Glob("frontend/src/stores/*.js")                  # stores
    Glob("frontend/src/extensions/*/router/index.js") # extensions that actually load

That last pattern is the discovery rule itself — `src/router/index.js` finds extensions with the same glob, so a directory it does not match is not a loaded extension no matter what else it contains.
```

## Task type

AskUserQuestion({
  questions: [{
    question: "What type of frontend development do you need?",
    header: "Task Type",
    options: [
      {
        label: "New component or view (Recommended)",
        description: "Create a new reusable component or a routed page view - I'll gather placement, section, and routing details"
      },
      {
        label: "Modify existing UI",
        description: "Update an existing component, view, or store - I'll identify the target and the modification details"
      },
      {
        label: "New frontend extension",
        description: "Create a self-contained extension under src/extensions/ with its own routes, views, stores, and locales"
      },
      {
        label: "Custom implementation",
        description: "Work directly with your provided task description for specific frontend requirements"
      }
    ],
    multiSelect: false
  }]
})

Match on the label PREFIX in every mapping below — the "(Recommended)" suffix may or may not be present.

Note on options: `AskUserQuestion` accepts a maximum of 4 options per question, and always offers the user an "Other" free-text choice automatically. Do not add an explicit "Other …" or "Custom …" option to any question below; it would waste a slot and duplicate the built-in escape hatch.

---

**If "New component or view" is selected:**

AskUserQuestion({
  questions: [{
    question: "Is this a reusable component or a routed page view?",
    header: "Kind",
    options: [
      {
        label: "Routed page view",
        description: "A page-level component in src/views/ reached by its own route - needs a router entry and route metadata"
      },
      {
        label: "Reusable component",
        description: "A component in src/components/ used by one or more views - no route of its own"
      }
    ],
    multiSelect: false
  }, {
    question: "Which section of the app does it belong to?",
    header: "Section",
    options: [
      {
        label: "Studies",
        description: "The /studies section - study-specific pages and components. Most require a selected study."
      },
      {
        label: "Library",
        description: "The /library section - reference data, codelists, templates, and activity definitions"
      },
      {
        label: "Administration",
        description: "The /administration section - admin-only pages, typically role-gated"
      },
      {
        label: "Shared or layout",
        description: "Cross-section UI not tied to one section - src/components/tools/ for most shared widgets, ui/ for low-level field wrappers, layout/ for app chrome"
      }
    ],
    multiSelect: false
  }]
})

`{UI_KIND}` = the selected kind label (or the user's "Other" text).
`{SECTION}` = the selected section label (or the user's "Other" text).

These four sections are hardcoded deliberately, unlike the extension and store lists below. They are architectural constants — the top-level route groups the router and the `app` store's section logic are built around — not a directory listing that churns. Still confirm against `ls frontend/src/views/` before placing files, and if the user's "Other" text names something not in that listing, ask rather than inventing a section.

Then invoke the Vue UI development agent:

```
Agent({
  description: "New frontend component or view",
  subagent_type: "vue-ui-developer",
  prompt: "I need help implementing new StudyBuilder frontend UI. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: New component or view
- Kind: {UI_KIND}
- Section: {SECTION}

{FRONTEND_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read before writing**: Enumerate the relevant directory, then read the nearest comparable component or view end to end as a worked example. Match it rather than importing conventions from outside this codebase.
2. **Place the file correctly**: Routed views go in src/views/<section>/ — that directory exists for studies, library, administration, and user. Components do NOT mirror those sections one-for-one: only src/components/studies/ and src/components/library/ exist. There is no components/administration/. Anything cross-section goes in src/components/tools/ (dialogs, charts, form fields, table helpers — the usual home for shared widgets), ui/ (low-level field wrappers), or layout/ (app chrome). Confirm the directory exists before writing to it rather than inferring it from the section name. Use PascalCase filenames and the `@/` path alias for imports.
   **Search src/components/tools/ before creating any shared widget.** It is large and flat, so what you need may already be there under a name you would not have guessed; see components.md.
3. **Use `<script setup>`**: All new components use the Composition API with `<script setup>` syntax.
4. **Wire up routing** (routed views only): Add the route in src/router/index.js. Take the full set of metadata keys and their semantics from `routing-auth.md` rather than from memory — several are easy to miss and two have non-obvious activation rules — then match how neighbouring routes in the same section are declared.
5. **Respect study context**: If the view or component is study-specific, check the selected study through the studies-general store before performing study-specific work, following the existing pattern.
6. **Externalize all user-facing strings**: Every visible string is referenced with $t()/t() and defined in the locale files described in components.md. Do not hardcode display text in templates.
7. **Follow the existing API call pattern**: Import the relevant module from src/api/, use async/await with loading and error state, and surface errors to the user.
8. **Report commands**: Close with the 'Commands to run' section described above.

The user's new UI request follows:

{USER_REQUEST}"
})
```

---

**If "Modify existing UI" is selected:**

Do NOT use a hardcoded list of components, views, or stores — there are far too many for a list written here to stay accurate. Enumerate first, scoped to what the user's description suggests:

```bash
ls frontend/src/views/ frontend/src/components/
ls frontend/src/stores/*.js | xargs -n1 basename | sed 's/\.js$//'
```

Then decide whether to ask at all:

- If the user's task description already names a file, component, view, or store that exists, skip the question. State what you matched and proceed.
- If the description names something that does NOT exist, say so and ask — do not silently substitute the nearest match.
- Otherwise ask, deriving the options from the enumeration and narrowing to what the description points at.
- `AskUserQuestion` caps options at 4. If more than 4 plausible targets are found, offer the 4 most likely given the user's description; the built-in "Other" choice covers the rest. Say in the question text that the list is filtered so the user knows to use "Other".

`{TARGET}` = the matched or selected file/component/store.

Then invoke the Vue UI development agent:

```
Agent({
  description: "Modify existing frontend UI",
  subagent_type: "vue-ui-developer",
  prompt: "I need help modifying existing StudyBuilder frontend UI. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Modify existing UI
- Target: {TARGET}
- Modification Type: Enhancement or bug fix to existing functionality

{FRONTEND_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Locate the target**: Find it and read it end to end, along with anything it imports that the change touches. If it does not exist, stop and report what you did find rather than guessing at a near-match.
2. **Trace the consumers before changing an interface**: If you are changing props, emits, exported store state, or actions, grep for usages first and update every call site. A component's props are a contract with the templates that use it.
3. **Follow existing patterns**: Match the surrounding code's style and structure rather than refactoring it to your own preference. If you believe the existing pattern is wrong, say so instead of silently changing it.
4. **Watch the reactivity traps**: Do not mutate store state directly from a component — go through actions. Do not destructure reactive store state without storeToRefs. Preserve ref/reactive boundaries.
5. **Keep strings externalized**: Any new user-facing string goes in the locale files described in components.md, not inline in the template.
6. **Scope the change**: Modify what the task requires. Do not reformat untouched code, and do not fix unrelated issues you notice — list them at the end instead.
7. **Report commands**: Close with the 'Commands to run' section described above.

The user's modification request follows:

{USER_REQUEST}"
})
```

---

**If "New frontend extension" is selected:**

The frontend has its own extension system, separate from the API's. Extensions are discovered at build time by `src/router/index.js` with:

    import.meta.glob('@/extensions/*/router/index.js', { eager: true })

and each matched module must export `addExtensionRoutes(routes)`. So a directory under `src/extensions/` is only a real extension if it contains `router/index.js` exporting that function. Enumerate the existing ones and read one as a worked example:

```bash
for d in frontend/src/extensions/*/; do n=$(basename "$d"); [ -f "${d}router/index.js" ] && echo "$n"; done
```

`frontend/src/extensions/README.md` documents the expected directory structure (`api/`, `locales/`, `router/`, `stores/`, `views/`). Read it before creating anything.

`{EXTENSION_NAME}` = the name the user gives for the new extension, or the existing one they want extended. If the user has not named it, ask.

Then invoke the Vue UI development agent:

```
Agent({
  description: "New frontend extension",
  subagent_type: "vue-ui-developer",
  prompt: "I need help implementing a new StudyBuilder frontend extension. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: New frontend extension
- Extension Name: {EXTENSION_NAME}

{FRONTEND_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read the spec first**: Read frontend/src/extensions/README.md, then read an existing extension end to end as a worked example.
2. **Satisfy the discovery rule**: The extension MUST contain router/index.js exporting `addExtensionRoutes(routes)`. Without both the file and the export it will be silently ignored at build time — no error, it simply will not load. Verify this before finishing.
3. **Create the directory structure**: Follow the README — api/, locales/, router/, stores/, views/ as needed. Do not invent a different layout.
4. **Keep it self-contained**: An extension exists so functionality can be added without modifying the core codebase. Do not edit files outside src/extensions/{EXTENSION_NAME}/ unless the task genuinely requires it, and call out any such edit explicitly.
5. **Provide its own translations**: Extensions carry their own locales/en/ files rather than adding keys to the core app.json.
6. **Set route metadata**: Give the extension's routes the same metadata treatment as core routes, using the key list in `routing-auth.md`.
7. **Report commands**: Close with the 'Commands to run' section described above.

The user's extension request follows:

{USER_REQUEST}"
})
```

---

**If "Custom implementation" is selected:**

Invoke the Vue UI development agent directly:

```
Agent({
  description: "Custom frontend implementation",
  subagent_type: "vue-ui-developer",
  prompt: "I need help with a custom StudyBuilder frontend implementation. Please analyze the user's request and implement the necessary changes following these guidelines:

DEVELOPMENT CONTEXT:
- Task: Custom implementation based on user's specific requirements
- Implementation Type: User-defined frontend task

{FRONTEND_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read before writing**: Enumerate and read the relevant parts of frontend/src/ before deciding on an approach.
2. **Follow conventions**: Match existing code style, naming conventions, and architectural patterns.
3. **Implement changes**: Create or modify components, views, stores, routes, and locales as needed.
4. **Keep strings externalized and config runtime-sourced**: No hardcoded user-facing text in templates, and no hardcoded API URLs. See `components.md` and `architecture-core.md` for where each belongs.
5. **Stay inside frontend/**: If the task turns out to need an API change, stop and say so — that is a different component with its own review path. Note the coupling rather than editing api/ from here.
6. **Report commands**: Close with the 'Commands to run' section described above.

The user's custom frontend development request follows:

{USER_REQUEST}"
})
```
