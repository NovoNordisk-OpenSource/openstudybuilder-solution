@REQ_ID:1070683 @skip_on_prv_val

Feature: Library - Concepts - Activities - Activities - Filtering
    As a user, I want to manage every Activities in the Concepts Library

    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activities' page is opened

    Scenario: [Table][Filtering][Status selection] User must be able to see that Final status is selected by default
        Then The Final status is selected by default

    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to filter instance depending on its status
        When [API] Activity in status Draft exists
        When User sets status filter to 'final'
        And Activity is searched for and not found
        When User sets status filter to 'draft'
        And Activity is present in first table row
        When User sets status filter to 'retired'
        And The item is not found and table is correctly filtered
        When User sets status filter to 'all'
        And Activity is present in first table row
        When [API] Activity is approved
        And The '/library/activities/activities' page is opened
        When User sets status filter to 'draft'
        And Activity is searched for and not found
        When User sets status filter to 'final'
        And Activity is present in first table row
        When User sets status filter to 'retired'
        And The item is not found and table is correctly filtered
        When User sets status filter to 'all'
        And Activity is present in first table row
        And [API] Activity is inactivated
        And The '/library/activities/activities' page is opened
        When User sets status filter to 'draft'
        And Activity is searched for and not found
        When User sets status filter to 'retired'
        And Activity is present in first table row
        When User sets status filter to 'final'
        And The item is not found and table is correctly filtered
        When User sets status filter to 'all'
        And Activity is present in first table row

    Scenario: [Table][Filtering][Status selection] User must be able to see that status filter is not available after expanding column based filters
        Then The status filter is not available when expanding available filters

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name               |
        | Library            |
        | Activity group     |
        | Activity subgroup  |
        | Activity name      |
        | Sentence case name |
        | Synonyms           |
        | NCI Concept ID     |
        | NCI Concept Name   |
        | Abbreviation       |
        | Data collection    |
        | Legacy usage       |
        | Modified by        |
        | Version            |
