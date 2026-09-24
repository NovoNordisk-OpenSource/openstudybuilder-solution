@REQ_ID:1370753
@neodash_tests

Feature: Audit Trail Report Dashboard - ReadMe

    As a user, I want to keep track of database changes made to libraries in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Audit Trail Report' page is opened

    Scenario: User must be able to read a small guide of the Audit Trail Report
        Given The neoDash 'ReadMe' tab is selected
        Then The following set of neoDash reports are displayed
            | report                         |
            | Guide                          |
            | Library Audit Trail User Guide |
            | Study Audit Trail User Guide   |
        And The panel 'Guide' displays 'Introduction'
        And The panel 'Guide' displays 'Report Tabs'
        And The panel 'Library Audit Trail User Guide' displays 'Filter Parameters'
        And The panel 'Library Audit Trail User Guide' displays 'Description of Tables'
        And The panel 'Study Audit Trail User Guide' displays 'Filter Parameters'
        And The panel 'Study Audit Trail User Guide' displays 'Description of Tables'



