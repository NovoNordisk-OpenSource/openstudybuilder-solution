@REQ_ID:2866190
Feature: Studies - Study Subparts

    Background: User must be logged in
        Given The user is logged in

    @pending_implementation
    Scenario:  User must be able to navigate to the Study Subparts page
        Given A test study is selected
        Given The '/studies' page is opened
        When The 'Study' submenu is clicked in the 'Manage Studies' section
        And The 'Study Subparts' tab is selected
        Then The current URL is '/studies/Study_000001/study_status/subparts'

    Scenario: User must be able to see the Study Subpart table with correct columns
        Given A test study is selected
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        And A table is visible with following headers
            | headers         |
            | Study ID        |
            | Study acronym   |
            | Subpart acronym |
            | Description     |
            | Modified        |
            | Modified by     |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to export the data in CSV format
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        And The user exports the data in 'CSV' format
        Then The 'StudySubparts' file is downloaded in 'csv' format

    Scenario: User must be able to export the data in JSON format
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        And The user exports the data in 'JSON' format
        Then The 'StudySubparts' file is downloaded in 'json' format

    Scenario: User must be able to export the data in XML format
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        And The user exports the data in 'XML' format
        Then The 'StudySubparts' file is downloaded in 'xml' format

    Scenario: User must be able to export the data in EXCEL format
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        And The user exports the data in 'EXCEL' format
        Then The 'StudySubparts' file is downloaded in 'xlsx' format

    @pending_implementation
    Scenario: User must be able to add an existing study as a study subpart to a parent study
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        When The 'Add Study Subpart' is selected from an existing study
        Then The selected exsisting study is added as a study subpart and visible within the table with correct data

    @pending_implementation
    Scenario: User must be able to create a new study as a study subpart to a parent study
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        When The 'Add Study Subpart' is selected creating a new study
        Then The newly created study is added as a study subpart and visible within the table with correct data

    @pending_implementation
    Scenario: User must be able to edit a study subpart to a parent study
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        When The 'Edit' action is selected for a Study Subpart
        Then The edited study subpart is visible within the table with correct data

    @pending_implementation
    Scenario: User must be able to change order of a study subpart to a parent study
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        When The 'Change order' action is selected for a Study Subpart
        Then The changed order of study subparts is visible within the table with correct data

    @pending_implementation
    Scenario: User must be able to remove a Study Suppart from a study
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        When The Study Subpart is removed
        Then The Study Subpart is no longer available

    @pending_implementation
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        When The user opens the page level version history
        Then The user is presented with version history of the output containing timestamp and username

    @pending_implementation
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/study_status/subparts' page is opened
        When The user clicks on History for particular row
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames
