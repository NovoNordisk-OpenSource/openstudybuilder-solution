@REQ_ID:1070683

Feature: Library - Concepts - Activities - Non Standard variables - Search
    As a user, I want to manage every Activities in the Concepts Library

    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/non-standard-variables' page is opened
        When [API] The feature flag 'nsvs_library' is enabled
    
    Scenario: [Test data] User must be able to create a test data to test non-standard variables Filtering
        And The plus button is clicked
        When Non-standard variable activity instance class value is selected as 'Interventions'
        And Non-standard variable code is set as random value
        And Non-standard variable label is set as 'NSV E2E label'
        And Non-standard variable role is selected as 'Identifier'
        And Non-standard variable data type is selected as 'CT Term'
        And Non-standard variable length is set as '30'
        And Form save button is clicked
        And The plus button is clicked
        When Non-standard variable activity instance class value is selected as 'Interventions'
        And Non-standard variable code is set as random value
        And Non-standard variable label is set as 'NSV E2E label'
        And Non-standard variable role is selected as 'Identifier'
        And Non-standard variable data type is selected as 'CT Term'
        And Non-standard variable length is set as '30'
        And Form save button is clicked

    Scenario: [Table][Search][Postive case] User must be able to search created activity
        And User sets status filter to 'draft'
        Then Non-standard variable is searched by code and found
        And User searches for 'NSV E2E label'
        Then More than one result is found 

    Scenario: [Table][Search][Negative case] User must be able to search not existing activity and table will correctly filtered
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity
        When User sets status filter to 'draft'
        When User searches for 'nsv e2e label' without checking the result
        And More than one result is found