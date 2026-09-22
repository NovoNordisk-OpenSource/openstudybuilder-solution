@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Epochs

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    @smoke_test
    Scenario: [Navigation] Opening the page
        Given The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Epochs' tab is selected
        Then The current URL is '/study_structure/epochs'

    Scenario: [Table][Options] Page structure
        Given The page 'study_structure/epochs' is opened for current study
        Then A table is visible with following options
            | options     |
            | select-rows |

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the Study Visit table with following columns
        Given The page 'study_structure/epochs' is opened for current study
        And A table is visible with following headers
            | headers          |
            | #                |
            | Epoch name       |
            | Epoch type       |
            | Epoch subtype    |
            | Start rule       |
            | End rule         |
            | Description      |
            | Number of visits |
            | Assigned colour  |

    Scenario: [Online help] User must be able to read online help for the page
        Given The page 'study_structure/epochs' is opened for current study
        And The online help button is clicked
        Then The online help panel shows 'Study Epochs' panel with content "The study epoch is a period of time that serves a purpose in the trial, e.g. Screening, Treatment, Follow-up. The purpose of ex. a Treatment epoch will be to expose subjects to a treatment."

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The page 'study_structure/epochs' is opened for current study
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    @smoke_test
    Scenario: [Create][Positve case] User must be able to add a Study Epoch
        Given The page 'study_structure/epochs' is opened for current study
        When User click create epoch button
        And User continues to next step of study structure stepper
        And User sets epoch 'type' as 'Post Treatment'
        And User sets epoch 'subtype' as 'Elimination'
        And User sets epoch 'start' rule as 'D10'
        And User sets epoch 'end' rule as 'D99'
        And User sets epoch description
        And User intercepts epochs data
        And User continues to next step of study structure stepper
        And User waits for epochs data
        When The form is no longer available
        And Study Epoch is found
        Then The added Epoch name, type 'Post Treatment' and subtype 'Elimination' is visible in the table
        And The Epoch name start rule 'D10' and end rule 'D99' are visible in the table
        And The Epoch description is visible in the table

    Scenario: [Actions][Edit] User must be able to edit a Study Epoch
        Given The page 'study_structure/epochs' is opened for current study
        And Study Epoch is found
        And The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And User sets epoch 'start' rule as 'D22'
        And User sets epoch 'end' rule as 'D33'
        And User updates epoch description
        And User intercepts epochs data
        And User continues to next step of study structure stepper
        And User waits for epochs data
        When The form is no longer available
        And Study Epoch is found
        Then The Epoch name start rule 'D22' and end rule 'D33' are visible in the table
        And The Epoch description is visible in the table

    Scenario: [Actions][Edit][Fields check] User must not be able to edit the Epoch Type and Subtype
        Given The page 'study_structure/epochs' is opened for current study
        And Study Epoch is found
        When The 'Edit' option is clicked from the three dot menu list
        Then The epoch type is disabled
        And The epoch subtype is disabled

    Scenario: [Actions][Delete] User must be able to delete the Study Epoch and all related study design cells
        Given The page 'study_structure/epochs' is opened for current study
        And Study Epoch is found
        And The 'Delete' option is clicked from the three dot menu list
        Then Study Epoch is not available

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The page 'study_structure/epochs' is opened for current study
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyEpochs' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The page 'study_structure/epochs' is opened for current study
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyEpochs' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The page 'study_structure/epochs' is opened for current study
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyEpochs' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The page 'study_structure/epochs' is opened for current study
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyEpochs' file is downloaded in 'xlsx' format

    @manual_test
    Scenario: User must not be able to delete the Study Epoch with study visits related
        Given The page 'study_structure/epochs' is opened for current study
        And The Study Epoch with Study Vist exists
        When The delete button is clicked for given Study Epoch
        Then User is presented with message 'Cannot remove Epochs with visist defined'

    @manual_test
    Scenario: User must be able to read change history of output
        Given The page 'study_structure/epochs' is opened for current study
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The page 'study_structure/epochs' is opened for current study
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames