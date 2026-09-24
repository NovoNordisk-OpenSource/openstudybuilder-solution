@REQ_ID:1070683
Feature: Library - Concepts - Activities - Activities by grouping
    As a user, I want to manage every Activities by Grouping items in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in

    @manual_test
    Scenario: User must be able to exspand display of rows for the Group/subgroup/activity column
        Given The '/library/activities/activities-by-grouping' page is opened
        When The '>' button is clicked
        Then the row exspand to display all nested rows

    @manual_test @BUG_ID:2770368
    Scenario:[BUG] Activities by Grouping should present correct group/subgroup combinations
        Given The '/library/activities/activities-by-grouping' page is opened
        Then The groups and subgroups are correctly presented for each item