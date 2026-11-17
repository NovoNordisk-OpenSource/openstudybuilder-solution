# Study Properties

**Where to find it:** Studies → Define Study → Study Properties.

## Purpose

The Study Properties section can be used to define detailed information for protocol authorisation or the Trial Summary SDTM domain.

## Concept & definitions

The Study Properties page contains four tabs for defining study metadata.

- **Study Type:** Describes the overall study type, phase, development stage, and related properties.
- **Study Attributes:** Describes the study's intervention and key design characteristics.
- **Other Study Attributes:** Captures additional study-level information in the Trial Summary dataset through required and optional parameters.
- **Age Rules:** Defines how a subject's age is determined at baseline and how subjects are grouped by age.

## Study Type

Record the protocol-defined values used to classify the study and capture its key design settings. Select controlled terms where available and provide protocol-based text or duration values. This metadata contributes to downstream Trial Summary reporting where applicable.

:::details Expand for Study Type table columns

| Column | Description |
|:--|:--|
| Study type information | This column lists the Study Type information fields. See the table below for details. |
| Selected values | The value or values recorded for each Study Type field. |
| Reason for missing | The reason recorded when a Study Type value is missing, where applicable. |

:::

:::details Expand for Study type information fields

| Study type information fields | Options | Description |
|:--|:--|:--|
| Study type | Select one term from the CDISC CT Study Type list. | The overall type of the study. |
| Trial type | Select one or more terms from the CDISC CT Trial Type list. | The type or types of trial that fall within the study's purpose. |
| Study phase classification | Select one term from the CDISC CT Trial Phase list. | The relevant phase or stage of the study. |
| Development stage | Select one term from the sponsor-defined Development Stage list. | The relevant development stage of the study. |
| Extension study | Yes or No | Indicates whether the study is an extension trial. |
| Adaptive design | Yes or No | Indicates whether the study prospectively allows aspects of its design or hypotheses to be modified based on participant data, usually interim data. |
| Study stop rules | Enter the stopping rule from the protocol, or select **NONE** if no stopping rule applies. | The protocol-specified rule, regulation or condition that determines when the trial will be terminated. |
| Confirmed response minimum duration | Enter a numeric duration and select a unit from the Study Time units, or select **NA** if not applicable. | The minimum protocol-specified time required to meet the definition of a confirmed response to treatment. |
| Post authorization safety study indicator | Yes or No | Indicates whether the study is a post-authorisation safety study. |

:::

To define Study Type information:

1. Select the **Study Type** tab.
2. Select the pencil (**Edit content**) button to open the form.
3. Enter or select values based on the study protocol, using the options described above. Select **NA** for confirmed response minimum duration when it is not applicable, or **NONE** if the study has no stopping rule.
4. Save the form to apply the changes.

To reuse values from another study, select **Copy from study**, choose a study, select the properties to copy, and select **Apply**. The selected properties replace their current values. Other Study Type values remain unchanged.

## Study Attributes

Record the protocol-defined intervention and design information for the study. Select controlled terms where available and provide protocol-based values for free-text and duration fields. This metadata contributes to downstream Trial Summary reporting where applicable.

:::details Expand for Study Attributes table columns

| Column | Description |
|:--|:--|
| Study intervention type information | This column lists the Study Attributes information fields. See the table below for details. |
| Selected values | The value or values recorded for each Study Attributes field. |
| Reason for missing | The reason recorded when a Study Attributes value is missing, where applicable. |

:::

:::details Expand for Study intervention type information fields

| Study intervention type information fields | Options | Description |
|:--|:--|:--|
| Intervention type | Select one term from the CDISC CT Intervention Type list. | The kind of product or procedure investigated in the study. |
| Study intent type | Select one or more terms from the CDISC CT Trial Indication Type list, or select **NA** if not applicable. | The planned purpose of the therapy, device, or agent under study in the clinical trial. |
| Control type | Select one or more terms from the CDISC CT Control Type list. | The comparator against which the study treatment is evaluated, such as an active, dose-response, or placebo control. |
| Intervention model | Select one term from the CDISC CT Intervention Model list. | The general strategy for assigning interventions to participants, such as a single-group, parallel, or crossover design. |
| Study is randomised | Yes or No | Indicates whether participants are assigned to treatment or control groups by randomisation. |
| Add-on to existing treatment | Yes or No | Indicates whether a therapeutic product is added to an existing regimen while both remain separate products. |
| Study blinding schema | Select one term from the CDISC CT Trial Blinding Schema list. | Describes which participants or investigators know the interventions they receive or administer. |
| Stratification factor | Enter free-text content, or select **NA** if not applicable. | Factors used during randomisation to balance relevant characteristics across study arms and, where appropriate, support statistical analyses. |
| Planned study length | Enter a numeric duration and select a unit from the Study Time units. | The planned length of observation for a single subject. |

:::

Define Study Attributes using the same workflow described above for Study Type information.

## Other Study Attributes

Use this section to add Trial Summary parameters not captured by the other Study Properties sections. Required and optional parameters are managed separately. Available value inputs depend on the selected parameter's semantic data type and code list.

:::details Expand for Other Study Attributes table columns

| Column | Description |
|:--|:--|
| Code | Submission value for the Trial Summary parameter. |
| Parameter | Name of the Trial Summary parameter. |
| Reference | Reference associated with the parameter, where provided. |
| Required level | Indicates whether the parameter is required or optional. |
| Semantic data type | The expected type of the parameter value. |
| Code list | Controlled terminology list that provides allowed values, where applicable. |
| Parameter value | Value recorded for the study. |
| Notes | Additional guidance associated with the parameter. |
| Null flavor | Reason recorded when a parameter value is missing, where applicable. |
| Modified | Date associated with the current parameter value. |
| Modified by | Username of the person associated with the current parameter value. |

:::

:::details Expand for Edit trial summary parameter form fields

| Other Study Attributes information fields | Options | Description |
|:--|:--|:--|
| Parameter | Select a parameter from the **Required Attributes** or **Optional Attributes** list. | Identifies the Trial Summary parameter to add or edit. |
| Parameter value | Enter text, choose **Yes** or **No**, enter a duration, or select a controlled term. Available inputs depend on the parameter. | The value recorded for the selected parameter. |
| Null flavor | Select a reason from the available list when the parameter value is missing. | Records why no parameter value is provided. Selecting a null flavor clears the parameter value. |
| Semantic data type | Displayed for the selected parameter. | Determines the type of value that can be entered or selected. |
| Code list | Displayed when the selected parameter uses controlled terms. | Shows the terminology list used to select an allowed parameter value. |
| Notes | Displayed when notes are available for the selected parameter. | Provides additional guidance about the parameter. |

:::

To add or edit Other Study Attributes:

1. Select the **+** button above the table. Its tooltip says **Add/edit Other Study Attributes** and opens the **Edit trial summary parameter** form.
2. The form displays existing parameters, with one blank entry in any section that has no saved parameters. To edit an existing parameter, use its existing entry. To add a new parameter when no blank entry is available, select **Add Required Study Attribute** or **Add Optional Study Attribute** in the corresponding section. Select the button again for each additional parameter.
3. For each new entry, select a **Parameter** from the corresponding list. The Parameter selector is disabled for existing entries.
4. Enter or select its **Parameter value**. Use the displayed semantic data type, code list, and notes as guidance.
5. If applicable, select a **Null flavor** instead of entering a parameter value.
6. Before saving, select **Remove** on any blank entries you do not intend to use, including the initial entry in a section with no parameter to add.
7. Select **Save** to apply your changes, or **Cancel** to close the form without saving.

[![Edit trial summary parameter form showing required and optional attributes](/images/user_guides/other_study_attributes.png)](/images/user_guides/other_study_attributes.png)
*Figure 1: Adding required and optional Trial Summary parameters*

## View Specifications

Study Properties parameters included in the SDTM Trial Summary (TS) domain are visible in **View Specifications** under **SDTM Study Design Datasets → Trial Summary**. Age Rules are separate from TS. The **Age at baseline rule** supports deriving **AGE** in the SDTM Demographics (DM) domain.

[![Trial Summary in View Specifications showing parameters populated from Study Properties](/images/user_guides/study_properties_02.png)](/images/user_guides/study_properties_02.png)
*Figure 2: Study Properties parameters in the Trial Summary dataset*

## Age Rules

Use this section to select the age rules applied to the study. Available rules and definitions depend on the terminology configured for your StudyBuilder environment.

:::details Expand for Age Rules table columns

| Column | Description |
|:--|:--|
| Age rule information | This column lists the age rules for the study. See the table below for details. |
| Selected values | The rules selected for the study. |
| Definition | The definition of the selected rule, where available. |

:::

:::details Expand for Add or edit age rules information form fields

| Age rule information fields | Options | Description |
|:--|:--|:--|
| Age at baseline rule | Select a rule from the available list. | Defines how age at baseline is determined for subjects in the study. |
| Age group rule | Select a rule from the available list. | Defines how subjects are grouped by age in the study. |

:::

To define Age Rules:

1. Select the **Age Rules** tab.
2. Select the pencil (**Edit content**) button to open the form.
3. Choose a value from each dropdown. Use the information icon beside the selected rule or point to another option in the dropdown to view its definition.
4. Select **Save** to apply the changes, or **Cancel** to close the form without saving.

To see earlier selections, select the **Show version history** button next to **Edit content**.

Age Rules are not parameters in the SDTM Trial Summary (TS) domain. The **Age at baseline rule** is referenced in the SDTM Demographics (DM) specification for deriving **AGE** (age at start of trial).

[![Age Rules dialog with the information icon showing the selected age rule definition](/images/user_guides/age_rules_information_icon.png)](/images/user_guides/age_rules_information_icon.png)
*Figure 3: Select the information icon to view the definition of the selected age rule*

[![Age Rules tab with the selected rules, their definitions and the Edit content button](/images/user_guides/age_rules_tab.png)](/images/user_guides/age_rules_tab.png)
*Figure 4: Age Rules tab with the selected rules and their definitions*
