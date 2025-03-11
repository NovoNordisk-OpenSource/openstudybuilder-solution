@REQ_ID:1070683

Feature: Library - Activities Filters

    As a user, I want to manage every Activities in the Concepts Library

    Background: User must be logged in
        Given The user is logged in
            
    Scenario Outline: User must be able to filter the table by text fields
        Given The '/library/activities/activities' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name               |
        | Library            |
        | Activity group     |
        | Activity subgroup  |
        | Activity name      |
        | Sentence case name |
        | Abbreviation       |
        | Data collection    |
        | Legacy usage       |
        | Modified by        |
        | Status             |
        | Version            |