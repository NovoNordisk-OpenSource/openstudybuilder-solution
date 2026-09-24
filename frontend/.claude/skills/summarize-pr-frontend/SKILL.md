---
name: summarize-pr-frontend
description: "Generates a concise pull request description summarizing the current branch changes against origin/main. Scopes strictly to the frontend/ directory and always covers every changed file in it. Use this when you want a frontend/-focused description; if the branch also touches api/ or any other component and you want ALL of it covered in one description, use /summarize-pr instead. Produces a short, reviewer-friendly summary suitable for pasting into a PR description."
---

# Summarize PR Changes (Frontend)

> Covers `frontend/` only. If the branch also touches `api/` or any other component and you want one description covering all of it, use `/summarize-pr` instead — it buckets the branch by component and summarizes every bucket.

I'll generate a concise PR description summarizing your frontend branch changes. Let me ask what to cover first.

Use AskUserQuestion to present this single question:

AskUserQuestion({
  questions: [{
    question: "What changes should I summarize for the PR description?",
    header: "Summary Scope",
    options: [
      {
        label: "Latest committed version (Recommended)",
        description: "Summarize ONLY commits on this branch ahead of origin/main - ideal for opening a PR. Working-tree/untracked changes are excluded."
      },
      {
        label: "Current uncommitted changes",
        description: "Summarize ONLY staged/unstaged/untracked changes vs HEAD. Already-committed work is excluded."
      }
    ],
    multiSelect: false
  }]
})

## Building the prompt

Map the scope selection to a single scope token by matching on the label PREFIX (the "(Recommended)" suffix may or may not be present depending on which option was tagged recommended):

- Selected label starts with **"Latest committed version"** → `{SCOPE}` = `committed`
- Selected label starts with **"Current uncommitted changes"** → `{SCOPE}` = `uncommitted`

Scope is the only question this skill asks. The area is fixed to `frontend/` — unlike `api/`, which contains three separately-deployed apps, the frontend is a single application with no equivalent internal boundary worth splitting on. There is also no detail-section question: the summary **always covers every changed file under `frontend/`**. A PR description that silently omitted part of the branch would mislead reviewers, so the filter is all-or-nothing at the `frontend/` boundary.

## Final agent invocation

Invoke the code-reviewer-frontend agent with the assembled prompt. `{SCOPE}` is substituted as described above.

```
Agent({
  description: "Summarize frontend changes for PR description",
  subagent_type: "code-reviewer-frontend",
  prompt: "Generate a concise pull request description for the current branch.

**Scope (set by the caller — strictly one, never both):** `{SCOPE}`
**Area (fixed for this skill):** the frontend/ directory

**MANDATORY PROTOCOL — follow before any other work:**

Use the `Read` tool to open `.claude/skills/branch-change-detection/SKILL.md`. **That path is relative to the monorepo root, not to this skill's own directory.** It is a shared helper that the api and frontend skills all delegate to; there is no per-component copy under `frontend/.claude/` or `api/.claude/`. If the Read fails, STOP and report it — do NOT substitute your own git commands, because the scope guards in that file are the whole point of the protocol.

Follow its protocol EXACTLY for the `{SCOPE}` scope. That file defines:

- the `git fetch origin main` refresh step
- the guard command that must run first and the exact abort message to emit if the scope is empty
- the allowed enumeration commands for this scope and the commands that are FORBIDDEN for this scope
- how to build the file inventory that bounds every subsequent step

Do not skip reading that file. Do not improvise commands. Do not use `git status`. If the guard aborts, output ONLY the abort message and stop — do NOT produce a PR summary, do NOT fall back to the other scope, do NOT read any working-directory files.

**AREA FILTER — apply only AFTER the protocol has produced the inventory:**

The area filter narrows the inventory; it never replaces the protocol. Do not substitute a path argument into the protocol's git commands to pre-filter — run them exactly as written, then discard files here.

Keep only inventory files whose repo-relative path starts with `frontend/`. Discard every other file: do not read it and do not describe it in the summary. In particular, changes under `api/`, `db/`, or `db_schema_migration/` are out of scope even when they are the reason the frontend changed.

Ignore `frontend/node_modules/` and `frontend/dist/` entirely; they are dependencies and build artifacts, not source. Count them as discarded.

Record the number of discarded files as N — you will need it below.

If the protocol's inventory is non-empty but NO file survives the area filter, output ONLY this and stop:
\"No frontend changes found for the `{SCOPE}` scope. N file(s) changed elsewhere in the repository.\"
(substituting the real count for N). Do NOT widen the area, do NOT summarize the excluded files.

Once the filtered inventory is settled, produce a PR description using EXACTLY this format (output only the markdown, nothing else):

---

## Summary

One to three sentences describing the overall purpose and motivation of the changes.

## Changes

- Bullet list of the key changes, grouped logically
- Each bullet should be one short sentence
- Focus on *what* changed and *why*, not implementation details
- Cover the whole filtered inventory: group related files into one bullet rather than dropping them
- Call out user-visible behaviour changes explicitly — new or moved screens, changed form fields, changed dialogs or table columns — a reviewer should be able to tell what the UI does differently
- Note route changes (added/removed routes, changed `meta` such as `authRequired`, `studyRequired`, `featureFlag`, `requiredPermission`) and any new feature flag gating in one bullet if present
- Note changes to `src/api/` in one bullet if present, naming the backend endpoints the UI now calls, stops calling, or calls differently. If the branch also touches `api/`, say in that same bullet that the change is coupled to a backend change — one line, no detail, since those files are out of scope
- Note added/removed/renamed i18n keys in `src/locales/` in one bullet if present, by count and area rather than by listing every key
- Omit trivial changes (formatting, imports, lockfile churn) unless they are the main point
- If smoke or fixture tests were added or modified, mention what they cover in one bullet

## Affected areas

Comma-separated list of the main areas/modules touched, using this codebase's own directory vocabulary (e.g. `views/studies`, `components/tools`, `stores`, `composables`, `api`, `router`, `locales`, `plugins`, `extensions`, `demo`, `tests/smoke`, `config`).

---

If N is greater than zero, append this as the last line of the markdown, verbatim apart from the count:

> _Scope note: this description covers only the `frontend/` portion of the branch. N file(s) outside `frontend/` are not summarized here._

Include that line even though it is not part of the format above — the output is meant to be pasted straight into a pull request, and a description that silently omitted half the branch would mislead reviewers. Do not itemize the excluded files. If N is zero, omit the line entirely.

Guidelines:
- Cover every file in the filtered inventory; do not cover any file outside it.
- Keep the whole description under 250 words.
- Write for a reviewer who knows the codebase but hasn't seen these changes yet.
- Use plain, direct language. No filler phrases.
- Do NOT include file-by-file breakdowns or code snippets.
- Do NOT include review feedback, suggestions, or judgements about code quality — this is a summary, not a review."
})
```
