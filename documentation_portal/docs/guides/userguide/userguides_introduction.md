# Introduction

This is the user guide of the OpenStudyBuilder application.
The solution is a combination of the following:
- A graph database - Here we are using Neo4j (in version 4.0)
- An API - We are using the Python FastAPI application
- A Frontend - The Vue.js + Vuetify system is being used

We have a central shared solution mostly dealing with an API.

[![Conceptual architecture for the Study Builder solution](/images/documentation/conceptual-architecture.png)](/images/documentation/conceptual-architecture.png)

> Note: For the current release of OpenStudyBuilder, documented evidence verifying the complete functionality has not been established. If output from OpenStudyBuilder is to be used in GxP relevant processes, sufficient quality gateways must be established ensuring fit for intended use for the specific process.

> The solution is named as "OpenStudyBuilder" and it is shared as an open-source project.


## Home page of the application


The URL to access the OpenStudyBuilder application will follow this pattern, where text in '[ ]' is optional and *italic* text is replaced by environment specific values:

> [open]studybuilder[.*environment*].*domain*

See your system environment definition for specific options and values.

![Study Builder](/images/schema_02.png)


## User authentication

Before being able to fully work with the **OpenStudyBuilder** you need to authenticate by providing a User and a Password information. This is done by SSO using the browser authentication.

## After being authenticated

You will see the OpenStudyBuilder application with your login user name in the top bar. If you select your user name you can see your system access roles and logout option.

## Different User access

Based on the Roles & Permissions of the user, you can have access to different areas of the tool.

## Navigation basics

Upon logging in, all navigation occurs within the same app. Navigating by using the browser arrows is possible, but not necessary, as the menus at the top and left of the screen allow simple, efficient navigation throughout the whole application, regardless of the user's current location.

The primary menu at the top of the screen provides access to the modules **"Library"**, **"Studies"**, optionally **"Administration"** and **"Reports"**. Additionally, a study selection button and the selected study information is available. Furthermore, the user sees a settings button ![Settings](/images/bt_settings_blue.png) and a help ![Help](/images/bt_help_blue.png), which provide customization options and navigation support. The logout button is reachable upon clicking on the user name. 

By clicking the sandwich icon ![Sandwich](/images/bt_sandwich_blue.png) the secondary navigation is hidden or shown.

The secondary navigation is located on the left-hand side and is distinct for each of the modules in the primary top menu.

![Navi](/images/navi_overview.png)


## Legend of signs and symbols

| Button | Behaviour       |
|:------:|:----------------|
| ![Add](/images/bt_add_blue.png) | **'Add'** button. Clicking on it will open a dialogue for creating new elements |
| ![Edit](/images/bt_modify_blue.png) | Click on the **'Edit'** button to update existing elements. This will open a dedicated pop up with the selected element in modification mode |
| ![Set Status to Final](/images/bt_validate_blue.png) | Click on the 'Set the status of this template to Final' button at the end of the row that you want to validate. This will update the status of the element to Final and the version number will be increased by 1. |
| ![Inactivate](/images/bt_inactivate_blue.png) | Click on the **'Inactivate this Template'** button at the end of the row that you want to deactivate. |
| ![Reactivate](/images/bt_reactivate_blue.png) | Click on the **'Reactivate this Template'** button at the end of the row that you want to reactivate. |
| ![New Version](/images/bt_newversion_blue.png) | Click on the **'Create a new version'** button at the end of the row that you want to create a new version of the selected template. |
| ![Export](/images/bt_export_blue.png) | Click on the **'Export'** button (before the Add button) to export the full set of *Objectives Templates*. |
| ![Bulk Edit](/images/bt_bulkedit_blue.png) | Click on the **'Bulk Edit'** button. This will enable bulk edits for activities |
| ![Copy](/images/bt_copy_blue.png) | Click on the **'Copy'** button. This enables copy features, e.g. to copy a structure from another study. |
| ![Filter](/images/bt_filter_blue.png) | Click on the **'Filter'** button. This enables additional filter features for the current display. |
| ![Columns](/images/bt_columns_blue.png) | Click on the **'Column'** button. This allows to select and unselect columns for the display. |
| ![Columns](/images/bt_download_blue.png) | Click on the **'Download'** button. This downloads the content - sometimes with different format options. |
| ![History](/images/bt_history_blue.png) | Click on the **'History'** button. This will open a new modal page like below:<br/>Please note that the history is sorted in versioning order |
| ![Delete](/images/bt_delete.png) | Click on the **'Delete'** button to remove an existing element. |
| ![Search](/images/bt_search_blue.png) | Click on the **'Search'** field. This will search in the current templates table based on the term of the search. |
| ![Rows per page](/images/bt_rows_blue.png) | You can also filter the number of records to be displayed in the table by changing the number of rows per page. |
| ![Pagination buttons](/images/bt_pagination_blue.png) | Based on the number of records displayed, the pagination of the table will display multiple pages. | 

## Versioning and Audit Trail

Versioning and audit trails are two sides of the same solution approach in OpenStudyBuilder system, as extracting data for a specific versioning actually is extracting data for a marked point in the audit trail.

Generally, you browse the audit trail by displaying the history for any versioned item that is being versioned, either by page level (showing the latest actions on items on a specific page), or by row level (showing the actions for a specific item).

Via the API, you generally have two GET endpoints, one named /xxx/audit-trail returning actions for all items covered by the /xxx/ (typically corresponding to page level history); and a /xxx/{uid}/versions returning the actions for a specific element (row history)

All elements have a workflow, corresponding to the state changes, with API POST endpoints actions for approval, new version, inactivate, reactivate and delete.

All of this is stored in the physical data model as a set of root-value pair nodes with relationships for all actions holding timestamps and audit trail info. This data model supports generic queries across any element and can be used by the global audit trail report. There are a few differences in principles between the versioning of library elements versus studies – thus two separate reports have been developed, one for versioning in library and one for versioning in studies.

We do also have a few ‘administrative’ data elements that are not versioned, so these are not covered by the audit trail – among them some configuration items (study fields) and project codes (intended to be imported from master data, currently done by an import pipeline).


### Versioning of each library element

Each library element in the MDR system is versioned automatically with its creation and has two attributes to support the process: 
- Status: Can be either **'Draft'**, **'Final'** or **'Retired'**. The status is changed manually upon verification of the library element.
- Version: Is incremented automatically upon adding a new version for a library element from the **'Actions'** column


### Versioning of each study definitions

Each study definition is versioned as a set of metadata definitions for the study - so the principle here is different than for library elements. A study can be in the following status: **'Draft'**, **'Released'** or **'Locked'**. **'Released'** corresponds to a minor version, **'Locked'** to a major version.

For more information on the study versioning see also the [Maintain Study Status and Versioning user guide](studies/manage_studies.md#maintain-study-status-and-versioning).


### Audit trail

Throughout the MDR application each entry made is documented in the audit trail.
The audit trail provides users with the appropriate permissions to view a table with the following sample information for a template about each event in the MDR system:

| Column name | Description |
|:------:|:----------------|
| Library | For templates this can be for Sponsor standards or user defined |
| Template | The syntax template text |
| Change description | Reason for change |
| Status | Draft, Final, Retired |
| Version | Version number |
| User | Containing the username of the person who made the last modification |
| From | Containing date and timepoint of the from modification |
| To | Containing date and timepoint of the to modification, missing means latest and not outdated |


## API activity logging (incl. Export and Extracts)
All OpenStudyBuilder application user activity (via user interface) and direct requests from interfacing systems goes through the OpenStudyBuilder API. All API activities are logged to Azure Monitoring, where they can be addressed and analysed as required.

To ensure sufficient logging of the business use of OpenStudyBuilder data, all business related data extracts and exports of data from OpenStudyBuilder, must be performed through API calls. 


## Working with the tables

In each module all activities are performed in tables.
Each table has general actions and such, which are module- or element-specific.
General actions are listed in the table ribbon:
[!Table Ribbon (/table_ribbon.png)]

The current export options include CSV, XML, JSON and Excel.


## Working with formatted text

Some data-models (usually Templates, ODM descriptions, guidance texts) allow 
users to input HTML formatted data.

The UI displays a simple rich-text formatting tools for such fields,
and it's also possible to paste HTML formatted text from other applications.

The back-end runs an HTML sanitizer on such input, and only allows a small 
subset of HTML tags to pass through, and none of the attributes.

| HTML tag   | description      |
|------------|------------------|
| ABBR       | abbreviation     |
| ACRONYM    | acronym          |
| B          | bold             |
| BLOCKQUOTE | block quote      |
| BR         | line break       |
| CODE       | code-styled text |
| EM         | emphasis         |
| I          | italic           |
| LI         | list item        |
| OL         | ordered list     |
| P          | paragraph        |
| STRONG     | strong emphasis  |
| SUB        | subscript        |
| SUP        | superscript      |
| U          | underline        |
| UL         | unordered list   |

