# Study Structure (Structural Study Design)

**Where to find it:** Studies → Define Study → Study Structure.

## Purpose

One of the main foundations in OpenStudyBuilder is the capacity to set up the Study Structure. The Study Structure consists of several parts, and further detailed descriptions are provided below the introduction. The Study Structure metadata can be used in systems and documents, e.g. for the Protocol, CRF and SDTM generation.

## Concept & definitions

The Study Structure menu consists of:

- The **Overview** that provides the user with an overview of the study, that has been set up
- The **Study Arms** which provide the option to add single or multiple arms with different arm types from Observational arms to investigational arms
- The **Study Branches** where users can split arms to branches
- The **Study Cohorts** for adding cohorts for a single arm/branch or across arms/branches
- The **Study Epochs** where the different periods in a study are described with a relation to treatment or not, and before, during or after treatment.
- The **Study Elements** tab, where the user can specify intended main purpose within an arm in a certain period (epoch)
- The **Study Visits** where the user can assign visits to the epoch with visit types and reference timepoints
- The **Design Matrix** that provides an overview of the combination of arms/branches, epochs, and elements

## When to use

Use this page when designing a study, to define its arms, branches, cohorts, epochs, elements and visits, and to link them in the Design Matrix. Set up the arms and epochs first: visits are assigned to epochs, and the Design Matrix links elements to arm/epoch combinations. Return to the page whenever the design changes, for example when an epoch is added or its lag times change.

## Overview

In the Overview section, the link between arms, branch arms, cohorts, elements, and epochs can be seen. The values are derived from the fields **Arm name**, **Branch name**, **Cohort name**, **Epoch name** and **Element name** found under each respective section.

Updates performed to any of the above fields will be reflected in the Overview table.

Elements are only visible after being assigned in the **Design Matrix** section.

[![Screenshot - Study Overview for 2-arms, parallel study](/images/user_guides/guide_sstruct_01.png)](/images/user_guides/guide_sstruct_01.png)

Figure 1: Study Overview for 2-arms, parallel study

## Study Arms

The Study Arms section is designed to support different types of study design classes. The user can create a study with arms only or a study with cohorts, branches and subpopulations. There is no limitation in the number of arms from an OpenStudyBuilder perspective.

:::details Show Quick Guide

**Selecting the study design class**

1. Go to the **Study Arms** tab and select the **+** button above the table.

   [![Study Arms tab with the + button highlighted](/images/user_guides/guide_sstruct_09.png)](/images/user_guides/guide_sstruct_09.png)

2. In the first step, **Select study design class**, choose one of the options:
   - **Study with cohorts, branches and subpopulations**

     [![Select study design class step with Study with cohorts, branches and subpopulations selected](/images/user_guides/guide_sstruct_12.png)](/images/user_guides/guide_sstruct_12.png)

     Select **Study with cohorts, branches and subpopulations** to do the full set-up with arms, cohorts/subpopulations and branch arms.

     [![Set up Arms step with Remove and Add Arm buttons highlighted](/images/user_guides/guide_sstruct_13.png)](/images/user_guides/guide_sstruct_13.png)

     Define the study arms. To add a new study arm, select the **Add Arm** button. To remove an arm that was added unnecessarily, select the **Remove** button next to it.

     [![Set up Cohorts/subpop. step with Remove and Add Cohort/subpop. buttons highlighted](/images/user_guides/guide_sstruct_14.png)](/images/user_guides/guide_sstruct_14.png)

     Define the study cohorts/subpopulations. To add a new study cohort/subpop., select the **Add Cohort/subpop.** button. To remove a cohort/subpop. that was added unnecessarily, select the **Remove** button next to it.

     [![Linking step with participant numbers per arm and cohort/subpop. highlighted](/images/user_guides/guide_sstruct_15.png)](/images/user_guides/guide_sstruct_15.png)

     Link the arms and cohorts/subpopulations by defining the number of participants for each arm–cohort/subpop. combination. A link (branch arm) is created automatically only when the number of participants is greater than 0.

   - **Study with arms only**

     [![Set up Arms step with Remove and Add Arm buttons and Number of participants fields highlighted](/images/user_guides/guide_sstruct_16.png)](/images/user_guides/guide_sstruct_16.png)

     Define the arms for your study. The **Number of participants** field is optional.

   - **Select from studies**

     [![Select study design class step with Select from studies option and source study selector](/images/user_guides/guide_sstruct_10.png)](/images/user_guides/guide_sstruct_10.png)

     To copy arms from another study, pick the source study in the study selector.

     [![Set up Arms step with selected arms, copy icons and Create arms button](/images/user_guides/guide_sstruct_11.png)](/images/user_guides/guide_sstruct_11.png)

     Select the arms from the source study that you want to copy to your study. The selected arms are displayed in the upper table, while the arms available for copying are listed in the lower table.

     > [!NOTE]
     > **Select from studies** copies only the arms from the source study, even if that study was set up with cohorts, branches and subpopulations.

3. To change the design class, go to the **Study Arms** tab and select the pencil icon. Then select a different class and select **Continue**. If the change would remove existing data, a warning is shown, and you can confirm with **Change study design class** or cancel with **Keep study design class**:
   - changing from **Study with arms only** to **Study with cohorts, branches and subpopulations**: all branch arms are removed;
   - changing from **Study with cohorts, branches and subpopulations** to **Study with arms only**: all cohorts and branch arms are removed.

The current class is displayed as **Study Design Class** in the **Overview** tab.

:::

A Study arm must be created with the following mandatory items:

- A **Study arm type** describing the main purpose of the arm. The current arm types are a subset of the CDISC Protocol Study Arm type code list (C174222)
- An **Arm name**
- An **Arm short name**

Optional choices for study arms:

- The **Number of participants** (for studies with arms only). This information will also be used to calculate the total planned number of subjects for the study structure overview.

  > [!NOTE]
  > When creating studies with cohorts, branches and subpopulations, the number of participants will be allocated to each arm after creating the individual branch arms.

- A **Randomisation group**
- An **Arm label**
- A free text **Description**
- An **Arm code**. The arm code can be reused as randomisation code, but it is also possible to write another randomisation code or leave randomisation code blank.

## Study Branches

A branch arm (study branch) is a sub-division of a study arm and can be used when participants within a study arm deviate on dosing, indication or another parameter. Branch arms can be created in one of two ways in OpenStudyBuilder:

1. Using the cohort stepper, which will be available when selecting the “Study with cohorts, branches and subpopulations” design class.
1. Manual creation of branch arms after selecting the “Study with arms only” design class.

When using the cohort stepper, branch arms must be created with the following mandatory items:

- The **Number of participants**

  > [!NOTE]
  > If there is no connection or no participants in a cohort/subpop-arm relation, then leave the participant number at 0. When the number of participants is set to greater than 0, the system will automatically create the branch relation between cohorts/subpop and arms.

- A **Branch name**

  > [!NOTE]
  > The Branch name is automatically generated based on the name of the arm and cohort the branch is related to but can be edited manually.

- A **Branch short name**

  > [!NOTE]
  > The Branch short name is automatically generated based on the short name of the arm and cohort the branch is related to but can be edited manually.

When creating manually defined branch arms (Requires the “Study with arms only” design class), all branch arms must be created with the following mandatory items:

- A **Study Arm**
- A **Study Branch Arm Name**
- A **Study Branch Arm Short Name**

Optional choices for manually defined branch arms include:

- A **Random. group**
- The **Planned number of subjects in branch**
- A free text **Description**

## Study Cohorts

Study cohorts can be created in one of two ways in OpenStudyBuilder:

1. Using the cohort stepper, which will be available when selecting the “Study with cohorts, branches and subpopulations” design class.
1. Manual creation of study cohorts after selecting the “Study with arms only” design class.

When using the cohort stepper, all cohorts must be created with the following mandatory items:

- A **Cohort/subpop. code**
- A **Cohort/subpop. name**
- A **Cohort/subpop. short name**

Optional choices for cohorts created using the cohort stepper include:

- A **Source variable** field with the option to select either **Cohort**, **Subgroup** or **Stratum**
- A free text **Source variable description**
- A free text **Description**

When creating manually defined cohorts (Requires the “Study with arms only” design class), all cohorts must be created with the following mandatory items:

- A **Cohort Name**
- A **Short Name**
- A **Cohort Code**

Optional choices for manually defined cohorts include:

- A **Study Arm**
- A **Study Branch Arm**
- The **No. of subjects**

  > [!NOTE]
  > In the case of a missing relation to an arm, it is not possible to add planned number of subjects expected for the cohort. The reason for this is that OpenStudyBuilder is validating the number of participants in a cohort against the number of subjects in related arms. If no arm is assigned, then the validation cannot take place.

- A free text **Description**

## Study Epochs

The study epochs must be set up for the different phases that the specific study goes through.

- **Epoch type**: The epoch type is used to specify what kind of epoch is being created, e.g. a treatment epoch.
- **Epoch subtype**: Depending on the epoch type, different epoch sub-types can be chosen in a logical setup. As an example, a treatment sub-type cannot be chosen in a pre-treatment epoch type.

The possible values are specified in the library, and the epoch sub-types are based on the CDISC Epoch codelist (see Figure 2).

[![Screenshot - Epoch subtype codelist based on CDISC SDTM codelist C99079](/images/user_guides/guide_sstruct_03.png)](/images/user_guides/guide_sstruct_03.png)

Figure 2: Epoch subtype codelist based on CDISC SDTM codelist C99079

**Reorder**: Epochs can be reordered if needed by using the reorder functionality in the top of the screen and edited by using the row-action menu in the three dots to the left of the row.

[![Screenshot - Reorder functionality and row-action menu](/images/user_guides/guide_sstruct_04.png)](/images/user_guides/guide_sstruct_04.png)

Figure 3: Reorder functionality and row-action menu

### Lag time

A lag time is the period after the end of an epoch during which an observation, such as an adverse event, is still attributed to that epoch. An epoch can hold up to three lag times:

| Field | Use it for |
|:--|:--|
| **Adverse event lag time** | The lag time applied to adverse events |
| **Hypoglycaemic event lag time** | The lag time applied to hypoglycaemic events |
| **Clinical event lag time** | The lag time applied to clinical events |

Each lag time has its own **Lag time unit**: **days** or **weeks**.

Which lag times are shown depends on two feature flags and on the study's migrated study indicator. The same rule applies to the columns in the Study Epochs table and to the fields in the epoch form:

| Study | Feature flag switched on | Lag times shown |
|:--|:--|:--|
| Study with the migrated study indicator | `study_epoch_lag_time` | All three |
| Any study | `study_epoch_ae_lag_time` | **Adverse event lag time** only |
| Any study | Neither flag | None |

> [!NOTE]
> The migrated study indicator is set when a study is migrated from a legacy system. It cannot be set or changed in OpenStudyBuilder.

:::details Show Quick Guide

1. Go to the **Study Epochs** tab. The lag time columns are at the right of the table: **Adverse event lag time** (A), **Hypoglycaemic event lag time** (B) and **Clinical event lag time** (C). Each value is shown with its unit.

   [![Study Epochs table with the lag time columns highlighted](/images/user_guides/study_epoch_lag_time_01.png)](/images/user_guides/study_epoch_lag_time_01.png)

2. Click the ellipsis (three dots) to the left of the epoch and select **Edit**. When adding a new epoch with the **+** button, the same fields are shown.
3. Enter the lag time as a whole number and select the **Lag time unit**.

   [![Lag time fields in the Edit study epoch form](/images/user_guides/study_epoch_lag_time_02.png)](/images/user_guides/study_epoch_lag_time_02.png)

   [![Lag time unit options: days and weeks](/images/user_guides/study_epoch_lag_time_03.png)](/images/user_guides/study_epoch_lag_time_03.png)

4. Enter a **Change description** and click **SAVE**.

> [!TIP]
> Lag times can be edited even when visits are assigned to the epoch and other fields of the epoch are locked.

To remove a lag time, clear the field with the clear (x) icon and save. To check when a lag time or its unit changed, click the ellipsis on the epoch row and select **History**. Changed values are highlighted, and each value is shown with its unit.

[![Epoch history showing lag time values with their units](/images/user_guides/study_epoch_lag_time_05.png)](/images/user_guides/study_epoch_lag_time_05.png)

On a study without the migrated study indicator, only **Adverse event lag time** is shown.

[![Study Epochs on a study that is not migrated, showing only the Adverse event lag time column](/images/user_guides/study_epoch_lag_time_06.png)](/images/user_guides/study_epoch_lag_time_06.png)

:::

| Symptom | Interpretation | Likely cause | Fix |
|:--|:--|:--|:--|
| "This field must contain only digits" under a lag time | Expected: lag times are whole numbers | A decimal or text was entered | Enter a whole number in the selected unit. Confirm the intended duration rather than rounding a fractional value |
| "Value can't be less than 0" under a lag time | Expected: a lag time cannot be negative | A negative number was entered | Enter 0 or a positive whole number |
| No lag time columns or fields at all | Expected: the feature is switched off | The `study_epoch_ae_lag_time` feature flag is off, and the study does not qualify for all three lag times | Contact the OpenStudyBuilder administrator |
| Only **Adverse event lag time** is shown | Expected on most studies | The study does not have the migrated study indicator, or the `study_epoch_lag_time` feature flag is off | No action needed |

## Study Elements

A study element is describing the intended intervention or purpose for a specific phase in the study.

A Study element is created by choosing:

- **Element type** - either treatment or no treatment.
- **Element subtype**: In the library a logical connection has been created for choosing an element sub-type based on the element type. The code lists for element type and element sub-type are available in the library as sponsor code lists.
- **Element name**
- **Element short name**
- The rest of the items in the element form are optional.

## Study Visits

The study visits tab contains all the visits needed for a study. OpenStudyBuilder contains four visit types:

- **Scheduled visit**. These are the normal visits scheduled in a study and visible in the schedule of activities
- **Unscheduled visit**. This is primarily a technical placeholder for events happening outside normal visits and not visible in the schedule of activities
- **Non-visit**. This is primarily a technical placeholder for data that are not visit related. This visit type is not visible in the schedule of activities
- **Special visit**. Other visits without specific timing but related to data collection. An example is early treatment discontinuation, where certain data are to be collected, but not at the timing of the planned End of Treatment visit. The special visit is always related to another visit and is shown in the schedule of activities as visit VXXA.

[![Screenshot - Special Visit added as related to visit 10 End of Treatment](/images/user_guides/guide_sstruct_06.png)](/images/user_guides/guide_sstruct_06.png)

Figure 4: Special Visit added as related to visit 10 End of Treatment

The **Global Anchor Visit** is used as a reference visit with timing as '0'. This can be the first visit, the second visit or any other visit. The important part is to define which visit to use as global anchor visit as all other visits will have timing related to this visit directly or indirectly (see Figure 5).

It is possible to duplicate visits, where the only difference is the timing. Other attributes can be edited using the edit button above the visit table.

> [!NOTE]
> The Global Anchor Visit is not defining an SDTM baseline (--BLFL) for any assessment.

[![Screenshot - Randomisation Visit as Global Anchor Visit](/images/user_guides/guide_sstruct_07.png)](/images/user_guides/guide_sstruct_07.png)

Figure 5: Randomisation Visit as Global Anchor Visit

**Groups of visits**/Visits stretching across several days can also be created in the OpenStudyBuilder. This is done via the "Add visit" form with defining an **Anchor visit in visit group** and linking additional sub-visits to this anchor visit.

The detailed visit functionalities will be separately covered in another guide.

## Design Matrix

In the design matrix, arms, branches, epochs, and elements can be linked together to visualise what the study will look like.

Elements must be linked to an arm/epoch combination and **saved** before exiting the page.

[![Screenshot - Design matrix in edit mode](/images/user_guides/guide_sstruct_08.png)](/images/user_guides/guide_sstruct_08.png)

Figure 6: Design matrix in edit mode
