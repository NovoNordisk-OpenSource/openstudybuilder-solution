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

    @skip_on_prv_val
    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The '/library/overviews/study_structures' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

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

    @manual_test
    # to be implemented later after API test complete
    Scenario: The grouping functionality must be able to work effectively on the study structure table
        Given The '/library/overviews/study_structures' page is opened
        When The study structure is the same across multiple studies
        Then The study structure should be listed only once, with all studies metioned in the StudyID column
