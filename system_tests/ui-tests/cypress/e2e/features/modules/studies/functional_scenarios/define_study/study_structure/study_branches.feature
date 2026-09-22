@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Manually Defined Study Branches

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study branch arms.

    Background: User is logged in
        Given The user is logged in
        When User selects study with id 'CDISC DEV-9878'
        And User intercepts study branches request
        Then The page 'study_structure/branches' is opened for current study
        And User waits for the table
        And User waits for the branches request

    Scenario: [Test data] User must be able to prepare test data for study branches tests
        And [API] Get all Study Arms within selected study
        And [API] Delete all Study Arms within selected study
        And [API] Uid of study type 'Investigational Arm' is fetched
        And [API] The Study Arm exists within selected study

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to Study Branches page using side menu
        Given User selects study with id 'CDISC DEV-9876'
        Given The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Branches' tab is selected
        Then The current URL is '/study_structure/branches'

    Scenario: [Table][Options] User must be able to see the Study Branches table with following options
        Then A table is visible with following options
            | options                                            |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the Study Branches table with following columns
        And A table is visible with following headers
            | headers             |
            | #                   |
            | Arm name            |
            | Branch name         |
            | Short name          |
            | Cohort name         |
            | Cohort code         |
            | Random. group       |
            | Random. Code        |
            | No. of participants |
            | Modified            |
            | Modified by         |

    Scenario: [Online help] User must be able to read online help for the page
        And The online help button is clicked
        Then The online help panel shows 'Study Branches' panel with content "The decision points where subjects are divided into separate treatment groups. For a simple parallel or cross-over design subject are branched into treatment arms at randomisation. i.e. have one branch decision point. A study can have more branching points if e.g. subjects are assigned to a recover treatment after initial randomisation. This second decision point could be based on a responsiveness to treatment."

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Create][Pre-condition][No Arms] User must be informed that no Study Arms are available
        When User selects study with id 'CDISC DEV-9880'
        Then The page 'study_structure/branches' is opened for current study
        Then The table display the note "No data available - Create Study Arm first"
        And The option to create branch arm is not visible

    @smoke_test
    Scenario: [Create][Existing Arm] User must be able to create a new study arm branch for existing arm
        And Add branch button is clicked
        And User continues to next step of study structure stepper
        And The first available arm is selected for the branch
        And The form for new study branch arm is filled
        And The Study Branch description is filled in
        And User continues to next step of study structure stepper
        And The Study Branch is found
        Then The study branch arm is visible within the table

    Scenario: [Actions][Edit] User must be able to edit the Study Branch Arm
        And The Study Branch is found
        And The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        When The study branch arm is edited
        And The Study Branch description is updated
        And User continues to next step of study structure stepper
        And The form is no longer available
        Then The pop up displays 'Branch Arm updated'
        And The Study Branch is found
        Then The study branch arm is visible within the table

    Scenario: [Actions][Edit][Fields check] User must not be able to change the Study Arm for created Study Branch Arm
        And Add branch button is clicked
        And User continues to next step of study structure stepper
        And The first available arm is selected for the branch
        When The form for new study branch arm is filled
        And The Study Branch description is filled in
        And User continues to next step of study structure stepper
        And The form is no longer available
        And The Study Branch is found
        And The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        Then The stady arm field is disabled

    Scenario Outline: [Create][Fields check] User must not be able to provide value other than positive integer for Number of subjects
        And Add branch button is clicked
        And User continues to next step of study structure stepper
        And The first available arm is selected for the branch
        And Planned number of subjects for branch is set as '-123'
        Then The validation message appears for branch number of subjects "Value can't be less than 1"
        And Planned number of subjects for branch is set as '-1'
        Then The validation message appears for branch number of subjects "Value can't be less than 1"
        And Planned number of subjects for branch is set as '0'
        Then The validation message appears for branch number of subjects "Value can't be less than 1"

    Scenario: [Create][Fields check] User must not be able to provide a value for number of subjects higher than the number defined for the study arm
        And Add branch button is clicked
        And User continues to next step of study structure stepper
        And The first available arm is selected for the branch
        And Planned number of subjects for branch is set as '101'
        Then The validation message appears for branch number of subjects 'Number of subjects in a branch cannot exceed total number of subjects in the arm'

    Scenario: [Create][Mandatory fields] User must not be able to create a Study Branch Arm without Study Arm selected
        And Add branch button is clicked
        And User continues to next step of study structure stepper
        When The Study Arm field is not populated in the Study Branch Arms form
        And User continues to next step of study structure stepper
        Then The validation message appears for empty study arm
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to create a Study Branch Arm without Branch Name
        And Add branch button is clicked
        And User continues to next step of study structure stepper
        And The Branch name field is not populated
        And User continues to next step of study structure stepper
        Then The validation message appears for empty branch name
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to create a Study Branch Arm without Branch Short Name
        And Add branch button is clicked
        And User continues to next step of study structure stepper
        And The Branch short name field is not populated
        And User continues to next step of study structure stepper
        Then The validation message appears for empty branch short name
        And The form is not closed

    Scenario: [Create][Uniqueness check][Name] User must not be able to create two Branch Arms within one study using the same Branch Arm name
        And Add branch button is clicked
        And User continues to next step of study structure stepper
        And The first available arm is selected for the branch
        And The form for new study branch arm is filled
        And The Study Branch description is filled in
        And User continues to next step of study structure stepper
        And The form is no longer available
        Then The pop up displays "Branch Arm created"
        And User waits for the table
        And Add branch button is clicked
        And User waits for 1 seconds
        And User continues to next step of study structure stepper
        And The first available arm is selected for the branch
        And Another Study Branch Arm is created with the same arm name
        And User continues to next step of study structure stepper
        Then The pop up displays "in field Branch Arm Name is not unique for the study"
        And The form is not closed

    Scenario: [Create][Uniqueness check][Short Name] User must not be able to create two Branch Arms within one study using the same Branch Arm short name
        And Add branch button is clicked
        And User continues to next step of study structure stepper
        And The first available arm is selected for the branch
        And The form for new study branch arm is filled
        And The Study Branch description is filled in
        And User continues to next step of study structure stepper
        And The form is no longer available
        Then The pop up displays "Branch Arm created"
        And User waits for the table
        And Add branch button is clicked
        And User waits for 1 seconds
        And User continues to next step of study structure stepper
        And The first available arm is selected for the branch
        And Another Study Branch Arm is created with the same branch arm short name
        And User continues to next step of study structure stepper
        Then The pop up displays "in field Branch Arm Short Name is not unique for the study"
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to use text longer than 20 characters for the Study Arm Arm Code field in the Study Arms form
        And Add branch button is clicked
        And User continues to next step of study structure stepper
        And The form for new study branch arm is filled
        And Branch arm code text is set to value longer than 20 characters
        And User continues to next step of study structure stepper
        Then The validation message appears for branch randomisation code 'This field must not exceed 20 characters'

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyBranches' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyBranches' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyBranches' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyBranches' file is downloaded in 'xlsx' format

    @manual_test
    Scenario: User must be able to remove the Study Branch Arm
        Given The page 'study_structure/branches' is opened for current study
        And The test Study Branch Arm is available
        When The delete action is clicked for the test Study Branch Arm
        Then The test Study Branch Arm is no longer available
        And related Study Design Cell selections are cascade deleted

    @manual_test
    Scenario: User must be presented with the warning message when removing the last Study Branch Arm
        Given The page 'study_structure/branches' is opened for current study
        And The test study branch arm is available
        And The test study arm is related to study design cell
        When The 'Delete' option is clicked from the three dot menu list
        Then The warning message appears 'Removing this Study Branch Arm will remove all related Study Cells'

    @manual_test
    Scenario: Deleting last Study Branch Arm for a Study Arm must update relationship to Study Design Cell
        Given a Study Arm has been defined for the study
        And only one Study Branch Arm exist related to this Study Arm
        And the Study Branch Arm have Study Design Cell relationships to Study Elements for a Study Epochs
        When The delete action is clicked for the Study Branch Arm
        Then The Study Design Cell selections will change their relationship from the Study Branch Arm to the related Study Arm

    @manual_test
    Scenario: User must be able to read change history of output
        Given The page 'study_structure/branches' is opened for current study
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The page 'study_structure/branches' is opened for current study
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames