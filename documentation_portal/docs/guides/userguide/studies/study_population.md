# Study Population

**Where to find it:** Studies → Define Study → Study Population.

## Purpose

This section is used to document population information as part of the study definition.

## Concept & definitions

The Study Population page has two tabs:

- **General Population Attributes:** describes the overall population planned for the study, including its clinical context, planned age range, sex, and relevant indicators. These study-level attributes are reported in the SDTM Trial Summary (TS) domain.
- **Study Design Population:** defines study-specific population groups and links the inclusion and exclusion criteria that apply to each group. Use this tab when different groups need different criteria.

## General Population Attributes

Use this tab to record the overall planned study population. The values entered here provide the population-level metadata for the SDTM Trial Summary (TS) domain.

:::details Expand for General Population Attributes table columns

Column | Description
-- | --
Study population information | This column lists the population attributes. See the table below for details.
Selected values | The value or values recorded for each population attribute.
Reason for missing | The reason recorded when an attribute value is missing, where applicable.

:::

:::details Expand for Study population information fields

| Study population information fields | Options | Description |
|:--|:--|:--|
| Therapeutic area | Select one or more terms from the SNOMED CT dictionary | The overall research or development area to which the study belongs, including areas focused on treatments for diseases and pathological findings, or prevention of conditions that negatively affect health. |
| Study disease, condition or indication | Select one or more terms from the SNOMED CT dictionary, or select NA if not applicable | The condition, disease or disorder that the study is intended to investigate or address. |
| Stable disease minimum duration | Enter a numeric duration and select a unit from the Study Time units, or select NA if not applicable | The protocol-specified minimum time needed to meet the definition of stable disease. |
| Diagnosis group | Select one or more terms from the SNOMED CT dictionary | A grouping of individuals based on a shared procedure or disease, or the absence of one. |
| Relapse criteria | Enter free-text content, or select NA if not applicable | The standard used to determine whether a disease has relapsed. |
| Total number of subjects | Enter a numeric value | The total number of subjects expected to be screened. |
| Healthy subject indicator | Yes or No | Indicates whether people without the condition(s) under study, or related conditions or symptoms, may participate according to the eligibility requirements. |
| Rare disease indicator | Yes or No | Indicates whether the condition under study is considered a rare disease. Definitions vary by authority; for example, the FDA threshold is fewer than 200,000 people in the United States, while the EU/WHO threshold is fewer than 5 in 10,000. |
| Sex of study participants | Male, Female or Mixed | The sex or combination of sexes of the participant group being studied. |
| Planned minimum age of study participants | Enter a numeric age and select a unit from the Study Time units | The anticipated minimum age of subjects to be enrolled in the study. |
| Planned maximum age of study participants | Enter a numeric age and select a unit from the Study Time units, or select PINF if no maximum age is specified | The anticipated maximum age of subjects to be enrolled in the study. |
| Paediatric study indicator | Yes or No | Indicates whether the study is a paediatric study, i.e. a study in children. |
| Paediatric investigation plan indicator | Yes or No | Indicates whether the study is part of a paediatric investigation plan (PIP). |
| Paediatric post-market study indicator | Yes or No | Indicates whether the study is a paediatric post-market study, conducted in children after initial approval of the compound being studied. |

:::

To define general population attributes:

1. Select the **General Population Attributes** tab.
2. Select the pencil (**Edit content**) button to open the form.
3. Enter or select values based on the study protocol, using the options described above. For fields that do not apply, select **NA** where available. Select **PINF** for the planned maximum age when no maximum age is specified.
4. Save the form to apply the changes.

## Study Design Population

> [!NOTE]
> This feature is controlled by a feature flag and may not be available in every environment.

Use this tab to define specific population groups within the study design and associate each group with its applicable inclusion and exclusion criteria. It is separate from the overall population metadata recorded in General Population Attributes.

:::details Expand for Study Design Population table columns

| Column | Description |
|:--|:--|
| Group ID | Identifier for the population group in the study design. |
| Name | Name of the population group. |
| Definition | Description of the population group. |
| Notes | Additional information about the population group. |
| Inclusion criteria | Criteria that participants must meet to belong to this population group. |
| Exclusion criteria | Criteria that disqualify participants from belonging to this population group. |
| Modified | Date associated with the latest version of the population group. |
| Modified by | Username of the person who made the latest change. |

:::

To define a study design population:

1. Select the **Study Design Population** tab.
2. Select **Add Study Design Population** (the plus button).
3. Enter at least one of **Group ID**, **Name**, **Definition**, or **Notes**. Describe the population group according to the study design.
4. Save the population. The criteria assignment dialog opens after the population is saved.
5. Select the applicable existing inclusion and exclusion criteria, then save the assignments. To assign or change criteria later, select **Link criteria** from that population row's actions.

## View Specifications

General Population Attributes that have a corresponding SDTM Trial Summary parameter are shown in View Specifications under SDTM Study Design Datasets → Trial Summary. Study Design Population groups and their linked inclusion and exclusion criteria are managed separately and are not displayed as Trial Summary parameters.

[![Trial Summary showing General Population Attributes in View Specifications](/images/user_guides/study_population_02.png)](/images/user_guides/study_population_02.png)
*Figure 1: General Population Attributes in the Trial Summary dataset*

## Related topics / links

- [Study Structure](guide_study_structure.html)
- [Study Data Standards](study_data_standard_versions.html)