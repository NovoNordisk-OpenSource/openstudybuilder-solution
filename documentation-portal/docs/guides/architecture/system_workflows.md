# System Workflows

This document describes dependencies in activities when using the StudyBuilder system. This is done in a series of activity diagrams followed by a short description of each activity.

This is a break down from the overall system data flows described (add link). When applicable links will be provided to the system user guides.

## Overall system activities

The StudyBuilder system covers the following overall activities:

[![StudyBuilder System Workflows](~@source/images/documentation/0-studybuilder-system-workflows.svg)](../../images/documentation/0-studybuilder-system-workflows.svg)


## Maintain Administrative Definitions

*To be made*

## Maintain Library Definitions

*To be made*

## Maintain Study Definitions

Within the "Studies" part of the OpenStudyBuilder, metadata for the studies can be created and managed. In the current release the focus is on the study setup and management to support the protocol process.

[![Maintain Study Definitions](~@source/images/documentation/1-maintain-study-definition.svg)](../../images/documentation/1-maintain-study-definition.svg)

| Activity     | Dependencies and prerequisites |
| ------------ | -------------------------------|
| **Create Study** <br> Creates a new study definition, or study sub part. | User must have 'Study Set-up User' access permission. <br> The related 'Clinical Programme' and 'Project' codes must be defined within the administrative module. |
| **Select Study** <br> Select the study to be defined. | Study must exist. |
| **List Studies** <br> List all draft, released and locked studies in one table and deleted studies on a seperate. | Studies in draft, released or locked state can be selected. <br> Core attributes for studies in draft status can be edited (same edit of core attributes as under manage study). |

### Manage Study

*To be made*

### Define Study

[![Define Study](~@source/images/documentation/4-define-study.svg)](../../images/documentation/4-define-study.svg)

The user must have 'Study Set-up User' access permission to add or edit any data for all activities under Define Study. All other access permissions will only enable display of data under Define Study.

| Activity     | Dependencies and prerequisites |
| ------------ | -------------------------------|
| **Study Titel** | Must be defined before a study can be locked. |
| **Registry Identifiers** | At the moment only specific registry identifiers can be defined. |
| ***Study Properties*** |
| **Study Type** | Sponsor defined extensions to the CDISC code lists for 'Trial Type' or 'Study Phase Classification' (Trial Phase) may be needed. Other terminologies on this page is not extensible. |
| **Study Atributes** | Sponsor defined extensions to the CDISC code lists for 'Study Intent Type' (Trial Intent Type), 'Intervention Model' or 'Study Blinding Schema' (Trial Blinding Schema) may be needed. Other terminologies on this page is not extensible. |
|  |
| ***Study Structure*** |
| **Study Arm** | Extensions for the sponsor code list 'Arm Type' may be needed. |
| **Study Branches** | Related Study Arm must be defined before a study branch arm can be made. |
| **Study Cohorts** |  |
| **Study Elements** |  |
| **Study Epochs** |  |
| **Study Visits** |  |
| **Study Design Matrix** |  |
|  |
| **Study Population** |  |
| ***Study Criteria*** |
| **Inclusion Criteria** |  |
| **Exclusion Criteria** |  |
| **Run-in Criteria** |  |
| **Randomisation Criteria** |  |
| **Dosing Criteria** |  |
|  |
| ***Study Interventions*** |  |
| **Study Compounds** |  |
| **Study Compound Dosing** |  |
| **Study Other Interventions** |  |
|  |
| ***Study Purpose*** |  |
| **Study Objectives** |  |
| **Study Endpoints** |  |
| **Study Estimands** |  |
|  |
| ***Study Activities*** |  |
| **Study Activities** |  |
| **Study Activity Instances** |  |
| **Detailed SoA** |  |
| **Protocol SoA** |  |
| **SoA Footnotes** |  |
| **Activity Instuctions** |  |
|  |


### View Specifications

*To be made*


### View Listings

*To be made*


## Down Stream Usage

*To be made*

