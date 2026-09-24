# Audit Trail Report

**Where to find it:** Reports button → NeoDash → "Audit Trail Report" in the Report navigation panel.

## Purpose

Browse the audit-trail history recorded in the OpenStudyBuilder graph database —
who changed what, when, and why — across library elements and study definitions.

## Concept & definitions

- **Library Audit Trail** — history of changes across all library elements.
- **Study Audit Trail** — history of changes across all study definitions.
- **Reason for change** — captured per change for library elements (GCP
  compliant); for studies it is captured at study lock and browsed under study
  versioning.

## When to use

Use when you need a cross-cutting history of changes filtered by user or date
range. Do **not** use it to inspect the history of one specific component — the
in-app History pages give a better focused view.

## Report tabs

The report is organised in different tabs, each supporting a different purpose. To open the report, see [Open NeoDash](./#open-neodash) on the section landing page.

| Tab | Use it to… |
| --- | --- |
| **ReadMe** | Get oriented — what the audit trail records, the filter parameters, and the tables shown. Start here. |
| **Library Audit Trail** | Browse the history of changes across all library elements; filter by user and/or date range, then drill into one action. |
| **Study Audit Trail by Date** | Browse changes to a study's definition within a date range; pick a study, then drill into one action. |
| **Study Audit Trail by Version** | Browse changes to a study's definition between two study versions; pick a study and a min/max version, then drill into one action. |

### ReadMe

**Purpose:** Orients you to what the audit trail records, the filter parameters available, and the tables each section produces.

**When to use:** Open this tab first, before browsing the Library or Study Audit Trail tabs.

:::details Show Quick Guide

1. Open the **ReadMe** tab to orient yourself before browsing.

[![ReadMe tab — report introduction and per-section user guides](/images/user_guides/neodash_audit_trail_readme.png)](/images/user_guides/neodash_audit_trail_readme.png)

The ReadMe is organised as three guide cards. The **Introduction** (A) explains what the report _is_ (a comprehensive picture of who changed what, when and why — value before and after, by whom, time-stamped, with a GCP-compliant reason for change) and what it _is not_ (it is not a tool for viewing the history of one specific component — the StudyBuilder UI does that). It also notes the report covers two areas: the **Library Audit Trail** (Sponsor Terms, Unit Definitions and other data surrounding the study design) and the **Study Audit Trail** (Study Design components such as Arms, Visits, etc.).

The **Library Audit Trail User Guide** (B) and **Study Audit Trail User Guide** (C) each describe their filter parameters (User ID, Start Date, End Date, Action ID — plus Study Definition for the study trail) and the detail tables produced (Actions Table; Before-and-After Values per Action ID; and, for the library trail, Outbound Relationships per Action ID).

:::

### Library Audit Trail

**Purpose:** Shows a cross-cutting history of changes to library elements, with before/after values and relationships for each action.

**When to use:** Use when you need to browse or filter library element changes by user and/or date range, and drill into a single action.

:::details Show Quick Guide

1. Optionally filter by **Select User** (A), **Select Start Date** (B) and **Select End Date** (C) — leave blank to show all.
2. In the **Actions Table** (D) click an **Action ID** to load that action's details.
3. Review the change detail in (E)–(H).

[![Library Audit Trail — Actions Table with one action expanded into its detail tables](/images/user_guides/neodash_audit_trail_library.png)](/images/user_guides/neodash_audit_trail_library.png)

Use the filters to narrow the trail: **Select User** (A) limits to one user (blank = all users), and **Select Start Date** (B) / **Select End Date** (C) bound the period (format `YYYY-MM-DD`; blank defaults to 2015 and today respectively). The **Actions Table** (D) lists every matching action — _Timestamp_, _User_, _Status_, _Action ID_, _Component ID_, _Action Type_ (CREATE, EDIT, STATUS CHANGE or NO MATCH) and _Component Labels_. Click an **Action ID** (in the worked example `1161949594583931555`, a STATUS CHANGE on the "Height" activity instance) to populate the detail cards:

- **Version/Status Changes** (E) — the version and status before/after the action (e.g. `2.0 → 2.1`, `Final → Draft`).
- **Field Value Changes** (F) — each field changed by the action, with its _Old Value_ and _New Value_.
- **Change Visualisation** (G) — a graph view of the component and its relationships for the action.
- **Outbound Relationships per Action ID Table** (H) — what the component was related to before/after, with a _Relationship Change_ of CREATED, DROPPED, MAINTAINED or NO CHANGE.

> [!NOTE]
> The detail cards stay empty until an Action ID is selected. The Actions Table is capped at 1000 rows.

:::

### Study Audit Trail by Date

**Purpose:** Shows the history of changes to a study's definition within a date range, with drill-down into each action's field changes.

**When to use:** Use when you need to review a study's changes by calendar date and drill into a single action.

:::details Show Quick Guide

1. Optionally filter by **Select User** (A), **Select Start Date** (B) and **Select End Date** (C).
2. Pick a study in **Select Study UID** (E) — the **Actions Table on Study_…** (F) then lists that study's actions.
3. Click an **Action ID** in (F) to load **Change Visualisation** (G) and **Field Value Changes** (H).

[![Study Audit Trail by Date — Study_000002 actions with one action expanded](/images/user_guides/neodash_audit_trail_study_by_date.png)](/images/user_guides/neodash_audit_trail_study_by_date.png)

The optional filters **Select User** (A), **Select Start Date** (B) and **Select End Date** (C) work as on the Library tab. The **Actions Table** (D) shows actions across all studies (with a _Study UID_ column); to focus on one study, pick it in **Select Study UID** (E) — in the worked example `Study_000002`. The **Actions Table on Study_000002** (F) then lists that study's actions (_Timestamp_, _Action ID_, _Component UID_, _Action Type_). Click an **Action ID** (here `1331030`, a Create on a StudyActivitySchedule) to populate the **Change Visualisation** graph (G) and the **Field Value Changes** table (H) with the action's before/after field values.

> [!NOTE]
> (G) and (H) stay empty until an Action ID is selected.

:::

### Study Audit Trail by Version

**Purpose:** Shows the history of changes to a study's definition between two study versions, with drill-down into each action's field changes.

**When to use:** Use when you need to compare a study's changes across specific study versions rather than by calendar date.

:::details Show Quick Guide

1. Pick a study in **Select Study UID** (A).
2. Select a row in **both** **Select Study Min Date Version** (B) and **Select Study Max Date Version** (C) — this defines the version window. (E) **Selections Table** confirms the chosen study and version dates.
3. In **Actions Table on Study_…** (F) click an **Action ID** to load **Change Visualisation** (G) and **Field Value Changes** (H). Optionally narrow by **Select User** (D).

[![Study Audit Trail by Version — Study_000002 between two versions, one action expanded](/images/user_guides/neodash_audit_trail_study_by_version.png)](/images/user_guides/neodash_audit_trail_study_by_version.png)

Pick the study in **Select Study UID** (A) — in the worked example `Study_000002`. Then choose the version window: select a row in **Select Study Min Date Version** (B) and one in **Select Study Max Date Version** (C); each row is a study version with its _Version Status_ and timestamp. The **Selections Table** (E) echoes the resolved selection (study UID + selected start/end version datetimes), and **Select User** (D) optionally filters by user. The **Actions Table on Study_000002** (F) lists the study's actions in that window; click an **Action ID** (here `1418135`, a Create on a StudyActivitySchedule) to populate the **Change Visualisation** graph (G) and the **Field Value Changes** table (H).

> [!IMPORTANT]
> You must select a row in **both** the Min and Max version cards. If only date-style parameters are present (for example carried over from the _by Date_ tab), the Actions Table can error with _"Cannot select datetime from: …"_; selecting the two version rows supplies full version datetimes and clears it.

:::

:::details Show Solution Architecture

The OpenStudyBuilder system is based on a linked graph database, and the audit
trail is an integrated part of how versioning is supported — see
[Versioning and Audit Trail](../userguides_introduction.html#versioning-and-audit-trail).
Study-definition reason-for-change is recorded at study lock, not per field.

:::

## Common errors

| Symptom | Interpretation | Likely cause | Fix |
| --- | --- | --- | --- |
| Reason for change is blank for a study change | Expected — not a missing value | Study reasons are captured at lock, not per change | Browse reasons under [study versioning](../studies/manage_studies.html#maintain-study-status-and-versioning) |
| Hard to see one component's history | This report is the wrong tool for that view | The Audit Trail is cross-cutting, not component-scoped | Use the in-app History page for that component |
| _"Cannot select datetime from: …"_ on **Study Audit Trail by Version** | A genuine input error, easily corrected | Date-style parameters carried over from another tab instead of version datetimes | Select a row in **both** the Min and Max version cards to supply full version datetimes |
| An Actions Table looks truncated | A display limit, not data loss | Tables are capped at a 1000-row display limit | Narrow the list with the user/date filters, or the study/version selection |

If this does not resolve the issue, contact your OpenStudyBuilder administrator.

## Related topics / links

- [Versioning and Audit Trail](../userguides_introduction.html#versioning-and-audit-trail)
- [Maintain study status and versioning](../studies/manage_studies.html#maintain-study-status-and-versioning)
- [Reports and Dashboards](./)
