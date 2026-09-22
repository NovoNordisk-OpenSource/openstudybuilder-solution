@REQ_ID:2866190
Feature: Studies - Manage Study - Study Subparts

    Background: User must be logged in
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [Test data] User must be able to prepare data before tests exeuction
        Given The page 'study_status/subparts' is opened for current study
        And User waits for the table
        Given User deletes all existing subparts

    Scenario: [Navigation] User must be able to navigate to the Study Subparts page
        Given The '/studies' page is opened
        When The 'Study' submenu is clicked in the 'Manage Study' section
        And The 'Study Subparts' tab is selected
        Then The current URL is '/study_status/subparts'

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the Study Subpart table with correct columns
        Given The page 'study_status/subparts' is opened for current study
        And A table is visible with following headers
            | headers         |
            | Study ID        |
            | Study acronym   |
            | Subpart ID      |
            | Subpart acronym |
            | Description     |
            | Modified        |
            | Modified by     |

    Scenario: [Create] User must be presented with main study acronym when creating subpart
        Given The page 'study_status/subparts' is opened for current study
        When The plus button is clicked
        And Form continue button is clicked
        Then User is presented with main study acronym 'E2E Main Test Study' during subpart creation

    Scenario: [Create] User must not be able to create study subpart without providing study subpart acronym
        Given The page 'study_status/subparts' is opened for current study
        When The plus button is clicked
        And Form continue button is clicked
        And Form save button is clicked
        Then User is presented with warnig that study subpart acronym is required filed

    Scenario: [Create] User must not be able to create study subpart with acronym exceeding 10 characters limit
        Given The page 'study_status/subparts' is opened for current study
        When The plus button is clicked
        And Form continue button is clicked
        And User sets study subpart acronym to value exceeding characters limit
        Then User is presented with warnig that study subpart acronym cannot exceed 10 characters

    Scenario: [Create] User must be able to create study subpart
        Given The page 'study_status/subparts' is opened for current study
        When The plus button is clicked
        And Form continue button is clicked
        And User sets study subpart acronym
        And Form save button is clicked
        Then Study subpart is searched for and found
        And Study subpart data is correctly displayed in the table
        When The '/studies/select_or_add_study/active' page is opened
        Then Study subpart is searched for and found in the study list
        And Study subpart data is correctly displayed in the study list table

    Scenario: [Edit] User must be able to edit study subpart
        Given The page 'study_status/subparts' is opened for current study
        Then Study subpart is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And User updates study subpart acronym
        And Form save button is clicked
        Then Study subpart is searched for and found

    Scenario: [Delete] User must be able to delete study subpart
        Given The page 'study_status/subparts' is opened for current study
        When The plus button is clicked
        And Form continue button is clicked
        And User sets study subpart for removal test
        And Form save button is clicked
        And The pop up displays 'Study subpart created'
        And User waits for 1 seconds
        And Study subpart is searched for and found
        When The 'Remove' option is clicked from the three dot menu list
        And The pop up displays 'Study subpart removed'
        And User waits for 1 seconds
        Then Study subpart is searched for and not found

    @pending_implementation
    Scenario: User must be able to read change history of study subpart
        Given The page 'study_status/subparts' is opened for current study
        When The user opens the page level version history
        Then The user is presented with version history of the output containing timestamp and username

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The page 'study_status/subparts' is opened for current study
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudySubparts' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The page 'study_status/subparts' is opened for current study
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudySubparts' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The page 'study_status/subparts' is opened for current study
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudySubparts' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The page 'study_status/subparts' is opened for current study
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudySubparts' file is downloaded in 'xlsx' format