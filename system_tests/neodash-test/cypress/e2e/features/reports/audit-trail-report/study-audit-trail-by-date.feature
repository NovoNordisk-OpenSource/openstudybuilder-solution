@REQ_ID:1370753
@neodash_tests

Feature: Audit Trail Report - Study Audit Trail by Date

    As a user, I want to keep track of database changes made to studis in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Audit Trail Report' page is opened
        And The neoDash 'Study Audit Trail by Date' tab is selected

    Scenario: User must be able to view audit trail entries in Study 
        Then The following set of neoDash reports are displayed
            | report                                      |
            | Select User                                 |
            | Select Start Date                           |
            | Select End Date                             |
            | Actions Table                               |
            | Select Study UID                            |
            | Action ID                                   |
            | Actions Table                               |
            | Change Visualisation                        |

    Scenario: User must be able to select an audit trail timeframe to view all study actions performed during that time
        When The user types '2025-01-01' in the Select Start Date field
        Then The panel 'Actions Table' should display data
        When The user selects the Action ID
        Then The Study Action ID card should not be empty
        And The panel 'Field Value Changes' should display data