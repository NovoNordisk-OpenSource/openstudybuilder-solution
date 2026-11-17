---
name: osb-develop-frontend
description: "Use when adding or changing UI in the StudyBuilder frontend (frontend/) — components, routed views, Pinia stores, routing, i18n, or frontend extensions. For API changes use /osb-develop-main-api."
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
The StudyBuilder frontend lives in `frontend/` — Vue 3 (Composition API), Vite, Vuetify 4, Pinia, npm. All file paths below are relative to the REPO ROOT: a bare `src/…` reference means `frontend/src/…`, so prefix it before you Read, Glob, or Grep. Commands marked "from `frontend/`" are the exception — that is process working directory, not a path.

The authoritative conventions are in `frontend/AGENTS.md` and the rule files it indexes, all under `frontend/.claude/rules/`:
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

## Invoking the specialist

There is no task-type question. Infer from the request which of these it is — new component or view, change to existing UI, new frontend extension — and state your reading in one line before invoking the agent. Ask only for the details below that the request leaves open.

**New component or view.** If the request does not make it clear, ask whether it is a routed page view (`src/views/`, needs a route) or a reusable component (`src/components/`), and which section it belongs to: Studies, Library, Administration, or Shared/layout. These four sections are hardcoded deliberately, unlike the lists below: they are architectural constants — the top-level route groups the router and the `app` store's section logic are built around — not a directory listing that churns. Still confirm against `ls frontend/src/views/` before placing files, and if the user's "Other" text names something not in that listing, ask rather than inventing a section.

**Change to existing UI.** Do NOT use a hardcoded list of components, views, or stores. Enumerate, scoped to what the request suggests:

```bash
ls frontend/src/views/ frontend/src/components/
ls frontend/src/stores/*.js | xargs -n1 basename | sed 's/\.js$//'
```

If the request names something that exists, state what you matched. If it names something that does NOT exist, say so and ask — do not silently substitute the nearest match. Otherwise ask with at most 4 plausible targets from the enumeration, and say the list is filtered so the user knows to use the built-in "Other".

**New frontend extension.** Extensions are discovered at build time by `src/router/index.js` with `import.meta.glob('@/extensions/*/router/index.js', { eager: true })`, and each matched module must export `addExtensionRoutes(routes)`. Enumerate the existing ones:

```bash
for d in frontend/src/extensions/*/; do n=$(basename "$d"); [ -f "${d}router/index.js" ] && echo "$n"; done
```

If the user has not named the new extension, ask.

`{TASK}` = new component/view, change to existing UI, or new frontend extension. `{DETAILS}` = whatever you settled above: kind and section, the matched target, or the extension name.

```
Agent({
  description: "Frontend implementation",
  subagent_type: "vue-ui-developer",
  prompt: "Implement the user's request in the StudyBuilder frontend.

DEVELOPMENT CONTEXT:
- Task: {TASK}
- Details: {DETAILS}

{FRONTEND_CONTEXT}

IMPLEMENTATION REQUIREMENTS:
1. **Read before writing**: Enumerate the relevant directory, then read the nearest comparable component, view, or extension end to end as a worked example, and match it rather than importing conventions from outside this codebase. When changing existing UI, read the target and anything it imports that the change touches; if it does not exist, stop and report what you did find rather than guessing at a near-match.
2. **Place files correctly**: Routed views go in src/views/<section>/ — that directory exists for studies, library, administration, and user. Components do NOT mirror those sections one-for-one: only src/components/studies/ and src/components/library/ exist. There is no components/administration/. Anything cross-section goes in src/components/tools/ (dialogs, charts, form fields, table helpers — the usual home for shared widgets), ui/ (low-level field wrappers), or layout/ (app chrome). Confirm the directory exists before writing to it. Use PascalCase filenames and the `@/` path alias for imports. **Search src/components/tools/ before creating any shared widget** — it is large and flat; see components.md.
3. **Use `<script setup>`**: All new components use the Composition API with `<script setup>` syntax.
4. **Wire up routing** (routed views and extensions): Take the full set of route metadata keys and their semantics from `routing-auth.md` rather than from memory, then match how neighbouring routes in the same section are declared.
5. **Extensions**: Read frontend/src/extensions/README.md first and follow its layout (api/, locales/, router/, stores/, views/). The extension MUST contain router/index.js exporting `addExtensionRoutes(routes)` — without both it is silently ignored at build time. Keep it self-contained: do not edit files outside src/extensions/<name>/ unless genuinely required, and call out any such edit. Extensions carry their own locales/en/ files rather than adding keys to the core app.json.
6. **Trace consumers before changing an interface**: If you change props, emits, exported store state, or actions, grep for usages first and update every call site.
7. **Watch the reactivity traps**: Do not mutate store state directly from a component — go through actions. Do not destructure reactive store state without storeToRefs. Preserve ref/reactive boundaries. If the UI is study-specific, check the selected study through the studies-general store first, following the existing pattern.
8. **Externalize strings and config**: Every visible string uses $t()/t() and lives in the locale files described in components.md. No hardcoded API URLs — see architecture-core.md. Follow the existing src/api/ call pattern: async/await with loading and error state, errors surfaced to the user.
9. **Scope the change**: Modify what the task requires. Do not reformat untouched code or fix unrelated issues — list them at the end instead. If you believe an existing pattern is wrong, say so instead of silently changing it. If the task needs an API change, stop and say so rather than editing api/.
10. **Report commands**: Close with the 'Commands to run' section described above.

The user's request follows:

{USER_REQUEST}"
})
```

When the agent returns, follow **## After the agent returns** below.

## After the agent returns

The agent has no Bash, so nothing has been formatted or linted yet. Run from `frontend/`:

```bash
npm run format
npm run lint     # eslint --fix
```

Also run any test command the agent listed under "Commands to run".

- If a check fails in a file the agent changed, fix it yourself or resume the agent with the error output, then re-run the check. Stop after two rounds on the same failure and report it.
- If a failure sits in a file the agent never touched, it is pre-existing: report it separately and do not fix it here.
- Report plainly what ran and what passed. Never claim a check passed that you did not run.
