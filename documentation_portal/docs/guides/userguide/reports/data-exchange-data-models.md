# Data Exchange Data Models

**Where to find it:** Reports button → NeoDash → "Data Exchange Data Models" in the Report navigation panel.

## Purpose

Browse CDISC-defined data models, sponsor extensions to CDISC data models, and
sponsor-defined data-exchange data models — e.g. CDISC SDTMIGs, sponsor-extended
SDTMIGs, and file-based lab data-exchange models.

## Concept & definitions

- **Catalogue / Model / Implementation Guide** — the layered CDISC structure for
  organising data models and their versions.
- **Sponsor Model** — sponsor extensions on top of a CDISC model.

## When to use

Use when you need to explore which data models, versions, and dataset/variable
classes are available, including sponsor extensions.

## Report tabs

The report is organised in different tabs, each supporting a different purpose. To open the report, see [Open NeoDash](./#open-neodash) on the section landing page.

| Tab | Use it to… |
| --- | --- |
| **ReadMe** | Get oriented before exploring the data models. Start here. |
| **Catalogues** | Explore overviews of data models in a graphical display. |
| **Models** | Select a data model, version, and general domain class, then browse variable classes and their use in dataset classes. |
| **Implementation Guides - Excl. CDASH** | Select an implementation guide, version, and dataset, then browse variables and extended sponsor model attributes. |
| **Sponsor Models** | Browse extended variable attributes for an SDTM sponsor model version and dataset, and extended variable class attributes by dataset class. |
| **Implementation Guides - CDASH** | Select a CDASHIG, version, and dataset, then browse variable attributes. |

### ReadMe

**Purpose:** Introduces the report and orients you before you explore the other tabs.

**When to use:** Use this tab first, before opening any of the other tabs.

:::details Show Quick Guide

1. Open the **ReadMe** tab.
2. Read the orientation before moving to the other tabs.

The ReadMe tab introduces the report; beside it the report holds the Catalogues, Models, Implementation Guides - Excl. CDASH, Sponsor Models, and Implementation Guides - CDASH tabs.

:::

### Catalogues

**Purpose:** Displays a graphical overview of the available data models.

**When to use:** Use this tab when you want a visual overview of the data models before drilling into details.

:::details Show Quick Guide

1. Open the **Catalogues** tab.
2. Explore the graphical overview of data models.

Exploring overviews of data models in a graphical display.

:::

### Models

**Purpose:** Lets you select a data model, version, and general domain class, then browse the variable classes used in each dataset class.

**When to use:** Use this tab when you need to drill into a specific data model to see which variable classes are used in which dataset classes.

:::details Show Quick Guide

1. Open the **Models** tab.
2. Select a data model, version, and general domain class.
3. Browse the variable classes and their use in dataset classes.

Select data model, version, and general domain class, browse variable classes and use in dataset classes.

:::

### Implementation Guides - Excl. CDASH

**Purpose:** Lets you select an implementation guide, version, and dataset, then browse the variables and extended sponsor model attributes.

**When to use:** Use this tab when you need variables and extended sponsor model attributes for a (non-CDASH) implementation-guide dataset.

:::details Show Quick Guide

1. Open the **Implementation Guides - Excl. CDASH** tab.
2. Select an implementation guide, version, and dataset.
3. Browse the variables and extended sponsor model attributes.

select implementation guide, version, and dataset, browse variables and extended sponsor model attributes.

:::

### Sponsor Models

**Purpose:** Lets you browse extended variable attributes for an SDTM sponsor model version and dataset, and extended variable class attributes by dataset class.

**When to use:** Use this tab when you need extended variable attributes for an SDTM sponsor model dataset, or extended variable class attributes by dataset class.

:::details Show Quick Guide

1. Open the **Sponsor Models** tab.
2. Select an SDTM sponsor model version and dataset to browse extended variable attributes.
3. Select a dataset class to browse extended variable class attributes.

select SDTM sponsor model version and dataset and browse extended variable attributes as well as selecting dataset classes and browsing extended variable class attributes.

:::

### Implementation Guides - CDASH

**Purpose:** Lets you select a CDASHIG, version, and dataset, then browse the variable attributes.

**When to use:** Use this tab when you need variable attributes for a CDASHIG dataset.

:::details Show Quick Guide

1. Open the **Implementation Guides - CDASH** tab.
2. Select a CDASHIG, version, and dataset.
3. Browse the variable attributes.

select CDASHIG, versions and datasets, browse variable attributes.

:::

:::details Show Solution Architecture

> [!NOTE]
> The data exchange data model dashboard is experimental and an initial
> version; additions and improvements will come in the next release.

:::

## Common errors

| Symptom | Interpretation | Likely cause | Fix |
| --- | --- | --- | --- |
| A model or attribute is missing | Expected — coverage is incomplete, not a lookup error | The dashboard is an experimental initial version | Expect coverage gaps; further additions arrive in later releases |

If this does not resolve the issue, contact your OpenStudyBuilder administrator.

## Related topics / links

- [Reports and Dashboards](./)
