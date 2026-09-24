@REQ_ID:987736
Feature: Studies - Study List - Deleted Studies
	Background: User must be logged in
		Given The user is logged in

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the Study List page
        Given The '/studies' page is opened
        When The 'Study List' button is clicked
        And The 'Deleted studies' tab is selected
        Then The current URL is '/studies/select_or_add_study/deleted'

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the page table with correct columns
        Given The '/studies/select_or_add_study/deleted' page is opened
        Then A table is visible with following headers
            | headers            |
            | Clinical Programme |
            | Project ID         |
            | Project name       |
            | Study number       |
            | Study ID           |
            | Study acronym      |
            | Study title        |
            | Status             |
            | Modified           |
            | Modified by        |

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The '/studies/select_or_add_study/deleted' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The '/studies/select_or_add_study/deleted' page is opened
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The 'Studies' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The '/studies/select_or_add_study/deleted' page is opened
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The 'Studies' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The '/studies/select_or_add_study/deleted' page is opened
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The 'Studies' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The '/studies/select_or_add_study/deleted' page is opened
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The 'Studies' file is downloaded in 'xlsx' format
    
    @pending_implementation
    Scenario: User must be able to see value changes for the study core attributes for deleted studies on history page
        Given the '/studies/select_or_add_study/deleted' page is opened
        When The 'View Page History' is clicked
        Then A pop-up window is opened and display a table with following headers
            | column | header              |
            | 1      | Clinical programme  |
            | 2      | Project ID          |
            | 3      | Project name        |
            | 4      | Study ID            |
            | 5      | Stuby number        |
            | 6      | Study acronym       |
            | 7      | Modified            |
            | 8      | Modified by         |