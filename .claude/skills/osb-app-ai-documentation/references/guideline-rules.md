# Documentation Practice & Design Guideline — rules the draft must follow

Source: the internal guideline (a .docx, not in the repo; summarised here so the
skill is self-contained). Order of the whole guide: **Intro → Quick Start →
Experienced → Troubleshooting** — widest audience first, depth later.

## Global rules

1. **No sponsor-specific information** in the external Documentation Portal:
   internal roles/job titles, drug names/doses/molecules, company-specific
   processes, confidential context. If unsure: remove, or use neutral wording, or
   ask the dev.
2. **UK English** — `-our` over `-or`, `-ise` over `-ize` (colour, organise, analyse).
3. **Exact UI wording.** Use labels as spelled in the app. A study is *added*, not
   "created", when the button says "Add". Take wording from `browser_snapshot`, not
   from memory or the source guide if they differ (flag the difference).
4. **Voice.** Avoid both "you" and "we" (the guideline itself says "you" vs "user":
   none if possible; the ban on "we" is the dev's added rule). Use verbs (Click, Go, Navigate, Select,
   Enter, Confirm) or an impersonal description. If a subject is unavoidable: "user".
5. **Capitalisation.** "User Guide", "Quick Guide" (capitalised). SoA names:
   Protocol SoA, Detailed SoA.
6. **Menu paths use arrows:** Library → Concepts → Activities. Not `>`.

## Section vs subsection

- A **Section** (e.g. Study Structure) has: title, where to find it, purpose/scope,
  the list of subsections it contains — and **no how-to steps**. Procedures live in
  subsections.
- A **Subsection** always uses the same blocks, in this order: **A Baseline, B Quick
  Guide, C Experienced, D Troubleshooting, F Related topics, G Glossary update**
  (the guideline skips "E"). `templates/subsection-howto.md` implements them.
- Order the content inside a subsection in the typical set-up flow: what must be
  decided or configured first comes first.
- Cover **every UI element** in the subsection — fields, buttons, actions, selectable
  options. When the user chooses between options, state the decision criteria: what
  each option is for and when to use which.
- **Avoid repetition** from block to block: Baseline says what/why, Quick Guide says
  how, Experienced says when-to-deviate, Troubleshooting says what-went-wrong. (The
  guideline states the rule after the Quick Guide: "From here, avoid repetition from
  above in below sections".)
- **Not in the guideline:** it sets no rule on list versus prose, bullet length or
  tables for definitions. Do not cite it for such points. When a guide's definition
  lists are long or duplicate other text, report that as a reviewer suggestion
  (judgement), separate from guideline deviations.

## Block contents

- **A Baseline** — where to find it (menu path); purpose (what it enables, why it
  matters); when to use / decision criteria; prerequisites / eligibility rules (what
  must be true for the feature to succeed, where and when relevant); optional "who
  fills this out", phrased by user requirements, never by role ("by a user taking part
  in X").
- **B Quick Guide** — expandable (`:::details Show Quick Guide`). Steps match OSB UI
  wording (Select/Enter/Confirm). Screenshots with red boxes and arrows supplement
  the text. Alert boxes for tips, notes and warnings. If an up-to-date Quick Guide
  already exists in the published guide, review it against the live UI (buttons,
  options, features all present?) instead of rewriting it.
- **C Experienced** — optional, only when it adds value (can be an expandable
  section): "do this when…" guidance,
  quality checks before moving on, clarifications of how fields/relationships are
  interpreted, implementation details in neutral system-behaviour terms,
  cross-references ("For more details, go to…").
- **D Troubleshooting** — table of common errors: symptom → interpretation → likely
  cause → fix / next safest action. Then: undo vs not undoable (what creates new
  versions or instances), what to check before acting, escalation guidance only if
  external-safe ("contact the administrator", never an internal team).
- **F Related topics** — cross-links to adjacent subsections or the section overview.
- **G Glossary** — list new words/terms for the reviewer; the skill does not edit the
  glossary.

## Callouts (VitePress alerts)

| Marker | Meaning |
|---|---|
| `> [!NOTE]` | Information a user should take into account, even when skimming |
| `> [!TIP]` | Optional information that helps a user be more successful |
| `> [!IMPORTANT]` | Crucial information necessary for success |
| `> [!WARNING]` | Critical content demanding immediate attention because of risk |
| `> [!CAUTION]` | Negative potential consequences of an action |

Use the alert syntax, not plain `>` blockquotes.

## External-sharing: what to hide in screenshots

Cover (do not just crop) before ANY screenshot is taken. See `sensitive-info.md`
for how.

| Hide | Where it shows |
|---|---|
| Employee names, emails and roles | Top-right user menu, **Author** / **Modified by** columns, version history tables |
| Company-specific processes | Free-text fields, descriptions |
| Drug names, doses, molecules | Study titles, Activity/Instance names, intervention tables |
| Sponsor (company) logo, top-right only | Header — the OpenStudyBuilder logo (top-left) is NOT masked |
| Study numbers / IDs | Top banner next to the username, Study Structure and other study windows |

Prefer a seeded/demo dataset. If the only data is real, mask it and say so in the
draft summary.
