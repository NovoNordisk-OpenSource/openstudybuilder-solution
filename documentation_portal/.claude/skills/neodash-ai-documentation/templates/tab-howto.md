<!--
Output template for the neodash-ai-documentation skill.

It mirrors the per-tab structure already used in the report guides under
docs/guides/userguide/reports/ (see activity-library-dashboard.md as the
canonical example), so a generated draft can be reviewed and pasted straight
into the real guide.

Variables:
  {{REPORT_TITLE}}   e.g. "Activity Library Dashboard"
  {{OVERVIEW_TABLE}} the | Tab | Use it to… | table, copied/derived from the
                     source guide's "## Report tabs" section
  {{TAB_BLOCKS}}     one block per documented tab (structure below)

Rules (match the repo convention):
- The `## Report tabs` overview table stays VISIBLE (not in a dropdown).
- Each tab is a `### <Tab>` heading with a VISIBLE `**Use this tab when** …`
  line, then ONE `<details><summary>Content guide</summary>` dropdown.
- Inside the Content guide: 1–3 short numbered steps (imperative voice: "Open",
  "Select", "Click"), then the screenshots and any walkthrough prose. Keep the
  source guide's lettered (A)(B)… references when they apply to a screenshot.
- Reference the ANNOTATED png in the markdown; the clean png is a sidecar.
- Image paths are RELATIVE to the draft markdown at `./neodash-docs/<report>.md`,
  whose assets live one level deeper in `./neodash-docs/<report>/assets/`. So
  prefix every reference with the report folder — `{{REPORT}}/assets/…`, NOT a
  bare `assets/…` (which resolves to a non-existent `neodash-docs/assets/` and
  shows a broken image). Use the same path for the image and its wrapping link.
- Blank line after every `<summary>` and before every `</details>` (so the
  markdown inside renders in VuePress).
- Use underscore for italics (_word_) to satisfy the repo's markdownlint (MD049).
-->

## Report tabs

The report is organised in different tabs, each supporting a different purpose.
To open the report, see [Open NeoDash](./#open-neodash) on the section landing page.

{{OVERVIEW_TABLE}}

{{TAB_BLOCKS}}

<!--
TAB BLOCK STRUCTURE (repeat per tab):

### {{TAB_NAME}}

**Use this tab when** {{WHEN}}.

<details><summary>Content guide</summary>

1. {{STEP_1}}
2. {{STEP_2}}

[![{{ALT}}]({{REPORT}}/assets/annotated-{{REPORT}}-{{TAB}}-{{NN}}-{{SLUG}}.png)]({{REPORT}}/assets/annotated-{{REPORT}}-{{TAB}}-{{NN}}-{{SLUG}}.png)

{{OPTIONAL_WALKTHROUGH_PROSE}}

</details>
-->
