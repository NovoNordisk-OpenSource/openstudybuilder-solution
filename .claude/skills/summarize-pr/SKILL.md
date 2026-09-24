---
name: summarize-pr
description: "Generates a concise pull request description covering the WHOLE monorepo branch, across every component it touches — api, frontend, db, db_schema_migration, import_standards, import_sponsor_data, export, verifications, system_tests, load_tests, documentation_portal, gateway, neodash, _tools, CI and root config. Use this for any branch that spans more than one top-level directory, or that touches a component other than api/ or frontend/. Produces a reviewer-friendly summary suitable for pasting into a PR description."
---

# Summarize PR Changes (whole repository)

I'll generate a single PR description covering every component your branch touches.

Unlike `/summarize-pr-api` and `/summarize-pr-frontend`, this skill **never discards files**. Every changed file lands in exactly one component bucket and every bucket is summarized, so the result carries no "N files not summarized here" disclaimer.

## Step 1 — Ask the scope

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

Map the selection to a single scope token by matching on the label PREFIX (the "(Recommended)" suffix may or may not be present depending on which option was tagged recommended):

- Selected label starts with **"Latest committed version"** → `{SCOPE}` = `committed`
- Selected label starts with **"Current uncommitted changes"** → `{SCOPE}` = `uncommitted`

Scope is the only question this skill asks. There is deliberately no area question — the area is "everything" — and no per-component detail-section question: a cross-component PR description that also carried endpoint tables and data-model tables for every component would be far too long to be useful. When you want that depth for one component, run `/summarize-pr-api` or `/summarize-pr-frontend` instead.

## Step 2 — Detect the changes YOURSELF, once

**Do this in the main loop. Do not delegate it to a subagent.**

Use the `Read` tool to open `.claude/skills/branch-change-detection/SKILL.md` and follow its protocol EXACTLY for the `{SCOPE}` scope. That file defines the `git fetch origin main` refresh step, the guard command that must run first, the exact abort message, the allowed enumeration commands for the scope, and the commands that are FORBIDDEN for it.

Do not improvise git commands. Do not use `git status`. If the guard aborts, output ONLY the abort message it specifies and stop — do NOT produce a PR summary, do NOT fall back to the other scope, do NOT spawn any agent.

This differs from `/summarize-pr-api` and `/summarize-pr-frontend`, which push the protocol down into their single agent. Here the protocol runs **once, up front, in the main loop**, because several agents run in parallel afterwards and each must be handed a slice of one consistent inventory. Letting each agent re-run detection would mean N redundant `git fetch` calls and, worse, N independently-derived inventories that can disagree.

## Step 3 — Bucket the inventory by component

Assign every file on the inventory to exactly one bucket, by its repo-relative path:

| Path starts with | Bucket | Agent |
|---|---|---|
| `api/` | `api` | `code-reviewer-api` |
| `frontend/` | `frontend` | `code-reviewer-frontend` |
| any **hidden** top-level directory (`.github/`, `.claude/`, …) or any root-level file (`CLAUDE.md`, `README.md`, `SECURITY.md`, `compose.yaml`, `.gitignore`, …) | `repo root & CI` | `general-purpose` |
| any other top-level directory | that directory's name | `general-purpose` |

Rules:

- **Do not hardcode a list of known components.** The root `CLAUDE.md` component table is not exhaustive — `gateway/` and `neodash/` are real top-level directories that it does not mention. Any unrecognized top-level directory gets its own bucket and its own agent, described as best the agent can from the diff.
- Drop `frontend/node_modules/` and `frontend/dist/` from the inventory entirely — dependencies and build artifacts, not source. They are the one exception to "never discard", and they are never mentioned in the output.
- Every remaining file must be in exactly one bucket. Verify the bucket sizes sum to the inventory size before continuing.
- **Renames are bucketed by their DESTINATION path, and count once.** `git diff --name-status` reports them as `R<score><TAB>old<TAB>new`; take `new`. This matters because a rename can cross a component boundary — moving `api/.claude/skills/foo/` to `.claude/skills/foo/` is a real and meaningful change that belongs to the destination component. When a rename does cross a boundary, say so in that bucket's `{FILE_LIST}` (`(renamed from <old path>)`), so the agent can describe the move rather than reporting a bare new file. Never place the same rename in both buckets.
- **Agent cap.** If bucketing yields more than 8 buckets, keep `api`, `frontend`, and the 5 largest others as their own buckets, and merge every remaining bucket into one `other components` bucket handled by a single `general-purpose` agent. Never drop a bucket to stay under the cap.

## Step 4 — Fan out, one agent per bucket

Spawn all bucket agents **in a single message so they run concurrently**. Each agent receives only its own file list and returns a *fragment*, not a finished PR description.

For each bucket, invoke:

```
Agent({
  description: "Summarize {BUCKET} changes",
  subagent_type: "{AGENT}",
  prompt: "You are summarizing ONE component's slice of a cross-component pull request. Another process has already enumerated the branch changes and assigned you this exact file list. Return a fragment that will be assembled with other components' fragments into a single PR description.

**Component:** {BUCKET}
**Your files (this list is complete and final):**
{FILE_LIST}

**Rules — read before doing anything:**

- Do NOT run `git fetch`, `git status`, or any branch-enumeration command. The inventory is already settled and handed to you above. Re-deriving it is forbidden.
- To read the change, use `git diff` limited to the paths above (for the `committed` scope: `git diff origin/main..HEAD -- <paths>`; for the `uncommitted` scope: `git diff HEAD -- <paths>`, and use `Read` for untracked files). The scope for this run is `{SCOPE}`.
- Cover EVERY file on the list. Do NOT read, diff, or describe any file not on it — other agents own those, and duplicating them corrupts the assembled description.

**Output contract — the FIRST seven characters of your response must be `PURPOSE`. Nothing may precede them: no heading, no acknowledgement, no note about what you found or decided, no sentence reasoning about whether you have gathered enough detail. Your response is parsed by another process, not read by a human. Think as much as you need to, then emit only the structure below — start it, and stop when `AREAS:` ends. No closing remarks.**

PURPOSE: one sentence on what this component's changes accomplish.
BULLETS:
- between 1 and 5 bullets, each one short sentence
- focus on *what* changed and *why*, not implementation details
- group related files into one bullet rather than listing files
- omit trivial churn (formatting, imports, lockfiles) unless it is the main point
- if tests were added or modified, cover them in one bullet
AREAS: comma-separated list of the submodules touched, using this component's own directory vocabulary.

Do NOT include review feedback, suggestions, or judgements about code quality — this is a summary, not a review. Do NOT include a file-by-file breakdown or code snippets."
})
```

Substitute `{BUCKET}`, `{AGENT}`, `{FILE_LIST}` (one path per line), and `{SCOPE}` per bucket.

Two buckets get an extra line appended to the prompt, because their agents carry component-specific knowledge worth steering:

- **`api`** — append: `Where endpoints changed, name them as `METHOD /path` inside the relevant bullet. If the change spans more than one of the three apps (clinical_mdr_api, consumer_api, extensions), make that split visible in the bullets. Note Neo4j data-model changes under domain_repositories/models/ in their own bullet if present.`
- **`frontend`** — append: `Call out user-visible behaviour changes explicitly — new or moved screens, changed form fields, dialogs, table columns. Note route changes (added/removed routes, changed `meta` such as `authRequired`, `studyRequired`, `featureFlag`, `requiredPermission`) in one bullet if present. Note added/removed/renamed i18n keys in `src/locales/` by count and area rather than listing keys. If `src/api/` changed, name the backend endpoints the UI now calls, stops calling, or calls differently.`

## Step 5 — Assemble the final description

**Parse each fragment defensively.** Agents do sometimes emit a line of reasoning above `PURPOSE:` despite the contract forbidding it. Discard everything before the first `PURPOSE:` and everything after the `AREAS:` line, in every fragment, without exception. Never copy a stray preamble into the output, and never let one make you think the fragment is malformed — a fragment containing `PURPOSE:`, `BULLETS:` and `AREAS:` is usable no matter what surrounds it. Treat a fragment as failed only if one of those three markers is genuinely absent.

Write the Summary yourself — it is the one part no single agent can produce, because it is the cross-component story. If the branch changes an API endpoint and the UI that calls it, say that in one breath rather than as two unrelated facts.

Output only the markdown below, nothing else:

---

## Summary

One to three sentences describing the overall purpose and motivation of the branch as a whole. Where components are coupled (an `api/` change the `frontend/` change depends on, a `db_schema_migration/` change behind an `api/` change), state the coupling here rather than leaving the reader to infer it.

## Changes

### {bucket name}

- the bullets that bucket's agent returned

_(one `###` subsection per bucket, in this order: `api`, `frontend`, then the remaining buckets by descending file count, then `repo root & CI` last)_

## Affected areas

Per component, on its own line: **{bucket}** — the AREAS list that bucket's agent returned.

---

Guidelines:

- If exactly ONE bucket came back, drop the `###` subsection heading and render `## Changes` as a flat bullet list — a single-component PR should not look like a table of contents. Consider mentioning that `/summarize-pr-api` or `/summarize-pr-frontend` would give more depth for that component.
- **Word budget scales with the number of buckets: `150 + 80 × buckets`.** A flat budget binds far too early here — with 5 buckets at up to 5 bullets each, a fixed 400 words forces you to drop roughly a bullet per component, losing real content the agents correctly surfaced. Worked values:

  | Buckets | 1 | 2 | 3 | 4 | 5 | 6 | 8 |
  |---|---|---|---|---|---|---|---|
  | Budget (words) | 230 | 310 | 390 | 470 | 550 | 630 | 790 |

  The 150 covers the Summary and the `## Affected areas` block, which grow slowly; the 80 per bucket covers one `###` subsection. Count the assembled markdown, headings included. If you are over, trim the least informative bullets — never drop a bucket, and never drop a bullet that is the only mention of a user-visible or breaking change.
- Never emit a scope note about excluded files. Nothing is excluded; if you find yourself wanting to write one, a bucket was dropped and that is a bug.
- If an agent returns nothing or fails, say so explicitly on that bucket's line (`### db — summary unavailable, N files changed`) rather than silently omitting the component.
- Write for a reviewer who knows the codebase but hasn't seen these changes yet. Plain, direct language, no filler.
- Do NOT include review feedback or suggestions — this is a summary, not a review.

## Related skills

- `/summarize-pr-api` — deeper `api/`-only summary, with optional endpoint and Neo4j data-model tables.
- `/summarize-pr-frontend` — deeper `frontend/`-only summary.
- `/review-api`, `/review-frontend` — actual code review, not a summary.
