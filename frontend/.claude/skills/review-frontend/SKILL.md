---
name: review-frontend
description: "Conducts a comprehensive code review of the current branch's frontend changes against the remote origin/main branch using the specialized code-reviewer-frontend agent. Scopes strictly to the frontend/ directory. Validates Vue 3 and Vuetify 4 architecture, component and composable patterns, routing and auth, i18n, and project conventions."
---

# Code Review Frontend

I'll perform a comprehensive review of the frontend changes against the remote origin/main branch. First, let me ask what you'd like to review.

Use AskUserQuestion to present these options:

AskUserQuestion({
  questions: [{
    question: "What would you like me to review against remote origin/main?",
    header: "Review Scope",
    options: [
      {
        label: "Current uncommitted changes (Recommended)",
        description: "Review ONLY staged/unstaged/untracked changes vs HEAD - ideal pre-commit validation. Already-committed work is excluded."
      },
      {
        label: "Latest committed version",
        description: "Review ONLY commits on this branch ahead of origin/main - ideal pre-PR validation. Working-tree/untracked changes are excluded."
      }
    ],
    multiSelect: false
  }]
})

## Building the prompt

Map the scope selection to a single scope token by matching on the label PREFIX (the "(Recommended)" suffix may or may not be present depending on which option was tagged recommended):

- Selected label starts with **"Current uncommitted changes"** → `{SCOPE}` = `uncommitted`
- Selected label starts with **"Latest committed version"** → `{SCOPE}` = `committed`

Also pick a scope-specific focus phrase:

- `uncommitted` → `{FOCUS}` = `pre-commit validation — ensuring changes are ready for commit and follow all project standards`
- `committed` → `{FOCUS}` = `pre-PR validation — ensuring the committed changes are ready for pull request and follow all project standards`

The area is fixed to `frontend/` — this skill does not ask an area question. Unlike `api/`, which contains three separately-deployed apps, the frontend is a single application with no equivalent internal boundary worth splitting on.

## Final agent invocation

Invoke the code-reviewer-frontend agent with the assembled prompt. Substitute `{SCOPE}` and `{FOCUS}` as described above.

```
Agent({
  description: "Frontend code review against origin/main",
  subagent_type: "code-reviewer-frontend",
  prompt: "Please conduct a comprehensive code review of the current branch's frontend changes against remote origin/main.

**Scope (set by the caller — strictly one, never both):** `{SCOPE}`
**Area (fixed for this skill):** the frontend/ directory

**MANDATORY PROTOCOL — follow before any other work:**

Use the `Read` tool to open `.claude/skills/branch-change-detection/SKILL.md`. **That path is relative to the monorepo root, not to this skill's own directory.** It is a shared helper that the api and frontend skills all delegate to; there is no per-component copy under `frontend/.claude/` or `api/.claude/`. If the Read fails, STOP and report it — do NOT substitute your own git commands, because the scope guards in that file are the whole point of the protocol.

Follow its protocol EXACTLY for the `{SCOPE}` scope. That file defines:

- the `git fetch origin main` refresh step
- the guard command that must run first and the exact abort message to emit if the scope is empty
- the allowed enumeration commands for this scope and the commands that are FORBIDDEN for this scope
- how to build the file inventory that bounds every subsequent step

Do not skip reading that file. Do not improvise commands. Do not use `git status`. If the guard aborts, output ONLY the abort message and stop — do NOT perform a review, do NOT fall back to the other scope, do NOT read any working-directory files.

**AREA FILTER — apply only AFTER the protocol has produced the inventory:**

The area filter narrows the inventory; it never replaces the protocol. Do not substitute a path argument into the protocol's git commands to pre-filter — run them exactly as written, then discard files here.

Keep only inventory files whose repo-relative path starts with `frontend/`. Discard every other file: do not read it, review it, or comment on it. In particular, changes under `api/` are out of scope even when they are the reason the frontend changed — note the coupling in one line if relevant, but do not review them.

Ignore `frontend/node_modules/` and `frontend/dist/` entirely; they are build artifacts and dependencies, not source.

If the protocol's inventory is non-empty but NO file survives the area filter, output ONLY this and stop:
\"No frontend changes found for the `{SCOPE}` scope. N file(s) changed elsewhere in the repository.\"
(substituting the real count for N). Do NOT widen the area, do NOT review the excluded files.

Once the filtered inventory is settled, follow your standard review methodology, touching EVERY file on the filtered inventory and only files on it:

1. **Analyze changes systematically**: Review each file for Vue 3 Composition API correctness, component and composable design, Pinia store usage, reactivity pitfalls, Vuetify 4 usage, accessibility, security, performance, and test coverage.
2. **Validate against project standards**: Check against the rules in `frontend/CLAUDE.md` and `frontend/.claude/rules/` — `architecture-core.md`, `components.md`, `patterns.md`, `routing-auth.md`, and `conventions-gotchas.md`.
3. **Watch for frontend-specific traps**: hardcoded strings that belong in `src/locales/` i18n files; API base URLs hardcoded rather than read from the runtime `public/config.json`; unguarded routes; direct mutation of store state outside actions.
4. **Provide structured feedback**: Use your standard format with critical issues, important issues, suggestions, positive observations, and detailed file-by-file review.

If the area filter excluded any files, close with a single line stating how many were excluded and that they were outside frontend/. Do not itemize them.

Focus on {FOCUS}."
})
```
