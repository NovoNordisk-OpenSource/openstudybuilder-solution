@REQ_ID:1074254
Feature: Studies - Study Epochs

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: Opening the page
        Given The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Epochs' tab is selected
        Then The current URL is '/studies/Study_000001/study_structure/epochs'

    Scenario: Page structure
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add select boxes to table to allow selection of rows for export |

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

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    Scenario: User must be able to add a Study Epoch
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        When A new Study Epoch is added
        Then The new Study Epoch is available within the table

    Scenario: User must be able to edit a Study Epoch
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        And The Study Epoch exists in the Study
        When The Study Epoch is edited
        Then The edited Study Epoch with updated values is available within the table

    Scenario: User must not be able to edit the Epoch Type and Subtype
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        And The Study Epoch exists in the Study
        When The Epoch edit form is opened
        Then The Type and Subtype fields are disabled

    Scenario: User must be able to delete the Study Epoch and all related study design cells
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        And The Study Epoch exists in the Study
        When The Study Epoch is deleted
        Then The Epoch is not visible in the table

    Scenario: User must be able to export the data in CSV format
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        And The user exports the data in 'CSV' format
        Then The study specific 'StudyEpochs' file is downloaded in 'csv' format

    Scenario: User must be able to export the data in JSON format
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        And The user exports the data in 'JSON' format
        Then The study specific 'StudyEpochs' file is downloaded in 'json' format

    Scenario: User must be able to export the data in XML format
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        And The user exports the data in 'XML' format
        Then The study specific 'StudyEpochs' file is downloaded in 'xml' format

    Scenario: User must be able to export the data in EXCEL format
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        And The user exports the data in 'EXCEL' format
        Then The study specific 'StudyEpochs' file is downloaded in 'xlsx' format

    @manual_test
    Scenario: User must not be able to delete the Study Epoch with study visits related
        Given The '/studies/Study_000001/study_structure/epochs' page is opened
        And The Study Epoch with Study Vist exists
        When The delete button is clicked for given Study Epoch
        Then User is presented with message 'Cannot remove Epochs with visist defined'

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '//studies/Study_000001/study_structure/epochs' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The '//studies/Study_000001/study_structure/epochs' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames