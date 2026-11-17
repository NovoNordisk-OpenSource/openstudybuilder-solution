@REQ_ID:1074256
Feature: Studies - Define Study - Study Design Population

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study design populations.

    Background: User is logged in and the test study is selected
        Given The user is logged in
        And A test study is selected

    @smoke_test
    Scenario: [Navigation] Navigation to Study Design Population page
        Given The '/studies' page is opened
        When The 'Study Population' submenu is clicked in the 'Define Study' section
        And The 'Study Design Population' tab is selected
        Then The current URL is '/population/study-design-populations'

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the Study Design Population table with following columns
        Given The test study '/population/study-design-populations' page is opened
        Then A table is visible with following headers
            | headers     |
            | Group ID    |
            | Name        |
            | Definition  |
            | Notes       |
            | Modified    |
            | Modified by |

    Scenario: [Table][Options] User must be able to see the Study Design Population table with following options
        Given The test study '/population/study-design-populations' page is opened
        Then A table is visible with following options
            | options                         |
            | add-study-design-population     |
            | columns-layout-button           |
            | table-export-button             |
            | search-field                    |
            | History                         |

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The test study '/population/study-design-populations' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @smoke_test
    Scenario: [Create][Positive case] User can add a new Study Design Population
        Given The test study '/population/study-design-populations' page is opened
        And [API] Delete all Study Design Populations within selected study
        When Add study design population button is clicked
        And The study design population form is filled
        And Form save button is clicked
        And The pop up displays 'Study design population added successfully'
        Then The new Study Design Population is visible within the table

    Scenario: [Actions][Edit] User can edit a Study Design Population
        Given The test study '/population/study-design-populations' page is opened
        And [API] The test Study Design Population exists
        And The 'Edit' option is clicked from the three dot menu list
        And User waits for 2 seconds
        And User waits for the table
        When The Study Design Population is edited
        And Form save button is clicked
        And The pop up displays 'Study design population updated successfully'
        And User waits for the table
        Then The updated Study Design Population is visible within the table

    Scenario: [Actions][Delete] Deleting an existing Study Design Population is possible
        Given [API] The test Study Design Population exists
        And The test study '/population/study-design-populations' page is opened
        And The 'Delete' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        And The pop up displays 'Study design population deleted successfully'
        Then The test Study Design Population is no longer available

    @smoke_test
    Scenario: [Criteria linking] User can link and unlink a Study Design Population on an inclusion criterion
        Given [API] The criteria template is created with type 'inclusion'
        And [API] An inclusion criterion is selected into the study
        And [API] A Study Design Population with a known Group ID exists
        And The test study '/selection_criteria/Inclusion%20Criteria' page is opened
        And The criteria table edit mode is activated
        When The Study Design Population is linked to the criterion
        Then The linked Study Design Population Group ID is visible on the criterion row
        When The Study Design Population is unlinked from the criterion
        Then The Study Design Population Group ID is no longer visible on the criterion row
