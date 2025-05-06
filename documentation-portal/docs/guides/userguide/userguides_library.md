---
title: The Library module
date: 03/May/2021
---

# The Library module

In this module, the user is able to create and manage all standards used in the MDR system.
The system offers access to the following directories:

| Section | Description       |
|:------:|:----------------|
| Dashboard| The most important metrics at a glance |
| Codelists  | Access to Controlled Terminology Catalogue, which is sored in the neo4j database. From here it is possible to create and edit code lists and add new terms. |
| Dictionaries | Manage standards such as MEDDRA, SNOMED, MED-RT and UNII |
| Concepts | Overview of reusable study-wide elements, such as measurements units, activities and assessments |
| Syntax Templates | Templates for  Objectives, Estimand, Endpoints, Assessments, Time frame and Criteria |
| Template Instantiations | Manage usage of each template |
| Template Collections | Library with templates on Project, Shared and Supporting Level |
| Data Exchange Standards | CDISC Controlled Terminology standards- CDASH, SDTM, ADaM  |
| List | Clinical Metadata listing |

## How to manage library elements
The management of each element follows the same pattern. Each action is traceable in the audit trail, specific for each type of element. Additionally, depending on the type of the element, each action will trigger a specific pop-up window with options for the specific template of choice.

### Add a new element

| Button | Behaviour       |
|:------:|:----------------|
| ![Add](~@source/images/bt_add_blue.png) | Click on the **'Add'** button. This will open a popup with a template form |

Adding a new template will automatically set it with a status of "Draft" and Version 0.1. The record in the audit trail would state "Initial Version".
After filling out the required fields, make sure to verify the syntax and avid any typos or mistakes.
When adding a new objective template, please first choose the Library, e.g. Sponsor Library.
Then describe the template in the "template" field and add any parameters in square brackets "[]".
Example:  'To document the safety profile of [StudyIntervention].'

The Parameter will then allow to choose from a list of elements which belong to this parameter, e.g. a list of Study Interventions.

![Add an Objective Template](~@source/images/library/standards/popup_add_objectivestemplates.png "Fig 3: Add a new Syntax Template")


### Modify

| Button | Behaviour       |
|:------:|:----------------|
| ![Search](~@source/images/bt_modify_blue.png) | Click on the **'Modify'** button at the end of the row that you want to update. This will open a dedicated popup with the template in modification mode like below |
Clicking the button described above will allow you to view the template details and describe the change in simple text.
Editing the template would open the same pop-up window with an additional field called "Change description", in which also [] can be used to specify a parameter.

![Modify an Objective Template](~@source/images/library/standards/popup_modify_objectivestemplates.png "Fig 4: Modify a template")

### Validate

| Button | Behaviour       |
|:------:|:----------------|
| ![Set Status to Final](~@source/images/bt_validate_blue.png) | Click on the **'Set the status of this template to Final'** button at the end of the row that you want to validate. |
This action is only available for templates with status "Draft". Validating the template will update the status to Final and the version number will be increased by 1.

### Inactivate / Reactive

| Button | Behaviour       |
|:------:|:----------------|
| ![Inactivate](~@source/images/bt_inactivate_blue.png) | Click on the **'Inactivate this Template'** button at the end of the row that you want to deactivate. |
| ![Reactivate](~@source/images/bt_reactivate_blue.png) | Click on the **'Reactivate this Template'** button at the end of the row that you want to re-ctivate. |

Deactivating an element will change its status to "Retired", the version number will remain the same. 
Re-activating an element will change its status to "Final", the version number will remain the same. 

### New version

| Button | Behaviour       |
|:------:|:----------------|
| ![New Version](~@source/images/bt_newversion_blue.png) | Click on the **'Create a new version'** button at the end of the row that you want to create a new version of the *Syntax Template*. |
To add a new version of an element, its status must be "Draft" or "Retired". Upon adding the new version, the numbering will increase automatically by +0.1. The change will be traceable in the audit trail with a description of the differences to the previous version.

### Export

| Button | Behaviour       |
|:------:|:----------------|
| ![Export](~@source/images/bt_export_blue.png) | Click on the **'Export'** button (before the Add button) to export the full set of the selected type of templates. |


### Delete an element

Deletion is available only for elements with status "Draft". Already approved elements, which are in use, can only be deactivated.



### View the Audit Trail

| Button | Behaviour       |
|:------:|:----------------|
| ![History](~@source/images/bt_history_blue.png) | Click on the **'History'** button.This will open a new modal page like bellow:<br/>Please note that the history is sorted in  |

The audit trail looks different, depending on the library section. The general columns are described in the Introduction section.

![Audit Trail Example](~@source/images/library/standards/library-standards-template-objective-history.png "Fig 5: Audit Trail Syntax Templates example page")




