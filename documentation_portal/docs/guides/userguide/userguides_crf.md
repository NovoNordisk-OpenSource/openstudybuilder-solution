---
title: CRF Library
date: 20/October/2025
sidebarDepth: 2
---
# CRF Library

<a id="data-collection-standards-sub-menu"></a>
This is the user guide describes how the Case Report Forms (CRFs) are created and managed and how to define a Collection of CRFs in the Library of the OpenStudyBuilder application.

![OSB Library CRF](/images/library/datacollection/OSB_Library_CRFModule.png)

The system offers access to the following sub-menus in the **Data Collection Standards** menu:

| Sub-menu           | Description                                           |
|:------------------:|:----------------------------------------------------- |
| CRF Viewer         | Display each CRF Collection in two formats: A CRF with annotations version and a copy of the Falcon version                         |
| CRF Builder.       | The place to manage CRF metadata. Create Forms, ItemGroups and Items |

**NB:** Before being able to display any metadata in the CRF Viewer, the system needs to have at least one OSB Vendor Extension namespace. This information is available in the **Administrative** module, under the **ODM Vendor Extensions module**:

![OSB Administration ODM Vendor Extensions](/images/library/datacollection/OSB_AdminODMVendorExtension.png)

<details style="background-color:lightgrey;">><summary style="background-color:yellow;">KWL:Comment (to be removed)</summary>
  Does more need to be in place? stylesheet somewhere?
</details>

## CRF Viewer

This page allows you to view a set of CRFs in a collection (standard forms). You can select one or more CRF Collection(s). The CRF drop-down will display the CRFs in the selected collection(s). The selections options in the drop-downs are multi-selection.

This viewer displays the **LATEST** version. For viewing a specific version use the [CRF Viewer tab](#crf-viewer-tab)

![OSB Library CRF module: Viewer using Annotated stylesheet](/images/library/datacollection/OSB_CRFViewerAnnotation.png)

To export, access the download symbol in the top-right side of the page.

![OSB Library CRF module: Export CRFs](/images/library/datacollection/OSB_CRFViewerExport.png)

### Stylesheets

You can select different stylesheet for viewing the CRFs. At the moment there are two stylesheets by default. Each of the stylesheets allow for viewing different information/annotation (like SDTM annotation).

Adding a new stylesheet needs to be done by a system administrator.

#### CRF with Annotations stylesheet

`CRF with Annotations` stylesheet is displaying every metadata with implementation and completion guidelines as well as keys (ODM oid and version number).

Note that if for example implementation guideline is not displayed, then it is because it is not specified for the CRF, Item Group or Item, see sections [Forms](#forms), [Item Groups](#item-groups), [Items](#items) for how to specify the metadata.

#### Downloable Falcon (word) stylesheet

`Downloadable Falcon (word)` stylesheet is displaying a form using the Falcon format. It can be saved in **HTML format** and then imported into Word.

![OSB Library CRF module: Viewer using Falcon stylesheet](/images/library/datacollection/OSB_CRFViewerFalcon.png)

## CRF Builder

From the left menu bar, select CRF Builder (see [Data Collection Standards - sub-menu](#data-collection-standards-sub-menu)).

The CRF Builder allows you to create Case Report `Forms` (CRFs) using modular building blocks. Each building block can be defined independently and then assembled into complete CRFs and collections of CRFs.

The CRF Builder uses four building blocks:

- **`CRF Collections`** – Sets of Forms that make up complete data collection instruments
- **`Forms`** – Structured pages containing one or more Item Groups
- **`Item Groups`** – Collections of related Items grouped together
- **`Items`** – Individual data fields (e.g., a question, measurement, or data point)
  
These building blocks can be created in the following tabs/sub-menus:

![OSB Library CRF module: CRF Builder - tabs](/images/library/datacollection/OSB_CRFBuilderTabs.png)

For `CRF Tree` and `CRF Viewer` tabs see Section [CRF Tree](#crf-tree) and [CRF Viewer tab](#crf-viewer-tab), respectively.

| Tab | Description       |
|:------:|:----------------|
| CRF Collections  | Displays the list of CRF Collections. In this menu you can create a `CRF Collection`, which is a 'container' for a collection of CRFs and version manage the `CRF collection`. If the collection contains CRFs (Forms, Item Groups and Items) it will make a final version of the whole CRF tree (see Section [CRF tree](#crf-tree)).  |
| Forms | Displays the list of Forms. Allow the definition of metadata related to the Form level. Allow the version management of a `Form`. If the `Form` contains Item Groups and Items it will make a final version of the whole Form tree (see Section [CRF tree](#crf-tree)).  |
| Item Groups | Displays the list of Item Groups. Allow the definition of metadata related to the Item Group level. Allow the version management of an `Item Group`. If the `Item Group` contains Items it will make a final version of the whole Item Group tree (see Section [CRF tree](#crf-tree)). |
| Items | Display the list of Items. Allow the definition of metadata related to the `Item` level. Allow the version management of Items.|
| CRF Tree | Display the tree of CRF Collections, with Forms, with Item Groups and Items to produce the CRF specifications. |
| CRF Viewer | Allow you to display all elements of the CRF: `CRF Collection`, `Form`, `Item Group` or `Item`. There are two formats/styles: A CRF with annotations version and a copy of the Falcon version. This viewer allows for selecting a specific version of a CRF element.|

### General UI functions

In each of the tabs/sub-menus use a common user interface (see [General tab menu UI](#tab-menu-general-ui) below).

<a id="tab-menu-general-ui"></a>
![OSB Library CRF module: CRF Builder - general UI in tabs](/images/library/datacollection/OSB_Library_general_tab_ui.png)

In the following the term `element` can be a [CRF Collection](#crf-collections), [Forms](#forms), [Item Groups](#item-groups), or [Items](#items). In the top right of the UI for the `element` the following is available:

| Button | Description       |Name in User Guide|
|:------:|:----------------|:----------------|
| ![OSB Library CRF module: Add button](/images/library/datacollection/OSB_CRFAddButton.png) | Add a new `element` |**Add**|
| ![OSB Library CRF module: Filter button](/images/library/datacollection/OSB_CRFFilterButton.png) | Open the filtering optional fields to filter the list of the `element` |**Filter**|
| ![OSB Library CRF module: Columns button](/images/library/datacollection/OSB_CRFColumnsButton.png) | Open the list of Columns to be displayed for the list of `element`s |**ColumnSelector**|
| ![OSB Library CRF module: Download button](/images/library/datacollection/OSB_CRFDownloadButton.png) | Allow the download of the selected list of elements, in CSV, JSON, XML or Excel format |**Download**|

In the table view, the first column in the table contains a menu (symbol is three vertical dot) which is dedicated to the management of elements.

When clicking on the 3 dots, based on the status of the `element`, we have the following:

<table>
  <thead>
    <tr>
      <th>Status</th>
      <th>Button</th>
      <th>Feature</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="4"><strong>Draft</strong></td>
      <td><img src="/images/library/datacollection/OSB_CRFApproveButton.png" alt="OSB Library CRF module: Approve button" style="height:26px; vertical-align:middle;"></td>
      <td><strong> Approve</strong></td>
      <td>This will turn the Draft <code>element</code> into a Final version</td>
    </tr>
    <tr>
      <td><img src="/images/library/datacollection/OSB_CRFEditButton.png" alt="OSB Library CRF module: Edit button" style="height:26px; vertical-align:middle;"></td>
      <td><strong>Edit</strong></td>
      <td>To edit an existing Draft <code>element</code> for update / modification</td>
    </tr>
    <tr>
      <td><img src="/images/library/datacollection/OSB_CRFDeleteButton.png" alt="OSB Library CRF module: Delete button" style="height:26px; vertical-align:middle;"></td>
      <td><strong>Delete</strong></td>
      <td>To delete an existing Draft <code>element</code> (work only for Version 0.1)</td>
    </tr>
    <tr>
      <td><img src="/images/library/datacollection/OSB_CRFHistoryButton.png" alt="OSB Library CRF module: Add button" style="height:26px; vertical-align:middle;"></td>
      <td><strong>History</strong></td>
      <td>To show the audit trail of an existing Draft <code>element</code> through version and history</td>
    </tr>
    <tr>
      <td rowspan="3"><strong>Final</strong></td>
      <td><img src="/images/library/datacollection/OSB_CRFNewVersionButton.png" alt="OSB Library CRF module: New Version button" style="height:26px; vertical-align:middle;"></td>
      <td><strong>New version</strong></td>
      <td>This will turn a Final <code>element</code> version into a new Draft version with an updated Version number</td>
    </tr>
    <tr>
      <td><img src="/images/library/datacollection/OSB_CRFInactivateButton.png" alt="OSB Library CRF module: Inactivate button" style="height:26px; vertical-align:middle;"></td>
      <td><strong>Inactivate</strong></td>
      <td>To retired an existing Final <code>element</code></td>
    </tr>
    <tr>
      <td><img src="/images/library/datacollection/OSB_CRFHistoryButton.png" alt="OSB Library CRF module: History button" style="height:26px; vertical-align:middle;"></td>
      <td><strong>History</strong></td>
      <td>To show the audit trail of an existing Final <code>element</code> through version and history</td>
    </tr>
    <tr>
      <td rowspan="3"><strong>Retired</strong></td>
      <td><img src="/images/library/datacollection/OSB_CRFDeleteButton.png" alt="OSB Library CRF module: Delete button" style="height:26px; vertical-align:middle;"></td>
      <td><strong>Delete</strong></td>
      <td>To delete a Retired <code>element</code> (Be careful, no warning)</td>
    </tr>
    <tr>
      <td><img src="/images/library/datacollection/OSB_CRFReactivateButton.png" alt="OSB Library CRF module: Reativate button" style="height:26px; vertical-align:middle;"></td>
      <td><strong>Reactivate</strong></td>
      <td>To reactivate a Retired <code>element</code></td>
    </tr>
    <tr>
      <td><img src="/images/library/datacollection/OSB_CRFHistoryButton.png" alt="OSB Library CRF module: History button" style="height:26px; vertical-align:middle;"></td>
      <td><strong>History</strong></td>
      <td>To show the audit trail of an existing Retired <code>element</code> through version and history</td>
    </tr>
  </tbody>
</table>

### CRF Collections

In this tab the end user can manage `CRF Collections` of forms. The table displays the list of existing `CRF Collection` as Draft or Final (or Retired).

The table display the following information for each `CRF Collection`:

| Tab | Description       |
|:------:|:----------------|
| OID  | Display the Object Identifier of the `CRF Collection`. It is a unique reference, see [OID Naming Convention]("oid-naming-convention")|
| Name | Name of the Collection. This name is used in the CRF Tree and in the CRF Viewer pages |
| Effective | Starting date of the `CRF Collection`. Nobody can use it before this date |
| Obsolete | Ending date of the `CRF Collection`. Nobody can use it after this date |
| Version | Version of the `CRF Collection`. Start as 0.1. The x.0 refers to a Final version |
| Status | Version status of the `CRF Collection`:[Draft\|Final\|Retired] |

#### Add CRF Collection

To add a `CRF Collection` click on the **Add** button. A popup is opened with the following metadata:

| Field | Description       |
|:------:|:----------------|
| Name | Provide the name of the `CRF Collection` that will be displayed in the different part of the application (Mandatory field) |
| OID  | Specify an 'Object Identifier' as a unique ID in the application. As we are defining a `CRF Collection`, it could starts with T.XXX. See [OID Naming Convention](#oid-naming-convention). This is not an ODM element but we are using it here to group `Forms`, `Item Groups` and `Items`. The field is not mandatory, but if it is left blank then a auto-generated OID is created. |
| Effective | Provide an effective start date, when this `CRF Collection` will be applicable (select a date in the date-picker) |
| Obsolete | Provide an obsolete stop date (a retired date), when this `CRF Collection` will be deprecated (select a date in the date-picker) |

Recall in this menu you are creating a building block and the `CRF Collection` is a 'container' for a collection of CRFs. Adding `Forms` to a `CRF Collection` is done in the [CRF tree](#crf-tree).

### Forms

In this tab you can manage `Forms`. The table displays the list of existing `Forms` as Draft or Final (or Retired). Recall that this is for definition the `Form` building block. Adding `Item Groups` to a `Form`, or adding a `Form` into a `CRF Collection` is done in the [CRF tree](#crf-tree)

The table displays the following information for each Form:

| Tab | Description       |
|:------:|:----------------|
| Name   | Name of the `Form`. This name is used in the CRF Tree and in the CRF Viewer pages |
| OID    | Display the Object Identifier of the `Form`. It is a unique reference. The filed is not mandatory, but best practise is to use  `F.<code>`. See [OID Naming Convention](#oid-naming-convention)|
| Description |  A free-text description of the `Form`. Is will be used when displaying the list of Forms in the UI. In addition, this information will be used as the /ODM/FormDef/Description/TranslatedText in the XML view of the `Form`|
|Design Notes |Notes for the designers of the `Form`|
| Completion Instructions |Text that will guide the users of the `Form` on how to enter data|
| Repeating | A form template designed to be completed multiple times during a study. Use for data that occurs repeatedly, such as Vital Signs (measured at each visit) or Adverse Events (recorded as they occur).  <br>In the CRF Tree this will be indicated by <MdiIcon icon="mdiRepeat" color="#747474"/>.  <br> Examples: <br>**Repeating Form**: Vital Signs form (completed at screening, baseline, week 4, etc.) <br /> **Non-repeating Form**: Informed Consent (completed once at study entry) <!-- markdownlint-disable-line --> |
| Version | Version of the `Form`. Start as 0.1. The x.0 refers to a Final version |
| Status | Version status of the `Form`:[Draft\|Final\|Retired] |

#### Add Form

To add a `Form` click on the **Add** button, a popup is opened with the following metadata:

| Field | Description       |
|:------:|:----------------|
| Name | Provide the name of the `Form` that will be displayed in the different part of the application (Mandatory field) |
| OID  | Specify an 'Object Identifier' as a unique ID in the application. As we are defining a `Form`, it  starts with F.XXX. See [OID Naming Convention](#oid-naming-convention). The field is not mandatory, but if it is left blank then a auto-generated OID is created as it is need for the ODM XML format of the `Form`. |
|Repeating|Indicate if this form can be completed multiple times during the study. Select "Yes" for forms like Vital Signs or Adverse Events that are filled out repeatedly. Select "No" for forms completed once, like Informed Consent or Demographics. In the CRF Tree this will be indicated by <MdiIcon icon="mdiRepeat" color="#747474"/> .|
|Description |Provide a detailed explanation of the form's purpose and what data it collects. This helps other users understand when and how to use this `Form`. |
|Design Notes |Add technical notes, design decisions, or implementation guidance for developers and data managers. This field is for internal documentation and is not displayed to study sites. |
|Display text|Enter the text that will appear as the `Form` title when displayed to users entering data. If left blank, the Name field will be used.|
|Completion Instruction |Provide instructions to guide users on how to complete this `Form` correctly. These instructions will be visible to data entry staff at clinical sites. Example: "Complete this `Form` at every scheduled visit" or "Record each adverse event as it occurs." |
|Vendor Extension |Specify any vendor-specific customizations or extensions that apply to this `Form`. This is used when the `Form` includes features specific to your EDC system that are not part of standard ODM. Leave blank if not applicable. <br>It will have this indicator in the CRF Tree: <MdiIcon icon="mdiToyBrickPlusOutline" color="#747474"/>|
|Alias |Provide alternative names or codes for this `Form` used in other systems or contexts. For example, if the `Form` is known by a different name in your datasets or in source documents. Multiple aliases can be added if needed. |
|Change Description |Document what changes were made if you are creating a new version of an existing `Form`. Explain what was added, modified, or removed. This creates an audit trail for `Form` revisions. |

### Item Groups

In this tab you can manage `Item Groups`. The table displays the list of existing `Item Groups` as Draft or Final (or Retired). Recall that this is for definition the `Item Group` building block. Adding `Items` to an `Item Group`, or adding an `Item Group` into a `Form` is done in the [CRF tree](#crf-tree)

The table display the following information for each `Item Group`:

| Tab | Description       |
|:------:|:----------------|
| Name   | Name of the `Item Group`. This name is used in the CRF Tree and in the CRF Viewer pages |
| OID    | Display the Object Identifier of the `Item Group`. It is a unique reference. The filed is not mandatory, but best practise is to use  `G.<code>`. See [OID Naming Convention](#oid-naming-convention)|
| Description |  A free-text description of the `Item Group`. Is will be used when displaying the list of `Item Groups` in the UI. In addition, this information will be used as the /ODM/ItemGroupDef/Description/TranslatedText in the XML view of the `Item Group`|
|Design Notes |Notes for the designers of the `Item Group`|
| Completion Instructions |Text that will guide the users of the `Item Group` on how to enter data|
| Repeating | A section within a `Form` that can repeat to capture multiple instances of the same type of information. Use for varying quantities of data within a single `Form`, such as a list of medications or procedures. <br>In the CRF tree this will have this indicator <MdiIcon icon="mdiRepeat" color="#747474"/>.<br><br>**Repeating Group**: For example Medications section within a Medical History form (one row per medication) <!-- markdownlint-disable-line -->|
| Version | Version of the `Item Group` Start as 0.1. The x.0 refers to a Final version |
| Status | Version status of the `Item Group`:[Draft\|Final\|Retired] |

#### Add Item Group

To add a `Item Group` click on the **Add** button, a popup is opened with the following metadata:

| Field | Description       |
|:------:|:----------------|
| Name | Provide the name of the `Item Group` that will be displayed in the different part of the application (Mandatory field) |
| OID  | Specify an 'Object Identifier' as a unique ID in the application. As we are defining an `Item Group`, it  starts with G.XXX. See [OID Naming Convention](#oid-naming-convention). The field is not mandatory, but if it is left blank then a auto-generated OID is created as it is need for the ODM XML format of the `Form` using the `Item Group`. |
|Repeating|Indicate if this section can repeat multiple times within a single form. Select "Yes" for sections like medications lists or procedure records where multiple rows may be needed. Select "No" for sections that appear only once per form. In the CRF Tree this will have this indicator <MdiIcon icon="mdiRepeat" color="#747474"/> |
|Description |Provide a detailed explanation of what data this `Item Group` collects and its purpose within the form. This helps users understand the group's role in the overall data structure.|
|Design Notes |Add technical notes, design decisions, or implementation guidance for developers and data managers. This field is for internal documentation and is not displayed to study sites. |
|Display text|Enter the text that will appear as the section heading when displayed to users entering data. If left blank, the Name field will be used. Example: "Concomitant Medications" or "Vital Signs Measurements."|
|Completion Instruction |Provide instructions to guide users on how to complete this section correctly. Example: "Add one row for each medication the subject is currently taking" or "Complete all fields for each measurement timepoint." |
|Domain |Specify the SDTM domain this `Item Group` maps to (e.g., VS for Vital Signs, CM for Concomitant Medications, AE for Adverse Events). This links the CRF structure to the SDTM datasets. Select from the drop-down. |
|SAS Dataset Name | Enter the name of the SAS dataset that will be created from this `Item Group`'s data. Typically matches the Domain (e.g., VS, DM, AE) but may differ for custom datasets.|
|Is Referential Data |Indicate if this group contains reference data that links to other data in the study (e.g., a subject ID that references the Demographics data). Select "Yes" if this group establishes relationships between datasets.|
|Origin |Specify where the data in this `Item Group` comes from. Common values: "CRF" (collected on the case report form), "Derived" (calculated from other data), "Assigned" (system-generated), or "Predecessor" (from prior studies). Select from the dropdown, see [Origin Values](#origin-options). |
|Purpose | Describe the analytical or operational purpose of this `Item Group`. <br>**Examples**: "Tabulation" (for SDTM datasets), "Analysis" (for ADaM datasets), "Operational" (for study conduct), or "Other" <!-- markdownlint-disable-line -->|
|Comment | Add any additional notes, clarifications, or context about this group that don't fit in other fields. This is a free-text field for supplementary information.|
|Vendor Extension |Specify any vendor-specific customizations or extensions that apply to this `Item Group`. Used when the `Item Group` includes features specific to your EDC system that are not part of standard ODM. Leave blank if not applicable. <br>It will have this indicator in the CRF Tree: <MdiIcon icon="mdiToyBrickPlusOutline" color="#747474"/>|
|Alias |Provide alternative names or codes for this `Item Group` used in other systems or contexts. For example, dataset names, legacy system identifiers, or alternative terminology used in documentation.|
|Change Description |Document what changes were made if you are creating a new version of an existing `Item Group`. Explain what was added, modified, or removed to maintain an audit trail of revisions.|

<a id="origin-options"></a>

**Origin Values**:

| Origin | Use When Data Is... |
|--------|---------------------|
| **Assigned Value** | System-generated (IDs, codes) |
| **Collected Value** | Entered on the CRF by site staff |
| **Copied Value** | Copied from another dataset |
| **Derived Value** | Calculated from other data |
| **Not Available** | Missing but should exist |
| **Protocol Value** | Defined in the study protocol |
| **Other** | From non-standard sources |

### Items

In this tab you can manage `Items`. The table displays the list of existing `Items` as Draft or Final (or Retired). Recall that this is for definition the `Item` building block. Adding an `Item` to a `Item Group` is done in the [CRF tree](#crf-tree)

The table display the following information for each `Item`:

| Tab | Description       |
|:------:|:----------------|
| OID    | Display the Object Identifier of the `Item`. It is a unique reference. The filed is not mandatory, but best practise is to use  `I.<code>`. See [OID Naming Convention](#oid-naming-convention)|
| Name   | Name of the `Item`. This name is used in the CRF Tree and in the CRF Viewer pages |
| Description |  A free-text description of the `Item`. Is will be used when displaying the list of `Items` in the UI. In addition, this information will be used as the /ODM/ItemDef/Description/TranslatedText in the XML view of the `Item`|
|Design Notes |Notes for the designers of the `Item`|
| Completion Instructions |Text that will guide the users of the `Item` on how to enter data|
|Type| The data type of the `item`|
|Length|The length of the `item`|
|SDS Var Name|The SDTM variable(s) this item maps to, with optional conditions. Simple mappings show just the variable name (e.g., SUBJID). Conditional mappings include "where" clauses to specify value-level metadata. The syntax is `DM:RFICDTC|DS:DSSTDTC|VS:VSTESTCD=SYSBP`|
| Version | Version of the Group. Start as 0.1. The x.0 refers to a Final version |
| Status | Version status of the Group:[Draft\|Final\|Retired] |

#### Add Item

To add an `Item` click on the **Add** button, a popup is opened with the following metadata:

**Note:** Some fields appear dynamically based on your Data Type selection. For detailed information about each data type and what additional fields it requires, see the [Data Types](#data-types) section.

| Field | Description       |
|:------:|:----------------|
| Name | Provide the name of the `Item` that will be displayed in the different part of the application (Mandatory field) |
| OID  | Specify an 'Object Identifier' as a unique ID in the application. As we are defining an `Item`, it starts with I.XXX. See [OID Naming Convention](#oid-naming-convention). The field is not mandatory, but if it is left blank then a auto-generated OID is created as it is need for the ODM XML format of the `Item Group` using the `Item`. |
| Data Type | Select the type of data this item will collect (e.g., String, Integer, Date, Float). The data type determines what kind of values can be entered and what validation rules apply. See [Data Types](#data-types) for complete list and guidance. |
| Length | Maximum number of characters or digits allowed. This field appears for: String, Text, Integer, and Float data types. |
| Significant Digits | Number of digits after the decimal point. This field appears only when Float data type is selected. |
| Unit | Unit of measurement for numeric values (e.g., kg, mmHg, mg/dL, bpm). This field appears for: Double, Float, hex Float, and Integer data types. |
| Code List | Reference to a controlled terminology or code list that defines allowed values. This field appears when String data type is selected. |
| Code List Subset | A subset of values from a larger code list. This field appears when String data type with code list is selected. |
| Description | Provide a detailed explanation of what data this `Item` collects and its purpose within the form. This helps users understand the item's role in the overall data structure. |
| Design Notes | Add technical notes, design decisions, or implementation guidance for developers and data managers. This field is for internal documentation and is not displayed to study sites. |
| Display text | Enter the text that will appear as the field label when displayed to users entering data. If left blank, the Name field will be used. Example: "Systolic Blood Pressure (mmHg)" |
| Completion Instruction | Provide instructions to guide users on how to complete this field correctly. Example: "Enter the systolic blood pressure in mmHg" |
| SAS Field Name | The SAS variable name for this item in datasets. Typically matches SDTM variable naming conventions. |
| SDS Var Name | The SDTM variable(s) this item maps to, with optional conditions for value-level metadata. Simple mappings show just the variable name The syntax is `DM:RFICDTC|DS:DSSTDTC|VS:VSTESTCD=SYSBP`. <!-- markdownlint-disable-line -->|
| Origin | Specify where the data in this `Item` comes from. Select from the dropdown, see [Origin Values](#origin-options) for descriptions of each option. |
| Comment | Add any additional notes, clarifications, or context about this `Item` that don't fit in other fields. This is a free-text field for supplementary information. |
| Vendor Extension | Specify any vendor-specific customizations or extensions that apply to this `Item`. Used when the `Item` includes features specific to your EDC system that are not part of standard ODM. Leave blank if not applicable. It will have this indicator in the CRF Tree: <MdiIcon icon="mdiToyBrickPlusOutline" color="#747474"/>|
| Alias | Provide alternative names or codes for this `Item` used in other systems or contexts. For example, legacy system identifiers, or alternative terminology used in documentation. |
| Change Description | Document what changes were made if you are creating a new version of an existing `Item`. Explain what was added, modified, or removed to maintain an audit trail of revisions. |

### CRF Tree

The CRF Tree is the UI where you combine the `elements`, so add forms into a Collection, add Item Groups into a Form, add Items to an Item Group.

Throughout the CRF Tree UI you will see then following buttons in the 3-dot context menu:

| Button | Description | Name in User Guide |
|:------:|:-----------|:------------------|
| <MdiIcon icon="mdiArrowLeft"/> | Opens the definition UI, view or edit detail for each of the `elements` in [Add Form](#add-form), [Add Item Group](#add-item-group), and [Add Item](#add-item)| Open definition |
| <MdiIcon icon="mdiPencilOutline"/> | Opens the reference attributes UI. This button will only appear if the `element`is in draft. See [Reference attributes](#reference-attributes) for more information.| Edit Reference Attributes |
| <MdiIcon icon="mdiFileXmlBox"/> |This will preview the `element`. This will take you to the CRF Viewer tab for you to view the `element`| Preview ODM |
| <MdiIcon icon="mdiPlusCircleOutline"/> | This will create a new version for the `element`| New version |
| <MdiIcon icon="mdiPlusCircleOutline"/> | This will create a new version for the `element` and its sub-components| New version of all child elements |
| <MdiIcon icon="mdiDownloadOutline"/> | You will be able to export the `element`in various formats and with or without annotations.| Export|
| <MdiIcon icon="mdiArrowExpandDown"/> | This will expand the CRF tree| Expand All|

#### Working with the CRF Tree

Using the CRF Tree, you can mix and assemble the building blocks in any combination to build your data collection structure. This modular approach allows you to:

- Reuse Items and Item Groups across multiple Forms
- Build consistent data structures
- Modify individual components without rebuilding entire CRFs
- Create complex hierarchies from simple building blocks

![OSB Library CRF module: CRF Tree](/images/library/datacollection/OSB_Library_CRFTree_start.png)  

Once you define a `CRF Collection` it will appear in this tree view. You can filter on a specific `CRF Collection` using the drop-down.

To add a `Form` click on the <span style="background-color: #005AD2; color: white; padding: 3px 9px; border-radius: 8px; font-weight: 500;">+Forms</span> button. <!-- markdownlint-disable-line --> 

![Link or create CRF element](/images/library/datacollection/OSB_Library_CRFTree_link_create_element.png)

You can now either link to a `Form` already defined (note this is the **latest** version displayed)

![Link CRF Form](/images/library/datacollection/OSB_Library_CRFTree_link_form.png)

or make a new one (see section [Forms](#forms))

![Add CRF Form](/images/library/datacollection/OSB_Library_CRFTree_add_form.png)

If the `Form` has been defined already (in another `CRF Collection`) then the `Form` and its `Item Groups` and `Items` will be displayed. It will add the **latest** version of the `Form`. If the latest version is a Final version and you need to alter the `Form` then you need to make a new version.

![New Version](/images/library/datacollection/OSB_Library_CRFTree_new_version.png)

If the `Form` is used in another `CRF Collection` which is in draft then you will get a warning (see [How Versioning Protects Your Data](#how-versioning-protects-your-data)).

If the other `CRF Collection` was in Final state then a new version of `Form` is created (not affecting the other collection). You can see the new draft `Form` in the Form tab.

From the CRF Tree, if a draft `Form` has been added, you now are able to add an `Item Group`. To add an `Item Group` click on the <span style="background-color: #3B97DE; color: white; padding: 3px 9px; border-radius: 8px; font-weight: 500;">+Item Groups</span> button. <!-- markdownlint-disable-line --> 

![Add Item Group and Item](/images/library/datacollection/OSB_Library_CRFTree_limk_group_item.png)

Similar with an `Item`. This can be added when the `Item Group` is in draft. To add an `Item` click on the <span style="background-color: #63A8A5; color: white; padding: 3px 9px; border-radius: 8px; font-weight: 500;">+Item</span> button. <!-- markdownlint-disable-line --> 

For more information in the versioning of `Form`, `Item Group`, and `Item`, see Section [How Versioning Protects Your Data](#how-versioning-protects-your-data)

#### Reorder elements

To reorder elements then slide the reorder toggle in the top right corner of the table and use the arrows to re-order.

![Reorder Elements](/images/library/datacollection/OSB_Library_CRFTree_reorder.png)

Note to re-order you need to have the `CRF Collection` and the relevant element (`Form`, `Item GRoup`and/or `Item`) in draft.

#### Reference attributes

On form-level you can specify if the `Form`is
- mandatory
- locked

![CRF Tree - Reference attributes - Form Level](/images/library/datacollection/OSB_Library_CRFTree_form_ref_attrib.png)  

On item-group-level and item-level you can specify if the `Item Group`/`Item`is:
- mandatory
- add vendor extension
![CRF Tree - Reference attributes - Item Group and Item Level](/images/library/datacollection/OSB_Library_CRFTree_group_item_ref_attrib.png)  

| Button | Description | Icon - CRF Tree |
|:------:|:-----------|:------------------|
| Mandatory |The `Form`is mandatory for the Investigator to complete| <MdiIcon icon="mdiDatabaseLock" color="#747474"/> | 
| Locked | ?????| <MdiIcon icon="mdiLockOutline" color="#747474"/> | 
| Vendor Extension| See vendor extension setting in [Vendor Extensions](#vendor-extensions), [Add Item Group](#add-item-group), and [Add Item](#add-item)|<MdiIcon icon="mdiToyBrickPlusOutline" color="#747474"/>|

### CRF Viewer tab

The **CRF Viewer** tab lets you preview your assembled structure as it will appear in a CRF.
![CRF Viewer tab](/images/library/datacollection/OSB_Library_CRFViewer_tab.png)

You are able to select a `Collection` and filter on `Forms` to subset the view.

In the CRF display you can click on the top-right buttons in the CRF display to view the ODM keys, the SDTM annotations, the Completion instructions and the Design Notes.

![CRF Viewer tab - view](/images/library/datacollection/OSB_Library_CRFViewer_tab_form_view.png)

If you slide the XML then you can see the xml version of the `element`

![CRF Viewer tab - xml view](/images/library/datacollection/OSB_Library_CRFViewer_tab_xml_view.png)


### Versioning - CRF Tree and Elements

**Important:** The system automatically uses the **latest version** of any `element` when you link it. You cannot select a specific version - this ensures you're always working with the most current definitions.

#### Scenario 1: Editing a Draft Element ✅

When an element is in **Draft** status:

<pre>
CRF Collection A (Draft) ─┐
                          ├─► Form v0.3 (Draft) ──► Editable
CRF Collection B (Draft) ─┘      (Latest version automatically used)
                                 Changes affect both collections
</pre>

**Result:** Direct editing allowed. All collections using this draft see the changes immediately.

#### Scenario 2: Editing a Final Element (Used in Final Collection) ✅

When an element is **Final** (x.0 version) and used in a **Final** collection:

**Before:**

<pre>
CRF Collection A (Final) ──► Form v1.0 (Final) ──► Locked
                             (Latest version = v1.0)
CRF Collection B (Draft) ──┘
</pre>

**Click "New (Form) Version" →**

**After:**

<pre>
CRF Collection A (Final) ──► Form v1.0 (Final) ──► Unchanged ✓
                             (Still locked to v1.0)              
CRF Collection B (Draft) ──► Form v1.1 (Draft) ──► Now editable
                             (Automatically uses new latest version v1.1)
</pre>

**Result:** New draft version (v1.1) created automatically. Collection A remains locked to v1.0. Collection B automatically switches to the new latest version v1.1.

#### Scenario 3: Editing a Final Element (Used in Draft Collection) ⚠️

When an element is **Final** (x.0 version) and used in another **Draft** collection:

**Before:**

<pre> 
CRF Collection A (Draft) ─┐
                          ├─► Form v1.0 (Final)
CRF Collection B (Draft) ─┘     (Both use latest version = v1.0)
</pre>

**Click "New (Form) Version" → Warning appears:**

![Version Warning](/images/library/datacollection/OSB_Library_CRFTree_new_form_version_warning.png)

**Why the warning?** Collection A is also using this form. Since the system always uses the latest version, creating v1.1 will automatically update Collection A as well.

**After creating new version:**

<pre>
CRF Collection A (Draft) ─┐
                          ├─► Form v2.1 (Draft)
CRF Collection B (Draft) ─┘     (Latest version = v2.1)

Both collections automatically use new latest version
</pre>

**Result:** New draft version (v1.1) created. Both draft collections automatically switch to v1.1 since it's now the latest version. This is why the warning appears - to alert you that another draft collection will be affected.

**Key Point:** You cannot keep Collection A on v1.0 while Collection B uses v1.1. Draft collections always use the latest available version automatically.

#### Version Numbering Rules

| Version Format | Status | Example | When Used |
|---------------|--------|---------|-----------|
| **x.0** | Final | 1.0, 2.0, 3.0 | Approved, locked versions |
| **x.1, x.2, x.3...** | Draft | 0.1, 0.2, 1.1, 2.3 | Work in progress, editable |

**Progression example:**

<pre>
Start with draft:  0.1 (Draft) → 0.2 (Draft)
Finalize:          → 1.0 (Final)
New changes:       → 1.1 (Draft) → 1.2 (Draft)
Finalize again:    → 2.0 (Final)
</pre>

#### Approval in the CRF Tree

When you approve a `CRF Collection` in the CRF Tree you will also approve the child elements
![Approve CRF Collection](/images/library/datacollection/OSB_Library_CRFTree_approve_collection.png)

You are get a notification of the child elements being approved

![Approve CRF Collection - notification](/images/library/datacollection/OSB_Library_CRFTree_child_new_version_warning.png)

#### New version of `CRF Collection`

If you have a final `CRF Collection` you can either choose to make a new version for all the child elements or just make a new version of the `CRF Collection` element itself.

![New CRF Collection Version](/images/library/datacollection/OSB_Library_CRFTree_new_version_collection.png)

Note that if you want to add a `Form` to the `CRF Collection` then only make a new version of the `CRF Collection` - not all the child elements. Putting the `CRF Collection` in draft will make the <span style="background-color: #005AD2; color: white; padding: 3px 9px; border-radius: 8px; font-weight: 500;">+Forms</span> button appear.<!-- markdownlint-disable-line -->      

#### Important Version Management Rules

- Rule 1: Latest version always used

  - When you link an element, the system automatically uses its latest version
  - You cannot select a specific older version
  - This ensures consistency across your data collection structures

- Rule 2: Draft elements are always editable

  - Version numbers like 0.1, 0.2, 1.1, 2.3
  - Changes immediately visible in all collections using this draft
  - All draft collections automatically see updates

- Rule 3: Final elements are locked

  - Version numbers like 1.0, 2.0, 3.0
  - Cannot be modified directly
  - Click "New Version" to create editable draft (becomes next x.1 version)

- Rule 4: Final collections are protected

  - Final collections lock in the specific versions they used at finalization
  - They do NOT automatically update to newer versions
  - Remains stable even when new versions are created

- Rule 5: Draft collections automatically update

  - Draft collections always use the latest available version
  - When a new version is created, all draft collections switch to it automatically
  - This is why you see warnings when other draft collections are affected

### Data Types

When defining an item (field) in your CRF, you must specify the data type that determines what kind of data can be entered. Select the appropriate data type based on the information you're collecting.

#### Data Type Reference Table

<table style="width: 98%; table-layout: fixed;">
<colgroup>
  <col style="width: 10%;">
  <col style="width: 25%;">
  <col style="width: 15%;">
  <col style="width: 10%;">
  <col style="width: 40%;">
</colgroup>
<thead>
  <tr>
    <th>Data Type</th>
    <th>Description</th>
    <th>Additional Fields Required</th>
    <th>Icon - CRF tree</th>
    <th>Example Use Case</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td><strong>BIT</strong></td>
    <td>Binary value that can only be 0 or 1</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
     <td>Flag for data verification status (0=not verified, 1=verified)</td>
  </tr>
  <tr>
    <td><strong>Base 64 Binary</strong></td>
    <td>Base 64 encoded binary data</td>
    <td>None</td>
    <td><MdiIcon icon="mdiOrderBoolAscending" color="#747474"/></td>
    <td>Encoded medical images or documents</td>
  </tr>
  <tr>
    <td><strong>Base64 Float</strong></td>
    <td>Base 64 encoded floating point number</td>
    <td>None</td>
    <td><MdiIcon icon="mdiNumeric" color="#747474"/></td>
    <td>Encoded numeric measurements</td>
  </tr>
  <tr>
    <td><strong>Boolean</strong></td>
    <td>True/false or yes/no values</td>
    <td>None</td>
    <td><MdiIcon icon="mdiOrderBoolAscending" color="#747474"/></td>
    <td>Serious adverse event flag (Yes/No)</td>
  </tr>
  <tr>
    <td><strong>CTTerm</strong></td>
    <td>Controlled terminology term from a standard code list</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
     <td>MedDRA coded adverse event terms</td>
  </tr>
  <tr>
    <td><strong>Comment</strong></td>
    <td>Descriptive text used for ODM comments (not data collection)</td>
    <td>None</td>
    <td><MdiIcon icon="mdiAlphabetical" color="#747474"/></td>
     <td>Internal documentation or annotations</td>
  </tr>
  <tr>
    <td><strong>Date</strong></td>
    <td>Complete date in format yyyy-mm-dd</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
     <td>Date of Birth: 1985-03-15, Visit Date: 2024-11-04</td>
  </tr>
  <tr>
    <td><strong>Date Time</strong></td>
    <td>Date and time in format yy-mm-dd hh:mm</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
    <td>Adverse event onset: 2024-11-04 14:30</td>
  </tr>
  <tr>
    <td><strong>Double</strong></td>
    <td>Decimal number with double precision</td>
    <td>Unit</td>
    <td><MdiIcon icon="mdiNumeric" color="#747474"/></td>
     <td>Laboratory value with high precision: 12.3456789 mg/dL</td>
  </tr>
  <tr>
    <td><strong>Duration Date Time</strong></td>
    <td>Length of time expressed as date-time</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
    <td>Study duration: P2Y3M (2 years, 3 months)</td>
  </tr>
  <tr>
    <td><strong>Float</strong></td>
    <td>Decimal number</td>
    <td>Unit, Length, Significant digits</td>
    <td><MdiIcon icon="mdiNumeric" color="#747474"/></td>
    <td>Systolic BP: 120.0 mmHg (unit=mmHg, length=5, sig digits=1)</td>
  </tr>
  <tr>
    <td><strong>Hex Binary</strong></td>
    <td>Hexadecimal binary data</td>
    <td>None</td>
    <td><MdiIcon icon="mdiOrderBoolAscending" color="#747474"/></td>
    <td>Binary data in hexadecimal format</td>
  </tr>
  <tr>
    <td><strong>hex Float</strong></td>
    <td>Hexadecimal floating point number</td>
    <td>Unit</td>
    <td><MdiIcon icon="mdiNumeric" color="#747474"/></td>
    <td>Specialized numeric encoding</td>
  </tr>
  <tr>
    <td><strong>Incomplete Date</strong></td>
    <td>Partial date (e.g., month and year only)</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
    <td>Date of prior surgery: 2020-03 (month and year only)</td>
  </tr>
  <tr>
    <td><strong>Incomplete Date Time</strong></td>
    <td>Partial date and time</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
    <td>Event time: 2024-11 (year and month only)</td>
  </tr>
  <tr>
    <td><strong>Incomplete Time</strong></td>
    <td>Partial time</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
    <td>Approximate dose time: 14:-- (hour known, minutes unknown)</td>
  </tr>
  <tr>
    <td><strong>Integer</strong></td>
    <td>Whole number</td>
    <td>Unit, Length</td>
    <td><MdiIcon icon="mdiNumeric" color="#747474"/></td>
    <td>Age: 45 years (unit=years, length=3), Heart Rate: 72 bpm</td>
  </tr>
  <tr>
    <td><strong>Interval Date Time</strong></td>
    <td>Time interval between two date-times</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
    <td>Treatment period: 2024-01-01/2024-03-31</td>
  </tr>
  <tr>
    <td><strong>Partial Date</strong></td>
    <td>Date with some components missing</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
    <td>Historical event date: ----06-15 (day and month, year unknown)</td>
  </tr>
  <tr>
    <td><strong>Partial Date Time</strong></td>
    <td>Date-time with some components missing</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
    <td>Approximate event: 2024-03----- (year and month, day unknown)</td>
  </tr>
  <tr>
    <td><strong>Partial Time</strong></td>
    <td>Time with some components missing</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
    <td>Morning dose: --:30 (minutes known, hour unknown)</td>
  </tr>
  <tr>
    <td><strong>String</strong></td>
    <td>Text with controlled values from a code list</td>
    <td>Length, Code list, Code list subset</td>
    <td><MdiIcon icon="mdiFormatListBulletedSquare" color="#747474"/></td>
      <td>Sex: "M" (code list: M/F/U), Race (code list with ethnic categories)</td>
  </tr>
  <tr>
    <td><strong>Text</strong></td>
    <td>Free-form text</td>
    <td>Length</td>
    <td><MdiIcon icon="mdiAlphabetical" color="#747474"/></td>
    <td>Adverse event description: "Patient experienced mild headache" (length=500)</td>
  </tr>
  <tr>
    <td><strong>Time</strong></td>
    <td>Time in format hh:mm</td>
    <td>None</td>
    <td><MdiIcon icon="mdiCalendarClock" color="#747474"/></td>
    <td>Dose administration time: 08:30, Sample collection: 14:45</td>
  </tr>
  <tr>
    <td><strong>URI</strong></td>
    <td>Uniform Resource Identifier (web address)</td>
    <td>None</td>
    <td><MdiIcon icon="mdiWeb" color="#747474"/></td>
     <td>Reference document URL: https://clinicaltrials.gov/study/NCT12345678</td>
  </tr>
</tbody>
</table>

#### Additional Information Fields Explained

| Field | Used With Data Types | Description | Example |
|-------|---------------------|-------------|---------|
| **Unit** | Double, Float, hex Float, Integer | Specify the unit of measurement | Weight field (Float): unit="kg"<br>Heart rate (Integer): unit="bpm"<br>Blood pressure (Integer): unit="mmHg" |
| **Length** | Float, Integer, String, Text | Maximum number of characters or digits | Subject ID (String): length=10<br>Comments (Text): length=500<br>Age (Integer): length=3 |
| **Significant digits** | Float | Number of digits after decimal point | Temperature (Float): significant digits=1 for 36.5°C<br>Lab value (Float): significant digits=2 for 12.34 mg/dL |
| **Code list** | String | Reference to controlled terminology | Sex: code list "SEX" containing M, F, U<br>Country: code list "ISO3166" for country codes |
| **Code list subset** | String | Subset of values from larger code list | Race: subset of comprehensive race code list containing only relevant values for study |

#### Common Use Cases and Recommended Data Types

| Use Case | Recommended Data Type | Settings | Example |
|----------|----------------------|----------|---------|
| **Subject Identifier** | String | Length=10, no code list | SUBJ-12345 |
| **Date of Birth** | Date | None | 1985-03-15 |
| **Sex** | String | Length=1, Code list=SEX | M |
| **Race** | String | Length=50, Code list=RACE | WHITE |
| **Visit Date** | Date | None | 2024-11-04 |
| **Systolic Blood Pressure** | Float | Unit=mmHg, Length=5, Sig digits=1 | 120.0 |
| **Heart Rate** | Integer | Unit=bpm, Length=3 | 72 |
| **Weight** | Float | Unit=kg, Length=5, Sig digits=1 | 75.5 |
| **Temperature** | Float | Unit=°C, Length=4, Sig digits=1 | 36.5 |
| **AE Description** | Text | Length=500 | Patient experienced mild nausea after dose |
| **AE Start Date** | Date Time | None | 2024-11-04 14:30 |
| **Lab Test Code** | String | Length=20, Code list=LBTESTCD | GLUC |
| **Lab Result** | Float | Unit varies, Length=10, Sig digits=2 | 95.50 |
| **Prior Surgery Date** | Incomplete Date | None | 2020-03 (when exact day unknown) |
| **Pregnancy Status** | Boolean | None | Yes |
| **Concomitant Med Name** | String | Length=100, Code list=WHODRUG | ASPIRIN |

#### Best Practices

1. **Choose the most specific data type**
   - ✅ Use Date for dates, not String
   - ✅ Use Integer for whole numbers, not String
   - ✅ Use Float for decimal measurements

2. **Set appropriate lengths**
   - Consider maximum realistic values
   - Example: Age length=3 (allows up to 999)
   - Example: Subject ID length based on your numbering scheme

3. **Use code lists when possible**
   - String with code list enables validation
   - Prevents data entry errors
   - Facilitates standardized analysis

4. **Specify units clearly**
   - Always include units for measurements
   - Examples: mmHg, kg, mg/dL, bpm, °C
   - Avoids confusion in data interpretation

5. **Consider partial dates for historical data**
   - Use Incomplete Date or Partial Date when precision may vary
   - Common for medical history dates

6. **Use Text sparingly**
   - Only for truly free-form content
   - Set reasonable length limits
   - Examples: comments, descriptions, narratives

#### Data Type Selection Decision Tree

<div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; border: 1px solid #dee2e6; font-family: monospace; white-space: pre; color: #212529;" > What type of data are you collecting? <!-- markdownlint-disable-line --> 
│
├── 📊 NUMERIC MEASUREMENT
│   │
│   ├── Whole number ───────────────► INTEGER
│   │   └─ Specify: unit, length
│   │   └─ Example: Age (45 years), Heart Rate (72 bpm)
│   │
│   ├── Decimal number ─────────────► FLOAT
│   │   └─ Specify: unit, length, significant digits
│   │   └─ Example: Weight (75.5 kg), Blood Pressure (120.0 mmHg)
│   │
│   └── High precision ─────────────► DOUBLE
│       └─ Specify: unit
│       └─ Example: Complex scientific calculations
│
├── 📅 DATE/TIME
│   │
│   ├── Complete date ──────────────► DATE
│   │   └─ Format: yyyy-mm-dd
│   │   └─ Example: 1985-03-15, 2024-11-04
│   │
│   ├── Date and time ──────────────► DATE TIME
│   │   └─ Format: yyyy-mm-dd hh:mm
│   │   └─ Example: 2024-11-04 14:30
│   │
│   ├── Time only ──────────────────► TIME
│   │   └─ Format: hh:mm
│   │   └─ Example: 08:30, 14:45
│   │
│   └── Partial/Unknown ────────────► INCOMPLETE/PARTIAL DATE/TIME
│       └─ Example: 2020-03 (month/year only)
│       └─ Example: 14:-- (hour only)
│
├── 📝 TEXT-BASED
│   │
│   ├── From code list ─────────────► STRING
│   │   └─ Specify: code list, code list subset(terms), length
│   │   └─ Example: Sex (M/F/U), Race, Country
│   │
│   ├── Medical terminology ────────► CTTERM
│   │   └─ Example: MedDRA coded adverse event terms
│   │
│   ├── Free-form text ─────────────► TEXT
│   │   └─ Specify: length
│   │   └─ Example: AE description, Comments
│   │
│   └── Yes/No or True/False ───────► BOOLEAN
│       └─ Example: Serious AE flag, Pregnancy status
│
└── 🔧 SPECIALIZED
    │
    ├── Web address ────────────────► URI
    │   └─ Example: Reference document URLs
    │
    ├── Binary data ────────────────► BASE 64 BINARY / HEX BINARY
    │   └─ Example: Encoded images, documents
    │
    └── Binary flag (0 or 1) ───────► BIT
        └─ Example: Data verification flags
</div>

### OID Naming Convention

In the definition of the different `elements` includes the option to specify the OID (Object IDentifier). This is an identifier used in CDISC ODM. An OID is a unique code that identifies each component of the data collection form. Every Form, Item Group, and Item has its own OID.

The OID field is not mandatory for you to fill out. If you leave blank it will generate an OID. However it is recommended to specify the OID.
Best practise is:

| Element Type | Pattern | Example | Description |
|-------------|---------|---------|-------------|
| `CRF Collection` | `T.<code>` | `T.LIB_A` | Collection named Library A |
| `Form` | `F.<code>` | `F.DM` | Form for Demographics |
| `Item Group` | `IG.<code>` | `IG.DM` | Demographics section |
| `Item` | `IT.<variable>` | `IT.USUBJID` | Subject ID field |

#### OID Structure Explained

Forms: `F.<code>`

Prefix F. identifies this as a Form
Code typically matches the SDTM domain (e.g., DM, VS, AE)
Example: F.VS for Vital Signs form

Item Groups: `IG.<code>`

Prefix IG. identifies this as an Item Group (section)
Code typically matches the associated form or dataset
Example: IG.VS for the Vital Signs section

Items: `IT.<variable>`

Prefix IT. identifies this as an Item (individual field)
Variable name follows SDTM/CDASH naming standards
Example: IT.VSTESTCD for Vital Signs Test Code

#### Examples in Context

**Demographics Form:**

```text
Collection:     T.LIB_A       (Collection of Forms)
Form:           F.DM          (Demographics)
  Item Group:   IG.DM         (Demographics data)
         Items: IT.USUBJID    (Unique Subject Identifier)
                IT.BRTHDAT    (Date of Birth)
                IT.SEX        (Sex)
                IT.RACE       (Race)
```

**Vital Signs Form:**

```text
Collection:     T.LIB_B        (Collection of Forms)
Form:            F.VS          (Vital Signs)
  Item Groups:   IG.VS         (Vital Signs measurements)
          Items: IT.VSTESTCD   (Test Code)
                 IT.VSORRES    (Result)
                 IT.VSORRESU   (Unit)
```

#### Best Practise OID Rules and Requirements

**Valid OID characters:**

- ✅ Letters (A-Z, a-z)
- ✅ Numbers (0-9)
- ✅ Periods (.)
- ✅ Hyphens (-)
- ✅ Underscores (_)
- ❌ Spaces (use underscore or hyphen instead)

**Important rules:**

1. **Uniqueness:** Each OID must be unique within its type. The system will ensure that. You will be notified if an OID already exist.
2. **Stability:** Never change an OID once data collection begins
3. **Case-sensitive:** `F.DM` and `f.dm` are different OIDs
4. **Start character:** Must begin with a letter or underscore

**In the interface:**

- You'll usually see the user-friendly **Display Name** (e.g., "Demographics")
- The technical **OID** (e.g., "F.DM") appears in detailed views and exports
- When selecting forms in the viewer, you can search by either name or OID

### Vendor Extensions

Vendor Extensions let you add custom information to your CRF elements beyond the standard fields provided by the system. This flexibility allows you to capture specific metadata without changing the core structure of your forms.

To define an extension you need to be an administrator.

For an `element` (Form, Item Group or Item) you can add pre-defined extensions, see [Add Form](#add-form), [Add Item Group](#add-item-group) and [Add Item](#add-item), respectively.

To add an extension you select from the list and specify the value.
![Select Vendor Extension](/images/library/datacollection/OSB_Library_CRFTree_vendor_extension.png)

Then when you view the `element` in the CRF Viewer tab and enable the xml view (see [CRF Viewer tab](#crf-viewer-tab)), you can see the extension:

![ODM XML Vendor Extension](/images/library/datacollection/OSB_Library_CRFViewerTab_xml_vendor_extension.png)

#### Common Uses

Vendor Extensions can be used to store for example:

- Custom display or formatting settings
- Internal approval or workflow tracking
- Links to external documentation or systems
- Organization-specific validation rules
- Any other metadata unique to your processes

#### How It Works

Each CRF element (`Collection`, `Form`, `Item Group`, or `Item`) can have multiple Vendor Extensions. You can add custom information in two ways:

- Attributes
  - Simple key-value pairs that store individual pieces of information directly.


- Elements with Attributes
  - A named container that can hold multiple related attributes together.

When to Use Each Type:

| Use Attributes | Use Elements with Attributes |
|----------------|------------------------------|
| Single, independent values | Group of related values |
| Simple tracking information | Complex configuration settings |
| Example: `department="Cardiology"`, `displayColor="#005BD2"` | Example: `ValidationRules` element with `minValue="0"`, `maxValue="100"`, `required="true"` |

### Glossary

- CRF: Case Report Forms
- ODM: Operational Data Model from CDISC (Standard)
- SDTM: Study Data Tabulation Model from CDISC (Standard)
