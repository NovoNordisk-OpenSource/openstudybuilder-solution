@REQ_ID:1370753
@neodash_tests
Feature: Audit Trail Report - Study Audit Trail by Version

    As a user, I want to keep track of database changes made to studies in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Audit Trail Report' page is opened
        And The neoDash 'Study Audit Trail by Version' tab is selected

    Scenario: User must be able to view audit trail entries in Study
        Then The following set of neoDash reports are displayed
            | report                        |
            | Select Study UID              |
            | Select Study Min Date Version |
            | Select Study Max Date Version |
            | Select User                   |
            | Selections Table              |
            | Action ID                     |
            | Actions Table on              |
            | Change Visualisation          |
            | Field Value Changes           |

    Scenario: User must be able to select the time period and an action ID to view all study actions performed during that time
        When The user selects the first Study Min Date Version
        And The user selects the first Study Max Date Version
        Then The panel 'Actions Table on' should display data
        When The user selects the Action ID
        Then The Study Action ID card should not be empty
        And The panel 'Field Value Changes' should not contain errors
