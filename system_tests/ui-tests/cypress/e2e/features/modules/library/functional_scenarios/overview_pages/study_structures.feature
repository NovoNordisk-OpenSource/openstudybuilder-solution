@REQ_ID:2866926
Feature: Library - Overview Pages - Study Structures

    As a user, I want to see the overview page of Study Structure for existing studies

    Background: User must be logged in
        Given The user is logged in

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the Study Structures page in the Library Overview Pages
        Given The '/library' page is opened
        When The 'Study Structures' submenu is clicked in the 'Overview Pages' section
        Then The current URL is '/library/overviews/study_structures'

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
        Given The '/library/overviews/study_structures' page is opened
        Then A table is visible with following headers
            | headers               |
            | Arms                  |
            | Pre-treatment epochs  |
            | Treatment epochs      |
            | Post-treatment epochs |
            | No-treatment epochs   |
            | No-treatment elements |
            | Treatment elements    |
            | Cohorts?              |
            | Study ID(s)           |

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given User intercepts study structures requests
        And The '/library/overviews/study_structures' page is opened
        And User waits for study structures requests
        When The user filters field '<name>'
        Then The slow table is filtered correctly

        Examples:
            | name                  |
            | Arms                  |
            | Pre-treatment epochs  |
            | Treatment epochs      |
            | Post-treatment epochs |
            | No-treatment epochs   |
            | No-treatment elements |
            | Treatment elements    |
            | Cohorts?              |
            | Study ID(s)           |
