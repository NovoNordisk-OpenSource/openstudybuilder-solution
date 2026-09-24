@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Groups - Filtering
    As a user, I want to manage every Activity Groups in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activity-groups' page is opened
    
    Scenario: [Table][Filtering][Status selection] User must be able to see that Final status is selected by default
        Then The Final status is selected by default

    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to filter instance depending on its status
        When [API] Activity group in status Draft exists
        When User sets status filter to 'final'
        And Activity group is searched for and not found
        When User sets status filter to 'draft'
        And Activity group is present in first table row
        When User sets status filter to 'retired'
        And The item is not found and table is correctly filtered
        When User sets status filter to 'all'
        And Activity group is present in first table row
        When [API] Activity group is approved
        And The '/library/activities/activity-groups' page is opened
        When User sets status filter to 'draft'
        And Activity group is searched for and not found
        When User sets status filter to 'final'
        And Activity group is present in first table row
        When User sets status filter to 'retired'
        And The item is not found and table is correctly filtered
        When User sets status filter to 'all'
        And Activity group is present in first table row
        And [API] Activity group is inactivated
        And The '/library/activities/activity-groups' page is opened
        When User sets status filter to 'draft'
        And Activity group is searched for and not found
        When User sets status filter to 'retired'
        And Activity group is present in first table row
        When User sets status filter to 'final'
        And The item is not found and table is correctly filtered
        When User sets status filter to 'all'
        And Activity group is present in first table row

    Scenario: [Table][Filtering][Status selection] User must be able to see that status filter is not available after expanding column based filters
        Then The status filter is not available when expanding available filters

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name               |
        | Activity group     |
        | Sentence case name |
        | Abbreviation       |
        | Definition         |
        | Version            |
