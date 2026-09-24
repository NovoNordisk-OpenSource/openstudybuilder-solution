# Activity Concepts

## Introduction

An ***Activity*** is by CDISC defined as an action, undertaking, or event, which is anticipated to be performed or observed, or was performed or observed, according to the study protocol during the execution of the study.

CDISC defines a ***Biomedical Concept*** as a unit of biomedical knowledge created from a unique combination of characteristics that include implementation details like variables and terminologies, used as building blocks for standardized, hierarchically structured clinical research information.

In OSB we support biomedical concepts of different types, and we see the concepts as definitions in more complex structures consisting of a set of related elements as opposed to controlled terminologies that can be represented as simpler term definitions in code lists. The term biomedical concepts has been difficult to grasp as it can cover many different things. In OSB we have therefore decided to simply name them **Concepts** as a broad term, and you can find the management of these under the menu **Library** > **Concepts**. The most important type of concept in OSB is concepts detailing activities, therefore simply named as **Activity Concepts**.

An Activity Concept in OpenStudyBuilder is made to support both the protocol specification (electronically) as well as the down-stream data flow (Forms, SDTM). An activity can be a clinical data recording (like measurement of body weight), but it can also be an activity performed during the study that is not leading to collection of data (like administration of study drug).

The OpenStudyBuilder activity concepts model consists of the following main elements each represented in tabs under the menu **Library** > **Concepts** > **Activities**:

- **Activities** are, as described in the introduction, actions, undertakings, or events that are anticipated to be performed or observed, or were performed or observed, according to the study protocol during the execution of the study. An activity related to data collection results in a semantic logical observation — meaning a formally defined, meaningful data point — which can have different identifications depending on context and qualifiers. An activity not related to data collection refers to a semantically specific activity, i.e. an activity with a precise definition but without resulting data (e.g. administration of study drug). Activities are represented at the most detailed level as needed in the protocol SoA, and are referred to in protocol section 8 and protocol appendixes.

- **Activity Groups** is high-level grouping of activities. The Activity Group can be what you decide to show in the protocol SoA. The Activity Group can be similar to CRF form names, but not necessarily. It is basically the clinical term relevant to show in the protocol both in overview section one as well as sub headings in section 8.

- **Activity Subgroups** is a second grouping level of activities similar to the Activity Groups.

- **Activity Instances** are similar to the CDISC BC SDTM specialisation, but defined semantically to an ADaM PARAM/PARAMCD specialisation.
The identification is for a specific semantic logical observation, this includes reference to context and qualifier values (like fasting plasma glucose). Primary identification is for ADaM BDS PARAM/PARAMCD, identification in occurrence datasets or column name in ADSL as well as identification in SDTM dataset. The Activity Instance can also include reference to external dictionaries (like NCI Thesaurus) and sponsor identification (like topic code). This will enable unique identification of source data, representation in SDTM by several qualifiers, and representation in ADaM BDS by PARAMCD value. The Activity Instance will always have a relationship to one Activity. The Activity Instance can have relationship to one or more Activity Instance Classes. The Activity Instance is the data collection specification of an activity to be used to link the operational SoA with data collection instruments such as CRFs and external data specifications.

> Note, coming in OSB later is support for derived Activity Instances as derivation concepts.

- **Activity Instance Classes** define the type of logical observation for an Activity Instance, and determine which Activity Item Classes (i.e. variable types) are relevant. For example, a numeric finding expects variables such as collection unit, collection value, standard unit, and value in standard unit — these are common characteristics of logical observations measuring numeric assessments. The Activity Instance Class has a recursive self-relationship describing the hierarchical relationship from general classes to more specific ones, where properties from the general ones are inherited by the sub classes (e.g. Subject Observation -> Finding -> Numeric Finding). The Activity Instance Class also has a relationship to zero or more Activity Item Classes.

- **Activity Item Classes** are the semantically defined generic types of variables related to a specific Activity Instance Class. Each Activity Item Class is related to a Semantic Item Role and a Semantic Item Data Type. Most Activity Item Classes will be related to an Activity Instance via an Activity Item. The Activity Item Class holds the relationship to Variable Class representations in various Data Models and Implementation Guides, connecting the semantic definition of a variable to its various representations in connected data models. The Activity Item Classes are typically defined based on general SDTM and ADaM model understanding, but are independent of any specific data models.

> NOTE, Each of the activity concepts main elements are individually versioned library objects in the OpenStudyBuilder repository solution. You can read more on the different versioning approaches in the user guide introduction section and other sections.

The following sections describe each of the tabs where you manage and browse the main elements of the activity concepts model. Note, within each section you have an expandable section with attribute details.

Each row in the display tables for activity concepts has hyper links into a detailed overview page for relevant column values. So e.g. a specific activity name will have a hyper link that opens a detailed overview of that specific activity, with relevant actions, different display views, and hyper links to related elements. 

## Activities

On the Activities tab you have fast filtering between activities in status Final, Retired, Draft or All. You have standard free search, filtering, column displays, history, export as well as add, edit and delete actions.

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
| NCI Concept name | NCI Thesaurus preferred name. As OSB currently does not have reference to the full NCI Thesaurus then we beside the NCI concept ID also keep a direct reference to the NCI Thesaurus preferred name. |
| Abbreviation | A sponsor defined abbreviation for the activity. |
| Data collection | Boolean flag to indicate if this activity relates to data collection. If not, the activity refers to reminders and procedures without data collection. |
| Legacy usage | Boolean flag to indicate if this activity is created for legacy data migration usage, and should not be used for new study specifications. |

:::


## Activity Groups

On the Activity Groups tab you have fast filtering between Activity Groups in status Final, Retired, Draft or All. You have standard free search, filtering, column displays, history, export as well as add, edit and delete actions.

::: details Activity Groups table

| Column  | Description         |
|---------|---------------------|
| Activity group | Sponsor name for the high-level grouping of activities. The activity group name can be used to be displayed in protocol SoA, as sub-section in protocol section 8, and as grouping in appendix 2 for lab assessments. |
| Sentence case name | Same name for the activity group in lower case, but with correct casing in abbreviations if these are part of the name. This sentence case name is intended to be used in text generation for protocol section 8 and other sections when in-text references are made to activity groups so these occur in correct case. |
| Abbreviation | A sponsor defined abbreviation for the activity. |
| Definition | The sponsor definition of the activity group, this can be made with input from external definitions. |
| NCI Concept ID | NCI Thesaurus concept code identifier |
| NCI Concept name | NCI Thesaurus preferred name. As OSB currently does not have reference to the full NCI Thesaurus then we beside the NCI concept ID also keep a direct reference to the NCI Thesaurus preferred name. |

:::


## Activity Subgroups

On the Activity Subgroups tab you have fast filtering between Activity Subgroups in status Final, Retired, Draft or All. You have standard free search, filtering, column displays, history, export as well as add, edit and delete actions.

::: details Activity Subgroups table

| Column  | Description         |
|---------|---------------------|
| Activity subgroup | Sponsor name for the second level grouping of activities. The activity subgroup name can also be used to be displayed in protocol SoA, as sub-section in protocol section 8, and as grouping in appendix 2 for lab assessments. |
| Sentence case name | Same name for the activity subgroup in lower case, but with correct casing in abbreviations if these are part of the name. This sentence case name is intended to be used in text generation for protocol section 8 and other sections when in-text references are made to activity subgroups so these occur in correct case. |
| Abbreviation | A sponsor defined abbreviation for the activity. |
| Definition | The sponsor definition of the activity subgroup, this can be made with input from external definitions. |
| NCI Concept ID | NCI Thesaurus concept code identifier |
| NCI Concept name | NCI Thesaurus preferred name. As OSB currently does not have reference to the full NCI Thesaurus then we beside the NCI concept ID also keep a direct reference to the NCI Thesaurus preferred name. |

:::


## Activities by Grouping

On the Activity by Groupings tab you can browse activities top-down by the grouping hierarchy. This page does not offer any searching, filtering or actions on managing activities or groupings.

::: details Activities by Groupings table

| Column  | Description         |
|---------|---------------------|
| Group/subgroup/activity | Nested hierarchy of sponsor name for the activity group, subgroup and activities. Note the same activity can exist multiple times if it is included in multiple groupings. |

:::


## Activity Instances

On the Activity Instances tab you have fast filtering between Activity Instances in status Final, Retired, Draft or All. You have standard free search, filtering, column displays, history, export as well as add, edit and delete actions.

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
| NCI Concept name | NCI Thesaurus preferred name. As OSB currently does not have reference to the full NCI Thesaurus then we beside the NCI concept ID also keep a direct reference to the NCI Thesaurus preferred name. |
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

 1. Select **Library** > **Concepts** > **Activities** > **Activity Instances** tab, click the **'Add activity instance'** icon.

     [Add screen dump]: #

 1. Search and select the Activity this Activity Instance is related to including the grouping. Once selected the header info box will show the selected Activity and Activity grouping. Then click Continue.

 1. First select the Activity Instance Class (see values and related definitions in following step). For all classes the following shared attributes must be made:
     - Related data domain (will map to CDISC SDTM dataset)
     - Data category and subcategory (will map to content categories in CDISC SDTM datasets)

    [Add screen dump]: #

 1. Depending on what Activity Instance Class is selected the following selections must be made:
     - For **NumericFindings** class: 
         - Test code and test name (will map to the finding test code and test name variables in CDISC SDTM datasets). Note, this selection is a paired selection, and you have the option to use an advanced search by clicking the search icon next to the drop down controls.
         - Unit dimension (grouping of a set of units where conversions can be made between these units)
         - Standard unit for the numeric finding (this will control the unit for the standard value in the CDISC SDTM dataset)

     [Add screen dump]: #

     - For **CategoricFinding** class:
         - Test code and test name (will map to the finding test code and test name variables in CDISC SDTM datasets). Note, this selection is a paired selection, and you have the option to use an advanced search by clicking the search icon next to the drop down controls.
         -  Code list for categoric finding original result and either all terms in this code list or a selected subset of terms as the valid response terms for the categoric finding. Note here you also have the option to use an advanced search by clicking the search icon next to the term value drop down control.

     [Add screen dump]: #

     - For **TextualFindings** class:
         - Test code and test name (will map to the finding test code and test name variables in CDISC SDTM datasets). Note, this selection is a paired selection, and you have the option to use an advanced search by clicking the search icon next to the drop down controls.
         
     [Add screen dump]: #

     > Note, Other Activity Instance Classes are still to be specified.

 1. Next is for the finding classes to specify optional potential Activity Item values that will drive the identification and name for the Activity Instance:
     - Depending on the selections made on the previous step the system will suggest default values for Activity Instance name attributes, the ADaM PARAM/PARAMCD values, and the sponsor topic code identifier.
     - If additional Activity Item Classes are added where their qualifier values are part of identifying the Activity Instance then those values will also be part of the system defaulted identifier values.
         - Click the '+ Activity Item Class' control, select an Activity Item Class, and if applicable a qualifier term value. 
     - You have the option to override the system defaulted values by clicking the 'Customize' control.
     - Enter the NCI Thesaurus preferred name and code ID. NCI values have to be looked up manually as OSB does not yet support dynamic search and reference to the NCI Thesaurus.
     - For the findings classes it is possible to flag if data from the Activity Instance will come from a research lab.

     [Add screen dump]: #

 1. Last is to specify optional Activity Items that are not part of identifying the Activity Instance. These values are used to specify data that can be collected on a CRF or an external specification. Examples are methods, anatomical locations or evaluator information.
     - Click the '+ Activity Item Class' control, select an Activity Item Class, and if applicable a qualifier term value. 

 1. Click **SAVE**.

 1. Approve the new Activity Instance by clicking the **Approve** icon or via the table row 3 actions dots menu.


### Edit Activity Instance

 1. Select **Library** > **Concepts** > **Activities** > **Activity Instances** tab, search and select the row to be edited, click the 3 action dots on the row, **New version (attributes)**, then select to display **Draft** rows, select **Edit attributes** on the 3 action dots menu.

     [Add screen dump]: #

 > Note, you cannot edit the related activity for an Activity Instance. If this is needed you need to retire the Activity Instance and then create a new one for the correct activity.
 > If you need to edit the groupings, then this is done by a dedicated versioning and edit action on the row menu.

 1. Edit the Activity Instance attributes.

 > Note, the Activity Instance Class, data domain and Activity Item Classes related to the identification of PARAM/PARAMCD cannot be edited.

 1. Enter a short change description.

 1. Click **SAVE**.

 1. Approve the changes by clicking the **Approve** icon or via the table row 3 actions dots menu.


### Edit Groupings for an Activity Instance

     [TO BE WRITTEN]: #


## Requested Activities

On the Requested Activities tab you have fast filtering between activities that are handled or archived. You have standard free search, filtering, column displays, history, export as well as action for handling an activity request.

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

On the Activity Instance Classes tab you can browse the nested definition of Activity Instance Classes by their hierarchy. This page only offers export and history. Management of Activity Instance Classes needs to be performed via the API directly.

::: details Activity Instance Classes table

| Column  | Description         |
|---------|---------------------|
| Name | Sponsor name for the activity instance class. |
| Definition | The sponsor definition of the activity instance class. |
| Domain specific |  |
| Library | Reference to which library the activity instance class belongs to. This can at the moment only be the sponsor library as the class model is OSB specific. |  |  |

:::


## Activity Item Classes

On the Activity Item Classes tab you can browse, free search, filtering, column display, history, and export. Management of Activity Item Classes needs to be performed via the API directly.

::: details Activity Item Classes table

| Column  | Description         |
|---------|---------------------|
| Name | Sponsor name for the activity item class. |
| Definition | The sponsor definition of the activity item class. |
| NCI Code |  |
| Library | Reference to which library the activity item class belongs to. This can at the moment only be the sponsor library as the class model is OSB specific. |  |  |

:::
