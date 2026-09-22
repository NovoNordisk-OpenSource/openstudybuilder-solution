---
name: summarize-pr-api
description: "Generates a concise pull request description summarizing the current branch changes against origin/main. Scopes strictly to the api/ directory, with optional endpoint and Neo4j data-model detail sections. Use this when you want an api/-focused description; if the branch also touches frontend/ or any other component and you want ALL of it covered in one description, use /summarize-pr instead. Produces a short, reviewer-friendly summary suitable for pasting into a PR description."
---

# Summarize PR Changes

> Covers `api/` only. If the branch also touches `frontend/`, `db_schema_migration/`, or any other component and you want one description covering all of it, use `/summarize-pr` instead — it buckets the branch by component and summarizes every bucket. This skill is the right choice when you want the extra `api/` depth below (endpoint lists, Neo4j data-model changes), which `/summarize-pr` deliberately omits.

I'll generate a concise PR description summarizing your branch changes. Let me ask a couple of questions first.

Use AskUserQuestion to present BOTH questions at once:

AskUserQuestion({
  questions: [
    {
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
    },
    {
      question: "Which additional detail sections should be included?",
      header: "Detail Sections",
      options: [
        {
          label: "Main API endpoint changes",
          description: "List added, removed, or modified endpoints in the main API (api/clinical_mdr_api/routers/)"
        },
        {
          label: "Consumer API endpoint changes",
          description: "List added, removed, or modified endpoints in the consumer API (api/consumer_api/)"
        },
        {
          label: "Extensions API endpoint changes",
          description: "List added, removed, or modified endpoints in the extensions API (api/extensions/)"
        },
        {
          label: "Neo4j data model changes",
          description: "List added, removed, or modified neomodel node/relationship definitions (api/clinical_mdr_api/domain_repositories/models/)"
        }
      ],
      multiSelect: true
    }
  ]
})

## Building the prompt

Map the scope selection to a single scope token by matching on the label PREFIX (the "(Recommended)" suffix may or may not be present depending on which option was tagged recommended):

- Selected label starts with **"Latest committed version"** → `{SCOPE}` = `committed`
- Selected label starts with **"Current uncommitted changes"** → `{SCOPE}` = `uncommitted`

The area is fixed to `api/` — this skill does not ask an area question. The per-app axis is already covered by the Detail Sections question above, which adds *more* detail per app rather than dropping files from the summary. A PR description that silently omitted part of the branch would mislead reviewers, so the filter is all-or-nothing at the `api/` boundary.

Build `{OPTIONAL_SECTIONS}` by concatenating the templates below for each detail section the user selected, in order. If none are selected, `{OPTIONAL_SECTIONS}` is empty.

**Main API endpoint changes section template:**
```
## Main API endpoint changes

Examine changes in `api/clinical_mdr_api/routers/` and `api/clinical_mdr_api/models/` directories.
List each endpoint that was added, removed, or modified using this format:
- `METHOD /path` — short description of what changed (e.g. "new endpoint", "added query parameter `x`", "changed response model", "removed")
If no main API endpoint changes exist in the inventory, write "No main API endpoint changes."
```

**Consumer API endpoint changes section template:**
```
## Consumer API endpoint changes

Examine changes in `api/consumer_api/` directory (routes, models, services).
List each endpoint that was added, removed, or modified using this format:
- `METHOD /path` — short description of what changed
If no consumer API endpoint changes exist in the inventory, write "No consumer API endpoint changes."
```

**Extensions API endpoint changes section template:**
```
## Extensions API endpoint changes

Examine changes in `api/extensions/` directory (extension main files, models, db modules).
List each endpoint that was added, removed, or modified using this format:
- `METHOD /path` — short description of what changed
If no extensions API endpoint changes exist in the inventory, write "No extensions API endpoint changes."
```

**Neo4j data model changes section template:**
```
## Neo4j data model changes

Examine changes in `api/clinical_mdr_api/domain_repositories/models/` directory (neomodel StructuredNode and StructuredRel subclasses).
List each node or relationship class that was added, removed, or modified:
- `ClassName` — short description of what changed (e.g. "new node", "added property `x`", "changed relationship to Y", "removed")
If no data model changes exist in the inventory, write "No Neo4j data model changes."
```

## Final agent invocation

Invoke the code-reviewer-api agent with the assembled prompt. `{SCOPE}` and `{OPTIONAL_SECTIONS}` are substituted as described above.

```
Agent({
  description: "Summarize changes for PR description",
  subagent_type: "code-reviewer-api",
  prompt: "Generate a concise pull request description for the current branch.

**Scope (set by the caller — strictly one, never both):** `{SCOPE}`
**Area (fixed for this skill):** the api/ directory

**MANDATORY PROTOCOL — follow before any other work:**

Use the `Read` tool to open `.claude/skills/branch-change-detection/SKILL.md`. **That path is relative to the monorepo root, not to this skill's own directory.** It is a shared helper that the api and frontend skills all delegate to; there is no per-component copy under `api/.claude/` or `frontend/.claude/`. If the Read fails, STOP and report it — do NOT substitute your own git commands, because the scope guards in that file are the whole point of the protocol.

Follow its protocol EXACTLY for the `{SCOPE}` scope. That file defines:

- the `git fetch origin main` refresh step
- the guard command that must run first and the exact abort message to emit if the scope is empty
- the allowed enumeration commands for this scope and the commands that are FORBIDDEN for this scope
- how to build the file inventory that bounds every subsequent step

Do not skip reading that file. Do not improvise commands. Do not use `git status`. If the guard aborts, output ONLY the abort message and stop — do NOT produce a PR summary, do NOT fall back to the other scope, do NOT read any working-directory files.

**AREA FILTER — apply only AFTER the protocol has produced the inventory:**

The area filter narrows the inventory; it never replaces the protocol. Do not substitute a path argument into the protocol's git commands to pre-filter — run them exactly as written, then discard files here.

Keep only inventory files whose repo-relative path starts with `api/`. Discard every other file: do not read it and do not describe it in the summary. In particular, changes under `frontend/`, `db/`, or `db_schema_migration/` are out of scope even when they are part of the same branch.

Record the number of discarded files as N — you will need it below.

If the protocol's inventory is non-empty but NO file survives the area filter, output ONLY this and stop:
\"No api/ changes found for the `{SCOPE}` scope. N file(s) changed elsewhere in the repository.\"
(substituting the real count for N). Do NOT widen the area, do NOT summarize the excluded files.

Once the filtered inventory is settled, produce a PR description using EXACTLY this format (output only the markdown, nothing else):

---

## Summary

One to three sentences describing the overall purpose and motivation of the changes.

## Changes

- Bullet list of the key changes, grouped logically
- Each bullet should be one short sentence
- Focus on *what* changed and *why*, not implementation details
- Omit trivial changes (formatting, imports) unless they are the main point
- If tests were added or modified, mention what they cover in one bullet

## Affected areas

Comma-separated list of the main areas/modules touched (e.g. `routers`, `services`, `domains`, `models`, `tests`, `config`).

{OPTIONAL_SECTIONS}

---

If N is greater than zero, append this as the last line of the markdown, verbatim apart from the count:

> _Scope note: this description covers only the `api/` portion of the branch. N file(s) outside `api/` are not summarized here._

Include that line even though it is not part of the format above — the output is meant to be pasted straight into a pull request, and a description that silently omitted half the branch would mislead reviewers. Do not itemize the excluded files. If N is zero, omit the line entirely.

Guidelines:
- Cover every file in the filtered inventory; do not cover any file outside it.
- Keep the Summary, Changes, and Affected areas sections together under 250 words.
- Each optional detail section should be concise — aim for a simple list, not paragraphs.
- Write for a reviewer who knows the codebase but hasn't seen these changes yet.
- Use plain, direct language. No filler phrases.
- Do NOT include file-by-file breakdowns or code snippets outside the optional sections.
- Do NOT include review feedback or suggestions — this is a summary, not a review."
})
```
