@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Manually Defined Study Arms

    As a system user,
    I want the system to ensure [Scenario],
    So that I must be able to make complete and consistent specification of study arms.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9878'
        Given User intercepts the design class request
        And User intercepts the study arms list request
        Given The page 'study_structure/arms' is opened for current study
        Given User waits for the design class request
        And User waits for the study arms list request

    Scenario: [Test data] User must be able to delete all existing arms and cohorts before tests start
        And [API] Get all Study Arms within selected study
        And [API] Delete all Study Arms within selected study
        And [API] Get all Study Cohorts within selected study
        And [API] Delete all Study Cohorts within selected study

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to Study Arms page using side menu
        Given User selects study with id 'CDISC DEV-9876'
        And The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Arms' tab is selected
        Then The current URL is '/study_structure/arms'

    Scenario: [Table][Options] User must be able to see the Study Arms table with following options
        Then A table is visible with following options
            | options                                            |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the Study Arms table with following columns
        Then A table is visible with following headers
            | headers             |
            | #                   |
            | Type                |
            | Arm name            |
            | Arm short name      |
            | Random. group       |
            | Random. code        |
            | No. of participants |
            | Connected Branches  |
            | Description         |
            | Modified            |
            | Modified by         |

    Scenario: [Online help] User must be able to read online help for the page
        Given The online help button is clicked
        Then The online help panel shows 'Study Arms' panel with content "Specification of the planned investigational treatment arms. An arm is a planned 'path' of interventions through the trial, e.g. arm AB is treatment A followed by treatment B."

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @smoke_test
    Scenario: [Create][Positive case] User must be able to add a new Study Arm
        And The plus button is clicked
        When User select manual study structure
        And User continues to next step of study structure stepper
        When New arm is added with type 'Placebo Arm'
        And User saves and exits study structure stepper
        Then User searches for 'Test Arm 1'
        And The new study arm data is available in the table

    Scenario: [Actions][Edit] User must be able to edit an existing Study Arm
        And The pencil button is clicked
        And User continues to next step of study structure stepper
        When The first arm data is edited
        And User saves and exits study structure stepper
        Then User searches for 'Test Arm 1 Update'
        And The new study arm data is updated in the table

    Scenario: [Create][Mandatory fields] User must not be able to provide value less than zero for number of participants
        And The pencil button is clicked
        And User continues to next step of study structure stepper
        When Number of subjects of study arm 1 is set to '-10'
        And User saves and exits study structure stepper
        Then Validation message "Value can't be less than 0" is displayed

    Scenario: [Create][Mandatory fields] User must not be able to create a Study Arm without Study Arm Type
        Given The pencil button is clicked
        And User continues to next step of study structure stepper
        When The study arm type is cleared
        And User defocus from field
        Then The validation message appears for empty arm type

    Scenario: [Create][Mandatory fields] User must not be able to create a Study Arm without Arm Name
        Given The pencil button is clicked
        And User continues to next step of study structure stepper
        When The study arm name is cleared
        Then The validation message appears for empty arm name
    
    Scenario: [Create][Mandatory fields] User must not be able to create a Study Arm without Arm Short Name
        Given The pencil button is clicked
        And User continues to next step of study structure stepper
        When The study arm short name is cleared
        Then The validation message appears for empty arm short name

    Scenario: [Create][Mandatory fields] User must not be able to use text longer than 20 characters for the Study Arm Arm Code field in the Study Arms form
        And The pencil button is clicked
        And User continues to next step of study structure stepper
        When The study arm code is updated to exceed 20 characters
        Then The validation message appears for arm code 'This field must not exceed 20 characters'

    Scenario: [Create][Positive case] User must be able to add multiple study arms
        Given User intercepts the study arms list request
        And The pencil button is clicked
        And User continues to next step of study structure stepper
        And User waits for the study arms list request
        When Users clicks button to add another arm
        When New arm is added with type 'Observational Arm'
        When Users clicks button to add another arm
        And New arm is added with type 'Investigational Arm'
        And User saves and exits study structure stepper
        And User waits for 3 seconds
        Then User searches for 'Test Arm 1 Update'
        And User searches for 'Test Arm 2'
        And User searches for 'Test Arm 3'

    Scenario: [Create][Uniqueness check][Name] User must not be able to create two Arms within one study using the same Arm name
        Given The pencil button is clicked
        And User continues to next step of study structure stepper
        When Arm name of study arm 1 is set to 'UV1'
        And Arm name of study arm 2 is set to 'UV1'
        And User saves and exits study structure stepper
        Then The pop up displays "Value 'UV1' in field Arm name is not unique for the study."

    Scenario: [Create][Uniqueness check][Short Name] User must not be able to create two Arms within one study using the same Arm short name
        Given The pencil button is clicked
        And User continues to next step of study structure stepper
        When Arm short name of study arm 1 is set to 'UV2'
        And Arm short name of study arm 2 is set to 'UV2'
        And User saves and exits study structure stepper
        Then The pop up displays "Value 'UV2' in field Arm short name is not unique for the study."

    Scenario: [Create][Uniqueness check][Randomisation group] User must not be able to create two Arms within one study using the same Arm randomisation group
        Given The pencil button is clicked
        And User continues to next step of study structure stepper
        When Arm randomisation group of study arm 1 is set to 'UV3'
        And Arm randomisation group of study arm 2 is set to 'UV3'
        And User saves and exits study structure stepper
        Then The pop up displays "Value 'UV3' in field Arm Randomization code is not unique for the study."

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyArms' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyArms' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyArms' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyArms' file is downloaded in 'xlsx' format

    @manual_test
    Scenario: User must be presented with the warning message when deleting Study Arm
        Given The study arm related to study branch arm and study design cell exists
        And The Study Arm is found
        When The 'Delete' option is clicked from the three dot menu list
        Then The warning message appears 'Removing this Study Arm will remove all related Study Cells and Branches'

    @manual_test
    Scenario: User must be able to delete all related items to Study Arm when Study arm is removed
        Given User selects study with id 'CDISC DEV-9876'
        And The study arm related to study branch arm and study design cell exists
        When The the study arm related to those elements is removed
        Then That study arm no longer exists
        And Related study design cells are deleted
        And Related study branch arms are deleted

    @manual_test
    Scenario: User must be able to read change history of output
        Given The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames