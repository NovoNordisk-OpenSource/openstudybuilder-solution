@REQ_ID:TBD
Feature: Library - Code Lists - Trial Summary Parameters - General Functionality

    As a user, I want to verify that the Trial Summary Parameters generic functions work correctly.

    Background: User must be logged in
        Given The user is logged in

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the Trial Summary Parameters page
        Given The '/library' page is opened
        When The 'Trial Summary Parameters' submenu is clicked in the 'Code Lists' section
        Then The current URL is 'library/trial_summary_parameters'

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table
        Given The '/library/trial_summary_parameters' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Pagination] User must be able to use table pagination
        Given The '/library/trial_summary_parameters' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Search] User must be able to search for a Trial Summary Parameter
        Given The '/library/trial_summary_parameters' page is opened
        When The user searches for a term in the search field
        Then The table is filtered to show only matching results

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The '/library/trial_summary_parameters' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
            | name               |
            | Library            |
            | Sponsor name       |
            | CT name            |
            | Code               |
            | Concept ID         |
            | Required level     |
            | Name status        |
            | Attributes status  |

    # Scenario: [Export][CSV] User must be able to export the main table data in CSV format
    #     Given The '/library/trial_summary_parameters' page is opened
    #     When User clicks table export button
    #     And User selects 'CSV' format to export the table content
    #     And Action is confirmed by clicking continue
    #     Then The 'TrialSummaryParameters' file is downloaded in 'csv' format

    # Scenario: [Export][Json] User must be able to export the main table data in JSON format
    #     Given The '/library/trial_summary_parameters' page is opened
    #     When User clicks table export button
    #     And User selects 'JSON' format to export the table content
    #     And Action is confirmed by clicking continue
    #     Then The 'TrialSummaryParameters' file is downloaded in 'json' format

    # Scenario: [Export][Xml] User must be able to export the main table data in XML format
    #     Given The '/library/trial_summary_parameters' page is opened
    #     When User clicks table export button
    #     And User selects 'XML' format to export the table content
    #     And Action is confirmed by clicking continue
    #     Then The 'TrialSummaryParameters' file is downloaded in 'xml' format

    # Scenario: [Export][Excel] User must be able to export the main table data in Excel format
    #     Given The '/library/trial_summary_parameters' page is opened
    #     When User clicks table export button
    #     And User selects 'EXCEL' format to export the table content
    #     And Action is confirmed by clicking continue
    #     Then The 'TrialSummaryParameters' file is downloaded in 'xlsx' format

    Scenario: [Actions][CT values history] User must be able to view CT values history of a Trial Summary Parameter
        Given The '/library/trial_summary_parameters' page is opened
        When The 'Open CT history' option is clicked from the three dot menu list
        Then The version history window is displayed

    Scenario: [Actions][Sponsor values history] User must be able to view Sponsor values history of a Trial Summary Parameter
        Given The '/library/trial_summary_parameters' page is opened
        When The 'Open sponsor history' option is clicked from the three dot menu list
        Then The version history window is displayed

    Scenario: [Overview][History][CT values] User must be able to view CT values history from the overview page
        Given The Trial Summary Parameter details page is opened
        When The CT values history button is clicked
        Then The version history window is displayed
        And The history contains timestamps and usernames

    Scenario: [Overview][History][Sponsor values] User must be able to view Sponsor values history from the overview page
        Given The Trial Summary Parameter details page is opened
        When The sponsor values history button is clicked
        Then The version history window is displayed
        And The history contains timestamps and usernames
