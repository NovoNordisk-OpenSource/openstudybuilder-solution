@REQ_ID:987736
Feature: Studies - Study List

    Background: User must be logged in
        Given The user is logged in

    Scenario:  User must be able to navigate to the Study List page
        Given The '/studies' page is opened
        When The 'Study List' button is clicked
        Then The current URL is '/studies/select_or_add_study/active'

    Scenario: User must be able to see the page table with correct columns
        Given The '/studies/select_or_add_study/active' page is opened
        Then A table is visible with following headers
            | headers               |
            | Clinical Programme    |
            | Project ID            |
            | Project name          |
            | Brand name            |
            | Study number          |
            | Study ID              |
            | Subpart ID            |
            | Sub study ID          |
            | Study acronym         |
            | Study subpart acronym |
            | Study title           |
            | Status                |
            | Modified              |
            | Modified by           |

    Scenario: User must be able to use column selection option
        Given The '/studies/select_or_add_study/active' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario Outline: User must be able to filter the table by text fields
        Given The '/studies/select_or_add_study/active' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
            | name                  |
            | Clinical Programme    |
            | Project ID            |
            | Project name          |
            # | Brand name            |
            | Study number          |
            | Study ID              |
            # | Subpart ID            |
            # | Sub study ID          |
            | Study acronym         |
            # | Study subpart acronym |
            | Study title           |
            | Status                |
            # | Modified              |
            | Modified by           |


    Scenario: User must be able to search in table
        Given The '/studies/select_or_add_study/active' page is opened
        When The user is searching for 'CDISC DEV' value
        Then The results are shown in the table

    @manual_test
    Scenario: User must be able to use table pagination
        Given The '/studies/select_or_add_study/active' page is opened
        When The user selects next page on the table
        Then The data is presented accordingly to table page

    Scenario: User must be able to add a new Study
        Given The '/studies/select_or_add_study/active' page is opened
        When A new study is added
        Then The study is visible within the table