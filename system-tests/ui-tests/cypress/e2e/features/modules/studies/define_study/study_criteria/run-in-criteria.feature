@REQ_ID:1074256
Feature: Studies - Study Run-in Criteria

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And A test study is selected

    Scenario: User must be able to navigate to the Run-in Criteria page
        Given The '/studies' page is opened
        When The 'Study Criteria' submenu is clicked in the 'Define Study' section
        And The 'Run-in Criteria' tab is selected
        Then The current URL is '/studies/Study_000001/selection_criteria/Run-in%20Criteria'

    Scenario: User must be able to see the page table with correct columns
        Given The '/studies/Study_000001/selection_criteria/Run-in%20Criteria' page is opened
        Then A table is visible with following headers
            | headers         |
            | #               |
            | Run-in Criteria |
            | Guidance text   |
            | Key criteria    |
            | Modified        |
            | Modified by     |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/selection_criteria/Run-in%20Criteria' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    @unstable_disabled
    Scenario: User must be able to create the Run-in Criteria based on existing criteria template
        Given The '/studies/Study_000001/selection_criteria/Run-in%20Criteria' page is opened
        When The 'runIn' criteria is copied from existing template
        Then The 'runIn' criteria created from existing template is visible within the table with correct data

    Scenario: User must be able to create the Run-in Criteria from scratch
        Given The '/studies/Study_000001/selection_criteria/Run-in%20Criteria' page is opened
        When The 'runIn' criteria is created from scratch
        Then The 'runIn' criteria created from new template is visible within the table with correct data

    Scenario: User must be able to select Run-in Criteria from other existing studies by study id
        Given The '/studies/Study_000002/selection_criteria/Run-in%20Criteria' page is opened
        When The 'Run-In' criteria is created from studies
        And The test study for 'Run-In' criteria copying is selected by study id
        And The 'Run-in' criteria from test study is copied
        Then The 'Run-in Criteria' copied from test study is visible within the table with correct data

    @pending_implementation
    Scenario: User must be able to select Run-in Criteria from other existing studies by study acronym
        Given The '/studies/Study_000002/selection_criteria/Run-in%20Criteria' page is opened
        When The 'Run-In' criteria is created from studies
        And The test study for 'Run-In' criteria copying is selected by study acronym
        And The 'Run-in' criteria from test study is copied
        Then The 'Run-in Criteria' copied from test study is visible within the table with correct data