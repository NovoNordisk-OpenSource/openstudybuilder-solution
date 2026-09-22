@REQ_ID:1070684

Feature: Library - Syntax Templates - Withdrawal Criteria - Search
    As a user I want to navigate to each page

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Test data] Data for search tests is created
        Given [API] Search Test - Create first 'Withdrawal' criteria template
        And [API] Search Test - Create second 'Withdrawal' criteria template

    @smoke_test
    Scenario: [Table][Search][Postive case] User must be able to search created Withdrawal Criteria template
        Given The 'library/criteria_templates/Withdrawal/parent' page is opened
        When User intercept getCriteria request
        And User awaits for the getCriteria request to finish
        And The criteria is found
        And The existing item is searched for by partial name
        Then More than one result is found

    Scenario: [Table][Search][Negative case] User must be able to search not existing Withdrawal Criteria and table will correctly filtered
        Given The 'library/criteria_templates/Withdrawal/parent' page is opened
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity
        Given The 'library/criteria_templates/Withdrawal/parent' page is opened
        When The existing item in search by lowercased name
        Then More than one result is found

    Scenario: [Table][Search][Filtering] User must be able to combine search and filters to narrow table results
        Given The 'library/criteria_templates/Withdrawal/parent' page is opened
        When The user adds status to filters
        And The user changes status filter value to 'Final'
        And The existing item is searched for by partial name
        And The item is not found and table is correctly filtered
        And The user changes status filter value to 'Draft'
        And The existing item is searched for by partial name
        Then More than one result is found 