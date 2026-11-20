# Activity Instance Export

**Where to find it:** Reports button → NeoDash → "Activity Instance Export" in the Report navigation panel.

## Purpose

A report for users who need to list, review or export the **items** that make up one or more activity instances in the Study Builder Library. For each selected activity instance it shows the activity instance class it belongs to, each of its activity items, and the codelist and terms selected for that item. The result can be downloaded as a CSV file.

## Concept & definitions

- **Activity instance** — a specific, versioned definition of how an activity is collected or derived (for example a particular measurement), described by a set of activity items.
- **Activity instance class** — the class in the Activity Instance Class model that the activity instance belongs to. It determines which items the instance can or must have.
- **Activity item** — one piece of information on an activity instance, such as a parameter, a unit or a result category. Each item is based on an **activity item class**.
- **Codelist and terms** — an activity item can point to a controlled terminology codelist and the terms selected from it. The report shows these in one value, written as `codelist:term1|term2`, using the submission values.
- **Version type** — the report shows either the latest **Final** version of each activity instance (**Latest Final**, the default) or its **Latest** version, which can be a Draft. With **Latest Final**, instances that only exist as Draft are not listed.

## When to use

Use when you need a flat list of the items of selected activity instances, for example to review how instances are defined, to compare instances, or to export the definitions for use outside OpenStudyBuilder.

## Report tabs

The report is organised in tabs. To open the report, see [Open NeoDash](./#open-neodash) on the section landing page.

| Tab | Use it to… |
| --- | --- |
| **ReadMe** | Get oriented — a short summary of the report's scope and how to use it. Start here. |
| **Activity Items** | Select activity instances and list (and download) their activity items. |

### ReadMe

**Purpose:** Gives a short summary of the report's scope and functionality.

**When to use:** Start here to get oriented before moving to the **Activity Items** tab.

:::details Show Quick Guide

1. Open the **ReadMe** tab.
2. Read the summary before moving to the **Activity Items** tab.

:::

### Activity Items

**Purpose:** Lists the activity items of the selected activity instances, one row per item.

**When to use:** Use when you want to review, compare or export the items of one or more activity instances.

:::details Show Quick Guide

1. Open the **Activity Items** tab.
2. In **Select Version Type** (A), keep the default **Latest Final** or choose **Latest**.
3. In **Select Activity Instances**, type part of an activity instance name in the field (B). The matching names are listed below the field (C). Pick the activity instance you want; repeat to add more instances.

[![Select Activity Instances](/images/user_guides/neodash_activity_instance_export_select_instance.png)](/images/user_guides/neodash_activity_instance_export_select_instance.png)

4. The selected activity instances are shown in the field (A in the next figure). Review the rows in the **Activity items** table (B); use **Rows per page** (D) to show more rows at a time.
5. Optionally click the download icon (C) to export the rows to a CSV file.

[![Activity items for the selected instance](/images/user_guides/neodash_activity_instance_export_results.png)](/images/user_guides/neodash_activity_instance_export_results.png)

**Select Version Type** decides which version is reported. **Latest Final** shows the latest Final version of each activity instance; **Latest** shows its latest version, which can be a Draft. The choice applies to the activity instance and also to its activity grouping, activity instance class and activity item classes. Changing it changes the names offered in **Select Activity Instances**.

**Select Activity Instances** is a multi-select. It suggests the names of the activity instances that have a version of the selected type and contain the text you typed (ignoring upper and lower case), in alphabetical order and up to 500 at a time, so type more of the name to narrow the list. Up to 20 activity instances can be selected at once. Until at least one is selected, the table shows the message _Select Activity Instances above_.

The **Activity items** table has one row per activity item and these columns. An activity instance without any activity items is still listed, as a single row where **ACTIVITY_ITEM_TYPE** and **ACTIVITY_ITEM_VALUE** are empty.

| Column | Content |
| --- | --- |
| **ACTIVITY_INSTANCE_NAME** | Name of the selected activity instance. |
| **ACTIVITY_ITEM_CLASS_NAME** | Name of the activity instance class that the instance belongs to. |
| **ACTIVITY_ITEM_TYPE** | Name of the activity item class the item is based on. Empty when the instance has no items. |
| **ACTIVITY_ITEM_VALUE** | The item's codelist and selected terms, written as `codelist:term1\|term2`. Empty when the item has no codelist. |
| **IS_ADAM_PARAM_SPECIFIC** | Reserved for the export format. Always empty in this report. |

Rows are sorted by activity instance name and then by item type.

> [!NOTE]
> The data displayed depends on the database content. The terms shown are the submission values of the terms currently selected on the item, and the codelist is shown by its submission value, taken from the latest version of the codelist attributes.

> [!TIP]
> To change the sort order, hide columns or filter the rows, use the column menu (**⋮**) described under [General features](./#general-features) on the section landing page. The CSV download follows the same table.

:::

:::details Show Solution Architecture

The report is a single custom Cypher query over the Library part of the graph:

- Starts from `ActivityInstanceValue` nodes whose `name` is in the selected values, and only those that are the target of a relationship of the selected version type (`LATEST_FINAL` or `LATEST`, from the **Select Version Type** parameter).
- Optionally follows `CONTAINS_ACTIVITY_ITEM` to each `ActivityItem`, and `HAS_ACTIVITY_ITEM` to the `ActivityItemClassRoot` and its `ActivityItemClassValue` of the selected version type (the item class name). Because these steps are optional, an instance without items still returns one row, with an empty item type.
- Follows `ACTIVITY_INSTANCE_CLASS` to the `ActivityInstanceClassRoot` and its `ActivityInstanceClassValue` of the selected version type (the instance class name).
- Requires, in an `EXISTS` check, that the instance has an activity grouping of the selected version type (`HAS_GROUPING_ROOT` → `ActivityInstanceGroupingRoot` → `LATEST_FINAL` or `LATEST` → `ActivityInstanceGroupingValue` → `ActivityGrouping` ← `ActivityValue`). Instances without such a grouping do not appear. The same is true for instances without an activity instance class of the selected version type.
- Optionally follows `HAS_CT_TERM` from the item to a `CTTermContext`, and from there to the selected term (`HAS_SELECTED_TERM` → `CTTermRoot` ← `HAS_TERM_ROOT` ← `CTCodelistTerm`) and the selected codelist (`HAS_SELECTED_CODELIST` → `CTCodelistRoot`, with the `LATEST` `CTCodelistAttributesValue` giving the codelist submission value).
- Groups the rows by instance, instance class, item class and codelist, and joins the distinct term submission values of each group with `|`.

The **Select Version Type** control offers the two relationship types `LATEST` and `LATEST_FINAL` and stores the choice in a parameter (default **Latest Final**). The **Select Activity Instances** control searches the `name` property of the `ActivityInstanceValue` nodes that are the target of a relationship of that type, with a case-insensitive "contains" match, and returns the distinct names sorted alphabetically and limited to 500.

:::

## Common errors

| Symptom | Interpretation | Likely cause | Fix |
| --- | --- | --- | --- |
| The table shows _Select Activity Instances above_ | Nothing is selected yet, not an error | No activity instance has been picked in the selector | Pick at least one activity instance |
| The table is empty after selecting an instance | The instance has no rows in this report | The instance has no version of the selected type, no activity grouping of that type, or no activity instance class of that type | Check the instance in the Library: finalise it and make sure it has a grouping, or switch **Select Version Type** to **Latest**. Compare with the [Activity Metadata Check](activity-metadata-check.md) report |
| The instance has one row and **ACTIVITY_ITEM_TYPE** is empty | The instance has no activity items | No items have been added to the instance, or its items have no activity item class of the selected version type | Review the items on the activity instance in the Library. Compare with the [Activity Metadata Check](activity-metadata-check.md) report |
| The instance I am looking for is not suggested | The suggestion list is limited | Only the first 500 matching names (alphabetically) are shown, and only those with a version of the selected type | Type more of the name to narrow the matches, and check that **Select Version Type** is set as intended; a Draft-only instance needs **Latest** |
| **ACTIVITY_ITEM_VALUE** is empty for an item | The item has no codelist selection | The item is not controlled by a codelist, or no term has been selected | Expected for such items; review the item on the activity instance in the Library if a value is missing |
| A selected term is missing from **ACTIVITY_ITEM_VALUE** | The term is not selected on the current item | The item selection has changed, or the codelist has no codelist attributes | Review the item selection on the activity instance in the Library |

If this does not resolve the issue, contact your OpenStudyBuilder administrator.

## Related topics / links

- [Activity Library Dashboard](activity-library-dashboard.md)
- [Activity Metadata Check](activity-metadata-check.md)
- [Reports and Dashboards](./)
