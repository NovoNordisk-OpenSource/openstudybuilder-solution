@REQ_ID:987736
Feature: Studies - List deleted studies

	Background: User must be logged in
		Given The user is logged in

    Scenario:  User must be able to navigate to the Study List page
        Given The '/studies' page is opened
        When The 'Study List' button is clicked
        And The 'Deleted studies' tab is selected
        Then The current URL is '/studies/select_or_add_study/deleted'

    Scenario: User must be able to see the page table with correct columns
        Given The '/studies/select_or_add_study/deleted' page is opened
        Then A table is visible with following headers
            | headers            |
            | Clinical Programme |
            | Project ID         |
            | Project name       |
            | Brand name         |
            | Study number       |
            | Study ID           |
            | Study acronym      |
            | Study title        |
            | Status             |
            | Modified           |
            | Modified by        |

    Scenario: User must be able to use column selection option
        Given The '/studies/select_or_add_study/deleted' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column
    
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