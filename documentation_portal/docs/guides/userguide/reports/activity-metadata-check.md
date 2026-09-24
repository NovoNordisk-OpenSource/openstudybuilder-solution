# Activity Metadata Check

**Where to find it:** Reports button → NeoDash → "Activity Metadata Check" in the Report navigation panel.

## Purpose

A dashboard for users who maintain the definition of activities and activity
instances in the Study Builder Library. It checks whether activity instances have
the required items and whether activities/instances are assigned to valid
groupings.

## Concept & definitions

- **Missing mandatory items** — required items absent from an activity instance,
  per the Activity Instance Class model.
- **Grouping** — the group/subgroup relationship that links activities and their
  instances; the report flags missing or invalid groupings.

## When to use

Use when curating the activity library, to find activity instances with missing
mandatory items or activities lacking valid groupings.

## Report tabs

The report is organised in different tabs, each supporting a different purpose. To open the report, see [Open NeoDash](./#open-neodash) on the section landing page.

<a id="tabs_in_report"></a>

[![Tabs in report](/images/user_guides/neodash_activity_metadata_check_tabs.png)](/images/user_guides/neodash_activity_metadata_check_tabs.png)

Some of the tabs go in pairs, indicated by the yellow underline in the [`Tabs in report`](#tabs_in_report).

| Tab | Use it to… |
| --- | --- |
| **ReadMe** | Get oriented — a short summary of the report's scope and functionality. Start here. |
| **Search bottom-up** | Browse groupings of activities and activity instances from the bottom up. |
| **List of Missing Activity Items for Activity Instances** | Filter top-down and list activity instances that have missing mandatory items. |
| **Grouping Check** | Check the status of activity groupings and spot outdated activity/instance versions. |
| **Display missing groupings** | Review counts of activities and instances with and without valid groupings. |

### ReadMe

**Purpose:** Gives a short summary of the report's scope and functionality.

**When to use:** Start here to get oriented before moving to the other tabs.

:::details Show Quick Guide

1. Open the **ReadMe** tab.
2. Read the summary of the report's scope before moving to the other tabs.

The two main things this dashboard focuses on are:

* to check if an activity instance has the required items
* to check if the activities and activity instances are assigned to valid groupings

Provides a short summary of the report's scope and functionality.

:::

### Search bottom-up

**Purpose:** Displays groupings of activities and activity instances from the bottom up.

**When to use:** Use when you want to browse activity groupings by starting from an activity or instance rather than a top-down search.

:::details Show Quick Guide

1. Open the **Search bottom-up** tab.
2. Search for activities to view the groupings of activities and activity instances.

This tab has been included for general display of groupings of activities and activity instances.
Please see [Activity Lib (search bottom-up)](activity-library-dashboard.md#activity-lib-search-bottom-up) for how that panel works.

:::

### List of Missing Activity Items for Activity Instances

**Purpose:** Lists activity instances that are missing mandatory items, filtered by a top-down search.

**When to use:** Use when you need to find and narrow down which activity instances have missing mandatory items.

:::details Show Quick Guide

1. Make a top-down search to limit the activities shown.
2. Review the listed activity instances that have missing mandatory items.
3. Use the full-path view to see missing items from other classes than the immediate parent.

The tabs _Activity Lib (search top-down)_ and the _List of Missing Mandatory Items for Instances_ go hand in hand.

#### Search top-down

To limit the number of activities shown in the _List of Missing Mandatory Items for Instances_ the user can make a top-down search. Please see [Activity Lib (search top-down)](activity-library-dashboard.md#activity-lib-search-top-down) for how that panel works.

#### Display missing items

On the _List of Missing Mandatory Items for Instances_ tab a list of Activities that has missing mandatory items are displayed.

Having made the following filter on the _Activity Lib (search top-down)_ tab — **Activity Class** (A), **Activity Subclass** (B), **Activity Group** (C), **Activity Subgroup** (D)

[![Filter](/images/user_guides/neodash_search_filter_metadata_check_example_1.png)](/images/user_guides/neodash_search_filter_metadata_check_example_1.png)

will display the filtered list of activity instances having missing mandatory items, in **Results** (A):

[![Missing Items](/images/user_guides/neodash_missing_mandatory_items_filter_example_1.png)](/images/user_guides/neodash_missing_mandatory_items_filter_example_1.png)

Note: The data displayed depends on the database content.

#### Full Path of Missing Items

The instances and their items follow a Activity Instance Class model, see [`Class Model`](#class_model)

<a id="class_model"></a>
[![Class Model](/images/user_guides/neodash_activity_class_model.png)](/images/user_guides/neodash_activity_class_model.png)

In this tab, activity instances with missing items belonging to other classes than the immediate parent are added in listing of missing item. For the filter example above:

[![Missing Items - Full path](/images/user_guides/neodash_missing_mandatory_items_filter_example_1_full_path.png)](/images/user_guides/neodash_missing_mandatory_items_filter_example_1_full_path.png)

Note that this tab has filter buttons. These are prefilled with values from the _Activity Lib (search top-down)_ tab, but can be changed on this page as well.

:::

### Grouping Check

**Purpose:** Shows the status of activity groupings, including counts and outdated activity/instance version mismatches.

**When to use:** Use when you need to check whether activities have a grouping assigned and spot outdated version mismatches.

:::details Show Quick Guide

1. Open the **Grouping Check** tab.
2. Review the top part for activities without a grouping assigned.
3. Review the bottom part for grouping counts and outdated activity instances.

This tab provides status of activities groupings.
The top part displays any activities that do not have a grouping assigned.

The bottom part shows, for an activity selected on the _Activity Lib (search bottom-up)_ tab, its activity/activity instance groupings and their instance count in **Activities and their Activity Instances** (A), and flags outdated activity/instance version mismatches in **Outdated Activities** (B) and **Activities with Outdated Activity Instances Only** (C):

[![Activity Grouping Count](/images/user_guides/neodash_activity_grouping_overview.png)](/images/user_guides/neodash_activity_grouping_overview.png)

**Outdated Activities** (B) lists activities that have no latest version but still have an activity instance with a latest version related to them.

**Activities with Outdated Activity Instances Only** (C) lists activities that are themselves latest, but have no activity instance with a latest version related to them — i.e. all of their related activity instances are outdated.

Note: The data displayed depends on the database content — the example above shows no outdated activities/instances currently in the database.

:::

### Display missing groupings

**Purpose:** Displays counts of activities and activity instances with and without valid groupings.

**When to use:** Use when you need an overview of how many activities and instances still lack a valid grouping.

:::details Show Quick Guide

1. Open the **Display missing groupings** tab.
2. Review the different counts of activity instances with and without valid groupings.

The activities and their instances are related via a grouping:

[![Grouping structure - example](/images/user_guides/neodash_grouping_structure_example.png)](/images/user_guides/neodash_grouping_structure_example.png)

This tab displays three counts for activity instances: the total with a `[:LATEST]` relationship in **Activity Instances with [:LATEST] Relationship** (A), how many of those latest instances have a grouping assigned in **[:LATEST] Activity Instances with a Grouping** (B), and how many have a grouping that is valid — meeting all of the above conditions — in **[:LATEST] Activity Instances with All Conditions Met** (C):

[![Missing grouping - counts](/images/user_guides/neodash_activity_missing_grouping_count.png)](/images/user_guides/neodash_activity_missing_grouping_count.png)

Note: The data displayed depends on the database content — the example above shows that most latest activity instances currently lack a grouping.

:::

:::details Show Solution Architecture

Instances and their items follow an Activity Instance Class model (see the class
model image above). The check walks the grouping relationships between activities
and activity instances; it surfaces activities with no grouping, instances
missing a valid group, and outdated activity/instance version mismatches.

:::

## Common errors

| Symptom | Interpretation | Likely cause | Fix |
| --- | --- | --- | --- |
| The missing-items list is empty or unexpected | Could be a filter effect, not necessarily zero results | The displayed data depends on database content and the top-down filter | Adjust the Search top-down filter; confirm database content |
| An activity shows as outdated | A flag, not an error — the report is designed to surface this | Activity has no latest version but a latest-version instance is related to it | Review the activity's versioning; the report flags the mismatch for you to resolve |

If this does not resolve the issue, contact your OpenStudyBuilder administrator.

## Related topics / links

- [Activity Library Dashboard](activity-library-dashboard.md)
- [Reports and Dashboards](./)
