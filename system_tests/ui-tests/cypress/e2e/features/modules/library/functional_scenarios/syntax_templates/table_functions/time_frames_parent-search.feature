@REQ_ID:1070684

Feature: Library - Syntax Templates - Parent Timeframes - Search
    As a user I want to navigate to each page

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Test data] Data for search tests is created
        When [API] Search Test - Create first timeframe template
        And [API] Search Test - Create second timeframe template

    @smoke_test
    Scenario: [Table][Search][Postive case] User must be able to search created Timeframe template
        Given The '/library/timeframe_templates/parent' page is opened
        Then Timeframe template created via API is searched for
        And The existing item is searched for by partial name
        Then More than one result is found

    Scenario: [Table][Search][Negative case] User must be able to search not existing Timeframe and table will correctly filtered
        Given The '/library/timeframe_templates/parent' page is opened
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity
        Given The '/library/timeframe_templates/parent' page is opened
        When The existing item in search by lowercased name
        And More than one result is found

    Scenario: [Table][Search][Filtering] User must be able to combine search and filters to narrow table results
        Given The '/library/timeframe_templates/parent' page is opened
        And The user filters table by status 'Final'
        And The existing item is searched for by partial name
        And The item is not found and table is correctly filtered
        And The user changes status filter value to 'Draft'
        And The existing item is searched for by partial name
        Then More than one result is found