@REQ_ID:1070683

Feature: Library - Concepts - Activities - Non Standard Variables - Filtering
    As a user, I want to manage every Activity Groups in the Concepts Library
    
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
        And Non-standard variable optional input field 'Add algorithm (optional)' is set to 'E2E algorithm'
        And Non-standard variable optional dropdown field 'Default origin type (optional)' is set to 'Other'
        And Non-standard variable optional dropdown field 'Default origin source (optional)' is set to 'Clinical Study Sponsor'
        And Non-standard variable optional input field 'Definition (optional)' is set to 'E2E definition'
        And Non-standard variable optional input field 'Derivation rule (optional)' is set to 'E2E derivation'
        And Non-standard variable optional input field 'NCI Code (optional)' is set to 'E2E nci code'
        And Non-standard variable optional input field 'NCI Concept Name (optional)' is set to 'E2E nci name'
        And Form save button is clicked

    Scenario: [Table][Filtering][Status selection] User must be able to see that All status is selected by default
        Then The All status is selected by default

    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to filter instance depending on its status
        When User sets status filter to 'final'
        And Non-standard variable is searched by code and not found
        When User sets status filter to 'draft'
        And Non-standard variable is searched by code and found
        When User sets status filter to 'retired'
        And Non-standard variable is searched by code and not found
        When User sets status filter to 'all'
        And Non-standard variable is searched by code and found
        And The 'Approve' option is clicked from the three dot menu list
        When User sets status filter to 'draft'
        And Non-standard variable is searched by code and not found
        When User sets status filter to 'final'
        And Non-standard variable is searched by code and found
        When User sets status filter to 'retired'
        And Non-standard variable is searched by code and not found
        When User sets status filter to 'all'
        And Non-standard variable is searched by code and found
        And The 'Inactivate' option is clicked from the three dot menu list
        When User sets status filter to 'draft'
        And Non-standard variable is searched by code and not found
        When User sets status filter to 'retired'
        And Non-standard variable is searched by code and found
        When User sets status filter to 'final'
        And Non-standard variable is searched by code and not found
        When User sets status filter to 'all'
        And Non-standard variable is searched by code and found

    Scenario: [Table][Filtering][Status selection] User must be able to see that status filter is not available after expanding column based filters
        Then The status filter is not available when expanding available filters

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name               |
        | NSV code           |
        | NSV label          |
        | Name               |
        | NCI code           |
        | NCI concept name   |
        | Multiple           |
        | CDISC defined      |
        | Semantic data type |
        | NSV XML data type  |
        | Length             |
        #| Codelist codes     |
        | Origin type        |
        | Origin source      |
        | Algorithm          |
        | Definition         |
        #| Modified           |
        #| Modified by        |
        | Version            |
