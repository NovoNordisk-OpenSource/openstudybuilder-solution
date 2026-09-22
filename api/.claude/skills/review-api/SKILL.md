---
name: review-api
description: "Conducts a comprehensive code review of the current branch changes against the remote origin/main branch using the specialized code-reviewer-api agent. Scopes the review to the whole api/ directory or to a single app (main, consumer, or extensions). Analyzes git diffs, validates DDD architecture compliance, checks code quality, and ensures adherence to project standards."
---

# Code Review API

I'll perform a comprehensive code review against the remote origin/main branch. Let me ask two questions first.

Use AskUserQuestion to present BOTH questions at once:

AskUserQuestion({
  questions: [
    {
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
    },
    {
      question: "Which part of the API should the review cover?",
      header: "API Area",
      options: [
        {
          label: "All api/ changes (Recommended)",
          description: "Review every changed file under api/, spanning the main, consumer, and extensions apps plus shared common/ code."
        },
        {
          label: "Main API only",
          description: "Review only changes under api/clinical_mdr_api/, plus shared api/common/."
        },
        {
          label: "Consumer API only",
          description: "Review only changes under api/consumer_api/, plus shared api/common/."
        },
        {
          label: "Extensions API only",
          description: "Review only changes under api/extensions/, plus shared api/common/."
        }
      ],
      multiSelect: false
    }
  ]
})

## Building the prompt

Map the scope selection to a single scope token by matching on the label PREFIX (the "(Recommended)" suffix may or may not be present depending on which option was tagged recommended):

- Selected label starts with **"Current uncommitted changes"** → `{SCOPE}` = `uncommitted`
- Selected label starts with **"Latest committed version"** → `{SCOPE}` = `committed`

Also pick a scope-specific focus phrase:

- `uncommitted` → `{FOCUS}` = `pre-commit validation — ensuring changes are ready for commit and follow all project standards`
- `committed` → `{FOCUS}` = `pre-PR validation — ensuring the committed changes are ready for pull request and follow all project standards`

Map the area selection to a path prefix list and a human label, again by label PREFIX:

| Selected label starts with | `{AREA_PATHS}` | `{AREA_LABEL}` |
|---|---|---|
| "All api/ changes" | `api/` | the api/ directory |
| "Main API only" | `api/clinical_mdr_api/`, `api/common/` | the main API (clinical_mdr_api) |
| "Consumer API only" | `api/consumer_api/`, `api/common/` | the consumer API |
| "Extensions API only" | `api/extensions/`, `api/common/` | the extensions API |

`api/common/` is included in every single-app selection on purpose — config, auth, database, telemetry, and exceptions are shared, so a change there is in scope for whichever app is under review. Note this in the handoff so the reviewer does not treat it as stray.

## Final agent invocation

Invoke the code-reviewer-api agent with the assembled prompt. Substitute `{SCOPE}`, `{FOCUS}`, `{AREA_PATHS}`, and `{AREA_LABEL}` as described above.

```
Agent({
  description: "Code review against origin/main",
  subagent_type: "code-reviewer-api",
  prompt: "Please conduct a comprehensive code review of the current branch against remote origin/main.

**Scope (set by the caller — strictly one, never both):** `{SCOPE}`
**Area (set by the caller):** {AREA_LABEL}

**MANDATORY PROTOCOL — follow before any other work:**

Use the `Read` tool to open `.claude/skills/branch-change-detection/SKILL.md`. **That path is relative to the monorepo root, not to this skill's own directory.** It is a shared helper that the api and frontend skills all delegate to; there is no per-component copy under `api/.claude/` or `frontend/.claude/`. If the Read fails, STOP and report it — do NOT substitute your own git commands, because the scope guards in that file are the whole point of the protocol.

Follow its protocol EXACTLY for the `{SCOPE}` scope. That file defines:

- the `git fetch origin main` refresh step
- the guard command that must run first and the exact abort message to emit if the scope is empty
- the allowed enumeration commands for this scope and the commands that are FORBIDDEN for this scope
- how to build the file inventory that bounds every subsequent step

Do not skip reading that file. Do not improvise commands. Do not use `git status`. If the guard aborts, output ONLY the abort message and stop — do NOT perform a review, do NOT fall back to the other scope, do NOT read any working-directory files.

**AREA FILTER — apply only AFTER the protocol has produced the inventory:**

The area filter narrows the inventory; it never replaces the protocol. Do not substitute a path argument into the protocol's git commands to pre-filter — run them exactly as written, then discard files here.

Keep only inventory files whose repo-relative path starts with one of: {AREA_PATHS}. Discard every other file: do not read it, review it, or comment on it. `api/common/` is shared infrastructure and is deliberately in scope for single-app selections.

If the protocol's inventory is non-empty but NO file survives the area filter, output ONLY this and stop:
\"No changes found under {AREA_LABEL} for the `{SCOPE}` scope. N file(s) changed elsewhere in the repository.\"
(substituting the real count for N). Do NOT widen the area, do NOT review the excluded files.

Once the filtered inventory is settled, follow your standard review methodology, touching EVERY file on the filtered inventory and only files on it:

1. **Analyze changes systematically**: Review each file for DDD architecture compliance, code quality, security issues, performance concerns, error handling, and testing coverage.
2. **Validate against project standards**: Check against CLAUDE.md rules for REST API conventions, code style, authentication patterns, database interactions.
3. **Provide structured feedback**: Use your standard format with critical issues, important issues, suggestions, positive observations, and detailed file-by-file review.

If the area filter excluded any files, close with a single line stating how many were excluded and that they were outside {AREA_LABEL}. Do not itemize them.

Focus on {FOCUS}."
})
```
