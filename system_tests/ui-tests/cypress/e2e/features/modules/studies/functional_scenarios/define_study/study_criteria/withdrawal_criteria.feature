@REQ_ID:1074256
Feature: Studies - Define Study - Study Criteria - Withdrawal Criteria

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And User selects study with id 'CDISC DEV-9876'

    @smoke_test
    Scenario: [Navigaion] User must be able to navigate to the Withdrawal Criteria page
        Given The '/studies' page is opened
        When The 'Study Criteria' submenu is clicked in the 'Define Study' section
        And The 'Withdrawal Criteria' tab is selected
        Then The current URL is '/selection_criteria/Withdrawal%20Criteria'
    
    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the page table with correct columns
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        Then A table is visible with following headers
            | headers             |
            | #                   |
            | Withdrawal Criteria |
            | Guidance text       |
            | Key criteria        |
            | Modified            |
            | Modified by         |

    Scenario: [Online help] User must be able to read online help for the page
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        And The online help button is clicked
        Then The online help panel shows 'General' panel with content "Study eligibility criteria as would be described in the protocol"
        Then The online help panel shows 'Study Criteria' panel with content "Follow the tabs to define the different criteria applicable for the study"

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    @unstable_disabled
    Scenario: User must be able to create the Withdrawal Criteria based on existing criteria template
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        And User clicks add study criteria button
        When User selects to create criteria from template
        And Form continue button is clicked
        When The 'withdrawal' criteria is copied from existing template
        And Form save button is clicked
        Then The 'withdrawal' criteria created from existing template is visible within the table with correct data

    @smoke_test
    Scenario: [Create][From scratch] User must be able to create the Withdrawal Criteria from scratch
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        When User clicks add study criteria button
        And User selects to create criteria from scratch
        And Form continue button is clicked
        When The 'withdrawal' criteria is created from scratch
        And Form continue button is clicked
        And Form save button is clicked
        Then The study criteria is searched and found

    Scenario: [Create][From studies][By Id] User must be able to select Withdrawal Criteria from other existing studies by study id
        And User selects study with id 'CDISC DEV-0'
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        When User clicks add study criteria button
        And User selects to create criteria from scratch
        And Form continue button is clicked
        When The 'withdrawal' criteria is created from scratch
        And Form continue button is clicked
        And Form save button is clicked
        Then The study criteria is searched and found
        And User selects study with id 'CDISC DEV-9876'
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        When User clicks add study criteria button
        And User selects to create criteria from study
        And User selects study 'CDISC DEV-0'
        And Form continue button is clicked
        And The 'Withdrawal' criteria from test study is copied
        And Form save button is clicked
        And User waits for the table
        Then The study criteria is searched and found

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCriteria' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCriteria' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCriteria' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCriteria' file is downloaded in 'xlsx' format

    @pending_implementation
    Scenario: User must be able to select Withdrawal Criteria from other existing studies by study acronym
        Given The page 'selection_criteria/Withdrawal%20Criteria' is opened for current study
        When User clicks add study criteria button
        And User selects to create criteria from study
        And Form continue button is clicked
        And The test study for 'Withdrawal' criteria copying is selected by study acronym
        And The 'Withdrawal' criteria from test study is copied
        And Form save button is clicked
        And User waits for the table
        Then The study criteria is searched and found