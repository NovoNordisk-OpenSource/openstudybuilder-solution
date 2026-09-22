@REQ_ID:1070683

Feature: Library - Concepts - Activities - Requested Activities - Filtering
    As a user, I want to manage Requested Activities in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The '/library/activities/requested-activities' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                           |
        | Activity group                 |
        | Activity subgroup              |
        | Activity                       |
        | Sentence case name             |
        | Abbreviation                   |
        | Definition                     |
        | Rationale for activity request |
        | Modified by                    |
        | Version                        |