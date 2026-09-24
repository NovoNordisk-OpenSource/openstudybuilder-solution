@REQ_ID:1370753
@neodash_tests

Feature: Audit Trail Report - Library Audit Trail

    As a user, I want to keep track of database changes made to libraries in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Audit Trail Report' page is opened
        And The neoDash 'Library Audit Trail' tab is selected

    Scenario: User must be able to view audit trail entries in Library Audit Trail tab
        Then The following set of neoDash reports are displayed
            | report                                     |
            | Select User                                |
            | Select Start Date                          |
            | Select End Date                            |
            | Actions Table                              |
            | Action ID                                  |
            | Version/Status Changes                     |
            | Field Value Changes                        |
            | Change Visualisation                       |
            | New Component ID                           |
            | Old Component ID                           |
            | Outbound Relationships per Action ID Table |

    Scenario: User must be able to select an audit trail timeframe to view all library actions performed during that time
        When The user types '2025-01-01' in the Select Start Date field on lib page
        And The user selects the first Action ID from the Actions Table on lib page
        Then The Lib Action ID card should not be empty
        And The panel 'Field Value Changes' should display data
        And The panel 'Old Component ID' should display data
        And The panel 'New Component ID' should display data