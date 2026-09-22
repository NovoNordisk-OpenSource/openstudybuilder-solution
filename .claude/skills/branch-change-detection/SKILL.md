---
name: branch-change-detection
user-invocable: false
disable-model-invocation: true
description: "Internal shared helper — do NOT invoke directly; use /summarize-pr or the relevant per-component summarize/review skill instead (e.g. /summarize-pr-api). Defines the strict command protocol those skills delegate to for enumerating branch file changes, scoped to EITHER committed changes (ahead of origin/main) OR uncommitted changes (working tree + untracked), never mixed and never already-merged."
---

# Branch Change Detection Protocol

> **This skill is a shared helper; it is not meant to be invoked directly. Use the relevant per-component summarize/review skill instead** (e.g. `/summarize-pr-api`) — they include this protocol by reference.

This file defines the strict command protocol for enumerating branch changes against `origin/main`. It is included by reference from `/summarize-pr` and from the per-component summarize and review skills. Whoever follows it — a subagent those skills invoked, or the main loop itself — MUST use the `Read` tool to open this file and follow it exactly before producing any output.

Note the two consumption patterns, both valid:

- **Per-component skills** (`/summarize-pr-api`, `/summarize-pr-frontend`, `/review-api`, `/review-frontend`) push the protocol down into their single agent, which runs it and then applies an area filter.
- **`/summarize-pr`** runs the protocol once in the main loop, then splits the resulting inventory across several parallel agents. Those agents are handed a final file list and are forbidden from re-running detection — running it N times would produce N inventories that can disagree.

## When to use

- A parent skill (`/summarize-pr`, a per-component summarize/review skill, or another skill that explicitly delegates to this one) has instructed you to follow this protocol before producing output.
- You need a canonical, scope-safe enumeration of branch file changes to bound a downstream task.

## When NOT to use

- **Do not invoke this skill directly from the slash-command menu.** It produces no user-facing output on its own — run the relevant per-component summarize/review skill instead (e.g. `/summarize-pr-api`).
- Do not use this protocol for arbitrary "what did I change?" questions outside the two supported scopes (committed-vs-`origin/main` and uncommitted-vs-`HEAD`). For example, diffs between two arbitrary commits, diffs against a non-`main` base branch, or cross-branch comparisons are out of scope.
- Do not use this protocol when the task legitimately needs the full working-tree state regardless of commit boundaries (e.g. running a linter over all files) — the scope guards will abort or exclude relevant files.
- Do not copy the commands into another skill ad-hoc; extend this file and delegate instead, so all consumers stay in sync.

## Core principle

The two scopes are mutually exclusive. An agent operating under this protocol looks at **EITHER** committed-vs-main changes **OR** uncommitted-vs-HEAD changes — **never both**, and **never** anything already merged into `origin/main`.

The caller passes a single scope value: `committed` or `uncommitted`. Apply ONLY the commands listed under that scope.

## Step 1 — Always refresh the remote ref first

Before any diff, run:

```
git fetch origin main
```

The local `origin/main` ref is a cached snapshot and may be stale; skipping this step silently produces diffs against an outdated baseline.

## Step 2 — Apply the commands for the selected scope

### Scope: `committed`

Covers ONLY commits on the local branch ahead of `origin/main`. Excludes working-tree, staged, and untracked changes.

**Guard — must run FIRST:**

```
git rev-list --count origin/main..HEAD
```

If the count is `0`, STOP immediately and output only:

> No committed changes ahead of origin/main — nothing to process.

Do NOT fall back to any other diff command. Do NOT silently switch to the uncommitted scope.

**Allowed enumeration commands:**

- `git log origin/main..HEAD --oneline`
- `git diff --name-status origin/main..HEAD`
- `git diff origin/main..HEAD --stat`
- `git diff origin/main..HEAD`

**Forbidden for this scope:**

- `git diff origin/main` — includes working tree, mixing scopes
- `git diff HEAD` — uncommitted-only, wrong scope
- `git status` — does not distinguish committed-vs-main from uncommitted and is a known source of scope bleed
- Reading any file from the working directory to infer a change (the working tree is out of scope)

### Scope: `uncommitted`

Covers ONLY staged, unstaged, and untracked changes relative to `HEAD`. Excludes any work that is already committed on the branch, regardless of whether those commits have been pushed.

**Guard — must run FIRST:** run BOTH of the following, and check whether their **combined** output is empty:

- `git diff --name-only HEAD`
- `git ls-files --others --exclude-standard`

You MUST run BOTH commands before deciding. If EITHER command produces any output, the scope is non-empty — do NOT abort; proceed to the enumeration step. Abort ONLY when BOTH commands produce no output.

If both produce no output, STOP immediately and output only:

> No uncommitted changes — nothing to process.

Do NOT fall back to any other diff command. Do NOT silently switch to the committed scope.

**Allowed enumeration commands:**

- `git diff --name-status HEAD` — tracked modifications, additions, deletions, renames vs HEAD
- `git ls-files --others --exclude-standard` — untracked files (then use `Read` on each for content)
- `git diff HEAD --stat`
- `git diff HEAD`

**Forbidden for this scope:**

- `git diff origin/main` — mixes in committed work
- `git diff origin/main..HEAD` — committed-only, wrong scope
- `git log origin/main..HEAD` — committed-only, wrong scope
- `git status` — does not distinguish the scopes and is a known source of scope bleed
- Treating any already-committed work as in-scope

## Step 3 — Build the file inventory

After running the allowed commands for the selected scope, compile an explicit, deduplicated list of every changed/added/deleted/renamed/untracked file. This list is the ground truth for every subsequent step.

## Step 4 — Operate strictly within the inventory

All diff content, file reads, and analysis must come from files on the inventory. If a file is not on the inventory, it is not in scope, even if it appears modified on disk. Do NOT omit any file on the inventory either — every file on it must be accounted for.
