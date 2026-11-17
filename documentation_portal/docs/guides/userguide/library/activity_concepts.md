# Activity Concepts

## Introduction

An ***Activity*** is by CDISC defined as an action, undertaking, or event, which is anticipated to be performed or observed, or was performed or observed, according to the study protocol during the execution of the study.

CDISC defines a ***Biomedical Concept*** as a unit of biomedical knowledge created from a unique combination of characteristics that include implementation details like variables and terminologies, used as building blocks for standardized, hierarchically structured clinical research information.

OpenStudyBuilder (OSB) supports biomedical concepts of different types. A concept is more than a single term in a codelist. Controlled terminology lists single terms, whereas a concept combines several related elements into one definition. Because the term *biomedical concept* can cover many different things and is difficult to grasp, OSB names them simply **Concepts**, as a broad term. Concepts are managed under **Library** → **Concepts**. The most important type is the concept that details activities, named **Activity Concepts**.

An Activity Concept in OpenStudyBuilder is made to support both the protocol specification (electronically) as well as Forms creation and SDTM/ADaM generation. An activity can be a clinical data recording (like measurement of body weight), but it can also be an activity performed during the study that is not leading to collection of data (like a reminder to hand out the ID card). Administration of study drug is not such an activity, as data about the administration is usually collected.

In OSB the broad description above is split into two levels, which are defined one after the other: an **Activity** states *what* is performed or observed in the study, and an **Activity Instance** is its detailed definition, stating *exactly* what is measured or recorded.

An Activity can have one or more Activity Instances. The **Multiple instances allowed** flag on the Activity controls whether more than one of its Activity Instances can be selected for the Activity in a study.

| | Activity | Activity Instance |
|---|---|---|
| Question answered | What is performed or observed in the study? | What exactly is measured or recorded for the Activity? |
| Defined by | Name, groupings, flags, synonyms and optional NCI reference | Activity Instance Class, Activity Items (including the standard unit), ADaM PARAM/PARAMCD and topic code |
| Used in | Protocol SoA and protocol section 8 | Operational SoA, data collection (Forms and external specifications), SDTM and ADaM |
| Example | Weight, grouped under the Activity group and Activity subgroup Body Measurements | Body Weight, with Activity Instance Class Numeric Findings, test code Weight, standard unit kg, ADaM PARAMCD WEIGHT and topic code BODY_WEIGHT |

> [!IMPORTANT]
> In OSB the ADaM PARAM/PARAMCD is part of the Activity Instance definition, which differs from other biomedical concept definitions (for example CDISC). The standard unit is defined for the Activity Instance, so the ADaM PARAM/PARAMCD is specified together with it. This applies to ADaM parameters that are not derived, other than by unit conversion.

> [!NOTE]
> Protocol section numbers in this guide refer to the [ICH M11 Clinical electronic Structured Harmonised Protocol (CeSHarP) template](https://www.ema.europa.eu/en/documents/template-form/ich-m11-clinical-electronic-structured-harmonised-protocol-cesharp-template-step-5_en.pdf), Step 5, 11 December 2025 (EMA/CHMP/ICH/778801/2022). The Schedule of Activities is section 1.3 and Trial Assessments and Procedures is section 8 of that template.

The activity concepts model is managed in the following tabs under **Library** → **Concepts** → **Activities**, each described in its own section below:

- [Activities](#activities): what is performed or observed in the study.
- [Activity Groups](#activity-groups) and [Activity Subgroups](#activity-subgroups): the two grouping levels for Activities.
- [Activities by Grouping](#activities-by-grouping): browse Activities by the grouping hierarchy.
- [Activity Instances](#activity-instances): the detailed definitions of what is measured or recorded for an Activity.
- [Requested Activities](#requested-activities): requests for new Activities, handled or archived.
- [Activity Instance Classes](#activity-instance-classes): the types of logical observation for Activity Instances.
- [Activity Item Classes](#activity-item-classes): the kinds of information that can be specified for an Activity Instance.
- [Non-Standard Variables](#non-standard-variables): variables that extend SDTM datasets.

Each of these library objects is individually versioned, see [Versioning of each library element](../userguides_introduction.md#versioning-of-each-library-element) in the User Guide introduction.

The tabs Activities, Activity Groups, Activity Subgroups, Activity Instances and Non-Standard Variables share the same features: fast filtering between status Final, Retired, Draft or All, free search, filtering, column displays, history and export, as well as the actions to add, edit and delete. Hyperlinked column values in the display tables open an overview page. The tabs that differ are described in their own sections.

Each section is described in the same way: (purpose, when to use, prerequisites), **Quick Guide** (expandable step-by-step), **Experienced** (best practice and quality checks), **Troubleshooting** and **Related topics**. The steps are:

- [Open an Activity overview](#open-an-activity-overview), [Create Activity](#create-activity)
- [Create Activity Group](#create-activity-group), [Create Activity Subgroup](#create-activity-subgroup)
- [Create Activity Instance](#create-activity-instance), [Edit Activity Instance](#edit-activity-instance), [Edit Groupings for an Activity Instance](#edit-groupings-for-an-activity-instance)
- [Import Non-Standard Variables](#import-non-standard-variables), [Create Non-Standard Variables](#create-non-standard-variables)

The row actions on the 3 action dots menu of a table row (for example **Edit**, **New version**, **Approve**, **Inactivate**) are shown only when the status of the row allows the action and the user has write access to the library.

## Activities

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activities** tab

Activities state what is performed or observed in the study, without specifying the data items; these are defined on the Activity Instances. An Activity not related to data collection has a precise definition but no resulting data (for example the reminder activity Hand Out ID Card). Activities are shown at the level of detail needed in the protocol SoA and are referred to in protocol section 8 and the protocol appendixes.

::: details Activities table

| Column  | Description         |
|---------|---------------------|
| Library | Reference to which library the activity belongs to. This is Sponsor for activities defined and approved as standard within OSB; it can be set to CDISC if imported from CDISC Library; and it can be Requested if this activity is part of a user request. |
| Activity group | Sponsor name for the high-level grouping of activities. The activity group name can be used to be displayed in protocol SoA, as sub-section in protocol section 8, and as grouping in appendix 2 for lab assessments. |
| Activity subgroup | Sponsor name for the second level grouping of activities. The activity subgroup name can also be used to be displayed in protocol SoA, as sub-section in protocol section 8, and as grouping in appendix 2 for lab assessments. |
| Activity name | Sponsor name for the activity in title case. This can be chosen to be displayed in protocol SoA, will be the name being referenced in protocol section 8 and appendixes. |
| Sentence case name | Same name for the activity in lower case, but with correct casing in abbreviations if these are part of the name. This sentence case name is intended to be used in text generation for protocol section 8 and other sections when in-text references are made to activities so these occur in correct case. |
| Synonyms | Array of synonyms, these are defined to support flexible search and selection of standardised activity names. |
| Definition | The sponsor definition of the activity, this can be made with input from external definitions. |
| NCI Concept ID | NCI Thesaurus concept code identifier |
| NCI Concept name | NCI Thesaurus preferred name. As OSB currently does not have a reference to the full NCI Thesaurus, a direct reference to the preferred name is kept in addition to the NCI concept ID. |
| Abbreviation | A sponsor defined abbreviation for the activity. |
| Data collection | Boolean flag to indicate if this activity relates to data collection. If not, the activity refers to reminders and procedures without data collection. |
| Multiple instances allowed | Boolean flag to indicate if more than one Activity Instance of this activity can be selected for the activity in a study. If not, only a single Activity Instance can be linked at study level. |
| Legacy usage | Boolean flag to indicate if this activity is created for legacy data migration usage, and should not be used for new study specifications. |

:::

### Open an Activity overview

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activities** tab

#### Baseline

**Purpose.** The overview page shows a single Activity with its relevant actions, different display views and hyperlinks to related elements (for example Activity group and Activity subgroup).

**When to use.** Use the overview when the table row does not give the full picture of an Activity, or to navigate to the Activity group, the Activity subgroup and the Activity Instances of the Activity.

#### Quick Guide

::: details Show Quick Guide

 1. Select **Library** → **Concepts** → **Activities** → **Activities** tab, search for the Activity and click its name in the table. The overview page opens.

     [![Activity name link on the Activities tab](/images/user_guides/activity_concepts_14_activity_name_link.png)](/images/user_guides/activity_concepts_14_activity_name_link.png)

 1. Review the attributes of the Activity at the top of the page. Select another entry in the **Version** list to see an earlier version of the Activity. The **Activity groupings** box lists the Activity group and Activity subgroup combinations of the Activity, with the Activity Instances related to it. Click a name in the box to open the related Activity group, Activity subgroup or Activity Instance.

     [![Activity overview page](/images/user_guides/activity_concepts_15_activity_overview.png)](/images/user_guides/activity_concepts_15_activity_overview.png)

     *Activity overview: (A) Version, (B) Activity groupings, (C) link to the Activity group.*

:::

#### Related topics

- [Activity Groups](#activity-groups) and [Activity Subgroups](#activity-subgroups)
- [Create Activity](#create-activity)

### Create Activity

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activities** tab

**Purpose.** An Activity states what is performed or observed in the study, without specifying the data items. It is the item selected for the protocol SoA and referred to in protocol section 8.

**When to use.** Add an Activity when the study needs something to be performed or observed that is not yet in the library. Search the Activities tab first, as an Activity with the same name cannot be added twice.

| Selection | Use it when |
|---|---|
| **Data collection** selected | The Activity results in collected data. Activity Instances can then be added for the Activity, see [Create Activity Instance](#create-activity-instance). |
| **Data collection** cleared | The Activity is a reminder or a procedure without data collection (for example the reminder activity Hand Out ID Card). |
| **Multiple instances allowed** selected | More than one Activity Instance of the Activity can be selected for the Activity in a study. |
| **Multiple instances allowed** cleared | Only a single Activity Instance can be linked at study level. |

**Prerequisites.**

- The Activity group and Activity subgroup to be used exist with status Final. Only Final groups and subgroups are offered in the form, see [Create Activity Group](#create-activity-group) and [Create Activity Subgroup](#create-activity-subgroup).

#### Quick Guide

::: details Show Quick Guide

 1. Select **Library** → **Concepts** → **Activities** → **Activities** tab, click the **'Add activity'** icon.

     [![Add activity icon on the Activities tab](/images/user_guides/activity_concepts_00_add_activity_button.png)](/images/user_guides/activity_concepts_00_add_activity_button.png)

 1. In the **Activity groupings** box, select the **Activity group** and **Activity subgroup**. Click the **+** icon to add a further grouping if the activity belongs to more than one.
 1. Enter the **Activity name** and the **Sentence case name**.
 1. Optionally enter the NCI Concept ID, NCI Concept Name, Synonyms and Abbreviation, and any other attributes described in the [Activities table](#activities) above.
 1. Select or clear **Data collection** and **Multiple instances allowed** as relevant for the activity.
 1. Click **SAVE**.

     [![Add activity form](/images/user_guides/activity_concepts_01_add_activity_form.png)](/images/user_guides/activity_concepts_01_add_activity_form.png)

     *Add activity form: (A) Activity groupings, (B) Activity name, (C) Sentence case name, (D) Data collection, (E) Multiple instances allowed, (F) SAVE.*

 1. The table keeps its **Final** status filter after saving, so the new Draft Activity is not listed. Select **Draft** or **All** in the status filter above the table.
 1. Approve the new Activity by clicking the **Approve** icon or via the table row 3 actions dots menu.

> [!NOTE]
> Define the Activity first, then add its Activity Instances. The detailed specification of what is collected is done when the Activity Instance is added.

:::

#### Experienced

- **Do this when.** An Activity belongs to more than one grouping: add each further grouping with the **+** icon in the **Activity groupings** box, so the Activity appears under every relevant group and subgroup.
- **Quality checks.** Before adding Activity Instances, confirm that the Activity has status Final. The Select activity step of the Add activity instance wizard lists only Final Activities of the Sponsor library that have **Data collection** selected.
- **Clarifications.** The Sentence case name can differ from the Activity name only in letter case (for example to keep abbreviations in capitals).

#### Troubleshooting

| Symptom | Interpretation | Likely cause | Fix / next safest action |
|---|---|---|---|
| The required Activity group or Activity subgroup is not in the list in the **Activity groupings** box | Only Final groups and subgroups are offered | The group or subgroup does not exist, or is still in Draft | Add it and approve it, see [Create Activity Group](#create-activity-group) and [Create Activity Subgroup](#create-activity-subgroup), then reopen the form |
| Saving is refused with a message that an Activity with that name already exists | Activity names must be unique | The Activity is already in the library | Search the Activities tab and use the existing Activity, or choose a more specific name |
| Saving is refused with a message that the lowercase versions of the name and the sentence case name must be equal | The Sentence case name differs from the Activity name by more than letter case | A word was changed or removed in the Sentence case name | Correct the Sentence case name so that only the casing differs |
| The Activity is not offered when an Activity Instance is added | The Select activity step lists only a subset of Activities | The Activity is not Final, is not in the Sponsor library, or has **Data collection** cleared | Approve the Activity. If data is to be collected, add a new version of the Activity, select **Data collection** and approve it |

**Undo vs not undoable.** A saved Activity is a Draft version. Approving makes it Final, and further changes then need **New version** on the row actions menu, which creates a new Draft version. An Activity that is no longer to be used is set to status Retired with **Inactivate** and brought back with **Reactivate**.

**Check before acting.**

- Search the Activities tab for an existing Activity with the same or a similar name.
- Confirm that the intended Activity group and Activity subgroup have status Final.

#### Related topics

- [Create Activity Group](#create-activity-group) and [Create Activity Subgroup](#create-activity-subgroup)
- [Create Activity Instance](#create-activity-instance)
- [Versioning of each library element](../userguides_introduction.md#versioning-of-each-library-element)

## Activity Groups

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Groups** tab

Activity Groups are the high-level grouping of Activities: the clinical term shown in the protocol SoA and as headings in protocol section 8. An Activity Group can resemble a CRF form name, but does not have to.

::: details Activity Groups table

| Column  | Description         |
|---------|---------------------|
| Activity group | Sponsor name for the high-level grouping of activities. The activity group name can be used to be displayed in protocol SoA, as sub-section in protocol section 8, and as grouping in appendix 2 for lab assessments. |
| Sentence case name | Same name for the activity group in lower case, but with correct casing in abbreviations if these are part of the name. This sentence case name is intended to be used in text generation for protocol section 8 and other sections when in-text references are made to activity groups so these occur in correct case. |
| Abbreviation | A sponsor defined abbreviation for the activity. |
| Definition | The sponsor definition of the activity group, this can be made with input from external definitions. |
| NCI Concept ID | NCI Thesaurus concept code identifier |
| NCI Concept name | NCI Thesaurus preferred name. As OSB currently does not have a reference to the full NCI Thesaurus, a direct reference to the preferred name is kept in addition to the NCI concept ID. |

:::

### Create Activity Group

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Groups** tab

**Purpose.** An Activity Group is the high-level grouping under which Activities are placed. It is shown in the protocol SoA and as a heading in protocol section 8.

**When to use.** Add an Activity Group when none of the existing groups fits the Activities to be added. Search the Activity Groups tab first.

**Prerequisites.** None. The group must be approved (status Final) before it can be selected when an Activity is added.

#### Quick Guide

::: details Show Quick Guide

 1. Select **Library** → **Concepts** → **Activities** → **Activity Groups** tab, click the **'Add activity group'** icon.

     [![Add activity group icon on the Activity Groups tab](/images/user_guides/activity_concepts_10_add_group_button.png)](/images/user_guides/activity_concepts_10_add_group_button.png)

 1. Enter the **Group name**. The **Sentence case name** is filled in from the Group name; edit it if abbreviations need other casing.
 1. Enter the **Definition**, which is mandatory. Optionally enter the Abbreviation, NCI Concept ID and NCI Concept Name.
 1. Click **SAVE**.

     [![Add activity group form](/images/user_guides/activity_concepts_11_add_group_form.png)](/images/user_guides/activity_concepts_11_add_group_form.png)

     *Add activity group form: (A) Group name, (B) Sentence case name, (C) Abbreviation, NCI Concept ID and NCI Concept Name, (D) Definition, (E) CANCEL and SAVE.*

 1. The table keeps its **Final** status filter after saving, so the new Draft Activity Group is not listed. Select **Draft** or **All** in the status filter above the table.
 1. Approve the new Activity Group by clicking the **Approve** icon or via the table row actions dots menu.

:::

#### Experienced

- **Clarifications.** An Activity Group is linked to Activities through the **Activity groupings** box when the Activity is added, see [Create Activity](#create-activity). The combination with an Activity Subgroup is made there, not on this form.
- **Quality checks.** The Sentence case name can differ from the Group name only in letter case.

#### Troubleshooting

| Symptom | Interpretation | Likely cause | Fix / next safest action |
|---|---|---|---|
| Saving is refused with a message that an Activity group with that name already exists | Group names must be unique | The group is already in the library | Search the Activity Groups tab and use the existing group |
| Saving is refused with a message that the lowercase versions of the name and the sentence case name must be equal | The Sentence case name differs from the Group name by more than letter case | A word was changed in the Sentence case name | Correct the Sentence case name |
| The form cannot be saved | A mandatory field is empty | The **Group name** or the **Definition** is not filled in | Complete the field marked as required |
| The new group is not offered when an Activity is added | Only Final groups are offered | The group is still in Draft | Approve the group |

**Undo vs not undoable.** A saved group is a Draft version until approved. Further changes to a Final group need **New version** on the row actions menu.

#### Related topics

- [Create Activity Subgroup](#create-activity-subgroup)
- [Create Activity](#create-activity)

## Activity Subgroups

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Subgroups** tab

Activity Subgroups are a second grouping level under the Activity Groups.

::: details Activity Subgroups table

| Column  | Description         |
|---------|---------------------|
| Activity subgroup | Sponsor name for the second level grouping of activities. The activity subgroup name can also be used to be displayed in protocol SoA, as sub-section in protocol section 8, and as grouping in appendix 2 for lab assessments. |
| Sentence case name | Same name for the activity subgroup in lower case, but with correct casing in abbreviations if these are part of the name. This sentence case name is intended to be used in text generation for protocol section 8 and other sections when in-text references are made to activity subgroups so these occur in correct case. |
| Abbreviation | A sponsor defined abbreviation for the activity. |
| Definition | The sponsor definition of the activity subgroup, this can be made with input from external definitions. |
| NCI Concept ID | NCI Thesaurus concept code identifier |
| NCI Concept name | NCI Thesaurus preferred name. As OSB currently does not have a reference to the full NCI Thesaurus, a direct reference to the preferred name is kept in addition to the NCI concept ID. |

:::

### Create Activity Subgroup

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Subgroups** tab

**Purpose.** An Activity Subgroup is the second grouping level under an Activity Group. It can be shown in the protocol SoA and as a sub-section in protocol section 8.

**When to use.** Add an Activity Subgroup when none of the existing subgroups fits the Activities to be added. Search the Activity Subgroups tab first.

**Prerequisites.** None. The subgroup must be approved (status Final) before it can be selected when an Activity is added.

#### Quick Guide

::: details Show Quick Guide

 1. Select **Library** → **Concepts** → **Activities** → **Activity Subgroups** tab, click the **'Add activity subgroup'** icon.

     [![Add activity subgroup icon on the Activity Subgroups tab](/images/user_guides/activity_concepts_12_add_subgroup_button.png)](/images/user_guides/activity_concepts_12_add_subgroup_button.png)

 1. Enter the **Subgroup name**. The **Sentence case name** is filled in from the Subgroup name; edit it if abbreviations need other casing.
 1. Enter the **Definition**, which is mandatory. Optionally enter the Abbreviation, NCI Concept ID and NCI Concept Name.
 1. Click **SAVE**.

     [![Add activity subgroup form](/images/user_guides/activity_concepts_13_add_subgroup_form.png)](/images/user_guides/activity_concepts_13_add_subgroup_form.png)

     *Add activity subgroup form: (A) Subgroup name, (B) Sentence case name, (C) Abbreviation, NCI Concept ID and NCI Concept Name, (D) Definition, (E) CANCEL and SAVE.*

 1. The table keeps its **Final** status filter after saving, so the new Draft Activity Subgroup is not listed. Select **Draft** or **All** in the status filter above the table.
 1. Approve the new Activity Subgroup by clicking the **Approve** icon or via the table row actions dots menu.

:::

#### Experienced

- **Clarifications.** The form does not link the Subgroup to an Activity Group. The Activity Group and Activity Subgroup are combined when the Activity is added, see [Create Activity](#create-activity).
- **Quality checks.** The Sentence case name can differ from the Subgroup name only in letter case.

#### Troubleshooting

| Symptom | Interpretation | Likely cause | Fix / next safest action |
|---|---|---|---|
| Saving is refused with a message that an Activity subgroup with that name already exists | Subgroup names must be unique | The subgroup is already in the library | Search the Activity Subgroups tab and use the existing subgroup |
| Saving is refused with a message that the lowercase versions of the name and the sentence case name must be equal | The Sentence case name differs from the Subgroup name by more than letter case | A word was changed in the Sentence case name | Correct the Sentence case name |
| The form cannot be saved | A mandatory field is empty | The **Subgroup name** or the **Definition** is not filled in | Complete the field marked as required |
| The new subgroup is not offered when an Activity is added | Only Final subgroups are offered | The subgroup is still in Draft | Approve the subgroup |

**Undo vs not undoable.** A saved subgroup is a Draft version until approved. Further changes to a Final subgroup need **New version** on the row actions menu.

#### Related topics

- [Create Activity Group](#create-activity-group)
- [Create Activity](#create-activity)

## Activities by Grouping

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activities by Grouping** tab

On the Activity by Groupings tab, activities can be browsed top-down by the grouping hierarchy. This page does not offer any searching, filtering or actions on managing activities or groupings.

::: details Activities by Groupings table

| Column  | Description         |
|---------|---------------------|
| Group/subgroup/activity | Nested hierarchy of sponsor name for the activity group, subgroup and activities. The same activity can exist multiple times if it is included in multiple groupings. |

:::

## Activity Instances

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Instances** tab

Activity Instances are the detailed definitions of an Activity, stating exactly what is measured or recorded (for example the test, the unit and the permitted results). Each belongs to one Activity and is categorised by an [Activity Instance Class](#activity-instance-classes) according to the nature of the observation it defines, for example a numeric measurement.

::: details More about Activity Instances

An Activity Instance is similar to the CDISC BC SDTM specialisation, but is defined semantically to an ADaM PARAM/PARAMCD specialisation.

An Activity Instance for an activity related to data collection results in a semantic logical observation — meaning a formally defined, meaningful data point — which can have different identifications depending on context and qualifiers.

The identification is for a specific semantic logical observation and includes reference to context and qualifier values (like fasting plasma glucose). Primary identification is for ADaM BDS PARAM/PARAMCD, identification in occurrence datasets or column name in ADSL, as well as identification in the SDTM dataset. The Activity Instance can also include reference to external dictionaries (like NCI Thesaurus) and sponsor identification (like topic code). This enables unique identification of source data, representation in SDTM by several qualifiers, and representation in ADaM BDS by PARAMCD value.

The Activity Instance always has a relationship to one Activity and can have a relationship to one or more Activity Instance Classes. It is the data collection specification of an activity, used to link the operational SoA with data collection instruments such as CRFs and external data specifications.

:::

> [!NOTE]
> Support for derived Activity Instances as derivation concepts is planned for a later OSB release.

::: details Activity Instances table

| Column  | Description         |
|---------|---------------------|
| Library | Reference to which library the activity instance belongs to. This is Sponsor for activity instances defined and approved as standard within OSB; it can be set to CDISC if imported from CDISC Library. |
| Activity group | Sponsor name for the high-level grouping of activities. The activity group name can be used to be displayed in protocol SoA, as sub-section in protocol section 8, and as grouping in appendix 2 for lab assessments. |
| Activity subgroup | Sponsor name for the second level grouping of activities. The activity subgroup name can also be used to be displayed in protocol SoA, as sub-section in protocol section 8, and as grouping in appendix 2 for lab assessments. |
| Activity name | Sponsor name for the activity in title case. This can be chosen to be displayed in protocol SoA, will be the name being referenced in protocol section 8 and appendixes. |
| Activity instance class | Name for the activity instance class. The activity instance class define the type of logical observation for an activity instance, and determine relevant activity item classes (i.e. variable types). |
| Activity instance | Sponsor name for the activity instance. |
| NCI Concept ID | NCI Thesaurus concept code identifier |
| NCI Concept name | NCI Thesaurus preferred name. As OSB currently does not have a reference to the full NCI Thesaurus, a direct reference to the preferred name is kept in addition to the NCI concept ID. |
| Research lab | Boolean flag that indicate if the analysis for this activity instance is performed by a dedicated research lab. |
| Molecular weight |  |
| Topic code | Internal unique identifier for the activity instance. It is made so it is readable and can be a longer text string (as opposite to the ADaM parameter). |
| ADaM parameter code | The related unique ADaM parameter code for the activity instance. The definition of an activity instance is made to be specific for an ADaM parameter code, thereby the ADaM parameter code is by definition also an unique identifier for the activity instance. The ADaM parameter code have a maximum length of 8 characters. |
| Required for activity | A Boolean flag that indicate if this activity is required to be included in the operational SoA if it's related parent activity is included in the detailed SoA. If so, the system will automatically add this to the operational SoA when the parent activity is added to the detailed SoA. |
| Default selected for activity | A Boolean flag that indicate this activity instance by default is selected to the operational SoA when the parent activity is added to the detailed SoA. But it is no mandatory and can be removed without giving error notifications. |
| Data sharing | A Boolean flag that indicate this activity instance not is sponsor specific or confidential and therefore generally can be shared with standards organisations (like CDISC), partners and publicly. |
| Legacy usage | A Boolean flag indicating this activity instance is defined to support data migrations for legacy study specifications and should as such not be used in new studies (even as the activity instance is available in final status). |

:::

### Create Activity Instance

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Instances** tab

**Purpose.** An Activity Instance defines exactly what is measured or recorded for an Activity. It is the data collection specification used by the operational SoA, Forms, external data specifications, SDTM and ADaM.

**When to use.** Add an Activity Instance for each distinct measurement or recording of an Activity, for example one per test and unit. The Activity Instance Class chosen in the second step of the wizard decides which attributes are asked for:

| Activity Instance Class | Use it when |
|---|---|
| **NumericFindings** | The result is a number with a unit. Test Name, Test Code, Unit dimension and Standardised unit are specified. |
| **CategoricFinding** | The result is one of a set of terms from a codelist. The codelist and the valid response terms are specified. |
| **TextualFindings** | The result is free text. Only the test code and test name are specified. |

> [!NOTE]
> Which Activity Instance Classes can be selected depends on what is enabled for the installation. Other Activity Instance Classes are still to be specified.

**Prerequisites.**

- The related Activity exists with status Final, is in the Sponsor library and has **Data collection** selected, see [Create Activity](#create-activity).
- The Activity group and Activity subgroup of the Activity have status Final.

#### Quick Guide

::: details Show Quick Guide

 1. Select **Library** → **Concepts** → **Activities** → **Activity Instances** tab, click the **'Add activity instance'** icon. The **Add activity instance** wizard opens with four steps: **Select activity**, **Required**, **PARAM/PARAMCD** and **Data specification**.

     [![Add activity instance icon on the Activity Instances tab](/images/user_guides/activity_concepts_02_add_activity_instance_button.png)](/images/user_guides/activity_concepts_02_add_activity_instance_button.png)

 1. **Select activity**: Search and select the Activity this Activity Instance is related to including the grouping. Once selected, the header info box shows the selected Activity and Activity grouping. Then click **CONTINUE**.

     [![Wizard step Select activity](/images/user_guides/activity_concepts_04_wizard_select_activity.png)](/images/user_guides/activity_concepts_04_wizard_select_activity.png)

     *Step Select activity: (A) Search, (B) row checkbox, (C) selected Activity and grouping, (D) CONTINUE.*

 1. **Required**: First select the **Activity instance class** (see the table in the Baseline above). For all classes the following shared attributes must be made:
     - **Data domain** (will map to CDISC SDTM dataset)
     - **Data category** and, optionally, **Data subcategory** (will map to content categories in CDISC SDTM datasets)

 1. Depending on what Activity Instance Class is selected, the following selections must also be made in this step:

     > [!NOTE]
     > Test Name and Test Code are a paired selection. An advanced search is available by clicking the search icon next to the drop-down controls.

     - For **NumericFindings** class:
         - **Test Name** and **Test Code** (will map to the finding test code and test name variables in CDISC SDTM datasets).
         - **Unit dimension** (grouping of a set of units where conversions can be made between these units)
         - **Standardised unit** for the numeric finding (this will control the unit for the standard value in the CDISC SDTM dataset)

     [![Wizard step Required for the NumericFindings class](/images/user_guides/activity_concepts_05_wizard_required.png)](/images/user_guides/activity_concepts_05_wizard_required.png)

     *Step Required for NumericFindings: (A) Activity instance class, (B) Data domain, (C) Data category, (D) Data subcategory (optional), (E) Test Name and Test Code, (F) Unit dimension, (G) Standardised unit, (H) CONTINUE.*

     - For **CategoricFinding** class:
         - Test code and test name (will map to the finding test code and test name variables in CDISC SDTM datasets).
         - Code list for categoric finding original result and either all terms in this code list or a selected subset of terms as the valid response terms for the categoric finding. An advanced search is also available by clicking the search icon next to the term value drop down control.

     [Add screen dump]: #

     - For **TextualFindings** class:
         - Test code and test name (will map to the finding test code and test name variables in CDISC SDTM datasets).

     [Add screen dump]: #

 1. **PARAM/PARAMCD**: Next is for the finding classes to specify optional potential Activity Item values that will drive the identification and name for the Activity Instance:
     - Depending on the selections made on the previous step the system will suggest default values for the Activity Instance name attributes (**Activity instance name** and **Sentence case name**), the **Topic code** and the **ADaM parameter code**.
     - If additional Activity Item Classes are added where their qualifier values are part of identifying the Activity Instance then those values will also be part of the system defaulted identifier values.
         - Click **ADD ACTIVITY ITEM CLASS**, select an Activity Item Class, and if applicable a qualifier term value.
     - The system defaulted values can be overridden by switching on the **Customize** toggle.
     - Enter the NCI Thesaurus preferred name and code ID (**NCI Code**). NCI values have to be looked up manually as OSB does not yet support dynamic search and reference to the NCI Thesaurus.
     - For the findings classes it is possible to flag if data from the Activity Instance will come from a research lab (**Data from a Research lab**).
     - Click **CONTINUE**.

     [![Wizard step PARAM/PARAMCD](/images/user_guides/activity_concepts_06_wizard_param_paramcd.png)](/images/user_guides/activity_concepts_06_wizard_param_paramcd.png)

     *Step PARAM/PARAMCD: (A) ADD ACTIVITY ITEM CLASS, (B) Customize, (C) generated name, topic code and ADaM parameter code, (D) NCI preferred name and NCI Code (optional), (E) Data from a Research lab, (F) CONTINUE.*

 1. **Data specification**: Last is to specify optional Activity Items that are not part of identifying the Activity Instance. These values are used to specify data that can be collected on a CRF or an external specification. Examples are methods, anatomical locations or evaluator information.
     - Click **ADD ACTIVITY ITEM CLASS**, select an Activity Item Class, and if applicable a qualifier term value.
     - Select **Required for activity**, **Data sharing** and **Default selected for activity** as relevant for the Activity Instance, see the [Activity Instances table](#activity-instances) above for the meaning of these flags.

     > [!NOTE]
     > If only one value is chosen within an Activity Item Class, it becomes the default. If several values are chosen, they become choices in the data collection instruments.

     [![Wizard step Data specification](/images/user_guides/activity_concepts_07_wizard_data_specification.png)](/images/user_guides/activity_concepts_07_wizard_data_specification.png)

     *Step Data specification: (A) Required for activity, Data sharing and Default selected for activity, (B) Activity Item Classes linked by default, (C) ADD ACTIVITY ITEM CLASS, (D) SAVE.*

 1. Click **SAVE**.

 1. After saving, the Activity Instance overview of the new Draft Activity Instance opens. The status filter and the row menu of the table are not available there. Approve the new Activity Instance with the **Approve** icon in the header of the **Activity Instance Attributes** section, and with the **Approve** icon in the header of the **Activity groupings** section if the groupings are shown as Draft. Alternatively, close the overview with the **X** icon to return to the Activity Instances tab, select **Draft** or **All** in the status filter and use **Approve attributes** or **Approve groupings** on the 3 action dots menu of the row.

:::

#### Experienced

- **Do this when.** An Activity Item Class is part of what identifies the Activity Instance (its qualifier value changes the meaning of the observation): add it on the **PARAM/PARAMCD** step, so it becomes part of the generated name, topic code and ADaM parameter code. An Activity Item Class that only describes how the data is collected (for example method, anatomical location or evaluator): add it on the **Data specification** step.
- **Do this when.** The generated names or codes do not fit the naming conventions of the library: switch on **Customize** on the **PARAM/PARAMCD** step and enter the values.
- **Quality checks.** Review the generated Activity instance name, Sentence case name, Topic code and ADaM parameter code before continuing from the **PARAM/PARAMCD** step. The Activity Instance Class and the Activity Item Classes that identify the Activity Instance cannot be edited after saving, see [Edit Activity Instance](#edit-activity-instance).

#### Troubleshooting

| Symptom | Interpretation | Likely cause | Fix / next safest action |
|---|---|---|---|
| The Activity is not in the table on the **Select activity** step | Only a subset of Activities is listed | The Activity is not Final, is not in the Sponsor library, or has **Data collection** cleared | Approve the Activity, or add a new version of it with **Data collection** selected, see [Create Activity](#create-activity) |
| Only NumericFindings can be selected as Activity instance class | The other classes are not enabled | Activity Instance Classes are enabled per installation | Use the enabled class, or contact the system administrator |
| Saving is refused with the message that an Activity Group or Activity Sub Group is currently not in Final status | The grouping of the selected Activity refers to a group or subgroup that is not approved | The group or subgroup is in Draft | Approve the group or subgroup, see [Create Activity Group](#create-activity-group) and [Create Activity Subgroup](#create-activity-subgroup), then save again |
| Clicking **CANCEL** in the wizard shows **Your changes will be lost** | The wizard asks for confirmation before closing | Entered values have not been saved | **CANCEL** returns to the wizard. **CONTINUE** discards the entries and closes the wizard |

**Undo vs not undoable.** Saving adds the Activity Instance as a Draft version. The Activity Instance Class and the identifying Activity Item Classes cannot be changed afterwards. If one of these is wrong, remove the Activity Instance with **Delete** or **Inactivate** on the 3 action dots menu (whichever is offered for its status) and add a new one. **Inactivate** applies to both the attributes and the groupings of the Activity Instance.

**Check before acting.**

- The Activity is Final, in the Sponsor library and has **Data collection** selected.
- The Activity Instance does not exist already: search the Activity Instances tab for the test and unit.

#### Related topics

- [Edit Activity Instance](#edit-activity-instance) and [Edit Groupings for an Activity Instance](#edit-groupings-for-an-activity-instance)
- [Activity Instance Classes](#activity-instance-classes) and [Activity Item Classes](#activity-item-classes)
- [Non-Standard Variables](#non-standard-variables)

### Edit Activity Instance

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Instances** tab

**Purpose.** Changes the attributes of an existing Activity Instance, for example its name, NCI reference, flags and Activity Items. The attributes and the groupings of an Activity Instance are versioned separately, so each has its own actions on the row menu.

**When to use.** Select the action that matches the change:

| Change | Action |
|---|---|
| Attributes of the Activity Instance | **New version (attributes)**, then **Edit attributes** and **Approve attributes**, as described below |
| Placement under Activity group and Activity subgroup | **New version (groupings)**, see [Edit Groupings for an Activity Instance](#edit-groupings-for-an-activity-instance) |
| Related Activity, Activity Instance Class or the Activity Item Classes that identify PARAM/PARAMCD | Cannot be edited. Inactivate the Activity Instance and add a new one for the correct Activity, see [Create Activity Instance](#create-activity-instance) |

**Prerequisites.**

- **Edit attributes** is offered only on a Draft version of the attributes. A Final Activity Instance first needs **New version (attributes)**.

#### Quick Guide

::: details Show Quick Guide

 1. Select **Library** → **Concepts** → **Activities** → **Activity Instances** tab, search and select the row to be edited, click the 3 action dots on the row, **New version (attributes)**, then select to display **Draft** rows, select **Edit attributes** on the 3 action dots menu.

     [![Row actions menu of an Activity Instance](/images/user_guides/activity_concepts_03_instance_row_menu.png)](/images/user_guides/activity_concepts_03_instance_row_menu.png)

     *Row actions menu of a Final Activity Instance with New version (attributes).*

     [![Row actions menu of a Draft Activity Instance](/images/user_guides/activity_concepts_16_draft_row_menu.png)](/images/user_guides/activity_concepts_16_draft_row_menu.png)

     *Row actions menu of a Draft Activity Instance with Edit attributes.*

 1. In the **Edit activity instance attributes** wizard, change the attributes. The wizard has three steps: **Required**, **PARAM/PARAMCD** and **Data specification**. Click **CONTINUE** to move between the steps.

     [![Edit activity instance attributes wizard, Required step](/images/user_guides/activity_concepts_17_edit_attributes.png)](/images/user_guides/activity_concepts_17_edit_attributes.png)

     *Required step: (A) Activity instance class, (B) Data domain, (C) Data category, (D) Data subcategory, (E) Activity Item Classes, (F) CONTINUE.*

     > [!NOTE]
     > The **Activity instance class** and the **Activity item class** selectors (for example Test Name and Test Code) are greyed out and cannot be changed.

 1. Enter a short change description.
 1. Click **SAVE**.
 1. After saving, the Activity Instance overview opens. Approve the changes with the **Approve** icon in the header of the **Activity Instance Attributes** section. Alternatively, close the overview with the **X** icon to return to the Activity Instances tab, select **Draft** or **All** in the status filter and select **Approve attributes** on the 3 action dots menu of the row.

:::

#### Troubleshooting

| Symptom | Interpretation | Likely cause | Fix / next safest action |
|---|---|---|---|
| **Edit attributes** is not on the 3 action dots menu | The action is offered only for Draft attributes | The row is Final or Retired, or the user has no write access to the library | Select **New version (attributes)** and display the **Draft** rows. If the action is still missing, contact the system administrator |
| The Activity Instance Class or an identifying Activity Item Class cannot be changed | These values are fixed after the Activity Instance is saved | By design | Inactivate the Activity Instance and add a new one |

**Undo vs not undoable.** Each save creates a Draft version with its change description, and approving makes it Final. **History (attributes)** on the 3 action dots menu shows the earlier versions.

#### Related topics

- [Create Activity Instance](#create-activity-instance)
- [Edit Groupings for an Activity Instance](#edit-groupings-for-an-activity-instance)

### Edit Groupings for an Activity Instance

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Instances** tab

**Purpose.** The groupings of an Activity Instance are the combinations of Activity group and Activity subgroup under which the related Activity is placed. Groupings are versioned separately from the attributes, so the actions on the row menu are dedicated to groupings: **New version (groupings)**, **Edit groupings**, **Approve groupings** and **History (groupings)**.

**When to use.** Add the Activity Instance to another grouping of the same Activity, or remove a grouping that no longer applies.

**Prerequisites.**

- **Edit groupings** is offered only on a **Draft** version of the groupings. A new version of the groupings leaves the attributes of the Activity Instance unchanged.
- The related Activity cannot be changed, and all selected rows must belong to the same Activity. If the Activity Instance is related to the wrong Activity, inactivate it and add a new Activity Instance, see [Create Activity Instance](#create-activity-instance).

#### Quick Guide

::: details Show Quick Guide

 1. Select **Library** → **Concepts** → **Activities** → **Activity Instances** tab, search and select the row to be edited, click the 3 action dots on the row and select **New version (groupings)**.
 1. Select **Draft** in the status filter, click the 3 action dots on the row and select **Edit groupings**. The **Edit activity instance groupings** wizard opens with two steps: **Select activity** and **Change description**.

     [![Row actions menu of an Activity Instance with Edit groupings](/images/user_guides/activity_concepts_18_edit_groupings_menu.png)](/images/user_guides/activity_concepts_18_edit_groupings_menu.png)

     *Row actions menu after New version (groupings), with Edit groupings.*

 1. **Select activity**: The table lists the groupings of the Activity that the Activity Instance is related to. Select the checkbox of each grouping that the Activity Instance is to belong to. The header info box shows the selected Activity and its groupings. Click the bin icon next to a grouping in the info box to remove it from the selection. Click **CONTINUE**.

     [![Edit activity instance groupings wizard, Select activity step](/images/user_guides/activity_concepts_19_edit_groupings_select.png)](/images/user_guides/activity_concepts_19_edit_groupings_select.png)

     *Select activity step: (A) selected Activity and its groupings, with the bin icon, (B) grouping selected for the Activity Instance, (C) CONTINUE.*

     > [!IMPORTANT]
     > The selection saved here replaces the current groupings of the Activity Instance. Make sure that every grouping to be kept is still selected before continuing.

 1. **Change description**: Enter a short description of the change to the groupings.

     [![Edit activity instance groupings wizard, Change description step](/images/user_guides/activity_concepts_20_edit_groupings_description.png)](/images/user_guides/activity_concepts_20_edit_groupings_description.png)

     *Change description step: (A) Change description, (B) SAVE. PREVIOUS returns to the Select activity step.*

 1. Click **SAVE**. The message **Activity Instance groupings updated** is shown.
 1. After saving, the wizard closes and the table is refreshed. The row is still listed because **Draft** is selected in the status filter. Approve the changes by selecting **Approve groupings** on the 3 action dots menu of the row.

:::

#### Experienced

- **Quality checks.** After approving, open **History (groupings)** on the 3 action dots menu to compare the new version of the groupings with the earlier ones.

#### Troubleshooting

| Symptom | Interpretation | Likely cause | Fix / next safest action |
|---|---|---|---|
| **Edit groupings** is not on the 3 action dots menu | The action is offered only for Draft groupings | The groupings are Final, or the user has no write access to the library | Select **New version (groupings)**, then display the **Draft** rows |
| The table on the **Select activity** step shows only the groupings of the Activity | The related Activity cannot be changed in this wizard | By design | To use a grouping that the Activity does not have, add the grouping to the Activity first, see [Create Activity](#create-activity) |
| A grouping that should have been kept is gone after saving | The saved selection replaced the previous groupings | The grouping was not selected on the **Select activity** step | If the groupings are still **Draft**, select **Edit groupings** on the 3 action dots menu (**New version (groupings)** is not offered on a Draft) and repeat the selection with the grouping included. If the groupings have already been approved, select **New version (groupings)**, then **Edit groupings**, and repeat the selection. **History (groupings)** shows the earlier version |

**Undo vs not undoable.** Each save creates a Draft version of the groupings with its change description, and the groupings stay in **Draft** until approved. There is no undo button; the way to restore a grouping depends on the status:

- **Draft groupings (not yet approved).** The row menu offers **Edit groupings**. **New version (groupings)** is not needed and not offered while the groupings are Draft. Select **Edit groupings** again and save the intended selection. Each save of a changed Draft automatically creates a new minor Draft version (for example 0.1 to 0.2), so the previous Draft version is not overwritten and remains available under **History (groupings)**.
- **Approved groupings (Final).** The approved version cannot be changed. **New version (groupings)** starts a new Draft version from the approved one. Select it, then **Edit groupings**, save the intended selection and approve it. The earlier version stays available under **History (groupings)**.

#### Related topics

- [Edit Activity Instance](#edit-activity-instance)
- [Create Activity](#create-activity), for the Activity groupings of an Activity

## Requested Activities

**Where to find it:** **Library** → **Concepts** → **Activities** → **Requested Activities** tab

The Requested Activities tab offers fast filtering between activities that are handled or archived. Standard free search, filtering, column displays, history, export as well as the action for handling an activity request are available.

::: details Requested Activities table

| Column  | Description         |
|---------|---------------------|
| Activity group | Sponsor name for the high-level grouping of activities. The activity group name can be used to be displayed in protocol SoA, as sub-section in protocol section 8, and as grouping in appendix 2 for lab assessments. |
| Activity subgroup | Sponsor name for the second level grouping of activities. The activity subgroup name can also be used to be displayed in protocol SoA, as sub-section in protocol section 8, and as grouping in appendix 2 for lab assessments. |
| Activity name | Sponsor name for the activity in title case. This can be chosen to be displayed in protocol SoA, will be the name being referenced in protocol section 8 and appendixes. |
| Sentence case name | Same name for the activity in lower case, but with correct casing in abbreviations if these are part of the name. This sentence case name is intended to be used in text generation for protocol section 8 and other sections when in-text references are made to activities so these occur in correct case. |
| Definition | The sponsor definition of the activity, this can be made with input from external definitions. |
| Rationale for activity request | The rationale for the new activity as given by the requester. |
| Study ID | The study ID from where the request was made. |

:::

## Activity Instance Classes

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Instance Classes** tab

Activity Instance Classes define the type of logical observation for an Activity Instance and determine which Activity Item Classes are relevant. A numeric finding, for example, expects collection unit, collection value, standard unit and value in standard unit. The classes form a hierarchy in which specific classes inherit from general ones (Subject Observation → Finding → Numeric Findings), as shown in the class model below.

On the Activity Instance Classes tab, the nested definition of Activity Instance Classes can be browsed by their hierarchy: expand a row with the arrow to show its child classes. The tab offers export and history, and the existing classes can be edited and versioned from the 3 action dots on each row, see [Edit Activity Instance Class](#edit-activity-instance-class). Adding a new Activity Instance Class is not offered in the user interface and needs to be performed via the API.

[![Activity Instance Class model](/images/user_guides/neodash_activity_class_model.png)](/images/user_guides/neodash_activity_class_model.png)

*Activity Instance Class model. Each arrow points from a class to its parent class.*

::: details Activity Instance Classes table

| Column  | Description         |
|---------|---------------------|
| Name | Sponsor name for the activity instance class. |
| Definition | The sponsor definition of the activity instance class. |
| Domain specific | Yes/No indicator of whether the activity instance class is specific to an individual data domain (Yes) or applies across domains (No). |
| Library | Reference to which library the activity instance class belongs to. This can at the moment only be the sponsor library as the class model is OSB specific. |

:::

### Edit Activity Instance Class

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Instance Classes** tab

**Purpose.** Changes the name, parent class, definition or domain-specific flag of an existing Activity Instance Class. The classes are versioned like other library objects, so a change is made on a Draft version and then approved.

**When to use.** The name or definition of a class needs correcting, or a class is to be moved under another parent class.

**Prerequisites.**

- **Edit** is offered only on a **Draft** version. A Final class first needs **New version** on the 3 action dots menu.
- The classes are shared reference data that every Activity Instance of the class depends on. Agree changes with the owner of the class model before saving. A **Parent class** change takes effect in the shared hierarchy immediately on **SAVE**, even while the class is Draft, and is not preserved per version. Record the previous parent before changing it; restoring it requires explicitly selecting that parent again, not retrieving it from **History**.

#### Quick Guide

::: details Show Quick Guide

 1. Select **Library** → **Concepts** → **Activities** → **Activity Instance Classes** tab. Expand a parent row with the arrow to reach its child classes. Click the 3 action dots on the row of the class to be changed and select **New version**.

     [![Row actions menu of a Final Activity Instance Class](/images/user_guides/activity_concepts_21_instance_class_menu.png)](/images/user_guides/activity_concepts_21_instance_class_menu.png)

     *Row actions menu of a Final Activity Instance Class: (A) New version. Inactivate and History are the other actions.*

 1. Click the 3 action dots on the row, which is now a Draft, and select **Edit**.

     [![Row actions menu of a Draft Activity Instance Class](/images/user_guides/activity_concepts_22_instance_class_draft_menu.png)](/images/user_guides/activity_concepts_22_instance_class_draft_menu.png)

     *Row actions menu of a Draft Activity Instance Class: (A) Edit. Approve and History are the other actions.*

 1. In the **Edit activity instance class** form, change the fields as needed.

     [![Edit activity instance class form](/images/user_guides/activity_concepts_23_instance_class_edit_form.png)](/images/user_guides/activity_concepts_23_instance_class_edit_form.png)

     *Edit activity instance class form: (A) Name, (B) Parent class, (C) Definition, (D) Domain specific, (E) Change description, (F) SAVE.*

     | Field | Description |
     |---|---|
     | **Name** | Name of the Activity Instance Class. |
     | **Parent class** | The class that this class inherits from. Leave empty for a root-level class such as General Observation. |
     | **Definition** | Free-text definition of the class. |
     | **Domain specific** | Select if the class applies to one data domain only. Leave cleared if it applies across domains. |
     | **Change description** | Short description of the change, stored with the version. |

 1. Click **SAVE**. The message **Activity instance class updated** is shown.
 1. Approve the change by selecting **Approve** on the 3 action dots menu of the row.

:::

#### Troubleshooting

| Symptom | Interpretation | Likely cause | Fix / next safest action |
|---|---|---|---|
| **Edit** is not on the 3 action dots menu | The action is offered only for Draft versions | The class is Final or Retired, or the user has no write access to the library | Select **New version** on a Final class. A Retired class first needs **Reactivate**. If the actions are still missing, contact the system administrator |
| The class to be changed is not visible in the table | Child classes are shown under their parent | The parent row is collapsed | Expand the parent row with the arrow |
| The form cannot be saved | A mandatory field is empty | **Name** or **Change description** is not filled in | Complete the field marked as required |
| A new class cannot be added | Adding classes is not offered in the user interface | By design | Add the class via the API |

**Undo vs not undoable.** Each save creates a Draft version with its change description, and approving makes it Final. **History** on the 3 action dots menu shows the earlier versions. There is no undo; a new version with the previous values restores them.

#### Related topics

- [Activity Instance Classes](#activity-instance-classes)
- [Activity Item Classes](#activity-item-classes)
- [Create Activity Instance](#create-activity-instance), where the Activity Instance Class is selected

## Activity Item Classes

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Item Classes** tab

Activity Item Classes are the kinds of information that can be specified for an Activity Instance, such as the test, the unit or the result value. Which ones apply depends on the [Activity Instance Class](#activity-instance-classes). Each has a role (what the information is used for) and a data type (what kind of value it holds), and is linked to the matching variables in data standards such as SDTM and ADaM, without being tied to a single standard. The value chosen for a specific Activity Instance is stored as an Activity Item.

The Activity Item Classes tab offers browsing, free search, filtering, column display, history and export. The existing classes can be edited and versioned from the 3 action dots on each row, see [Edit Activity Item Class](#edit-activity-item-class). Adding a new Activity Item Class is not offered in the user interface and needs to be performed via the API.

::: details Activity Item Classes table

| Column  | Description         |
|---------|---------------------|
| Name | Sponsor name for the activity item class. |
| Definition | The sponsor definition of the activity item class. |
| NCI Code | NCI code ID for the activity item class. |
| Library | Reference to which library the activity item class belongs to. This can at the moment only be the sponsor library as the class model is OSB specific. |

:::

### Edit Activity Item Class

**Where to find it:** **Library** → **Concepts** → **Activities** → **Activity Item Classes** tab

**Purpose.** Changes the name, display name, order, role, data type, NCI code or definition of an existing Activity Item Class. As for the Activity Instance Classes, a change is made on a Draft version and then approved.

**When to use.** The name, display name or definition of a class needs correcting, or its role, data type or NCI code is to be changed.

**Prerequisites.**

- **Edit** is offered only on a **Draft** version. A Final class first needs **New version** on the 3 action dots menu.
- The classes are shared reference data used by every Activity Instance Class that lists them. Agree a change with the owner of the class model before approving it.

#### Quick Guide

::: details Show Quick Guide

 1. Select **Library** → **Concepts** → **Activities** → **Activity Item Classes** tab, search for the class to be changed, click the 3 action dots on the row and select **New version**.
 1. Click the 3 action dots on the row, which is now a Draft, and select **Edit**.

     [![Row actions menu of a Draft Activity Item Class](/images/user_guides/activity_concepts_24_item_class_draft_menu.png)](/images/user_guides/activity_concepts_24_item_class_draft_menu.png)

     *Row actions menu of a Draft Activity Item Class: (A) Edit. Approve and History are the other actions.*

 1. In the **Edit activity item class** form, change the fields as needed.

     [![Edit activity item class form](/images/user_guides/activity_concepts_25_item_class_edit_form.png)](/images/user_guides/activity_concepts_25_item_class_edit_form.png)

     *Edit activity item class form: (A) Name, (B) Display name, (C) Order, (D) Role, (E) Data type, (F) NCI Code, (G) Definition, (H) Change description, (I) SAVE.*

     | Field | Description |
     |---|---|
     | **Name** | Name of the Activity Item Class. |
     | **Display name** | Display name of the class. |
     | **Order** | Display order of the class. |
     | **Role** | Variable role of the class, for example Result Qualifier. |
     | **Data type** | Kind of value that the class holds, for example CTterm. |
     | **NCI Code** | NCI concept ID associated with the class. |
     | **Definition** | Free-text definition of the class. |
     | **Change description** | Short description of the change, stored with the version. |

 1. Click **SAVE**. The message **Activity item class updated** is shown.
 1. Approve the change by selecting **Approve** on the 3 action dots menu of the row.

:::

#### Troubleshooting

| Symptom | Interpretation | Likely cause | Fix / next safest action |
|---|---|---|---|
| **Edit** is not on the 3 action dots menu | The action is offered only for Draft versions | The class is Final or Retired, or the user has no write access to the library | Select **New version** on a Final class. A Retired class first needs **Reactivate**. If the actions are still missing, contact the system administrator |
| The form cannot be saved | A mandatory field is empty | **Name**, **Role**, **Data type** or **Change description** is not filled in | Complete the field marked as required |
| A new class cannot be added | Adding classes is not offered in the user interface | By design | Add the class via the API |

**Undo vs not undoable.** Each save creates a Draft version with its change description, and approving makes it Final. **History** on the 3 action dots menu shows the earlier versions. There is no undo; a new version with the previous values restores them.

#### Related topics

- [Activity Item Classes](#activity-item-classes)
- [Edit Activity Instance Class](#edit-activity-instance-class)
- [Create Activity Instance](#create-activity-instance), where the Activity Item Classes are selected

## Non-Standard Variables

**Where to find it:** **Library** → **Concepts** → **Activities** → **Non-Standard Variables** tab

Non-Standard Variables (NSVs) extend SDTM datasets with variables for information not covered by standard variables. In OSB an NSV is a special type of [Activity Item Class](#activity-item-classes), managed on this tab, and is therefore part of the activity concepts model.

::: details Non-Standard Variables table

| Column  | Description         |
|---------|---------------------|
| Library | Reference to which library the activity item class belongs to. This can at the moment only be the sponsor library as NSVs are not yet part of the CDISC Library and the model is OSB specific (so this library column is hidden in the UI). OSB supports import of the NSVs defined by CDISC as part of TA guides; the Excel file shared by CDISC must first be converted to CSV, see [Import Non-Standard Variables](#import-non-standard-variables). A Boolean flag can be used to indicate if a NSV definition is made by CDISC. |
| NSV code | The NSV code attribute is an alias for the SDTM QNAM variable in -SUPP datasets, a 8 char upper case without blanks and cannot start with a number. |
| NSV label | The NSV label attribute is an alias for the SDTM QLABEL variable, cannot be longer than 40 chars. |
| Name | Sponsor name for the NSV that are used when the NSV is referenced from documents like CRF, can be longer than 40 chars. |
| NCI code | NCI code ID for the NSV variable. |
| NCI concept name | NCI concept name related to the NCI code ID. |
| Multiple | Boolean flag indicating if multiple occurrences can be made for the NSV for one related observation. |
| CDISC defined | Boolean flag to indicate if this NSV is defined by CDISC, e.g. in a CDISC TA guide. |
| Semantic data type | The semantic data type. In OSB multiple representations of data types are supported, each linked in a hierarchy. |
| NSV XML data type | The ODM XML data type applicable for an NSV in a CDISC define.xml file. |
| Length | Max response length for a text based NSV. |
| Codelist codes | If NSV responses are from a codelist, then the submission value of the codelist. |
| Origin type | The default origin type for the NSV. |
| Origin source | The default origin source for the NSV. |
| Algorithm | Specification of algorithm if the NSV is based on a derivation algorithm. |
| Definition | Definition of the NSV. |
| Derivation rule | Specification of derivation rule if the NSV is based on a rule. |

:::

### Import Non-Standard Variables

**Purpose.** Loads many NSVs at once instead of adding them one by one.

**When to use.** Use the import to load the NSVs defined by CDISC, to move NSVs between OSB installations, or to migrate NSVs from a legacy sponsor MDR. The import is run with a script, not from the user interface, so there is no Quick Guide on this page.

The import reads **CSV files only**. Excel workbooks and JSON files are not read directly and cause the import to fail or skip the file. Three file formats are recognised, and the format is detected per file from the CSV header:

| Source | File requirements | How to obtain the file |
|---|---|---|
| NSVs defined by CDISC | Comma-delimited CSV with a `variable_name` column | CDISC shares the NSV registry as an Excel file on [its website](https://www.cdisc.org/standards/terminology/non-standard-variables). Convert it to CSV with the converter script, see below |
| OSB export | Comma-delimited CSV with the header `non_standard_variable.code` | Export the table on the **Non-Standard Variables** tab as **CSV**. The **JSON** and **Excel** export options cannot be imported |
| Legacy sponsor MDR | Pipe-delimited file (columns separated by the pipe character) with the columns `cd_list_id` and `cd_val` | Export from the legacy MDR in this layout |

**Convert the CDISC Excel file.** The converter needs a spreadsheet reader that is not installed with the `import_sponsor_data` project: `xlrd` for legacy `.xls` files, `openpyxl` for `.xlsx` files. Run from the `import_sponsor_data` folder of the OSB repository, adding the reader that matches the file format to the command:

```sh
# legacy .xls file
uv run --with "xlrd<2.1" python cdisc_nsv_excel_converter.py path/to/cdisc_nsv.xls

# .xlsx file
uv run --with openpyxl python cdisc_nsv_excel_converter.py path/to/cdisc_nsv.xlsx
```

Without the reader, the script stops with an error before the CSV is written. A file saved as `.xlsx` from Excel or LibreOffice can be used instead of installing `xlrd`.

The script reads the **Approved NSVs** sheet and writes `datafiles/sponsor_library/nonstandard_variables/cdisc_nsv.csv`. An optional second argument sets a different output path.

**Run the import.** Place the CSV files in the NSV directory and run the import as described in `import_sponsor_data/README.md` (step *non-standard variables*). The directory, library, default lengths and automatic approval are set with the `MDR_MIGRATION_NONSTANDARD_VARIABLES_*` environment variables.

> [!NOTE]
> From an OSB export, the `status`, `version`, `start_date` and `uid` columns are ignored. Imported NSVs receive new UIDs and are always added as sponsor-defined, so the **CDISC defined** flag is not carried over. Whether they are approved depends on the automatic approval setting.
>
> The codelist links are not carried over either. An NSV with the semantic data type 'CT Term' is imported without its allowed-response codelist. After the import, restore the link for each such NSV: on the **Non-Standard Variables** tab select **Edit** on the 3 action dots menu (on a Final NSV, select **New version** first), select the codelist code, save and approve the NSV, see [Create Non-Standard Variables](#create-non-standard-variables).

For the importer itself, see `import_sponsor_data/importers/run_import_nonstandard_variables.py` in the OSB repository.

#### Related topics

- [Create Non-Standard Variables](#create-non-standard-variables)

### Create Non-Standard Variables

**Where to find it:** **Library** → **Concepts** → **Activities** → **Non-Standard Variables** tab

**Purpose.** An NSV extends SDTM datasets with a variable for information that standard variables do not cover.

**When to use.** Add an NSV when a variable is needed that is not part of the standard SDTM variables and not already on the Non-Standard Variables tab. Search the tab first.

**Prerequisites.**

- An NSV is linked to an Activity Instance Class that defines its scope. By default the general SubjectObservation class is selected, which enables the NSV to be applied for all classes.
- An NSV whose responses come from a codelist needs the semantic data type 'CT Term', and the codelist must exist in the controlled terminology.

#### Quick Guide

::: details Show Quick Guide

 1. Select **Library** → **Concepts** → **Activities** → **Non-Standard Variables** tab, click the **'Add Non-Standard Variable'** icon.

     [![Non-Standard Variables tab](/images/user_guides/activity_concepts_08_nsv_tab.png)](/images/user_guides/activity_concepts_08_nsv_tab.png)

     *Non-Standard Variables tab: (A) status filter, (B) Add Non-Standard Variable.*

 1. Select the Activity Instance Class that defines the scope of the NSV.

 1. Define all attribute values for the NSV
    - The selection of data type is a combined selection of the semantic data type including displaying the related Define.xml data type (like the semantic type 'Code' will be 'text' in define.xml data type).
    - Only if the semantic data type 'CT Term' is selected can a value for codelist code be selected.
    - If data type is 'CT Term' then an advanced codelist search is enabled by clicking the search icon next to codelist code.

     [![Add Non-Standard Variable form](/images/user_guides/activity_concepts_09_nsv_add_form.png)](/images/user_guides/activity_concepts_09_nsv_add_form.png)

     *Add Non-Standard Variable form: (A) Activity Instance Class, (B) Allow for multiple?, (C) NSV defined by CDISC, (D) NSV code, NSV label and Name, (E) Role, (F) Data Type and Length, (G) Codelist code, (H) Add algorithm, (I) Default origin type and Default origin source, (J) Definition and Derivation rule, (K) NCI Code and NCI Concept Name, (L) CANCEL and SAVE. The example is the CDISC-approved NSV NCF (Never Current Former Usage) from the CDISC Approved Non-Standard Variable Registry.*

 1. Click **SAVE**.

:::

#### Experienced

- **Do this when.** The NSV can occur more than once for one related observation: select **Allow for multiple?**. The NSV code is then limited to 7 characters instead of 8.
- **Quality checks.** The field limits are: NSV code 8 characters (7 with **Allow for multiple?**), NSV label 40 characters, Length 1 to 200, Definition and Derivation rule 200 characters each. The attributes are described in the [Non-Standard Variables table](#non-standard-variables) above.
- **Clarifications.** Approval and editing of NSVs follow the general workflow as for any versioned library elements in OSB.

#### Troubleshooting

| Symptom | Interpretation | Likely cause | Fix / next safest action |
|---|---|---|---|
| **SAVE** cannot be completed and a field is marked | A mandatory field is empty or a limit is exceeded | The NSV code, NSV label, Length, Definition or Derivation rule is outside the limits above | Correct the marked field |
| The NSV code is cut off at 7 characters | **Allow for multiple?** is selected | The code limit is 7 characters when multiple occurrences are allowed | Shorten the code, or clear **Allow for multiple?** if only one occurrence is possible |
| The codelist code cannot be selected | The codelist is available only for the semantic data type 'CT Term' | Another semantic data type is selected | Select 'CT Term' as the semantic data type |

**Undo vs not undoable.** A saved NSV follows the general versioning workflow: it is a Draft version until approved, and changes to a Final version need a new version, see [Versioning of each library element](../userguides_introduction.md#versioning-of-each-library-element).

#### Related topics

- [Import Non-Standard Variables](#import-non-standard-variables)
- [Activity Item Classes](#activity-item-classes) and [Activity Instance Classes](#activity-instance-classes)
