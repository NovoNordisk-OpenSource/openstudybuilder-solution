---
name: osb-app-ai-documentation
description: "Use when you need end-user documentation (markdown draft + annotated, sensitive-info-masked screenshots) for a page or feature of the OpenStudyBuilder web application — e.g. filling the '[Add screen dump]' placeholders in a User Guide, or drafting a Quick Guide for a Library/Studies page. Follows the Documentation Practice & Design Guideline. Requires Playwright MCP and a running, reachable OSB frontend (local Vite or a deployed URL). Not for NeoDash reports — use osb-neodash-ai-documentation for those."
---

# OSB Application AI Documentation

Generate **draft** user-guide content for the main OpenStudyBuilder web application:
read the existing guide (or a stated page/feature), drive Playwright through the
live UI to capture **masked**, box+arrow-annotated screenshots, and write a draft
that follows the Documentation Practice & Design Guideline (Baseline → Quick Guide →
Experienced → Troubleshooting → Related topics) to `documentation_portal/osb-app-docs/`
for the dev to review and paste into the real guide.

Sibling of `osb-neodash-ai-documentation` (same annotation style and draft-only
discipline). Differences: this targets the Vue/Vuetify app, which **writes** to a real
database and shows **sensitive data** — so read-only browsing, a masking step and the
guideline's structure and voice rules are added.

**Path convention:** every path in this skill is relative to the REPO ROOT. This
skill's directory is `.claude/skills/osb-app-ai-documentation/`; a bare
`references/…` or `templates/…` path below names a file inside it — prefix it before
you Read or run it. Drafts go to `documentation_portal/osb-app-docs/` (gitignored).
Published guides live under `documentation_portal/docs/guides/userguide/`.

The output is a draft. The skill **never edits published guides** and never edits the
glossary (it lists new terms instead).

## When to use

- A guide has `[Add screen dump]: #` placeholders (or no screenshots) and needs real,
  annotated, anonymised ones.
- A page/feature has no Quick Guide yet, or an existing one must be checked against the
  current UI (buttons, options, features all present?).
- Playwright MCP is available and the OSB frontend + its API are reachable.

If Playwright MCP is missing, **fail loudly** and tell the dev to install it.

## Requirements

- **Playwright MCP** — `mcp__playwright__*` or `mcp__plugin_playwright_playwright__*`.
  Screenshot files must be written under the working directory (e.g. under
  `documentation_portal/.playwright-mcp/` or the draft folder), not `/tmp`.
- **A running OSB frontend** — local (`http://localhost:5174`; setup in
  `references/local-setup.md`, run by the dev) or a deployed URL — **already signed in by the dev**
  or running against a local setup the dev prepared. Authentication is never
  automated, bypassed or switched off by this skill.
- **Pillow** (optional) for the manual path; `.claude/skills/osb-neodash-ai-documentation/templates/*.py`.

## Inputs

**Phase 1 — one `AskUserQuestion` (picklists only):**

- **Mode** — Fill screenshot placeholders in an existing guide / Draft a new Quick Guide
  for a page / Review an existing Quick Guide against the UI.
- **Environment** — Local frontend (`http://localhost:5174`) / Deployed / Custom.

**Phase 2 — plain chat (one question per message; never freeform values in
AskUserQuestion):**

- The source guide path (default: ask), or the menu path of the page/feature.
- Which subsections/steps to cover (default: all placeholders/steps in the guide).
- For Deployed/Custom: the exact URL (`http://` or `https://`).
- Whether any **write** flow is approved (default: none — read-only, see
  `references/fail-loud.md`).

Derive `<slug>` from the guide filename or page (kebab-case, e.g. `activity-concepts`).

## Pipeline

**REQUIRED BACKGROUND — read all five at their full paths before running:**
`.claude/skills/osb-app-ai-documentation/references/guideline-rules.md`,
`…/references/app-navigation.md`, `…/references/fail-loud.md`,
`…/references/sensitive-info.md`, `…/references/annotation-conventions.md`.

### Step 1 — Read the source

Open the guide (`documentation_portal/docs/guides/userguide/…`). List every
`[Add screen dump]: #` placeholder with its numbered step and the surrounding text
(this is the capture plan), and the exact UI labels the text mentions. Note existing
wording that disagrees with the guideline (you/we, "create" vs "add") — report it, do
not edit the guide. Also report structure deviations (no Section/Subsection blocks A–G,
content repeated between blocks) as guideline findings, and long or duplicated
definition lists as reviewer suggestions — the guideline sets no list or length rule. Fail loud if the file is missing. For a new page with no guide,
draw the plan from the menu path and the live UI.

### Step 2 — Reachability and backend check

If the dev has no running environment, point to `references/local-setup.md` (the dev
runs it). Local: `curl -s -o /dev/null -w "%{http_code}" http://localhost:5174/`. Not 200 → stop:
"Frontend not reachable — start it with `npm run dev` in `frontend/`." Read
`frontend/public/config.json` for `API_BASE_URL` and, if local, check the API
(`curl -s -o /dev/null -w "%{http_code}" <API_BASE_URL>/system/information`). Tell the
dev when the backend is a shared database → **read-only**.

### Step 3 — Open the app (dev signs in)

`browser_navigate` to the base URL. A login/SSO page → stop and ask the dev to sign in
(never automate). `browser_wait_for` the left navigation. Resize the viewport to
**1440×900** for consistent shots (`browser_resize`).

### Step 4 — Navigate and verify labels

Follow the menu path click by click. Before each click, literal-label check against
`browser_snapshot` (`references/fail-loud.md`). Record the live label of every
control, tab and field — the draft uses these, not the guide's.

### Step 5 — Per target: mask, annotate, capture

For each placeholder / step:

1. Wait for the final state (dialog title, table row, tab name).
2. `browser_evaluate` the contents of
   `.claude/skills/osb-app-ai-documentation/templates/annotation-snippet.js`
   (idempotent; re-inject after every page load).
3. Apply masks (`references/sensitive-info.md`); log the counts.
4. `osbAnnotate(osbFind('<exact label>'), { arrow: 'auto', label, mark })` — `mark` is a
   LETTER and only when the shot has several targets.
5. `browser_take_screenshot` → `annotated-<slug>-NN-<step>.png`.
6. `osbAnnotateClear()` → `browser_take_screenshot` → `<slug>-NN-<step>.png`.
7. **Read both PNGs** and confirm: boxes landed on the right control, nothing sensitive
   is readable (names, emails, study IDs, drug names, Novo logo). Redo if not.
8. Act (click/open) and continue. Close any opened form with **CANCEL**/close —
   **never SAVE** unless a write flow was approved.

Save to `documentation_portal/osb-app-docs/<slug>/assets/`. Zero-padded step numbers,
kebab-case slug. Overview shots of whole pages need no annotation but still need masks.

### Step 6 — Render the draft

Write `documentation_portal/osb-app-docs/<slug>.md` from
`.claude/skills/osb-app-ai-documentation/templates/subsection-howto.md`: one block per
subsection, blocks A–F in guideline order, voice and UI-wording rules applied. In
**placeholder mode** also write a mapping table at the top of the draft:

| Guide step (file:line) | Placeholder | Image to use |
|---|---|---|

so the reviewer can drop each image in place. Image links are relative to the draft
(`<slug>/assets/…`). Cover every field/button/option seen in the UI; for choices
explain the decision criteria. Mark anything not exercised (write flows) as such.

### Step 7 — Voice and wording lint

Before finishing, grep the draft: no `\byou(r)?\b`, no `\bwe\b|\bour\b|\bus\b`, no
US spellings (`-ize`, `color`, `behavior`), no plain `>` blockquote alerts, `→` not `>` in
menu paths, "User Guide"/"Quick Guide" capitalised. Fix every hit.

### Step 8 — Summary

Print: draft path, screenshot count, the mapping of placeholders → images, any
low-confidence flags (empty tables, controls not found, steps not exercised, labels
that differ from the guide, sensitive content masked and how), **new glossary terms**, and a reminder that this
is a draft to review and paste into the real guide. Remind the dev to stop any local
API they started for the capture and that `.env` files hold credentials.

## Fail loud — never substitute

Literal-label check, name the gate, duplicate-screenshot tripwire, **read-only by
default**, never automate login. On failure stop and write
`documentation_portal/osb-app-docs/<slug>-FAILED.md`. Full rules:
`references/fail-loud.md`.

**Red flags — STOP:**

- Login/SSO page → the dev signs in; never automate or bypass.
- A dialog shows **SAVE**/**Approve**/**Delete** and the next step would click it →
  not approved → do not click.
- Expected label not on screen → do not click a near-match.
- Table says "No data available" → do not invent rows.
- Any name/email/study ID/drug name/Novo logo readable in a PNG → redo, do not ship.
- Two identical consecutive screenshots → previous click was a no-op.

## Output

Drafts only, to `documentation_portal/osb-app-docs/` (gitignored via
`documentation_portal/.gitignore`). Never edits published guides, the glossary or
`documentation_portal/docs/public/images/`.

## Out of scope

Auth automation; video/GIF; write flows unless approved; automatic redaction of
free-text drug/person names (flag and skip instead); multi-language; editing
published guides in place; NeoDash reports (use `osb-neodash-ai-documentation`).

## Skill files

Relative to `.claude/skills/osb-app-ai-documentation/`:

- `templates/annotation-snippet.js` — `osbFind` (exact-label lookup), `osbAnnotate`/`osbAnnotateClear` (red box, arrow, label, letter badge), `osbMask`/`osbMaskMatching`/`osbMaskClear` (opaque cover over sensitive content).
- `templates/subsection-howto.md` — draft template for the guideline's subsection blocks A–F.
- `references/guideline-rules.md` — guideline distilled: structure, voice, wording, callouts, what to hide.
- `references/local-setup.md` — running API + frontend locally for capture (data choice, auth, ports, Playwright notes).
- `references/app-navigation.md` — environments, auth stance, layout vocabulary, waiting.
- `references/annotation-conventions.md` — two-file convention, style, exact matching.
- `references/sensitive-info.md` — masking procedure and checks.
- `references/fail-loud.md` — no-substitution, read-only, stop conditions.

Shared tooling reused from the NeoDash skill (Pillow/stdlib, app-agnostic), under
`.claude/skills/osb-neodash-ai-documentation/templates/`: `annotate-manual.py`
(no-browser annotation), `contact_sheet.py` (review strip of several PNGs),
`pngcrop.py` (stdlib-only crop). Do not use `crop-blank-space.py` — it is specific to
NeoDash full-height captures.
