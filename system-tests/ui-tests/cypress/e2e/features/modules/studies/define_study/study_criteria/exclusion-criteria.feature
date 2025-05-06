@REQ_ID:1074256
Feature: Studies - Study Exclusion Criteria

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And A test study is selected

    Scenario: User must be able to navigate to the Exclusion Criteria page
        Given The '/studies' page is opened
        When The 'Study Criteria' submenu is clicked in the 'Define Study' section
        And The 'Exclusion Criteria' tab is selected
        Then The current URL is '/studies/Study_000001/selection_criteria/Exclusion%20Criteria'

    Scenario: User must be able to see the page table with correct columns
        Given The '/studies/Study_000001/selection_criteria/Exclusion%20Criteria' page is opened
        Then A table is visible with following headers
            | headers            |
            | #                  |
            | Exclusion Criteria |
            | Guidance text      |
            | Key criteria       |
            | Modified           |
            | Modified by        |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/selection_criteria/Exclusion%20Criteria' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    @unstable_disabled
    Scenario: User must be able to create the Exclusion Criteria based on existing criteria template
        Given The '/studies/Study_000001/selection_criteria/Exclusion%20Criteria' page is opened
        When The 'exclusion' criteria is copied from existing template
        Then The 'exclusion' criteria created from existing template is visible within the table with correct data

    Scenario: User must be able to create the Exclusion Criteria from scratch
        Given The '/studies/Study_000001/selection_criteria/Exclusion%20Criteria' page is opened
        When The 'exclusion' criteria is created from scratch
        Then The 'exclusion' criteria created from new template is visible within the table with correct data

    Scenario: User must be able to select Exclusion Criteria from other existing studies by study id
        Given The '/studies/Study_000002/selection_criteria/Exclusion%20Criteria' page is opened
        When The 'Exclusion' criteria is created from studies
        And The test study for 'Exclusion' criteria copying is selected by study id
        And The 'Exclusion' criteria from test study is copied
        Then The 'Exclusion Criteria' copied from test study is visible within the table with correct data

    Scenario: User must be able to export the data in CSV format
        Given The '/studies/Study_000002/selection_criteria/Exclusion%20Criteria' page is opened
        And The user exports the data in 'CSV' format
        Then The study specific 'StudyCriteria' file is downloaded in 'csv' format

    Scenario: User must be able to export the data in JSON format
        Given The '/studies/Study_000002/selection_criteria/Exclusion%20Criteria' page is opened
        And The user exports the data in 'JSON' format
        Then The study specific 'StudyCriteria' file is downloaded in 'json' format

    Scenario: User must be able to export the data in XML format
        Given The '/studies/Study_000002/selection_criteria/Exclusion%20Criteria' page is opened
        And The user exports the data in 'XML' format
        Then The study specific 'StudyCriteria' file is downloaded in 'xml' format

    Scenario: User must be able to export the data in EXCEL format
        Given The '/studies/Study_000002/selection_criteria/Exclusion%20Criteria' page is opened
        And The user exports the data in 'EXCEL' format
        Then The study specific 'StudyCriteria' file is downloaded in 'xlsx' format

    @pending_implementation
    Scenario: User must be able to select Exclusion Criteria from other existing studies by study acronym
        Given The '/studies/Study_000002/selection_criteria/Exclusion%20Criteria' page is opened
        When The 'Exclusion' criteria is created from studies
        And The test study for 'Exclusion' criteria copying is selected by study acronym
        And The 'Exclusion' criteria from test study is copied
        Then The 'Exclusion Criteria' copied from test study is visible within the table with correct data