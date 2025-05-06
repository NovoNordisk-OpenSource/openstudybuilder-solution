# Versioning of Study Data standards

A study definition refers to many different types of library elements, all versioned after different principles. In this section we describe how these version related references work for a study, and how these behave when a study is [released or locked](#manage_studies.html#maintain-study-status-and-versioning).

Generally, a study selection of a versioned library element can be of the following types:

- **Controlled Terminology** like selection of study phase for a study.
- **Dictionary Terminology** like selection of indication for the study.
- **Syntax Templates** like selection of in- and exclusion criteria.
- **Concepts** like selection of an Activity for the SoA.

> ***Is this relevant for me to understand when defining a study definition for a protocol?***
> No, this is only relevant when applying the study definition for the study data specification mainly driving the data management and analysis deliverables.
> See last section on how the system behave when releasing or locking a study without selecting study data standard versions.

> ***So why is this then important?***
> If e.g. similar phase III studies within a program are run almost at the same time, or an extension study is made for a main study, then it is important to apply consistent use of terminologies across these studies from protocol to submission data deliverables.
> When different data standard versions is selected for a study specification (as it will be when a study is released or locked) then this can impact any of the related deliverables potentially including the structured protocol content. This must be acknowledged, and the system will support impact assessment of changes related to updates in related versioned library elements.
> In future ICH M11 based digital protocol submissions related to Controlled Terminology (CT) will be part of the protocol submission and the system therefore need to be prepared for control applied CT versions.


## Controlled Terminology Selections

These can be either CDISC or sponsor defined Controlled Terminology (CT). For both we define the sponsor preferred name, or synonym, we will use in protocol documents, CRFs and other documents beside the submission value used in the submission datasets. The sponsor preferred name is defined both in title case for e.g. display in listings as well as in sentence case to be part of syntax template structured text.

These are versioned in CT Packages by CDISC, but as we define extensions to these code lists of terms as well as our sponsor preferred names, we also version these as sponsor CT packages. Each sponsor CT package is always based on a CDISC CT package for a specific domain (like SDTM CT).

The system is made so all study selections related to CT is made version independent of a CT Package version. The selection of the CT package version is then done centrally for the study enabling you can decide to apply a specific version as well as up-versioning or down-versioning the CT Package version. If the relevant CT Package is not selected the UI will show the latest sponsor value. If the selected value is not available in the currently selected CT Package for the study a notification will be displayed.

Reports also support impact analysis of these changes and the UI support notifications if a current CT selection is not valid according to the currently selected CT Package version.

[> NOTE, section on impact assessment is to further be defined and written]: #

Selection of a CT Package version is done on the page: Studies -> Manage Study -> Data Standard versions -> Controlled Terminology ([see section on how to select and edit CT Package Version](#How-to-select-and-edit-CT-Package-Version)).

[![Study CT Package Versions](~@source/images/user_guides/study_data_standard_versions_01.png)](../../../images/user_guides/study_data_standard_versions_01.png)

### How to select and edit CT Package Version

You can select CT Package versions from the menu **Manage Study --> Data Standard Versions** on the tab **Controlled Terminology**. 

#### Follow these steps to add a CT Package selection:

1. Select the (+) button.
1. Select the related CT Catalogue (e.g. SDTM CT). Note, you can only select one CT Package per CT Catalogue.
1. Check if any Sponsor CT Package exist that can be used.
1. Select to create a new Sponsor CT Package related to a CDISC CT Package or select an existing Sponsor CT Package.
1. When selecting an existing Sponsor CT Package, you can filter by selecting a CDISC CT Package (e.g. SDTM CT 2020-01-30).
1. When creating a new Sponsor CT Package, the CDISC CT Package it is based on must be selected.
1. Click the select or create Sponsor CT Package button.

[![Select CT Package Version](~@source/images/user_guides/study_data_standard_versions_01.png)](../../../images/user_guides/study_data_standard_versions_01.png)

#### Follow these steps to edit a CT Package version selection

1. Select the ... row action for the CT Package you will like to edit and select [Edit] action.
1. Change CT Package version selection.
1. Save changes.

The selection will always be driven by selecting a Sponsor CT Package related to a CT Catalogue. This Sponsor CT Package is then always based on a CDISC CT Package, so the selection is implicitly also selecting a CDISC CT Package.

#### Follow these steps to remove a CT Package version selection

1. Select the ... row action for the CT Package you will like to remove and select [Delete] action.
1. Confirm the detetion by selcting [Continue]


## Dictionary Terminology Selections

The dictionary terminologies are defined by different data standard organizations, and they all have different versioning and release principles. Currently the system support subsets from the following dictionaries:

- SNOMED CT (Systematized Nomenclature of Medicine - Clinical Terms) for Diseases and Disorders
- MED-RT (Medication Reference Terminology) for Pharmacologic Class (PCLASS)
- UNII (Unique Ingredient Identifier) for Active Substances
- UCUM (Unified Code for Units of Measure)

>**It is planned to add support of more dictionaries in later releases.**

The study selection of dictionary terms is also made independent of versions following the same principles as for CDISC and Sponsor terminologies. The system does however not yet support study level selection of dictionary versions. The latest available version will therefore always be displayed until the version support is added for dictionaries in a later release.

[### How to select and edit Select Dictionary Version]: #

[> *Management and selection of dictionary versions are not yet supported in the system.*]: #


## Syntax Templates Selections

The syntax templates are used to manage structured text with parameterization for study objectives, endpoints, time frames, criteria, and footnotes.

The syntax templates are versioned as individual elements in the library and the study selection of a syntax template is always made as a version specific selection.

If a syntax template is available in a newer version the system will show a notification for the user to use the new version or keep using the current version of the syntax template.

>**The central selection for study data standards for a study will therefore not cover versions of syntax templates.**


## Concepts Selections

The concepts are most importantly used for activities, linked to our activity concepts, being the main biological concepts in the system ([see also section on Study Activities](userguide_activities)). But compounds, unit definitions and the CRF data collection instruments are also regarded as concepts as they correspond to a complex library element.

The concepts are versioned as individual elements in the library and the study selection of a concepts is always made as a version specific selection.

>**The central selection for study data standards for a study will therefore not cover versions of concepts.**
>But note concepts can have relationships to CT terms, like the specimen or collection units.

In the process of extracting metadata for the metadata driven programs supporting e.g. the pre-SDTM the correct terminology can be applied based on the selected CT Package for the study. So, in this context the CT Package selection for a study is also applied for concept definitions.


[## Data Exchange Standard Selections - to be written]: #

[### How to select and edit Data Exchange Standard Version]: #

[> *Selection of data exchange standard versions are not yet supported in the system.*]: #


## Study Data Standards Plan

> *Display of the study data standards plan are not yet supported in the system.*

When the display of the study data standards plan will be supported, two versions will be displayed. One only for the external data standard version references, this version will support the external submission requirements for the study data standardization plan. The second is for internal use and include references to the internal versions of sponsor extensions as well as external standards (like laboratory data exchange standards).

The display will also be supported in two views. One view only displaying the standard versions for a specific study, and extended display show the standard versions for all studies in the project related to the selected study.

[### For external data standards]: #

[> *More details to be added when supported*]: #

[### For internal data standards]: #

[> *More details to be added when supported*]: #


## Releasing and Locking a study without selecting terminology versions

Internally the system must have a static reference to a Sponsor and CDISC CT Package when a study is released or locked to enable a persistent data extract of study level CT selections. This is due to the principle that CT package selections is done for the complete study with the option to up- and down-version the CT package for a study.

In the early phases of the study specification process it is however not feasible to make these selections yet. The system is therefore designed so if no CT Package selection have been made the system will automatically select a CT Package from the same date. If a CT Package do not exist on the same date, one will dynamically be created.

This will make the release and lock process more smooth hiding this versioning complexity for the user and at the same time enable persistent data extract of study level CT selections. The CT Package version selection will however only be applied to the released or locked data, the subsequent draft study definition will not keep this selection.

If the study is re-released or re-locked at a later date without specifying a particular version, the version of the CT package applied will be the one current on the day the release or lock is executed.

### How to Release or Lock a study without a CT Package version selected

When releasing or locking the study ([see section on how to manage studies](manage_studies#maintain-study-status-and-versioning)), then the system will check if a SDTM CT Sponsor CT package version is selected. If it is not selected then the system will dynamically select one from the day or create one and select it if no one exist on the day.

If the released or locked study definition is selected, then the automatically selected CT packages will be displayed on the study data standard versions page. But the selection will not be kept for the following draft version of the study definition.

### How a study will be cleared from an automatically selected CT Package version when unlocked

When unlocking a locked study ([see section on how to manage studies](manage_studies#maintain-study-status-and-versioning)), then any automatically selected CT Package will be cleared and no longer be listed on the study data standard versions page.

The previously automatically selected CT Packages will be listed in the history pages.


> NOTE: See also sections on [Study Versioning](#manage_studies.html#maintain-study-status-and-versioning)



