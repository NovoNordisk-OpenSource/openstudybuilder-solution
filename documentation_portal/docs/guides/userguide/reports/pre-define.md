# Pre-Define

**Where to find it:** Reports button → NeoDash → "Pre-Define" in the Report navigation panel.

## Purpose

Shows a define.xml-style view of a study's datasets, variables, and controlled
terminology against a chosen sponsor SDTM data model standard. Variables are
resolved from the chosen standard itself; the list of Datasets (domains) and
the item list shown in **Codelist/Terms** both depend on the Activities and
Activity Instances selected in the study's Schedule of Activities (SoA) — so
you can get a feeling for how the study's define.xml and its Value-Level
Metadata (VLM) will look before it is generated.

> [!NOTE]
> As this is a NeoDash report, it does not create a true define.xml file.

## Concept & definitions

- **define.xml** — the CDISC-standard metadata file that describes a study's
  datasets, variables, and controlled terminology for a regulatory submission.
- **Standard (Sponsor Model)** — the Sponsor Model IG and its underlying CDISC
  Model IG version (for example `sdtmig_mastermodel_3.3_NN01`, based on SDTMIG
  v3.3) that this report resolves datasets and variables against. Chosen in
  **Standard selection**.
- **SDTM CT version** — the SDTM Controlled Terminology package used to
  resolve codelists and terms for a variable.
- **Study version / subpart** — a study can have multiple versions over time
  (DRAFT or LOCKED), and can be split into subparts (for example a device
  used on top of a drug study). The report always works against one specific
  version or subpart at a time, picked by row in **Select study version or
  subpart**.
- **Dataset** — an SDTM domain (for example AE, HO) applicable to the study,
  derived from the Activities and Activity Instances selected in the study's
  SoA.

## When to use

Use before generating or reviewing a study's define.xml, to check which
datasets, variables, and controlled terminology would be included for a given
standard and CT version — and to catch missing SoA selections, or a
standard/version mismatch, early.

## Report tabs

The report is organised in different tabs, each supporting a different purpose. To open the report, see [Open NeoDash](./#open-neodash) on the section landing page.

| Tab | Use it to… |
| --- | --- |
| **ReadMe** | Get oriented on the select-study / select-standard / review-datasets workflow. Start here. |
| **Pre-Define.xml** | Select a study version (or subpart), an SDTM Sponsor Model standard, and an SDTM CT version, then review the resulting datasets, variables, and codelist/terms. |

### ReadMe

**Purpose:** Introduces the report and summarises its three-step workflow.

**When to use:** Start here before reviewing a study's define.xml view, to get oriented on the report's workflow.

:::details Show Quick Guide

[![ReadMe tab overview](/images/user_guides/neodash_pre_define_readme.png)](/images/user_guides/neodash_pre_define_readme.png)

The ReadMe tab explains:

1. **Select a Study** — use **Filter Study** and/or **Filter subpart for**
   (each narrows the other; start typing to refresh the list), then pick a
   specific version or subpart in **Select study version or subpart** (the
   LATEST version first, then the others, most recent first).
2. **Select a standard** — choose the Sponsor Model IG in **Standard
   selection** and the SDTM Controlled Terminology package in **Select SDTM
   CT version**.
3. **Review datasets** — **Datasets** lists the datasets derived from the
   Activities and Activity Instances in the study's SoA; click a dataset to
   see its variables (defined by the standard), and a variable's codelist to
   see its terms and the Topic Variables they apply to (VLM). If no terms
   are shown, the item is either not defined for the Activity Instances
   included in the study, or has no terms defined.

:::

### Pre-Define.xml

**Purpose:** Lets you pick a study version (or subpart) and a standard, then drills from Datasets down to variables and codelist/terms.

**When to use:** Use to check which datasets, variables, and controlled terminology a study would produce in its define.xml for a given standard and CT version.

:::details Show Quick Guide

**Select a study**

[![Pre-Define.xml tab before any selection — Filter Study (A), Filter subpart for (B), Select study version or subpart (C)](/images/user_guides/neodash_pre_define_study_selection_cards.png)](/images/user_guides/neodash_pre_define_study_selection_cards.png)

**Filter Study** (A) and **Filter subpart for** (B) are two independent entry
points into the same selection, and each one narrows the other. Start from
whichever you know:

1. **Start from the study** — pick a Study Number in **Filter Study** (A).
   **Filter subpart for** then offers only that study's subparts (B).

[![Filter Study set to CDISC DEV-7567 (A); Filter subpart for offers only its subpart (B)](/images/user_guides/neodash_pre_define_study_narrows_subpart.png)](/images/user_guides/neodash_pre_define_study_narrows_subpart.png)

2. **Or start from the subpart** — pick a subpart acronym in **Filter
   subpart for** (A). **Filter Study** then offers only the studies that have
   that subpart (B).

[![Filter subpart for set to MD on top SD (A); Filter Study offers only CDISC DEV-7567 (B)](/images/user_guides/neodash_pre_define_subpart_narrows_study.png)](/images/user_guides/neodash_pre_define_subpart_narrows_study.png)

> [!TIP]
> The narrowed list only appears once you start typing. Opening an empty
> dropdown can still show the full, unfiltered list — type at least one
> character to refresh it.

**Study subparts** — some studies are split into subparts (for example a
device used on top of a drug study). For such a study, **Select study version
or subpart** shows a SubpartTrialID button (A) next to the TrialID. With a
subpart chosen in **Filter subpart for** (B), the table lists only that
subpart's rows. Click the SubpartTrialID button to pick the subpart record.

[![SubpartTrialID button (A) and Filter subpart for set to MD on top SD (B), for CDISC DEV-7567](/images/user_guides/neodash_pre_define_subpart_selection.png)](/images/user_guides/neodash_pre_define_subpart_selection.png)

3. **Select study version or subpart** (A) lists every version of the study
   with its DRAFT/LOCKED status. The **LATEST** row comes first, followed by
   the other versions, most recent first. Click the TrialID button on a row
   (B) to pick that specific study record. The rest of this walkthrough uses
   the LATEST version of CDISC DEV-0.

[![Select study version or subpart for CDISC DEV-0 with the LATEST row first (A); TrialID button of the LATEST row (B)](/images/user_guides/neodash_pre_define_select_version.png)](/images/user_guides/neodash_pre_define_select_version.png)

4. The **Study** details card (A) then shows the selected version's own
   properties (Study ID, Description, Acronym, Date, Version, Latest,
   Status). Set **Rows per page** to 10 to see all of them at once.

[![Study details card populated for the selected version (A)](/images/user_guides/neodash_pre_define_study_details.png)](/images/user_guides/neodash_pre_define_study_details.png)

> [!IMPORTANT]
> Selecting a specific version/subpart row — not just the Study Number — is
> what drives the Study details card and every card further down the report.
> Until you click a row, the Study card keeps showing the previously
> selected record.

**Select a standard**

[![Select SDTM CT version (A) and Standard selection (B)](/images/user_guides/neodash_pre_define_ct_and_standard.png)](/images/user_guides/neodash_pre_define_ct_and_standard.png)

1. Choose a package in **Select SDTM CT version** (A) — the Controlled
   Terminology used to resolve codelists and terms (here SDTM CT 2025-03-28).
2. Click **SELECT** on a row in **Standard selection** (B) to choose the
   Sponsor Model IG and its underlying CDISC Model IG version (here
   `sdtmig_mastermodel_3.3_NN03`, based on SDTMIG v3.3).

**Review datasets**

1. **Datasets** (A) lists the SDTM domains applicable to the selected study
   record for the chosen standard. The list is derived from the Activities
   and Activity Instances selected in the study's SoA — for CDISC DEV-0 this
   gives domains such as LB, DS, MH, VS, and AE. Where the Sponsor Model
   extends a domain, **Sponsor Dataset** shows the sponsor dataset name.
   Click a dataset's button (B, here **VS**) to see its variables.

[![Datasets using sdtmig_mastermodel_3.3_NN03 for CDISC DEV-0 (A); VS dataset button (B)](/images/user_guides/neodash_pre_define_datasets.png)](/images/user_guides/neodash_pre_define_datasets.png)

2. The variables card (A) lists the dataset's variables as defined by the
   chosen standard — CDISC core, type, length, role, and any applicable
   codelist. This card does not depend on the study. Click a variable's
   Codelist button (B) to see its terms — here **VSRESU** on the VSORRESU
   variable (use the table's page arrows to reach it).

[![VS Using sdtmig_mastermodel_3.3_NN03 variables card (A); VSRESU Codelist button on VSORRESU (B)](/images/user_guides/neodash_pre_define_vs_variables.png)](/images/user_guides/neodash_pre_define_vs_variables.png)

3. **Codelist/Terms** (B) lists the terms of the selected codelist (A) that
   are used by the study's Activity Instances, resolved against the chosen
   CT package. The **For Topic Variable** column (C) shows which Topic
   Variable each term applies to — the study's Value-Level Metadata (VLM).
   For VSRESU, the units cm, in, and m apply to HEIGHT, beats/min to PULSE,
   and breaths/min to RESP.

[![VSRESU Codelist button (A); Codelist/Terms - VSRESU card (B); For Topic Variable column showing the VLM (C)](/images/user_guides/neodash_pre_define_codelist_terms_vlm.png)](/images/user_guides/neodash_pre_define_codelist_terms_vlm.png)

> [!NOTE]
> If **Codelist/Terms** shows "Query returned no data." for a codelist, the
> item is either not defined for any of the Activity Instances included in
> the study, or it has no terms defined. The card title still updates to the
> codelist name, so you can confirm the selection itself worked.

4. **See which Activity Instances are in the domain** — click the **DOMAIN**
   Codelist button (A) on the DOMAIN variable. **Codelist/Terms - DOMAIN**
   (B) then shows the dataset's own domain term (here VS, Vital Signs
   Domain), and its **For Topic Variable** column (C) lists the Topic
   Variables of every Activity Instance in the study that maps to this
   domain — here WEIGHT, PULSE, HEIGHT, RESP, and RESPRATE.

[![DOMAIN Codelist button on the VS variables card (A); Codelist/Terms - DOMAIN (B); For Topic Variable listing the Activity Instances in the VS domain (C)](/images/user_guides/neodash_pre_define_codelist_domain.png)](/images/user_guides/neodash_pre_define_codelist_domain.png)

:::

## Common errors

| Symptom | Interpretation | Likely cause | Fix |
| --- | --- | --- | --- |
| **Select study version or subpart** shows "Query returned no data." | Not an error | No Study Number has been typed into **Filter Study** yet | Type a Study Number and pick a row |
| **Datasets** is empty after selecting a version and a standard | Not necessarily an error | The selected study version has no datasets derived from its SoA (Activity/Activity Instance) selections for the chosen standard | Confirm the study's SoA has Activities/Activity Instances selected; try a different version or Sponsor Model, or use a study known to have SoA-derived datasets |
| **Codelist/Terms** stays empty after clicking a variable's Codelist button | Not an error | The item is not defined for any of the Activity Instances included in the study, or it has no terms defined (in the chosen CT package) | Confirm the card title updated to the codelist name (the selection worked); check the Activity Instances in the study's SoA, or try a different SDTM CT version |
| The Study details card shows the study's general values, not the version you clicked | Wrong parameter was set | A row was picked in **Filter Study** (Study Number) rather than in **Select study version or subpart** | Click the specific TrialID/SubpartTrialID row in **Select study version or subpart**, not just the Study Number |

If this does not resolve the issue, contact your OpenStudyBuilder administrator.

## Related topics / links

- [Reports and Dashboards](./)
- [Data Exchange Data Models](data-exchange-data-models.md)
- [Activity Library Dashboard](activity-library-dashboard.md)
