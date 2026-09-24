@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Groups - Search
    As a user, I want to manage every Activity Groups in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in
        When [API] First activity group for search test is created
        And [API] Second activity group for search test is created
        And The '/library/activities/activity-groups' page is opened
        And User sets status filter to 'draft'
    
    @smoke_test
    Scenario: [Table][Search][Postive case] User must be able to search created group
        Then Activity group is searched for and found
        And The existing item is searched for by partial name
        Then More than one result is found 

    Scenario: [Table][Search][Negative case] User must be able to search not existing group and table will correctly filtered
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: [Table][Search][Filtering] User must be able to combine search and filters to narrow table results
        When User sets status filter to 'final'
        And The existing item is searched for by partial name
        And The item is not found and table is correctly filtered
        And User sets status filter to 'draft'
        And The existing item is searched for by partial name
        Then More than one result is found

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity
        When The existing item in search by lowercased name
        And More than one result is found