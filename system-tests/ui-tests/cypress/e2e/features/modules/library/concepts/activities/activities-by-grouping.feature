@REQ_ID:1070683
Feature: Library - Activities by Grouping

    As a user, I want to manage every Activities by Grouping items in the Concepts Library
    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to the Activities by Grouping page
        Given The '/library' page is opened
        When The 'Activities' submenu is clicked in the 'Concepts' section
        And The 'Activities by Grouping' tab is selected
        Then The current URL is '/library/activities/activities-by-grouping'

    Scenario: User must be able to see the columns list on the main page as below
        Given The '/library/activities/activities-by-grouping' page is opened
        Then A table is visible with following headers
            | headers                 |
            | Group/subgroup/activity |
            | Modified                |
            | Status                  |
            | Version                 |
            
    @manual_test
    Scenario: User must be able to exspand display of rows for the Group/subgroup/activity column
        Given The '/library/activities/activities-by-grouping' page is opened
        When The '>' button is clicked
        Then the row exspand to display all nested rows
