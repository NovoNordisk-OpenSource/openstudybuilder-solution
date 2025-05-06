# OpenStudyBuilder Commits changelog

## V 0.15

New Features and Enhancements
============

### Fixes and Enhancements

- Added support for Sponsor Controlled Terminology terms through USDM Code instances fetching data from database. Updated USDM Intervention model, Study phase, Trial phase, Study type code, Arms type, Epoch type, Objective level, Endpoint level, Visit type, Visit contact modes, Therapeutic area codes, Trial types, Trial intent types. Reintegrated previously remove Study intervention export mapping.
- Added functionality to change the epoch if it was selected incorrectly for a newly added visit. Previously, the only option in such situations was to delete the visit and then add it again with the correct epoch. Now, a visit with the wrong epoch can be edited, the epoch can be corrected, and the visit can be saved.
- Various code improvements for better performance in the history pages of study structure. 
- Various quality improvements in the API for easier maintenance and better stability.  
- Improved logic for ODM descriptions in the API. It is now possible to select SoA groups for many activities at once when adding study activities.
- UI improvements to Schedule of Activities to accommodate smaller screens.
- Bulk edit feature has been updated to make the 'SoA group' field not required. This allows users to leave the field blank when completing the bulk edit of multible activities.

### New Features
- New compontent was added: The StudyBuilder Word Add-In can be build and installed on Microsoft Word as an Add-In to connect to an OpenStudyBuilder instance enabling live updates in a Protocol Word document.
- Drag-and-drop reordering of the SoA.  Rows in the detailed SoA can now be reordered using drag-and-drop. To enable, click the 3 dots to the left of a row title, select 'Reorder' in the menu and then you can reorder rows using your mouse.
- A first version of a new guided flow (wizard stepper) for creating Activity Instances has been included in the application.  This first version covers the creation of the numerical findings activity instance class and will later be extended to cover more activity instance classes as well as adding editing functionality.
- In the Library, overview pages have been added for Activity Groups and Activity Subgroups similar to the existing overview pages for Activities and Activity Instances. This will provide a better overview of the hierarchy of activities and their groupings.
- When creating a new study it is now possible to copy the study design from an existing structure. This will make it easier to set up sister trials as once the first trial has been setup it can be replicated with almost no effort.
- Study Audit Trail Version Filtering:  A new "Study Audit Trail" tab has been introduced, allowing users to select a Study UID and filter changes between two specific versions. This enhancement provides greater traceability by enabling users to view only the changes that occurred between selected study versions, improving audit clarity and version comparison.
- A new option, Allowed Extensions, has been added for including and excluding specific vendor extensions when generating the CRF View.

# End-to-End Automated test enhancements
- Various code improvements to ensure easier maintenance and overall tests stability.
- Implemented tests for table search.
- Implemented tests for table pagination.
- Implemented tests for exporting data in different formats.
- Studies > Study Structure > Study Vistis: Added test for epoch edition.
- Library > Concepts > Activities: Added tests for overview page (version 1.0).
- Library > Concepts > Activity > Activity Instances: Added tests for New wizard stepper (version 1.0).
- Library > Concepts > Units: Added tests for optional conversion factor.
- Library > Concepts > Activities: Moved test data creation to API calls.
- Library > Concepts > Units: Moved test data creation to API Calls.
- Library > Syntax Templates > Objectives & Endpoints: Moved test data creation to API calls.

Solved Bugs
============

### Library

 **Code Lists -> CT Packages** 

- Filtering CT Catalogues and others by date picker is not sending the requests

 **Concepts -> Activities** 

- Error in counting of rows in the view in Concept Library
- It should be impossible to use a newly drafted Activity Group in a study

 **Concepts -> Activities -> Activities** 

- Not able to save edited item from the existing activities

 **Concepts -> Activities -> Activities by Grouping** 

- Activities by Grouping showing wrong Group/Subgroup combinations

 **Concepts -> Activities -> Activity Subgroups** 

- Group name not shown in activity subgroup history table

 **Concepts -> Activities -> Activity instances** 

- PATCHing to remove optional values doesn't work

 **Concepts -> CRFs -> CRF Tree** 

- When adding a new Form to a Template, then the tree is not reloaded

 **Concepts -> CRFs -> CRF View** 

- The SDTM annotation are badly colorised versus the ItemGroup Domain color

### Reports

 **NeoDash** 

- NeoDash Study Compare report fail study visit comparison in some cases

 **NeoDash** 

- Download of CSV from Neodash report is blocked

### Studies

 **About Studies - > View Listings** 

- Analysis Study Metadata (New) is visible on Studies Summary page when feature flag is turned off

 **Define Study -> Data Specifications** 

- Downloaded file of Study Activity Instances does not have STUDY ID

 **Define Study -> Study Activities** 

- Exclamation mark doesn't disappear when updating the activity version
- Issue with selecting activity from other studies

 **Define Study -> Study Activities ->  Study Activities** 

- Not able to edit the data collection flag for a requested activity
- User is unable to create activity from another study

 **Define Study -> Study Activities -> Schedule of Activities -> Detailed** 

- Detailed SoA table misalignment in user interface (UI) view
- Performance issue in detailed soa with hiding and/or unhiding activities groups and/or subgroups
- issue with selecting or deselecting checkboxes next to activities

 **Define Study -> Study Activities -> Study Activities** 

- Retiring a SoA group results in error in study SoA

 **Define Study -> Study Structure** 

- API performance issue on Study Structure version history

 **Define Study -> Study Structure -> Study Visits** 

- Save button is not responding when user is editing non-visit, unscheduled visit and special visit
- Special visit and the issue with editing it in edit mode
- Unique visit number is editable for non-visit and unscheduled visit

 **Define Study -> Study Title** 

- When editing study title results in error due to study has subparts

 **Study List** 

- Problem with mouse-over in Study List on the column list

 **View Specifications -> ICH M11** 

- ICH M11 page error with no further response

 **View Specifications -> USDM** 

- USDM page results in error



## V 0.14.2

New Features and Enhancements
============
This release does not include any new features.

Solved Bugs
============
### Studies

 **Define Study -> Study Activities -> Schedule of Activities -> Detailed** 

- Issue in detailed soa with hiding and/or unhiding activities groups and/or subgroups

## V 0.14.1

New Features and Enhancements
============

- Enhancements to API performance concerning study visits, study epochs, and study activities are expected to significantly boost the performance of the StudyBuilder system when managing the Schedule of Activities (SoA).
- Schema migration scripts updated which unifies window units for StudyVisits within a single study. This migration also resulted in the unification of window units for Locked Studies.
- An option is now available to select the same Schedule of Activities (SoA) group for all chosen Study Activities.

Solved Bugs
============

### Library

 **Concepts -> Activities -> Activities** 

- Automatic instance up versioning creates more than one new version of instances
- User is unable to save edited item from the existing activities resulted in showing '2 Validation errors'

### Studies

 **Define Study -> Study Activities ->  Study Activities** 

- Error while adding Library activities to a study with a Bulk copying function

 **Define Study -> Study Activities -> Schedule of Activities -> Protocol** 

- Issue where some Activity groups and subgroups were missing in the protocol SoA, that affected both draft and locked studies.


## V 0.14

### Fixes and Enhancements

- Refactored the way we store end-user information so that we can properly identify and maintain unique users of the system.   Instead of just storing user initials, we now store user's id, username, name and other relevant information embedded in their JWT (authentication token).  In the UI we are now displaying username instead of initials of each change author.
- Ensuring that the Protocol SoA design doesn't changed for a locked study over time.
- Consistency requirement has been build in for the use of visit window time units across visits in a study. The visit window unit selected for the first visit created in a study will be used for all subsequent visits added to that study.
- The data model for activity instances has been expanded with properties for molecular weight, research lab and NCI concept names.
- The Activity Instance table now includes Activity Groups and Activity Subgroups. Updates to the sponsor import script to follow changes in the API Stricter validation of required text fields, such as name, to ensure that the text fields do not have redundant white spaces. This will improve the content quality of the StudyBuilder database. Improved handling of batch operations in the API, this ensures that the entire batch operation either succeeds or fails as a  whole. Various quality improvements in the API for easier maintenance and better stability
- We have implemented a new Boolean field to indicate complex unit conversion, and "molecular weight" has been included as an activity instance property. Please note that the feature implementation is ongoing, and additional updates will be released in upcoming versions.
- Alias is a temporary solution to hold Veeva internal identifiers, until an actual Veeva namespace is implemented.
- Updates to the import scripts and import data to prepare for the future activity instance wizard stepper, this is mostly relevant while developing the StudyBuilder application. Added extensions to the API to support the upcoming activity instance wizard stepper.
- Removed "Process Overview" screen as it did not add value as the process steps can be followed along the navigation menu

### New Features

- Leveraging USDM JSON metadata, we have added a new page to the Frontend displaying the ICH M11 template alongside the current metadata.
- It is now possible to bulk edit and bulk delete activities from the Detailed SoA.    A bulk edit and bulk delete button has been introduced in upper right hand corner of the Detailed SoA page. To use the bulk feature select the activities by clicking in the selection boxes in front of the activity and click on the Bulk action button and follow the guide on the screen. Only allowed edits (e.g. SoA group, Visit) will be possible via the screen.
- It is now possible to add a new activity directly from the Detailed SoA. This is done by clicking on the three small dots in front of an activity. Then select 'Add activity' from the pop-up and follow the flow.
- Configuring a new Neodash report entails presenting a Pre-define.xml report specifically tailored to a designated Study. This report includes a dataset list, SDTM variables, and, when relevant, a list of CT terms. These metadata selections are derived from the chosen ActivityInstance originating from the Schedule of Activity.
- Introducing the DDF USDM to StudyBuilder data model mapping for version 3.6. More technical adjustments on API layer will commence in further release.


Solved Bugs
============

### General

 **Miscellaneous** 

- Word "environment" to be removed from Production Application Home page

### Library

 **Code Lists -> Sponsor -> SDTM CT** 

- Error while trying to show all the codelist values

 **Concepts -> Activities -> Activities** 

- Not showing the correct Group in overview
- Sorting order is not in Alphabetical order

 **Concepts -> Activities -> Activities Instances** 

- Incorrect duplication check when creating new instances

 **Concepts -> Activities -> Activity Subgroups** 

- Activity Subgroup creating error while editing a draft activity subgroup

 **Concepts -> Units** 

- Edited unit is not shown in the table
- History is missing at Units table

### Studies

 **Define Study -> Data Specifications  -> Study Activity Instances** 

- Red-bell alert is not disappearing even after Dispensing visit instance changing into new version for some of trial IDs

 **Define Study -> Study Activities** 

- Unable to edit and submit Study Activity

 **Define Study -> Study Activities ->  Study Activities** 

- 'Update Activity Version' should be removed/nor displayed for placeholders which were rejected.
- Menu item option "delete" should be changed to "remove" for consistency
- Searching is not working as intended

 **Define Study -> Study Activities -> Schedule of Activities** 

- "Left/Right" scroll bar to be displayed in Protocol and Operational SoA without need to scroll to the bottom of the page

 **Define Study -> Study Activities -> Schedule of Activities -> Detailed** 

- 'Data validation error' when batch editing in SoA
- Collapse visits in detailed SoA: not possible if the activities are different. Wrong Pop-up message showing that visits are not the same
- Footnotes from other studies cannot be added
- Issue with displaying Activity/Visit when linking footnotes
- Unable to group visits that have sub-visits

 **Define Study -> Study Activities -> Schedule of Activities -> Protocol** 

- Some Trials having issue with displaying the protocol SoA table, throwing XML token error

 **Define Study -> Study Activities -> Schedule of Activities ->Detailed** 

- Activity instance contain blank option when edit SoA footnote

 **Define Study -> Study Properties -> Study Type** 

- Trial type cannot be updated under Study Type section

 **Define Study -> Study Structure -> Design Matrix** 

- Columns sliders are not showing correct status of columns in table

 **Define Study -> Study Structure -> Study Visits** 

- Duplicating special visit, unscheduled visit or non visit should not be possible.
- Study Visits can be edited to create circular timing relationships
- When visits are collapsed and de-collapsed, the visit type is also merged

 **View Specifications -> Clinical Transparency** 

- Make the Clinical Transparency XML file configurable to allow for sharing as Open Source
- Removal of the page header 'PharmaCM Specification'

 **View Specifications -> SDTM Study Design Datasets -> Trial Arm** 

- SDTM Study Design Datasets - trial arm table can not be shown due to missing value in ARMCD


## V 0.13

New Features and Enhancements
============

### Fixes and Enhancements

- It is now possible to exchange an activity directly on the Detailed SoA page by clicking the three dots in front of the activity.
- The Consumer API version 1 has been extended with two new GET endpoints: /studies/{uid}/detailed-soa /studies/
- The disclosure information from OpenStudyBuilder can now be downloaded as an XML file for upload to PharmaCM Specification.
- The SoA group for an activity can now be edited from the Detailed SoA page.
- Neodash dashboards are changed from Neo4j style to OpenStudyBuilder style.
- Clean-up of the API code to improve readability and maintainability. The API has been upgraded to run on Python 3.13.0 from 3.11.0.  The Study Visits endpoint in the Consumer API version 1 has been improved to give a relevant response for studies with no visits defined. Minor improvements to the CRF module in the Library. The title of the middle step of the "Add SoA footnotes" stepper has been changed from 'Create template' to 'Create footnote' to indicate that when creating a footnote from scratch it's not a template.  In the Unlink footnote pop-up window, that comes when hovering over an activity with a footnotes and pressing the "-" sign, the wording has been updated to make it more clear that the footnote is being unlinked from this particular activity. The previous wording could be interpreted as the footnote was going to be completely deleted. The Clinical Programmes & Projects pages under Admin Definitions in the library have been improved by adding filtering and column selection buttons. Further a title has been added to the two pages to align with the general look and feel of StudyBuilder.

### New Features

- A new menu option (Need help?) has been added to the Help menu (? icon) to allow navigation to the https://openstudybuilder.com/ site.
- In the Library a new Study Structures overview page is introduced. It will assist Standards Developers by offering an overview of how existing trials have been defined and allows users to view the study structures they can replicate, identify trends, and spot any deviations. The Study Structures page aims to increase consistency when setting up new trials. Studies that share the same structure are grouped together and listed in the table under the same row. The columns display numeric values indicating the number of arms/epochs/elements in the trial or Y/N to indicate if cohorts are part of the trial design.
- To facilitate that the different StudyBuilder environments are used for their intended purposes the top bar and front page of StudyBuilder environments: Development, Test, Preview, Validation and Education will now clearly indicate what environment the user is about to log on to.
- A feature toggle has been implemented to allow a StudyBuilder administrator to toggle on/off the "Analysis Study Metadata (New)" page under View Listings in the Studies module.
- New Neodash Dashboard for Activity Metadata Check.


Solved Bugs
============

### API

- When user tries to edit instance, an error appears on the screen

 **Miscellaneous** 

- It is still possible to link to an activity in requested library

### Library

 **Admin Definitions -> Projects** 

- Possible to create multiple projects with the same number

 **Code Lists -> Sponsor CT package** 

- Blank page with no data, no further response

 **Concepts -> Activities** 

- 'Clear All' not working as expected in the Filters
- 'Modified by' column has disappeared from Library/activities

 **Concepts -> Activities -> Activities** 

- Activity overview page fetches concepts/activities/activities/Activity_00000n twice
- Adding filter and use hyperlink is not aligned across library and study
- Legends for page history is covered by the lower 'close' bar

 **Concepts -> Activities -> Activity Subgroups** 

- Add missing translation entries for activity subgroup

 **Data Exchange Standards -> CDASH** 

- Misalignment between page content and breadcrumbs

 **Syntax Templates -> Templates -> Footnote templates** 

- Template footnote cannot be removed/unlinked using "-" function

 **Syntax Templates -> Time frames -> Parent** 

- Deleting Timeframe Template resets the table length

 **Template Instantiations -> Endpoints** 

- Clicking on view button is not working for Template Instantiations

### Reports

 **NeoDash** 

- NeoDash report for Syntax Templates do not show empty template parameters

### Studies

 **Define Study -> Data Specifications  -> Study Activity Instances** 

- If more than 10 instances exists, then it is not possible to select linkage
- Multiple required instances cannot be added after the activity is added to the study
- Activity Instance is linked to non-data carrying Activity.

 **Define Study -> Study Activities ->  Study Activities** 

- In the add activity flow - add from studies/acronym cannot be selected alone
- to remove DUPLICATE for manually defined visits

 **Define Study -> Study Activities -> Schedule of Activities** 

- Visit window with zero appears as '+0'

 **Define Study -> Study Activities -> Schedule of Activities -> Detailed** 

- Misalignment of text in Schedule of Activities

 **Define Study -> Study Activities -> Study Activities** 

- When sub group is not chosen, an error appears on the screen

 **Define Study -> Study Properties -> Study Attributes** 

- Align design of dialog box for copying study metadata
- Missing data on form when data were imported and then you want to edit them

 **Define Study -> Study Structure -> Study Visits** 

- Missing columns in downloaded versions (CSV and Excel)
- Repeating visit - repeating frequency is not populated in table

 **Manage Study -> Study -> Study Status** 

- Locking study should have a 'Locking description' title instead 'Release description'

 **Manage Study -> Study -> Study Subparts** 

- Adding subpart from existing studies, studies that do not belong to same project as parent study are on the list
- Adding subpart from existing studies: Study ID column is missing
- It should not be possible to change master study acronym for the subpart
- Removal of subpart is not present in audit trail

 **View Specifications -> Protocol Elements -> Study Population** 

- All criterias are not shown in Study Population section
- Empty rows show up in Study Population page
- Unnecessary functionality in Study Population

 **View Specifications -> USDM** 

- Misalignment between page content and breadcrumbs


## V 0.12.1

New Features and Enhancements
============

This release does not include any new features.

Solved Bugs
============

### Library

 **Concepts -> Activities** 

- Error Message appears when activating an activity

### Studies

 **Define Study -> Study Activities -> Schedule of Activities** 

- User cannot able to see the study activities in the protocol view due to error showing 'Maximum recursion depth exceeded in comparison'


## V 0.12

New Features and Enhancements
============

### Fixes and Enhancements

- Minor visual changes have been made to the System Announcement functionality to increase readability
- The edit "Activity Instance" form has been rewritten so it only fetches up to 20 activities instead of all (1000+) activities. This makes the form usable after a fraction of a second instead of the more than 20 seconds it used to take. The parameters in the URL path has gotten a unified naming scheme making the API easier to use for API users. In the "Add Visits" form it is now more intuitive for Standard Developers what information needs to be filled out when creating a visit meant to be a Global Anchor visits.  The Protocol SoA no longer shows "+/-" in front of a time window value of 0. Neomodel has been upgraded to version 5.3
- Various quality improvements by increased coverage of automated tests for the System Announcements functionality.
- The online help has been updated to include details about selection by Study Acronym.
- Footnotes can now be managed from the SoA table directly.
- Backend updates have been implemented to prepare for the need to save the Protocol SoA in a new database design. No changes to the frontend or impact on end users.
- Backend updates have been implemented to prepare for the ability to edit activity grouping
- Up-versioning an Activity now retains the existing links between Activities and Activity Instances. This significantly improves the time spend on managing Activities for Standards Developers as it requires 10 mouse clicks to to add a link to an Activity Instance from an Activity
- Under manage study StudyBuilder now support selection of Sponsor and CDISC CT Package. This selection will control display and submission values for study selections related to sponsor and/or CDISC CT.
- Updated activity instance classes and activity item classes.

### New Features

- Implemented API endpoints to read and write the state of feature flags, which are simple toggles for enabling or disabling selected parts of the application. The features in question can be anything from a complete module, such as the "Compounds" module under Library/Concepts, or something much smaller as a single button in a form. Once fully implemented this will allow us to perform more targeted user research (e.g. A/B testing) as well as allow the open source community to configure what parts of the application to use.
- The first version of the consumer API has been initiated and contains three endpoints to get a list of studies, a list of study visits for a study and an operational SoA for a study.
- It is now possible to remove an activity directly from the Detailed Schedule of Activities (SoA) page
- In the Studies part of the application the menu option 'Clinical Transparency' has been added. The new menu ensures the transparency information needed for upload to clinicaltrial.gov is made available in a downloadable format.



Solved Bugs
============

### API

 **Miscellaneous** 

- Fix linking to System Information API in Swagger

### General

 **Miscellaneous** 

- Performance issue or Slowness in StudyBuilder Application

### Library

 **Code Lists -> CT Catalogues** 

- Error message when adding an existing term to a codelist
- Remove codelist_library_name filter from term search in CT Catalogues

 **Code Lists -> Sponsor -> All** 

- Searched text gets added to output string

 **Concepts -> Activities -> Activities Instances** 

- Not able to change the activity for an activity instance

 **Concepts -> Activities -> Requested Activities** 

- Handling placeholders are not looking as expected
- User cannot able to change subgroup in handling of activity request

 **Syntax Templates -> Endpoint Templates** 

- Rows per page dropdown not working for User Defined Syntax Templates

### Studies

 **Define Study -> Data Specifications -> Study Activity instances** 

- When data collection = No, then 'add instance' must not be an option

 **Define Study -> Study Activities -> Schedule of Activities > Detailed** 

- Activities are assigned to non-visit and unscheduled visits via batch editing option
- Cannot able to remove a few Study Footnotes from the same item in SoA by issuing a few API endpoint calls

 **Define Study -> Study Activities -> Study Activities** 

- Filtering in Study activities causes error
- SoA group change having a dependency to activity grouping

 **Define Study -> Study Structure -> Study Branch** 

- Add branch arm: save button is spinning after the warning that subject number is higher than in arm

 **Define Study -> Study Structure -> Study Branches** 

- issue with ordering Study Branches

 **Define Study -> Study Structure -> Study Visits** 

- Issue with displaying save icon when Study visits in edit mode
- It is possible to mark visits without timing (non-visit, unscheduled visit) as SoA milestone via edit mode

 **Manage Study -> Study -> Study Subparts** 

- Sorting not working as expected in Study Subparts table
- It should be not possible to update study id of the study subpart
- Study subpart was created without "study acronym" which cannot be edited further




## V 0.11.2

No New features and/or enhancements added


Solved Bugs
============

### Library

 **Code Lists -> Sponsor -> All** 

- Terms deleted from sponsor codelists are removed or deleted from locked studies

 **Concepts -> Activities -> Activity Instances** 

- New Activity Instance versions sometimes link to an old version of the Activity


## V 0.11.1

No new features and/or enhancements added

Solved Bug
============

### Studies

**Define Study -> Study Activities ->Activities**

- Search doesn't result in relevant results


## V 0.11.0

## Fixes and Enhancements

- In the Protocol SoA the top-left cell text is now always displaying the word "Procedure" in an alignment with both the Novo Nordisk and TransCelerate protocol templates.
- Various quality improvements by increased coverage of automated tests. Various improvements to data import scripts for activity content. Simplified the process for creating new visit types in the Library and removed restrictions on what epochs a visit type can belong to.

## New features

- A new administration page has been created where administrators of the StudyBuilder application can toggle system wide announcements. This can be used for eg communicating closing windows to the end-users.



Solved Bugs
============

### Library

 **Code Lists -> Sponsor -> All** 

- Code list 'search with terms' shows terms connected to non-sponsor library

 **Concepts -> Activities -> Activities** 

- Cannot add a space while searching for a term or word

 **Concepts -> Activities -> Activities by Grouping** 

- Activity grouping showing incorrect result

 **Concepts -> Activities -> Requested Activities** 

- Incorrect system behaviour when trying to 'Add activity request'

### Studies

 **Define Study -> Data Specifications -> Study Activity Instances** 

- Selection of instances showing list includes instances not yet approved (Final)

 **Define Study -> Study Activities ->  Study Activities** 

- While adding study activities from other studies, an issue identified with displaying studies acronyms in the drop down list

 **Define Study -> Study Activities -> Schedule of Activities > Detailed** 

- Only the first 10 footnotes are visible in the protocol SoA
- visit numbers appears in the batch edit activities in detailed SoA

 **Define Study -> Study Activities -> Study Activities** 

- Colour for 'Not submitted' placeholder is not matching with the colour displayed as reference stated below the table

 **Define Study -> Study Structure -> Study Visits** 

- Additional sub visit radio button is missing
- Numbers for 'non-visit' and 'unscheduled visit' has been mixed up
- Required fields are not marked with '*' when creating visits under 'Study structure'

 **Process Overview -> Protocol process** 

- Study Activities menu items has incorrect links

## V 0.10.0

## Fixes and Enhancements

- The automatic visit numbering and naming functionality now support naming a visit as 'Visit 0' when the first visit in the study timeline is defined as an information visit.
- CDISC USDM generation is now integrated into the native API and can also be displayed and downloaded under the menu Studies -> View Specifications -> USDM.
- Introducing a new visit subclass called Repeating visit, which can typically be used in non-interventional studies. It is useful when participants need to return for the same visit multiple times based on their individual needs (for example, one participant may come to visit 3 five times, while another may have 10 visits as visit 3). If there are any requirements about the repetition of such visits (daily, weekly, monthly), then it can be defined via the Repeating frequency item. Note that Repeating visits should be used if you do not know in advance the number of repeats that will occur. If a fixed number of similar visits is planned, then these should be created as single scheduled visits and grouped in a consecutive visit group. Please find more details in the StudyBuilder Documentation Portal.
- Compound API partly prepared for refactoring, but functionality is not yet enabled for use.
- The API supports returning study selections related to sponsor and CDISC CT for the specific CT package selected for the study.
- It is now possible to edit and delete Clinical Programmes and Project on the Admin Definitions pages in Library.
- Study Visits can be marked as a SoA milestone, and then the related visit type can be displayed in the protocol SoA table header. On the protocol SoA page you can decide to display the SoA milestone, the study epochs, or both. The SoA milestones can also be displayed on the Study Design figure.
- Various performance improvements for Activities in Library
- When adding a study visit, the list of "Existing visits Names and Timing" can now show visit timing as either Week or Day depending on what "Time unit" the user selects in the Add study visit form. A sticky bar has been added to all History pages making actions for download or closing the window easy available at all times without the need for scrolling.
- When adding Activities from other studies it is now possible to search for a study to select from by using its acronym instead of the study id.
- Selected components in tables (eg. search fields, filter, dropdowns and action buttons) of the StudyBuilder user interface have been aligned to the Novo Nordisk design system to increase the visual consistency of the user interface.
- Front-end refreshes data from the back-end on switching pages/tabs
- Redesign of the Schedule of Activities and the footnotes section has been initiated. Among other improvements several of the SoA tabs have been combined into one tab.

## New Features

- New Neodash report to search and list CT code list and terms with history evolution over time.
- First version of StudyBuilder Consumer API exposing GET /studies endpoint
- A "Reports" button have been added to the top bar. Clicking this button opens a landing page in a new tab where existing NeoDash reports and dashboards are available. These reports can be used to deep dive in the standards and study information available in the StudyBuilder database.


Solved Bugs
============

### Library

#### Code Lists -> CT Catalogues

- Search bar has to be reloaded to show records when the search delivered none results

#### Code Lists -> Sponsor -> All

- Code list 'search with terms' creates duplicate search string and errors

#### Concepts -> Activities -> Activities

- Even after clearing the filter value the resulting rows are still showing in the window
- Filter does not return the full list of relevant results
- Filter on 'activity status=final' is not effective after selection of an activity

#### Concepts -> Activities -> Activity Groups

- Filter issues in library activity groups
- Search term is not removed when the page is refreshed

#### Concepts -> Activities -> Activity Instances 

- Wrong breadcrumbs (i.e. Navigation path) shown in Library section when navigated via Studies

#### Syntax Templates

- Adding missing new_version_default_description entry in locales

#### Syntax Templates -> Criteria Templates

- Audit trail part not working as expected both in Parent and Pre-instance of Inclusion criteria

#### Syntax Templates -> Criteria Templates -> Exclusion -> Parent

- Default filters are not selectable again after being removed

#### Syntax Templates -> Criteria Templates -> Inclusion -> Parent

- Error in header values when filtering in criteria templates

#### Syntax Templates -> Endpoints

- Endpoint template added twice at the same time

#### Syntax templates -> Objective templates -> Pre-instance

- For pre-instances unit is in uppercase if put it in start of sentence

### Studies

#### About Studies

- text in 'View Listing' is wrong

#### Define Study -> Registry Identifiers

- Edit form not reloading field values (after entry)

#### Define Study -> Study Activities

- Reload SoA Preferences & Time Unit when switching SoA tabs and opening SoA Settings

#### Define Study -> Study Activities -> Study Activities

- Removing search time does not update view

#### Define Study -> Study Criteria 

- When adding a Criteria based on a parent template from the Library, if the table on the screen has not loaded completely after toggling from pre-instances to parents, then the application throws an error

#### Define Study -> Study Criteria -> Inclusion Criteria

- Error in number of rows displayed per page

#### Define Study -> Study Population

- selection for PINF in study population disappears

#### Define Study -> Study Purpose -> Study Objectives

- Not possible to copy objectives from another study

#### Define Study -> Study Structure -> Study Cohorts

- Cohort short name 20 char limit not working

#### Define Study -> Study Structure -> Study Visits

- Duplicating study visits reverts table length to 10 items
- Fields visit number 1 and visit name visit 1 are not unique of the study as a manually defined value exists for some trials

#### Define Study-> Study Criteria-> Inclusion Criteria

- Activity groups are Title case inside sentences in Inclusion criteria
- Cannot able to view more than 10 rows in Inclusion criteria

#### General

- Study set-up user cannot save endpoints, error message is appearing for some trials

#### Manage Study -> Study ->  Study Core Attributes

- Cannot edit study acronym from study core attributes

#### Studies

- Studies main page - studies page has non functional buttons

#### Study List

- Sorting is not working in the 'Study list' menu


## V 0.9.2

New Features and Enhancements
============
No new features and/or enhancements are added

Solved Bugs
============

### Library

#### Concepts -> Activities -> Requested Activities

- Activity requests are missing from the 'Requested Activities' tab under 'Activities' in the Library

### Studies

#### Define Study -> Study Activities -> Study Activities

- Unable to change the SoA groups

#### Define Study -> Study Activities ->Activities

- Missing activities in "Studies" part compared with "Libary" part

#### Define Study -> Study Structure -> Study Visits

- Bulk edit for study visits not working
- When editing study visits the existing timing value is cleared

## V 0.9.1

New Features and Enhancements
============
No new features and/or enhancements are added

Solved Bugs
============

### Library

#### Concepts -> Activities -> Activities Instances

- Not able to change the Activity group / activity subgroup combination on an activity instance

### Studies

#### Define Study -> Study Activities -> Study Activities

- Not able to view History page - Results in 404 error
- Issue with creating manually defined visit
- Study Activities are having wrong order when navigating to next page

#### Define Study -> Study Purpose -> Study Objectives

- Can select Requested activities as template parameters

## V 0.9

New Features and Enhancements
============

### Disabled Features

- The placeholder tab for 'Activity instructions' has been removed from the 'Study Activities' page under the 'Define Study' menu as this functionality is not developed yet. The tab is planned to be added back once the functionality has been completed.  The placeholder tab for 'Study Estimands' has been removed from the 'Study Purpose' page under the 'Define Study' menu as this functionality is not developed yet. The tab is planned to be added back once the functionality has been completed.
- The compound module is under refactoring to be aligned with the Identification of Medical Products (IDMP) model, as this is not yet completed the Compound menu under Library, Concepts and the Study interventions menu under Studies, Define study is disabled. These will be added again in a future release.

### Fixes and Enhancements

- Improvements to API GET endpoints for an internal SDTM solution supplying metadata supporting SDTM generation.
- Improved workflow and functionalities for handling study activity placeholders and requests.
- The Neodash environment now support multiple reports and selection between them within the Neodash navigation panel.
- The entire StudyBuilder frontend have been migrated from Vue2 to Vue3
- When adding a new study it is now possible to search for the project ID. 
- When The main page of the Studies module now have additional descriptions of the different menu items under Studies. 
- When adding activities the Definition field is no longer mandatory to fill out The pre-selected filters for Activity Instances have been reduced to Activities, Activity instances, Status, Topic code and Legacy status Various minor update to the Library menu to improve readability. 
- When adding a Study Visit, the drop down list to select the time unit is now shown before the field to capture the timing - this will reduce the likelihood of users getting errors due to visits being defined out of order Various text fields for Study Properties and Study Populations have been made longer on the screen to avoid text being truncated when displayed.
- Various minor improvements to sorting and filtering
- Refactoring of API to improve performance when working with study selections Refactoring of UI to improve performance when working with drop down lists and filters
- The study visits pages now support manually defined visits with manually defined visit numbers and names.
- Implement support for additional registry identifiers in UI (API support was implemented in previous release).
- In the Detailed SoA identical activity groups are merged, so they not are displayed as duplicates. Improved error handling for import of study activity schedules. Performance improvements for study activities and SoA.
- Additional API tests are made to ensure that the study selections leave trace on the audit trail on every library update after the selection, so we can be in compliance with audit trail and study versioning solution design.
- Improved synchronisation logic between parent study and study subparts. Existing studies can be added as a study subpart. Correction to audit trail information for study subparts.
- When defining a Study Criteria, a warning text and exclamation mark is now shown to users if the criteria text exceeds 200 characters  The left-side menu is now highlighting the page currently shown on the screen after reloading the screen
- Refactoring of API to improve performance when working with Schedule of Activities (SoA).
- The system support selection of study duration time in days and weeks with baseline time as time 0.
- A number of performance improvements have been made for the SoA DOCX generation including a spinner when the system is processing the DOCX generation.

### New Features

- New functionality to define Sponsor CT Packages that enable a persistent reference to sponsor names and terms for a CDISC CT package.
- New main menu item under Studies, Define Study, Data Specifications for managing Study Activity Instance selections and display of the Operational SoA.
- New Neodash report for comparing two studies or two versions of a study.
- New Neodash report listing available template parameters, values, syntax templates for all types as well as study usage.
- New Neodash report that enable searching and listing audit trail information across data domains by users and datetime. This is a supplement to the view history forms within the application, as these is limited to a specific data domain.
- New Neodash report enabling listing all data exchange data models.


Solved Bugs
============

### API

#### Miscellaneous
- Clearing a StudyField get recorded in a non-standard way in audit trail
- Error message for syntax instances
- Front End sends multiple duplicated requests to API

### General

#### Both Studies and Libraries
- Navigation paths are missing in Breadcrumbs

### Library

#### Code Lists -> CT Catalogues
- 502 error appearing several times
- Putting a filter for "Submission value" on the page "All" causes an error

#### Code Lists -> CT Packages
- Modify the API endpoint dealing with displaying the CT Packages with only the Codelists/Terms belonging to the package

#### Code Lists -> Sponsor
- Duplicate options visible while searching for a term in sponsor codelists

#### Concepts
- Menubar items in Study affected by menubar items in Library and vice versa

#### Concepts -> Activities
- Sorting on Activity Group and/or Subgroup table throws error

#### Concepts -> Activities -> Activity Subgroups
- Filtering on Status column for Activity Subgroups not showing all options
- Sorting on Activity Group does not work
- Sorting on tables is not carried over when viewing next 10 items in a table

#### Concepts -> Activities -> Requested Activities
- Possible to select non-approved activity placeholders in the syntax templates in studies

#### Concepts -> CRFs -> CRF Templates
- UI CRF building cannot reorder questions (Items) in an ItemGroup
- UI CRF building does not retain previous data when adding new items
- UI ODM export length error

#### Concepts -> CRFs -> CRF Tree
- The Reorder toggle in the CRF Tree tab is not working

#### Concepts ->Activities
- 'Retired' state of requested Study Activities are displayed

#### List -> General Clinical Metadata
- Page is still showing for General Clinical Metadata (Removal needed)

#### Syntax Templates
- If you hide a parameter in a sequence of parameters the sentence generation is incorrect (Applicable for all Syntax templates)
- Library subsection name not aligned as 'Activity Instructions'

#### Syntax Templates -> Criteria Templates -> Inclusion (Parent)
- Searching for syntax templates extend the scope of the list
- Study can select criteria in draft state

#### Syntax Templates -> Endpoint Templates
- Activity parameter shown default in Step 1 is not reflected in the Step 2 (Test template)

#### Syntax templates
- URL for all of the templates showing wrong if you are navigate to 'Parent' template

#### Syntax templates -> Objective templates
- 'NA' answer is not stored correctly for the Template index when updating

### Studies

#### Define Study
- Missing sorting options (Ascending or Descending) under three dot menu of the column headers

#### Define Study -> Registry Identifiers
- Study Fields not cleaning the field value when selecting NA
- Page for Registry Identifiers do not display content for a study subpart

#### Define Study -> Study Activities
- Adding activities from other studies - "Requested" activities cannot be added by other studies
- 502 error appearing several times when adding new study activity
- Adding activity placeholder should not be possible from other studies.
- After changing the initial grouping of requested activity, then for this activity the activity group and subgroup are lost on study level
- Copy all button is not working when copying activities from other studies
- It must not be possible to copy a requested activity from one study to another
- Non-Display of Activities seen in Study Activities tab
- Search functionality comes with partly wrong results
- Study Set-up user must be able to edit any 'user-defined' syntax template
- Studies are not able to copy when adding Study Activities
- Study set-up users cannot edit their own SoA footnotes due to limited access (i.e, Library.Write access)
- Unable to add multiple activities from library due to an error stating one activity is already there
- Unable to copy all footnotes from one study to another study
- Batch edit study activities functionality is not working
- Fix time-unit mismatch in the Detailed SoA
- Adding footnotes from other studies has performance issue with displaying footnotes
- Lacking of footnote SoA tag when first time edit and assign the footnote SoA to a study activity
- SoA DocX performance issue

#### Define Study -> Study Criteria -> Inclusion Criteria
- Alignment of items in filter section
- Filtering in add study criteria from template is not unique to the type of criteria
- Filtering on in/exclusion criteria shows filtering options for both inclusion and exclusion criteria
- Retired criteria templates are appearing when choosing from library syntax template
- Template parameters starting letter appears with lower case (case sensitive)

#### Define Study -> Study Purpose -> Study Endpoints
- Copy all button is not working when copying activities from other studies
- Edit endpoint form doesn't support multiple units as there's no field for entering unit separator
- Study Endpoint not showing the separator dropdown menu when editing and adding multiple units
- Unable to create Study endpoints resulted in throwing error

#### Define Study -> Study Structure
- "Existing visits Names and Timing" on Add Study Visit is not showing all previously entered visits or not showing any visits at all
- The "Timeline preview" on the Study Visits tab is incorrectly limited to only show the amount of visits set to be shown by the "Rows per page" dropdown list at the bottom of the page

#### Define Study -> Study Structure -> Study Visits
- Could not delete Final treatment  ('End of treatment' ) as it is showing  Error: "NoneType" object has no attribute "visit_order"
- Time line preview is not refreshing automatically after adding the visit
- Adding visits manually defined visits in "Existing visits Names and timing window" not displayed in proper order
- Error in calculation of negative study duration time

#### Define Study -> Study Structure -> Study branches
- Updates to number of Patients in arm is only impacting in branch after F5

#### Define Study -> Study properties
- History page not showing study intent type null value code

#### Manage Study -> Study -> Study Core Attributes
- Navigation path for Study core Attributes missing (Breadcrumb error)

#### Manage Study -> Study -> Study Status
- Possible to open release and lock form for study subpart

#### Manage Study -> Study -> Study Subparts
- Multiple issues found when adding new study (or) existing study as Study Subparts
- Not possible to Edit a study subpart when logged in as a 'Study Setup User'
- Option to edit and reorder study subparts should be disabled for a locked parent study
- Possible to add a study subpart to a locked parent study

#### Study List
- Filtering on study list is not working correctly for study subparts
- It must be possible to add a study without Study number
- Not possible to see who has created a study
- The lack of sorting order for Project IDs made it difficult to search for specific individual Project IDs


## V 0.8.1

## New Features
- Initially one NeoDash report is included in the deployment process into the database. The NeoDash report can be opened when connecting manually to the database, see system user guide. Short NeoDash userguide added on the documentation protal.
- Under Library, Admin Definitions new pages support maintenance of Clinical Programmes and Projects.

## Feature Enhancements

### General
- Release number correctly displayed on About page. Various minor improvements to table displays.

### Studies
- Empty column is added to the Protocol SoA to support manual references to protocol sections.
- Add display of additional timing variable in Study Visits table. If a footnote is added to a level, that is hidden for the protocol SoA, then the footnote letter should be carried up to the next level above.  Hide retired library activities from the listing on the Add new study activity from library form.  Add unit name in API response for /concepts/numeric-values-with-unit.  Return all code lists for a CT term in API response from /ct/terms/{term_uid}/names.
- Possibility to control the display of the SoA groups in the Protocol SoA from the detailed SoA. Improved filtering on activity group and subgroup. DocX generation supported for Detailed SoA and available for download together with .csv files.
- All pages under Define Study menu now supports display of a released or locked study.
- Study Structure, Study Activities and Study Interventions pages also support display only views that can be used by all user groups including users with view only access.
- Under Manage studies the system supports defining sub part studies for a parent study, thereby supporting study definitions covering multiple parts with independent study design, SoA, etc.

### Libraries
- Performance Improvements done for Syntax Templates to work bit faster and to achieve better user experience.
- Additional attributes and minor improvements to activity request form (activity placeholders).
- Support multiple groupings can be defined for activity concepts.
- Improvements of sponsor preferred names for a number of CDISC controlled terminology as part of sample datasets.
- Overview pages for activities and activity instances now include an simple CDISC COSMoS YAML display page with a download option. Overviews are improved including cross reference hyperlinks.
- Uppercase first letter in template instantiation when first text is a Template Parameter.
- Add permanent filters on Library/concept/activities/List of activities and Activities Instances. Avoid overwriting existing choices in batch edit functionality in detailed SoA. Improve About StudyBuilder page front end. Option to go one step back in Library overview pages. Correct sorting of project ID when adding studies. Change key criteria column in criteria template table to Yes/No from True/False and include selection of value to edit dialogue. Update display of SBOM in About page.

### API
- Refactoring parts of the API code, including reduction of the number of calls made by the backend to the DataBase, to improve loading times when working with syntax templates
- API support study activity instances as part of the Operational SoA, UI implementation will follow in next release.
- Implement support for additional registry identifiers in API (UI implementation will follow in next release).
- Indexes and constraints added to the database to improve query performance. This reduces loading times for the various pages related to syntax templates in the front-end.


## Bug Fixes

### API
-  StudyBuilder Production Application stops working due to API logging overloaded
-  API cannot find correct authentication key after keyrotation.
-  Clearing a StudyField get recorded in a non-standard way in audit trail.
-  DELETE /ct/terms/{term_uid}/attributes/activation -> Unable to retire a term that is not included in the latest CT Package.

### DB Schema migration
- Missing relationships in Activities in the Library

### Library
-  Code Lists -> CT Packages:  Viewing code lists in past CDISC packages does not include all terms.
-  Code Lists -> CT catalogues: 502 error appearing several times (Temporary fix applied).
-  Concepts -> Activities: Default filters are bypassed when changing some other filtering parameter.
-  Concepts -> Activities: Error when filtering out Activity Group in Activity Subgroups tab.
-  Concepts -> Activities: The history pages of Activity Instances do not show Activity name.
-  Concepts -> Units: It is not possible to filter units on Unit Subset.
-  Concepts ->Activities: Handling placeholder request form greyes out.
-  Concepts ->Activities: Possible to select draft activities while creating and editing activity instances.
-  Syntax Templates -> Criteria Templates: When exporting preinstance templates to Excel the exported file contains no data and the column headers are not releated.
-  Syntax Templates -> Criteria templates: When downloading Inclusion Criteria pre-instances only the column headers are included in the downloaded file.

### Studies
-  Define Study -> Study Activities: Adding activities from other studies - "Requested" activities cannot be added by other studies
-  Define Study -> Study Activities: After adding activity placeholders, system does not allow to hide activity grouping
-  Define Study -> Study Activities: Creating activity placeholders without activity group and subgroup gives an error
-  Define Study -> Study Activities: Not possible to change preferred time unit in visit overview
-  Define Study -> Study Activities: Sorting of reference visit for special visit is not in ascending order
-  Define Study -> Study Activities: Retired' and 'Draft' activities are also shown by default in the 'Add study activities' window
-  Define Study -> Study Activities: Batch editing several activities in Detailed SoA sometimes adds an activity to more visits than selected
-  Define Study -> Study Activities: Clicking on the Protocol SoA tab returns an error in some cases
-  Define Study -> Study Activities: Default filters are bypassed when changing some other filtering parameter in the pop-up window to Add study activities from Library
-  Define Study -> Study Activities: It is not possible to filter on more than one column at a time when adding Activities from Library on the Study Activities tab
-  Define Study -> Study Activities: Performance issues when grouping visits on the Detailed SoA tab
-  Define Study -> Study Activities: Studies in production cannot remove activities 
-  Define Study -> Study Activities: The export of Study Activities do not include information in all columns
-  Define Study -> Study Activities: User is not directed back to the Edit dialogue after saving the footnote assignment on the Detailed SoA page
-  Define Study -> Study Activities: When adding activities from library, the filter put to selecting study activities is showing final activity request that have not yet been approved.
-  Define Study -> Study Activities: When creating a placeholder for a new activity request then it is possible to select subgroups that are still in draft, this makes the application throw an error
-  Define Study -> Study Activities: 502 error appearing several times when add new study activity (Temporary fix applied).
-  Define Study -> Study Criteria: Cannot change rows per page for criteria's
-  Define Study -> Study Criteria: When filling in any template some codelists have Empty 'codes' 
-  Define Study -> Study Criteria: Units showing in lower case in inclusion Criteria
-  Define Study -> Study Criteria: Filtering selection fields showing long HTML scripted text format of 'Guidance text'
-  Define Study -> Study Purpose: Difference in objective/endpoint from define to view spec to download
-  Define Study -> Study Purpose: Endpoint titles come with HTML when using a filter
-  Define Study -> Study Purpose: Previous selection does not disappear after importing a template
-  Define Study -> Study Purpose: Duplicated template parameters found in the Study Endpoint section.   
-  Define Study -> Study Structure: In Study Elements only 10 elements are shown even though more elements have been created
-  Define Study -> Study Structure: This page is not functional if a "Special Visit"  incorrectly is the only visit in a "Study Epoch" 
-  Define Study -> Study Structure: Week selected as preferred time unit is not reflected in Protocol SoA
-  Define Study -> StudySoAFootnotes is automatically updated when FootnotesRoot is updated, API returning latest FootnotesValue
-  View Listings -> Analysis study Metadata(New):  Page displays "white page" on Analysis Study Metadata page
-  View Specification -> SDTM Study Design Datasets: Excel download replace Null value by None - Should stay as empty cells


##  V 0.7.3 (01-FEB-2024)

## Fixes and Enhancements

### Studies
- Unwanted HTML tags are removed when listing 'Study Endpoint' template parameter values for selection in e.g. Study Objectives of Study Purpose.
- In the Version history table for various study elements, HTML characters in the text columns have been removed in Study Criteria.
- SDTM study design datasets can now be downloaded without error.
- Hiding retired activities and showing only Final activities in the list by default for better view in 'Studies' Module.

### Libraries
- Out of Memory error issue resolved when comparing the first and last version of a SDTM CT package in codelists.
- Removing "ADaM parameter code" as a mandatory field when adding a new Activitiy instance under concepts.
- If you hide a parameter in a sequence of parameters, the sentence generation is in correct format going forward for all template categories under Syntax templates.
- Hiding retired activities and showing only Final activities in the list by default for better view in 'Library' Module.
- On the "Overview" pages of "Activities" and "Activities Instances" boolean values are now displayed properly on the OSB YAML pane.
- Downloaded (.csv file) version of Inclusion Criteria Pre-instances contains all information going forward.

### API
- Refactoring parts of the API code, including reduction of the number of calls made by the backend to the DataBase, to improve loading times when working with syntax templates.
- The fundamental fix on API query parameter 'at_specified_date_time'is implemented resulted with no errors in API endpoints going forward.

##  V 0.7.2 (28-NOV-2023)

### Fixes and Enhancements
- Physical data model updates made for relationships from ActivityItemClass via ActivityItems to CTTerms for each ActivityInstnance, including simplifying the relationship cardinality. Name attribute removed from ActivityItem node, and ActivityItem node is no longer individually versioned in root/value pairs, but versioned as part of the outbound relationship from ActivityInstanceValue nodes..
- Study activity selection support selection of a specific activity grouping combination. Support the same activity can be added to the study activities multiple times under different groupings. Ability to display/hide groups for specific Activity Group combination. Ability to add SoA footnote at Activity Group level for specific group combination. Data collection Boolean added when searching and selection activities. Filtering corrected when searching and selection activities.is not working yet.
- New tabs added under Library -> Concepts -> Activities to support to support definition of activity groups and subgroups.Definition of activities and activity instances updated to use new activity groupings. Exiting tab for Activities by Groping now only support a hierarchal display of activity groupings. Page/size numbering is corrected when displaying activities in multiple groups. Data collection Boolean added for activities. NCI concept ID added for activities, activity instances and activity item class. Filtering and other display issues are corrected.
- Deleting a study epoch now reorders the remaining epochs correctly.
- The content on the Study Epoch page now remains visible after loading the Study Epochs page
- Adding a new visit more than once is now possible without reloading the Study Visit page under Study Structure.
- Proper error handling of strings with unbalanced parenthesis in Syntax Templates has been implemented in the API.
- API patching has been implemented for activityitemclass, if more than one version exists.
- Users are now able to select multiple study endpoints for secondary objectives under Study Purpose.
- The search bar on the Study Endpoints under Study Purpose is now working as intended.
- Indexes and constraints added to the database to improve query performance. This reduces loading times for the various pages related to syntax templates in the front-end.


### Other Changes

- StudyBuilder now supports creation and maintenance of footnotes in the Protocol SoA.

##  V 0.6.1 (27-SEP-2023)

### Fixes and Enhancements
- Syntax template refactorting includes 
    - Audit trial settings
    - API endpoints to retrieve Acitivity template instances
    - UI/UX improvements for study selections of syntax templates under study criteria
    - Study purpose and study activities, refinement of sequence numbering
    - Updates to 'edit' function for Objectives and Criterias
    - A number of improvements to both parent and pre-instance templates including display of history on both row and page level.

- Support multiple groupings and sub-groupings can be defined for activity concepts for both studies and libraries.

### New Features
- Under Study Activities sections, menu items and breadcrumbs where 'Flowchart' renamed to 'SoA' (Schedule of Activities), 'List of Study activities'renamed to 'Study Activities', 'Detailed Flowchart' renamed to 'Detailed SoA' and 'Protocol flowchart' renamed to 'Protocol SoA' in accordance with TransCelerate Common Protocol Template and ICH M11 terminology.
- SoA Footnotes implemented under Activities tab for Studies Module which helps the user can decide if the Activity Group or Subgroup is to be displayed or hidden in the Protocol SoA.

### Technical updates
- Renaming of 'data-import' repository to 'studybuilder-import'
- DDF adaptor repo changes from 'DDF-translator-lib' to 'studybuilder-ddf-api-adaptor'
- Neo4j DB version upgrade from V.4.4 to V.5.10, which includes Cypher changes (new syntax updates) and Management changes (changes to neo4j-admin, new command options, new backup file format and Custom procedures declaration updates). The versions precisely as neo4j DB version 5.10.0 and APOC version 5.10.1.

##  V 0.5 (05-JUL-2023)

### Fixes and Enhancements
- Improvements to audit trail tracking changes in outbound relationships to related nodes as changes.
- Documentation regarding packaging of python components (e.g. API) is outdated in several places. Corrected API issues reported by schemathesis. Auto-increment of version number enabled in the auto-generated openapi.json API specification.
Upgrade to Python version 3.11.
- Adding missing 'Number of Studies' column for Timeframe instance.
- Some column displays for activity instances has been removed, they will for the moment only be part of detailed displays.
- Improvements to license and SBOM display on About page.
- Various UI, Audit trail and Stability improvements.
- Syntax template functionalities in Library is refactored with improved data model and consistency.

### New Features
- System documentation and Online help on Locking and Versioning of Studies improved.
- Initial implementation for display of Data Exchange Standards for SDTM in Library menu (Part of the foundational data model representation linked to the Activity Concepts model similar to the CDISC Bio-medical Concepts mode).
- Import of core SDTM and SDTMIG data models from CDISC Library is supported going forward.
- New pre-instantiations of syntax templates replacing previous default values.
- Create and Maintain ClinSpark CRF Library using StudyBuilder
- Two sample study Metadata (MD) listings implemented to support ADaM dataset generation.

## V 0.4 (24-APR-2023)

### Fixes and Enhancements
- UI/UX improvements.
- Activity Placeholder updates and its corresponded API, UI, Logical and Physical data model updates.
- Sharing OpenStudyBuilder Solution code to Public gitlab (NN SBOM task file updates).
- Activity concepts model improvements, logical & physical data model updates.
- Enabling Study Metadata Listings, properties for generation of SDTM and relevant API endpoint updates.
- Improvements of CRF Management with vendor extension, CRF display in HTML or PDF format and OID & UID refactoring.
- Database Consistency Checks for Versioning Relationships on Library Nodes.
- Additional capabilities on Activity Instance and Item Class Model.
- Improved support for ODM.XML vendor extensions.
- Legacy migration of Activity Instance concepts have been adjusted to match the updated data model. Note the content is not fully curated yet, improvements will therefore come in next release.
- Global Audit Trail report shared as a NeoDash report (intially NeoDash report runs separately).

### New Features
- Locking and Versioning of Study Metadata (incl. API and UI Designs, Logical and Physical Data model updates).
- Import of core SDTM and SDTMIG data models from CDISC Library is supported now (Part of the foundational data model representation linked to the Activity Concepts model similar to the CDISC Bio-medical Concepts mode).
- The Data Model and Data Model IG data structures is extended with a number of attributes to support sponsor needs. Note the UI is not yet made for these part - sample data is loaded into the system database for utilisation by NeoDash reports.
- Initial version of DDF API adaptor enabling Digital Data Flow (DDF) compatible access to StudyBuilder as a DDF Study Definition Repository (SDR) solution.
- The data import repository will also include a DDF sample study. 
- The listing of activity concepts include links to overview pages of bot an Activity Concept and an Activity Instance Concept. This is on two separate tabs, one showing a form based overview and one showing a simplifies YAML based overview. The YAML based overview will in a later release be made fully CDISC COSMoS compliant.
- A NeoDash Report displayed with outbound relationships from the versioned value node.
- A NeoDash based report is included with a more comprehensive display and browsing capabilities of Activity Concepts. This NeoDash report in shared in the neo4j-mdr-db git repository and must be launched manually. 

## V 0.3 (17-FEB-2023)

### Fixes and Enhancements
- Fixes on CRF library
  - Issues on the Reference Extension on the Front-end fixed.
- Improvements on Study structure and Study Interventions.
- Fix applied on visual indication of required/mandatory (*) fields in UI so unnecessary error messages can be avoided.

### New Features
- Further additions to CRF library module.
- API refactoring done, majorly use of snake case and aligning SB API with Zalando Rest API guidelines.
- Implemented API to support Activity Placeholders and User Requested Activity Concept Requests.
- Audit trail history studies.
- Implemented Disease Milestones under Study Structure.
- OS packages has been added for generating PDF. OS software licenses are included in git repositories, including the third party licenses. 


## V 0.2 (12-DEC-2022)

### Fixes and Enhancements
- Locked version of documentation portal. 
- neo4j database version updated in dockerfile. 
- Updated README to correct default password error.
- Added README section about platform architectures and docker.
- Added separate README to allow for starting up the OpenStudyBuilder only using Docker for neo4j and the respective technologies for the rest of the components, such as python and yarn. This can be found in DeveloperSetupGuide.md.
- General source code quality improvements, below mentioned:
  - Aligned SB API with Zalando REST API Guidelines, e.g. naming of endpoints, query and path parameters, proper usage of HTTP methods etc.
  - A number of API refactorings to be more consistent in design and use of snake case including: Aligned StudyBuilder API with Zalando REST API Guidelines, e.g. naming of endpoints, query and path parameters, proper usage of HTTP methods etc.
  - Fixed major warnings reported by Pylint/SonarLint static code analyzers.
  - Removed unused endpoints and code.
- Filtering corrected for Activities in a number of places.
-  A number of fixes and improvements to CRF module:
  - Edit references from CRF tree.
  - Improvements in UI for CRF Instructions.
  - Support for exporting attributes as ODM.XML alias.
  - A number of corrections and improvements to the CRF Library pages and ODM.XML import and export capabilities
  - Improvements for ODM-XML Import.
  - API: Added a new field 'dispaly_text' on the relation between OdmItemRoot and CTTermRoot.
  - Data Model: Added 'display_text' between ODM Item and CT Term.
  - Mapper for ODM XML export added.
  - Added Import library for ClinSpark.
- A number of bug fixes including: 
   - All Study Field Selections related to CT must have relationships in the database to selected CT Term.
   - StudyBuilder is hanging when duplicating a StudyVisit is fixed.
   - All timings are available for syntax templates
- Improvements to sample data, data import and readme descriptions
- Improvements to SDTM Study Design dataset listings.
- Improvements on ease-of-use, clean and simplify sample data
- Page level Version History on Study Activities, Study Endpoints, Study Intervention, Registry identifier pages.
- Fix applied for Page level version history on Study Properties and on row level studies/criterias.

### New Features
- Flowchart fitting for studies with many visits.
- Improvements to Word add-in
- Support creation of special visits without a specific time point reference
- Support multiple ODM.XML styles and extensions.
- Initial implementation to support generation of Clinical Trial Registration information in CDISC CTR.XML format. Note this is in part one only available via the API, a display via the View Spcifications menu item will be added later. Study Objectives & Endpoints HTML table built in the UI.


## V 0.1 (24-OCT-2022)

Initial commit to Public Gitlab.

