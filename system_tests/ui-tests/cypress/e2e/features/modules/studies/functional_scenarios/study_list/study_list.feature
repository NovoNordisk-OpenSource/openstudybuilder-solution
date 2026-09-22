@REQ_ID:987736
Feature: Studies - Study List - Study List

    Background: User must be logged in
        Given The user is logged in

    @smoke_test
    Scenario:  [Navigation] User must be able to navigate to the Study List page
        Given The '/studies' page is opened
        When The 'Study List' button is clicked
        Then The current URL is '/studies/select_or_add_study/active'

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the page table with correct columns
        Given The '/studies/select_or_add_study/active' page is opened
        Then A table is visible with following headers
            | headers                 |
            | Clinical Programme      |
            | Project ID              |
            | Project name            |
            | Study number            |
            | Study ID                |
            | Subpart ID              |
            | Study acronym           |
            | Study subpart acronym   |
            | Study title             |
            | Latest version          |
            | Latest locked version   |
            | Latest released version |
            | Status                  |
            | Modified                |
            | Modified by             |

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The '/studies/select_or_add_study/active' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The '/studies/select_or_add_study/active' page is opened
        When The user filters study list by field '<name>'

        Examples:
            | name                  |
            | Clinical Programme    |
            | Project ID            |
            | Project name          |
            | Study number          |
            | Study ID              |
            #| Subpart ID            |
            | Study acronym         |
            #| Study subpart acronym |
            | Study title           |
            | Status                |
            #| Modified by           |


    @smoke_test
    Scenario: [Table][Search][Positive case] User must be able to search in table
        Given The '/studies/select_or_add_study/active' page is opened
        And User waits for the table
        Then User searches for 'CDISC DEV'

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The '/studies/select_or_add_study/active' page is opened
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The 'Studies' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The '/studies/select_or_add_study/active' page is opened
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The 'Studies' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The '/studies/select_or_add_study/active' page is opened
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The 'Studies' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The '/studies/select_or_add_study/active' page is opened
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The 'Studies' file is downloaded in 'xlsx' format

    @manual_test
    Scenario: User must be able to use table pagination
        Given The '/studies/select_or_add_study/active' page is opened
        When The user selects next page on the table
        Then The data is presented accordingly to table page

    @smoke_test
    Scenario: [Create][Positive case] User must be able to add a new Study
        Given The '/studies/select_or_add_study/active' page is opened
        And User waits for the table
        And The Add Study button is clicked
        When New study project id, study number and study acronym are filled in
        And User intercepts all available studies request
        And Form save button is clicked
        Then The pop up displays 'Study added'
        And User waits for available studies request
        And Study is found
        Then The study is visible within the table