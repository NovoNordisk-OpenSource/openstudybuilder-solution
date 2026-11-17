<!--
Output template for the osb-app-ai-documentation skill.

It implements the "Subsection template" of the Documentation Practice & Design
Guideline (blocks A-G, in this order, for every subsection) using the markdown
conventions already used in documentation_portal/docs/guides/userguide/.

Variables:
  {{TITLE}}         subsection title, exactly as the UI spells it
  {{MENU_PATH}}     e.g. Library → Concepts → Activities → Activity Instances
  {{SLUG}}          kebab-case folder name, e.g. activity-instances
  {{NN}}, {{STEP}}  zero-padded screenshot number / short kebab-case step slug

Rules:
- Voice: NO "you", NO "we". Imperative verbs (Select, Enter, Click, Confirm) or the
  impersonal ("OSB supports ...", "The field is mandatory"). "user" only when a
  subject is unavoidable. UK English (-our, -ise).
- Use the UI wording exactly as spelled in the app (an item is 'added', not 'created',
  where the button says "Add"). Bold UI labels: **Library**, **Add activity**.
- Menu paths use arrows: Home → Settings → ...  (not ">").
- "User Guide" and "Quick Guide" are capitalised.
- Callouts: > [!NOTE] / [!TIP] / [!IMPORTANT] / [!WARNING] / [!CAUTION]. Use each for
  its meaning only (see references/guideline-rules.md).
- Quick Guide is an expandable block:  :::details Show Quick Guide ... :::
  Blank line after the opening line and before the closing :::.
- Screenshots: reference the ANNOTATED png, wrapped in a link to itself. Image paths
  are RELATIVE to the draft markdown at documentation_portal/osb-app-docs/<slug>.md,
  assets live in documentation_portal/osb-app-docs/<slug>/assets/ — always prefix
  with <slug>/assets/, never a bare assets/. The reviewer rewrites them to
  /images/user_guides/... when publishing.
- Do not repeat in a later block what an earlier block already said ("avoid
  repetition from above"). Drop any block that would only repeat; never pad.
- No study IDs, employee names, drug names/doses, internal processes, sponsor (company) logo. The OpenStudyBuilder logo stays visible.
-->

## {{TITLE}}

**Where to find it:** {{MENU_PATH}}

### Baseline

**Purpose.** {{WHAT_THE_SUBSECTION_ENABLES_AND_WHY_IT_MATTERS}}

**When to use.** {{PROBLEM_IT_SOLVES}}

{{DECISION_CRITERIA_TABLE_IF_THE_USER_CHOOSES_BETWEEN_OPTIONS}}

<!-- Example of a decision table (delete if there is a single path):
| Option | Use it when |
|---|---|
| **{{OPTION_A}}** | {{WHEN_A}} |
| **{{OPTION_B}}** | {{WHEN_B}} |
-->

**Prerequisites.**

- {{WHAT_MUST_EXIST_OR_BE_TRUE_BEFORE_THE_FEATURE_SUCCEEDS}}

<!-- Optional, anonymous phrasing only (no roles/job titles):
**Filled out by.** A user taking part in {{ACTIVITY}}.
-->

### Quick Guide

:::details Show Quick Guide

1. Select **{{MENU_1}}** → **{{MENU_2}}** → **{{TAB}}**, then click the **'{{BUTTON}}'** icon.

    [![{{ALT}}]({{SLUG}}/assets/annotated-{{SLUG}}-{{NN}}-{{STEP}}.png)]({{SLUG}}/assets/annotated-{{SLUG}}-{{NN}}-{{STEP}}.png)

2. Enter the **{{MANDATORY_FIELD}}** (mandatory) and, optionally, the **{{OPTIONAL_FIELD}}**.

    > [!NOTE]
    > {{INFORMATION_TO_TAKE_INTO_ACCOUNT}}

3. Confirm with **SAVE**.

:::

### Experienced

<!-- Only when it adds value beyond the Quick Guide. Delete the heading otherwise. -->

- **Do this when.** {{BEST_PRACTICE_OR_SPECIAL_CASE}}
- **Quality checks.** {{WHAT_TO_VALIDATE_BEFORE_MOVING_ON}}
- **Clarifications.** {{HOW_FIELDS_OR_RELATIONSHIPS_SHOULD_BE_INTERPRETED}}
- **Implementation details.** {{SYSTEM_BEHAVIOUR_IN_NEUTRAL_TERMS}}

For more details, see [{{RELATED_ARTICLE}}]({{LINK}}).

### Troubleshooting

| Symptom | Interpretation | Likely cause | Fix / next safest action |
|---|---|---|---|
| {{WHAT_THE_USER_SEES}} | {{WHAT_IT_MEANS}} | {{WHY_IT_HAPPENS}} | {{WHAT_TO_DO}} |

**Undo vs not undoable.** {{WHICH_ACTIONS_CREATE_A_NEW_VERSION_OR_ITEM_AND_CANNOT_BE_UNDONE}}

**Check before acting.**

- {{MINIMAL_VERIFICATION_ITEM}}

<!-- Escalation only if external-safe, e.g. "Contact the system administrator." Never name an internal team or role. -->

### Related topics

- [{{RELATED_SUBSECTION}}]({{LINK}})

<!-- Block G, the glossary update, is NOT part of the page: list new terms in the
     draft summary so the reviewer can add them to the glossary. -->
