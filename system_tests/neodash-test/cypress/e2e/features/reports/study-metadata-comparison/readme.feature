@REQ_ID:1741028

Feature: Study Metadata Comparison - ReadMe

    As a user, I want to compare metadata for two studies or two study versions in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Study Metadata Comparison' page is opened

    Scenario: User must be able to read a small guide of the report
        Given The neoDash 'ReadMe' tab is selected
        Then The following set of neoDash reports are displayed
            | report |
            | Guide  |
