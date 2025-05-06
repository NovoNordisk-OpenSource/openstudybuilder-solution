# Study Data Specifications

## Study Activity Instances

A Study activity instance is a related package that is linked to the activity provided from the library. The package consists of codes needed for the downstream processing of data, like data collection, SDTM and ADaM. These codes are required for submissions and the intention is to standardise deliveries, so Health authorities can perform the review of the submission faster.
The Study Activity Instances page provides an overview of activities and related instances, connecting metadata end-to-end from protocol to analysis and CSR.

## Study Activity Instance Table Content: 

When you open this tab, you will see a table containing all study activities, related instances, and attached attributes. The table has the following column headers:

| Header  | Short explanation   |
|---------|---------------------|
| Library | Will usually be ‘Sponsor’ |
| SoA Group | The selected SoA group from the Study Activity |
| Activity Group | The Activity Group, that the selected study activity belongs to, e.g. AE Requiring Additional Data |
| Activity Subgroup | The Activity Subgroup, that the selected study activity belongs to, e.g. Laboratory assessment |
| Activity | The Study Activity in the study, e.g. Albumin |
| Data Collection | Yes or No. No will only be used for reminders or system operators or triggers |
| Activity Instance | The name of the Activity Instance, e.g. Albumin Urine |
| Topic Code | Code used for convert collected data to SDTM, e.g. ALBUMIN_N_URINE |
| State/Action | Will depend on the setup in the library. Please refer to section named Investigating the table |
| ADaM Parameter code | The code used ADaM e.g. ALBU |

*Table 1, Content in the Study Activity Instance table*


[![Activity Instance relation](~@source/images/user_guides/data_specifications_01.png)](../../../images/user_guides/data_specifications_01.png)

*<p style="text-align: center;">Figure 1 Screenshot of the Activity - Activity Instance relation</p>*

## Investigating the table

There is one row per activity-instance relation.

If an activity has more than one required activity instance related, then one row will be available for each activity instance related to the activity.

This means that some activities like ‘Treadmill Test’ will have 3 rows as the validated test includes 3 measurements:

[![Activity Instance table](~@source/images/user_guides/data_specifications_02.png)](../../../images/user_guides/data_specifications_02.png)

*<p style="text-align: left;">Table 2 One row per required activity Instance</p>*

If a study only wants to collect one of the measurements, then it is no longer the validated instrument, and a new Activity will have to be created with a single related instance.

If an activity has more than one defaulted activity instance related, then only one of them will show up, and it possible to select one of the others instead, but not possible to have more than one activity instance selected in the study. If a study wants to have more than one activity instance presented for an activity, where this is currently not the case, then the study must request a new activity with multiple required activity instances.

The colour legends in the Activity Instance column are:
- <font style="background-color:green;">Green</font>: Action is not required
- <font style="background-color:yellow;">Yellow</font>: Notification/suggestion
- <font style="background-color:red;">Red</font>: Action required due to no available activity instance

Independent of the colours, it is advisable to check all content for a study to make sure that all needs are covered.

## Rules for populating activity instance relations

Most activity-instance relations are auto-selected and auto-published by basic rules:

[![Activity Instance rules](~@source/images/user_guides/data_specifications_03.png)](../../../images/user_guides/data_specifications_03.png)

*<p style="text-align: left;">Table 3 Rules for activity instance selection</p>*

## Edit relationship

In the Row Actions to the left (the 3 dots) several options are available:
- Edit Activity-Instance relationship: opens a form to edit the relationship. Only activity instances that are available for the activity can be chosen. It is not possible to select multiple instances for an activity on the study level. This can only take place in the library and should only take place in a global setting. 
- Delete Activity-Instance relationship: deletes the relationship, with a warning before deletion
- Update Instance to new version: only available when a new version of the activity instance is available in the library. A small form will ask if you wish to update, with the option to select Yes, No, or Cancel.
- Row History: shows all changes

Currently you cannot request new activity instances from inside StudyBuilder. If needed, this must go through the study Standards Developer.

The page comes with two default filters on Activity and Activity Instance. These can be removed or replaced using the filter button.

It is possible to download the Study Activity Instances as .csv, .json, .xml and excel, where excel is very easy to filter on.  


## Purpose of the Operational SoA table

The table contains all the information from the Study Activities tab, the detailed SoA tab and the Activity Instances tab. 

The table is intended for QC of Protocol (Similar to the Protocol Metadata Document (PMD), CRF content, SDTM and ADaM generation and for providing information to vendors.

## Investigating the Operational SoA table

In this table, there is no option to add, edit, or delete information, besides normal page actions and view options. It is possible to download the table in different formats in the upper right corner.

The top rows of the table display the visit scheduling information, including epochs, visits, visit window, and timing towards the global anchor (baseline).

The selected preferred time unit will also be visual in the grey area above the table content.
The left-hand column displays the hierarchy for the activities, starting with the SoA group (if turned on), Activity Group, Activity subgroup, Activity, and Activity Instance. The legends of the levels are currently not implemented.

There is a fold-out option with expand or collapse all, and the option to expand within the groupings.
On the activity instance level, the Topic Code and ADaM Parameter Code are visual. The activity instances carry a hyperlink to access additional instance information in the library.


[![Operational SoA table](~@source/images/user_guides/data_specifications_04.png)](../../../images/user_guides/data_specifications_04.png)

*<p style="text-align: left;">Figure 2 Operational SoA table</p>*




