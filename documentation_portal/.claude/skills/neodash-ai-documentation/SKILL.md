---
name: neodash-ai-documentation
description: "Use when you need end-user how-to documentation (markdown + annotated screenshots) for the tabs of a NeoDash report in the OpenStudyBuilder docs — capturing per-tab screenshots from the live app and drafting step-by-step guides. Requires Playwright MCP and a running NeoDash (local Docker at localhost:5005, or a deployed neodash URL)."
---

# NeoDash AI Documentation

Generate per-tab how-to **draft** docs for a NeoDash report: read the report's
existing guide for the tab list and intent, drive Playwright through the live
NeoDash app to capture box+arrow-annotated screenshots, and write drafts to
`./neodash-docs/` for the dev to review and paste into the real guide.

This is an MVP. The output is a draft — it never edits the published report
guides. Authentication/connection is handled interactively by the dev.

## When to use

- You want step-by-step, screenshot-led documentation for the tabs of a NeoDash
  report (Activity Library Dashboard, CRF Library Versions, etc.).
- Playwright MCP is available and NeoDash is running and reachable.
- The report already has a guide under `docs/guides/userguide/reports/` (the
  source of tab names + intent). If it doesn't, stop and ask the dev to create
  the guide skeleton first.

If Playwright MCP is missing, **fail loudly** and tell the dev to install it.

## Requirements

- **Playwright MCP** — `mcp__plugin_playwright_playwright__*` tools.
- **A running NeoDash** — local Docker (`http://localhost:5005/`) or a deployed URL.
- **The report's existing guide** — `docs/guides/userguide/reports/<report>.md`.

## Inputs

Gather in two phases. **Phase 1 is the only `AskUserQuestion` call** (picklists).
**Phase 2 is plain chat** — do NOT put freeform values (URLs) inside
AskUserQuestion; the paste lands in the option label, not the answer.

### Phase 1 — picklists only

- **Report** — one of: Activity Library Dashboard, Audit Trail Report, Data
  Exchange Data Models, Study Metadata Comparison, Syntax Template Dashboard,
  Activity Metadata Check, CRF Library Versions, Laboratory Data Specification.
- **Environment** — Local NeoDash (`http://localhost:5005/`) / Deployed / Custom.

### Phase 2 — plain chat (one question per message)

- If Environment = Deployed or Custom → ask for the exact URL (must start with
  `http://` or `https://`).
- Optional → which tabs to document (default: all tabs from the guide).

Derive the report slug from the guide filename (e.g. `activity-library-dashboard`).

## Pipeline

**REQUIRED BACKGROUND:** read `references/neodash-navigation.md`,
`references/annotation-conventions.md`, and `references/fail-loud.md` before running.

### Step 1 — Read the source guide

Open `docs/guides/userguide/reports/<report>.md`. Parse the `## Report tabs`
overview table (tab names + "Use it to…") and each `### <Tab>` block (the
`**Use this tab when**` line, the Content-guide steps, the lettered (A)(B)…
call-outs). This is the tab list, intent, and draft-step source. **Fail loud** if
the file is missing.

### Step 2 — Reachability precheck (Local only)

If Environment = Local: `curl -s -o /dev/null -w "%{http_code}" http://localhost:5005/`.
If not `200`, stop: "NeoDash not reachable at localhost:5005 — start it with
`docker compose up -d`, then re-run." For Deployed/Custom, skip (Playwright
surfaces reachability on navigate).

### Step 3 — Connect (interactive)

`browser_navigate` to the base URL. The dev connects (local: click **Connect**;
deployed: SSO). `browser_wait_for` until the **Report navigation panel** report
list is visible. Capture in **reader mode**. Open the chosen report from the nav
panel; confirm the **Report title** matches.

### Step 4 — Enumerate & verify tabs

`browser_snapshot` the page tab bar. Confirm the tabs match the guide's list
(literal-label check). A guide tab missing from the UI → flag and stop for that
tab; do not guess (see `references/fail-loud.md`).

### Step 5 — Per tab: capture annotated + clean screenshots

For each tab: click it, `browser_wait_for` cards to load. For each control/step
the guide describes:

1. `browser_evaluate` the contents of `templates/annotation-snippet.js` (idempotent).
2. `neodashAnnotate("<selector>", { arrow: "auto", label, number })` — red box (+ arrow).
3. `browser_take_screenshot` → `annotated-<report>-<tab>-NN-<slug>.png`.
4. `neodashAnnotateClear()` → `browser_take_screenshot` → `<report>-<tab>-NN-<slug>.png`.
5. Act, continue. **Annotated first, clean second.**

Save under `./neodash-docs/<report>/assets/`. Zero-padded step numbers,
kebab-case slug. A bare tab-overview shot (no click) needs no annotation. Locate
cards by their **exact** title — several share a prefix (`Number of Activities
and Instances` vs `… by Group and Subgroup`), so a substring match boxes the
wrong card and a call-out goes missing (see `references/annotation-conventions.md`).

### Step 5b — Trim blank space

Full-height capture (CSS-expand the inner scroll container, then `fullPage`)
grows the document past the actual content, so every shot ends with a tall band
of empty dashboard background — plus a stray sidebar-toggle icon at the far
bottom-left that defeats a naive trim. For some reports (e.g. the Audit Trail
Report) the same expansion ALSO opens a tall band of empty background *above* the
title: it is normally scrolled out of view so it never shows on a real screen,
only in the full-page capture. After ALL captures for the report are saved, run
once over the assets dir:

```
python3 .claude/skills/neodash-ai-documentation/templates/crop-blank-space.py \
  ./neodash-docs/<report>/assets
```

It crops each `annotated-*.png` to just below its lowest red call-out box (+24px
margin), trims the matching clean sidecar to the same geometry, and — if the
leading top band is abnormally tall (> 120px) — collapses it to the app bar plus
a small gap (a normal ~30px gap is left untouched). All edits are in place and
idempotent. If you have already copied annotated images into `docs/images/…`,
re-copy them afterwards so the published copies are cropped too.

### Step 6 — Render the draft

Write `./neodash-docs/<report>.md` using `templates/tab-howto.md`: the
`## Report tabs` overview table on top, then one `### <Tab>` block each with the
visible `**Use this tab when**` line and a single `Content guide` dropdown
(1–3 imperative steps + the annotated screenshot(s) + any walkthrough). Keep the
guide's (A)(B)… references aligned with the matching screenshot. Image links are
relative to the draft md (one level above its assets), so prefix every reference
with the report folder — `<report>/assets/…`, never a bare `assets/…` (which
points at a non-existent `neodash-docs/assets/` and renders broken).

### Step 7 — Summary

Print: the draft path, screenshot count, any low-confidence flags (e.g. "card
showed 'Query returned no data' — verify"), and a reminder that this is a draft
to review and paste into the real guide.

## Annotation

Two files per target (annotated + clean), red box + optional arrow/label, via
DOM/SVG injection. See `references/annotation-conventions.md` and
`templates/annotation-snippet.js`.

## Fail loud — never substitute

Before every click: literal-label check; name the gate (NeoDash: wrong database /
report not loaded / empty data); duplicate-screenshot tripwire. On failure, stop
and write `./neodash-docs/<report>-FAILED.md`. Full rules:
`references/fail-loud.md`.

**Red flags — STOP:**
- Expected tab/label not on screen → do not click a near-match.
- A card says "Query returned no data" → don't invent a result in the prose.
- Editor-only controls visible (rename pencil, drag handle, add-page `+`) → not
  reader mode; switch first.
- Two identical consecutive screenshots → previous click was a no-op.

## Output

Drafts only, to `./neodash-docs/` (gitignored). Matches the per-tab structure of
`docs/guides/userguide/reports/activity-library-dashboard.md`. The skill does not
edit the published guides.

## Out of scope (MVP)

Auth automation; video/GIF; wiki upload; PII redaction in screenshots;
multi-language; editing the real report guides in place.

## Skill files

- `templates/annotation-snippet.js` — red box + arrow + label overlay (inject via `browser_evaluate`).
- `templates/crop-blank-space.py` — trims trailing blank space below the last call-out box (Step 5b). Needs Pillow.
- `templates/pngcrop.py` — stdlib-only single-file PNG crop/convert, for boxes where Pillow can't be installed (no pip/ensurepip). No red-detection or pair-alignment; verify output.
- `templates/tab-howto.md` — output template mirroring the repo's per-tab guide structure.
- `references/neodash-navigation.md` — connect, nav panel, tabs, reader mode, element names.
- `references/annotation-conventions.md` — when/how to annotate, two-file convention, style.
- `references/fail-loud.md` — no-substitution rules and NeoDash stop conditions.
