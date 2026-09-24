@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Groups - Filtering
    As a user, I want to manage every Activity Groups in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activity-subgroups' page is opened
    
    Scenario: [Table][Filtering][Status selection] User must be able to see that Final status is selected by default
        Then The Final status is selected by default

    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to filter instance depending on its status
        When [API] Activity subgroup in status Draft exists
        When User sets status filter to 'final'
        And Activity subgroup is searched for and not found
        When User sets status filter to 'draft'
        And Activity subgroup is present in first table row
        When User sets status filter to 'retired'
        And The item is not found and table is correctly filtered
        When User sets status filter to 'all'
        And Activity subgroup is present in first table row
        When [API] Activity subgroup is approved
        And The '/library/activities/activity-subgroups' page is opened
        When User sets status filter to 'draft'
        And Activity subgroup is searched for and not found
        When User sets status filter to 'final'
        And Activity subgroup is present in first table row
        When User sets status filter to 'retired'
        And The item is not found and table is correctly filtered
        When User sets status filter to 'all'
        And Activity subgroup is present in first table row
        And [API] Activity subgroup is inactivated
        And The '/library/activities/activity-subgroups' page is opened
        When User sets status filter to 'draft'
        And Activity subgroup is searched for and not found
        When User sets status filter to 'retired'
        And Activity subgroup is present in first table row
        When User sets status filter to 'final'
        And The item is not found and table is correctly filtered
        When User sets status filter to 'all'
        And Activity subgroup is present in first table row

    Scenario: [Table][Filtering][Status selection] User must be able to see that status filter is not available after expanding column based filters
        Then The status filter is not available when expanding available filters

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given User sets status filter to 'all'
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                  |
        | Activity subgroup     |
        | Sentence case name    |
        | Abbreviation          |
        | Definition            |
        | Version               |
