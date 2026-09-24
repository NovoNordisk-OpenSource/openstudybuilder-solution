@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Manually Defined Study Cohorts

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study cohorts.

    Background: User is logged in
        Given The user is logged in
        Given User selects study with id 'CDISC DEV-9878'
        And [API] Uid of study type 'Investigational Arm' is fetched
        And [API] The Study Arm exists within selected study
        Then The page 'study_structure/cohorts' is opened for current study
        And User waits for the table

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to Study Cohorts page using side menu
        And The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Cohorts' tab is selected
        Then The current URL is '/study_structure/cohorts'

    Scenario: [Table][Options] User must be able to see the Study Cohorts table with following options
        Then A table is visible with following options
            | options                                            |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the Study Cohorts table with following columns
        And A table is visible with following headers
            | headers             |
            | #                   |
            | Arm name            |
            | Branch name         |
            | Cohort Name         |
            | Short Name          |
            | Cohort Code         |
            | No. of participants |
            | Description         |
            | Modified            |
            | Modified by         |

    Scenario: [Online help] User must be able to read online help for the page
        And The online help button is clicked
        Then The online help panel shows 'Study Cohorts' panel with content "A group of individuals who share a common exposure, experience or characteristic or a group of individuals followed-up or traced over time in a cohort study. Example could be first human dose-escalation studies where increasing doses are given until stopping criteria are met. Some dose-escalation studies enroll a new cohort of subjects (a new group of subjects) for each new dose. Cohorts are also used for observational studies where no randomisation takes place or single arm randomised study. Then cohorts are being defined based on some characteristics and comparisons are made between the different cohorts, e.g. treatment of a drug in subjects with a liver disease compared to a group of healthy subjects. Cohorts are not the same as strata. Stratification is the process of dividing members of the population into homogeneous subgroups before sampling/randomisation. If the study with liver diseased and healthy subjects had to examine the effect of a drug compared to placebo then liver diseased/healthy would be a stratification factor, since it is expected that the treatment responses will be different in the two groups. Stratification is made to ensure homogeneity of the groups in which the treatments are being compared."

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @smoke_test
    Scenario: [Create][Positive case] User must be able to create a new study cohort
        And Add cohort button is clicked
        When The form for new study cohort is filled
        And Cohort description is set to 'Cohort description'
        And Form save button is clicked
        And The Study Cohort is found
        Then The study cohort is visible within the table

    Scenario: [Actions][Edit] User must be able to edit the Study Cohort
        When The Study Cohort is found
        And The 'Edit' option is clicked from the three dot menu list
        And User waits for cohort edit form to load
        When The study cohort is edited
        And Cohort description is set to 'Cohort description Update'
        And Form save button is clicked
        And The form is no longer available
        And The pop up displays 'Cohort updated'
        And The Study Cohort is found
        Then The study cohort is visible within the table

    Scenario: [Actions][Edit] User must be able to edit the Arm and Branch Arm while editing the Study Cohort
        When The 'Edit' option is clicked from the three dot menu list
        Then The field study arm is enabled for edition
        And The field study branch is enabled for edition

    Scenario Outline: [Create][Fields check] User must not be able to provide value other than positive integer for Number of subjects
        When Add cohort button is clicked
        And First available study arm is selected
        When Planned number of subjects for cohort is set as '-123'
        Then The validation message appears for cohort number of subjects "Value can't be less than 1"
        When Planned number of subjects for cohort is set as '-1'
        Then The validation message appears for cohort number of subjects "Value can't be less than 1"
        When Planned number of subjects for cohort is set as '0'
        Then The validation message appears for cohort number of subjects "Value can't be less than 1"

    Scenario: [Create][Fields check] User must not be able to provide a value for number of subjects higher than the number defined for the study arm
        When Add cohort button is clicked
        And First available study arm is selected
        When Planned number of subjects for cohort is set as '101'
        Then The validation message appears for cohort number of subjects 'Number of subjects in a cohort cannot exceed total number of subject in the study'

    Scenario: [Create][Mandatory fields] User must not be able to create a Study Cohort without providing necessary data as in this scenario
        And Add cohort button is clicked
        When The form for new study cohort is filled
        And The Cohort name field is not populated
        And The Cohort short name field is not populated
        And The Cohort code field is not populated
        And Form save button is clicked
        Then The form is not closed

    Scenario: [Create][Uniqueness check][Name] User must not be able to create two Cohorts within one study using the same Cohort name
        And Add cohort button is clicked
        When The form for new study cohort is filled
        And Form save button is clicked
        And The form is no longer available
        And Add cohort button is clicked
        And User waits for 1 seconds
        And First available study arm is selected
        And Another Study Cohort is created with the same cohort name
        And Form save button is clicked
        Then The pop up displays "in field Cohort Name is not unique for the study"
        And The form is not closed

    Scenario: [Create][Uniqueness check][Short Name] User must not be able to create two Cohorts within one study using the same Cohort short name
        And Add cohort button is clicked
        When The form for new study cohort is filled
        And Form save button is clicked
        And The form is no longer available
        And Add cohort button is clicked
        And User waits for 1 seconds
        And First available study arm is selected
        And Another Study Cohort is created with the same cohort short name
        And Form save button is clicked
        Then The pop up displays "in field Cohort Short Name is not unique for the study"
        And The form is not closed

    Scenario: [Create][Uniqueness check][Cohort code] User must not be able to create two Cohorts within one study using the same Cohort code
        And Add cohort button is clicked
        When The form for new study cohort is filled
        And Form save button is clicked
        And The form is no longer available
        And Add cohort button is clicked
        And User waits for 1 seconds
        And First available study arm is selected
        And Another Study Cohort is created with the same cohort code
        And Form save button is clicked
        Then The pop up displays "in field Cohort code is not unique for the study"
        And The form is not closed

    Scenario: [Create][Mandatory fields] Outline: User must not be able to use text longer than specified in this scenario for Study Cohorts form
        And Add cohort button is clicked
        When Cohort name is set as string with length 201
        And Form save button is clicked
        Then The validation message appears for cohort name "This field must not exceed 200 characters"

    Scenario: [Create][Mandatory fields] Outline: User must not be able to use text longer than specified in this scenario for Study Cohorts form
        And Add cohort button is clicked
        When Cohort short name is set as string with length 21
        And Form save button is clicked
        Then The validation message appears for cohort short name "This field must not exceed 20 characters"

    Scenario: [Create][Fields validation] User must be able to create a Cohort with any text value
        And Add cohort button is clicked
        When The form for new study cohort is filled
        And Cohort description is set to 'Cohort description'
        When Cohort code is set to random string
        And Form save button is clicked
        And The Study Cohort is found
        Then The study cohort is visible within the table

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCohorts' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCohorts' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCohorts' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCohorts' file is downloaded in 'xlsx' format

    @manual_test
    Scenario: User must be able to remove the Study Cohort
        And The test Study Cohort is available
        When The delete action is clicked for the test Study Cohort
        Then The test Study Cohort is no longer available
        And related Study Design Cell selections are cascade deleted

    @manual_test
    Scenario: User must be able to read change history of output
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames