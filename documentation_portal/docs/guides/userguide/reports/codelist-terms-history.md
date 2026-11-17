# Codelist / Terms history

**Where to find it:** Reports button → NeoDash → "Codelist / Terms history" in the Report navigation panel.

## Purpose

Browse the Controlled Terminology — both CDISC and Sponsor Codelists and
Terms — and see how a Codelist and its Terms have evolved from CT Package to
CT Package: when a Term was created, how many times it changed, whether it
is still active or has been retired, and where it is used.

## Concept & definitions

- **CT Package** — a dated, versioned snapshot of a CDISC or Sponsor
  Codelist/Term catalogue (for example a quarterly CDISC CT package). Not every
  Codelist is part of a CT Package: Sponsor Codelists typically are not, and
  **Select CT Package** then shows **(none)** in the **Package** column.
- **CT Type** — the CT catalogue a Codelist belongs to, for example SDTM CT.
  It is the same whether the Codelist is CDISC or Sponsor owned. The optional
  **CT Type** filter narrows **Pick a Codelist** to one catalogue; its extra
  value **Sponsor** narrows it to the Codelists owned by the Sponsor library.
- **Owner** — the library that owns a Codelist or Term, for example CDISC or
  Sponsor. It is separate from the CT Type: a Sponsor-owned Codelist can sit in
  a CDISC catalogue such as SDTM CT.
- **Codelist / Term** — a Codelist is a named list of controlled values; each
  value is a Term, identified by its Submission Value.
- **Term usage** — the places a Term is selected, for example an Activity Item
  of an Activity Instance, or an ODM Item on an ODM Form or Item Group. Usage
  belongs to the Term itself, not to one of its versions.
- **#Changes** — the number of times a Term's attributes have changed across
  the CT Packages that contain it, counted from its distinct version-start
  dates (a Term that has never changed since creation shows 0).
- **Retire Date / Status** — whether the Term is currently **active** or
  **retired**, taken from the status of its latest recorded version, and the
  date that Retired version started (the Retire Date stays empty for an active
  Term). A Submission Value that is no longer in the Codelist shows
  **replaced** (another Submission Value took over) or **removed** (none did).
- **Replaced Submission Value** — the Submission Value of a Term can change
  while its other attributes stay the same. The Term then appears as two
  Submission Values: the old one, which leaves the Codelist, and the new one,
  which joins it on the same date. Both share the Term's C-code.

## When to use

Use when you need to find out when a Codelist or Term was introduced, how
often a Term's attributes have changed, whether a Term is still active, or
where a Term is used — for example when investigating why a Term behaves
differently in an older study than in a current one, or before changing or
retiring a Term.

## Report tabs

The report is organised in different tabs, each supporting a different purpose. To open the report, see [Open NeoDash](./#open-neodash) on the section landing page.

| Tab | Use it to… |
| --- | --- |
| **ReadMe** | Get oriented before browsing codelists and terms and their history. Start here. |
| **Codelist and Terms** | Select a Codelist and CT Package, then drill from a codelist-level overview down into the full version history and usage of an individual Term. |

### ReadMe

**Purpose:** Introduces the report and summarises what each tab covers.

**When to use:** Start here before browsing codelist and term history, to get oriented on the report's tabs.

:::details Show Quick Guide

[![ReadMe tab — introduces the report and the Codelist and Terms tab](/images/user_guides/neodash_codelist_terms_history_readme.png)](/images/user_guides/neodash_codelist_terms_history_readme.png)

The ReadMe tab introduces the report. Besides the ReadMe tab the report holds one further tab, **Codelist and Terms**, which uses a drill-down approach: search for and select a Codelist by name in **Pick a Codelist**, then click a row in **Select CT Package** (which shows each version's CT Type, Owner and Package, limited to the versions matching the optional **CT Type** filter) to choose a CT Package and Version — selecting the Codelist first, before the CT Package, so that **Select CT Package** and **Terms History for Codelist** have something to populate.

:::

### Codelist and Terms

**Purpose:** Lets you select a Codelist and CT Package, see the Codelist as it stood in that package, and drill into the full version history and usage of any individual Term.

**When to use:** Use this tab to find out when a Codelist or Term was introduced, how many times a Term has changed, whether a Term is still active or has been retired, and where a Term is used.

:::details Show Quick Guide

[![Codelist and Terms tab — CT Type filter and Pick a Codelist (A), Codelist ID (B), Select CT Package (C), Overview at Date (D), Terms in Codelist (E), Terms History for Codelist (F), Submission Value checkbox (G), History of terms in Codelist (H), Details for Term(s) (I), Term(s) used in (J)](/images/user_guides/neodash_codelist_terms_history_codelist_and_terms.png)](/images/user_guides/neodash_codelist_terms_history_codelist_and_terms.png)

1. Optionally, choose a **CT Type** in the filter above **Pick a Codelist** to narrow the list: either a CT catalogue (for example SDTM CT) or **Sponsor** for the Codelists owned by the Sponsor library, which are typically not part of a CT Package. A catalogue lists all its Codelists, whether CDISC or Sponsor owned, so a Sponsor Codelist can appear under both its catalogue and **Sponsor**. Leave the filter empty to search all. Then, in **Pick a Codelist** (A), type and select a Codelist by name.
2. Review the **Codelist ID** card (B), which shows the Codelist's C-code — or its name for a Sponsor Codelist that has no C-code.
3. **Select CT Package** (C) lists the versions of the picked Codelist (only those matching the **CT Type** filter, if you set one) with its **CT Type** (the catalogue, for example SDTM CT, whether the Codelist is CDISC or Sponsor owned), **Owner** (the library that owns the Codelist, for example CDISC or Sponsor), **Package**, **Version** and **Date**. Click a row to choose the CT Package and Version you want to inspect — this updates the **Overview at Date** graph and the **Terms in Codelist** table. A Codelist that is not part of a CT Package shows **(none)** in the **Package** column; click its Version row all the same.
4. Review the **Overview at Date** graph (D), which displays the Codelist's Terms as they stood in the selected CT Package. For a Codelist with Package **(none)** it displays the Terms currently in the Codelist.
5. Review the **Terms in Codelist** table (E), the tabular twin of the graph. For each Term it lists the Submission Value, C-code, Preferred Term, Synonyms, Definition, Term Version, Term Status, Start Date and Term Owner. Use the download icon to export it.
6. Review the **Terms History for Codelist** table (F), which lists every Term recorded for the Codelist across all CT Packages, with:
   - **Codelist Owner** / **Term Owner** — the library that owns the Codelist / Term.
   - **Term C-code** / **Submission Value** — the Term's identifiers.
   - **Replaces** / **Replaced by** — if the Term's Submission Value was changed, the other Submission Value and the date of the change. For example, `UNDIFFERENTIATED` shows **Replaced by** `INTERSEX (2023-12-15)` and `INTERSEX` shows **Replaces** `UNDIFFERENTIATED (2023-12-15)`. Empty for a Term whose Submission Value never changed.
   - **In Codelist** — the period the Submission Value was in the Codelist. A Submission Value that was removed and later added again has one row for each period.
   - **#Changes** — how many times the Term's attributes have changed. A change of Submission Value is not counted here; see **Replaces** / **Replaced by**.
   - **Creation Date** / **Date of Change(s)** — when the Term was created and, if it changed, every later change date.
   - **Retire Date** / **Status** — the date the Term was retired (empty for an active Term), and whether it is **active**, **retired**, **replaced** or **removed**. Retired is taken from the status of the Term's latest version.
7. Tick one or more Terms' **Submission Value** checkboxes (G) in that table to select them.
8. Review the **History of terms in Codelist** timeline (H), which plots a bar per Term version. If you ticked one or more Terms in step 7, only those are shown; otherwise every Term in the Codelist is plotted. Where a version changed an attribute from the one before it, the bar's tooltip shows the old value in green and the new value in red. A Term whose Submission Value was changed is plotted as one chain of bars: the bars of each Submission Value are limited to the period that value was in the Codelist and labelled with it followed by the Term's C-code, for example `INTERSEX (C45908)`, and an arrow leads from the old Submission Value to the new one.
9. Review the **Details for Term(s)** table (I) for the attributes of the Term(s) you ticked, one row per recorded version. **Start Date**, **End Date** and **Version** are those of the Term's attributes, which are versioned separately from the Submission Value; **In Codelist** gives the period the Submission Value was in the Codelist. If a ticked Term had its Submission Value changed, the rows of the old and the new Submission Value are both shown, with **In Codelist** giving the period of each and the changed Submission Value highlighted in red.
10. Review the **Term(s) used in** table (J) to see where the ticked Term(s) are used — for example the Activity Instance of an Activity Item, or the ODM Form and Item Group of an ODM Item. Each row gives the Term's **C-code** (or its Sponsor code, for a Term that has no C-code), Submission Value and Term version. A Term that is not used anywhere shows **Not used**.

> [!NOTE]
> Only the **CT Type** filter and **Pick a Codelist** are available from the start. The filter narrows both the Codelists offered by **Pick a Codelist** and the rows shown by **Select CT Package**; changing it does not clear a Codelist you have already picked. The other cards stay empty ("Query returned no data" or a prompt to select a Codelist) until a Codelist is selected. **Overview at Date** and **Terms in Codelist** also need a row chosen in **Select CT Package**.
>
> Only **Overview at Date** and **Terms in Codelist** depend on the selected CT Package. **Terms History for Codelist**, **History of terms in Codelist**, **Details for Term(s)** and **Term(s) used in** look across all CT Packages, and work for every Codelist, with or without a CT Package.
>
> Ticking a Term's **Submission Value** checkbox also selects any other Term row that shares the same Submission Value — the checkbox selects by Submission Value, not by row.
>
> Ticking one Submission Value of a Term whose Submission Value was changed also includes the other Submission Value of that Term in **History of terms in Codelist** and **Details for Term(s)**, so the full lineage is shown.
>
> **Term(s) used in** lists usage per Term, not per Term version, so the same usage is shown under every version of the Term. Only the versions that were in the Codelist under the ticked Submission Value are listed, the same as in **Details for Term(s)**.

> [!TIP]
> For a Codelist with Package **(none)**, **Terms in Codelist** and **Overview at Date** show the Terms currently in the Codelist, not a snapshot of an older Codelist version.

The same tab for a Sponsor Codelist without a CT Package (**Epoch Allocation**, picked with the **CT Type** filter set to **Sponsor**). **Codelist ID** (B) shows the name because the Codelist has no C-code, and **Package** in **Select CT Package** (C) shows **(none)**:

[![Codelist and Terms tab for a Codelist without a CT Package — Epoch Allocation, with Term ACTUAL TREATMENT ticked](/images/user_guides/neodash_codelist_terms_history_package_less.png)](/images/user_guides/neodash_codelist_terms_history_package_less.png)

:::

:::details Show Solution Architecture

The tab layers two levels of history over one Codelist. The **Select CT
Package**, **Overview at Date** and **Terms in Codelist** cards resolve the
Codelist as it was packaged on a specific date — the Codelist's own version at
that point in time — through the CT Package, its Codelists and its Terms. A
Codelist that is not part of any CT Package has no such snapshot: **Select CT
Package** then shows **(none)**, and **Overview at Date** and **Terms in
Codelist** fall back to the Terms currently linked to the Codelist.

The **Terms History for Codelist**, **History of terms in Codelist**, and
**Details for Term(s)** cards instead start from the Codelist's own Terms and
walk every `HAS_VERSION` relationship recorded for each Term across all CT
Packages, independent of which package is selected, so a Term's full change
history is visible even if it spans many packages, and also for Codelists
outside any package. **#Changes** is derived by counting the distinct
version-start dates collected for a Term and subtracting one for its initial
creation, so a Term with a single version shows 0.

A change of Submission Value is not stored in the Term's attributes but on the
link between the Codelist and the Term (`HAS_TERM`): the old Submission Value's
link is end-dated and a new one is started, both pointing to the same Term. The
three cards therefore read these link dates as well. **Terms History for
Codelist** has one row for each period a Submission Value was in the Codelist
(periods that follow on from each other, as when a Term is reordered, count as
one) and pairs two Submission Values of the same Term in the same Codelist,
where one ended before the other started, to fill **Replaces** / **Replaced by**,
taking the nearest following value as the successor. The two need not touch:
when there is a gap between them, the Term was out of the Codelist for a while,
and **In Codelist** shows the period of each value. A Submission Value shows
**removed** only when no other value of the Term follows it.
**History of terms in Codelist** and **Details for Term(s)** add the other
Submission Values of the ticked Term and show each attribute version only for
the period that Submission Value was in the Codelist. This applies to every
Term, including one with a single Submission Value: versions that ended before
the Term joined the Codelist, or started after it left, are left out. A
Submission Value that was removed and later added again has several separate
periods in the Codelist; each period is handled on its own, so no version is
shown for the gap in between. Links that merely follow on from each other, as
when a Term is reordered, count as one period. The
bars in **History of terms in Codelist** are clipped to the period in the
Codelist, whereas **Details for Term(s)** keeps each attribute version's own
dates and version number and shows the Submission Value's period separately in
**In Codelist**.

The **Term(s) used in** card looks up where a Term is selected through its
term context. Usage is attached to the Term itself rather than to one of its
versions, and the Term's versions and those of the Activity Instance or ODM
item that uses it are versioned independently of each other. The card therefore
repeats the same usage under every listed version of the Term instead of trying
to match version dates. The listed versions are limited to the period the
Submission Value was in the Codelist, using the same bounds as **Details for
Term(s)**, so both cards show the same versions. The **C-code** column shows the
Term's C-code, or its Sponsor code for a Term that has none. An ODM Item that is
not part of any Item Group is listed as **Not in any Item Group**.

See
[Clinical MDR Database Architecture](../../architecture/mdr_data_architecture.md)
for how `HAS_VERSION`, `start_date`, and `end_date` represent a term's
open/closed versions.

:::

## Common errors

| Symptom | Interpretation | Likely cause | Fix |
| --- | --- | --- | --- |
| **Select CT Package**, **Terms in Codelist** or **Terms History for Codelist** shows "Query returned no data" or asks you to select a Codelist | Expected — not an error | No Codelist has been selected yet in **Pick a Codelist**, or no row has been chosen in **Select CT Package** | Select a Codelist first, then click a row in **Select CT Package**; the dependent cards populate once chosen |
| **Package** shows **(none)** | Expected — not an error | The Codelist, typically a Sponsor Codelist, is not part of any CT Package | Click the Version row anyway; **Overview at Date** and **Terms in Codelist** then show the Terms currently in the Codelist |
| **#Changes** shows 0 for a Term you know has changed | Not necessarily an error | The Term has only one recorded version in the CT Packages currently loaded | Confirm the expected earlier/later CT Package has been imported |
| The same Term appears as two rows in **Terms History for Codelist**, with the same C-code | Expected — not an error | The Term's Submission Value was changed (see **Replaces** / **Replaced by**), or the same Submission Value was removed and added again, which gives one row per period | Read the two rows as one Term; **In Codelist** shows which value applied when |
| **Status** shows **replaced** or **removed** | Expected — not an error | The Submission Value is no longer in the Codelist: another value took over (**replaced**) or none did (**removed**) | No action needed; see **Replaced by** for the successor |
| **Term(s) used in** shows **Not used** | Not necessarily an error | Nothing currently selects the Term, for example in an Activity Item or ODM Item | No action needed; if you expected usage, check the Term's Submission Value is the one you ticked |
| **Term(s) used in** repeats the same rows for each version of a Term | Expected — not an error | Usage belongs to the Term, not to a single Term version; the versions listed are those that were in the Codelist under the ticked Submission Value | Read the rows once; the version column only identifies the Term version listed, and the versions match **Details for Term(s)** |

If this does not resolve the issue, contact your OpenStudyBuilder administrator.

## Related topics / links

- [Reports and Dashboards](./)
