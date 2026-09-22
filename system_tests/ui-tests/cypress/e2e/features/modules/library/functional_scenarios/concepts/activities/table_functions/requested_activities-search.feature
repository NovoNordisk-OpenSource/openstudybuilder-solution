@REQ_ID:1070683

Feature: Library - Concepts - Activities - Requested Activities - Search
    As a user, I want to manage Requested Activities in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/requested-activities' page is opened

    @smoke_test
    Scenario: [Table][Search][Postive case] User must be able to search created activity request
        Given [API] First requested activity for search test is created
        And [API] Second requested activity for search test is created
        When One activity request is found after performing full name search
        And The existing item is searched for by partial name
        Then More than one result is found

    Scenario: [Table][Search][Negative case] User must be able to search not existing activity request and table will correctly filtered
        Given The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: [Table][Search][Filtering] User must be able to combine search and filters to narrow table results
        Given User adds column 'Status' to filters
        When The user changes status filter value to 'Final'
        And The existing item is searched for by partial name
        And The item is not found and table is correctly filtered
        And The user changes status filter value to 'Draft'
        And The existing item is searched for by partial name
        Then More than one result is found

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity
        Given The existing item in search by lowercased name
        And More than one result is found
