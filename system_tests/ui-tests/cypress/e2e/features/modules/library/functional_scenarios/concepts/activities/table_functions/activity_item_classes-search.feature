@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Item Classes - Search
    As a user, I want to manage every Activities in the Concepts Library

    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activity-item-classes' page is opened

    @smoke_test
    Scenario: [Table][Search][Postive case] User must be able to search created activity instance
        Then Activity Item class is searched for and found
        And Activity Item class is searched for by partial name
        Then More than one result is found

    Scenario: [Table][Search][Negative case] User must be able to search not existing group and table will correctly filtered
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: [Table][Search][Filtering] User must be able to combine search and filters to narrow table results
        And The user filters table by status 'Final'
        And Activity Item class is searched for by partial name
        Then More than one result is found