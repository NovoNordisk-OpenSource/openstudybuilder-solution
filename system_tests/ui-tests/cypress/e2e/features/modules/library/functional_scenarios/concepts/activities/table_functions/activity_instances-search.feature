@REQ_ID:1070683 @skip_on_prv_val
Feature: Library - Concepts - Activities - Activity Instances - Search
    As a user, I want to manage every Activity Instances in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activity-instances' page is opened
        
    @smoke_test
    Scenario: [Table][Search][Postive case] User must be able to search created activity instance
        When [API] First activity instance for search test is created
        And [API] Second activity instance for search test is created
        And User sets status filter to 'draft'
        Then Activity Instance is searched for and found
        And The existing item is searched for by partial name
        Then More than one result is found

    Scenario: [Table][Search][Negative case] User must be able to search not existing group and table will correctly filtered
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity
        When User sets status filter to 'all'
        And The existing item in search by lowercased name
        Then More than one result is found
