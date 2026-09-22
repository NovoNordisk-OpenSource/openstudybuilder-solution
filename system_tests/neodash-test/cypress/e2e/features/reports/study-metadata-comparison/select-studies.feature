@REQ_ID:1741028
Feature: Study Metadata Compare - Select Studies

    As a user, I want to compare metadata for two studies or two study versions in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Study Metadata Comparison' page is opened

    Scenario: User must be able to view the selected studies report panels
        Given The neoDash 'Select studies' tab is selected
        Then The following set of neoDash reports are displayed
            | report                |
            | Show Only Differences |
            | Select Project(s)     |
            | Select Base           |
            | Select Compare        |
            | Selected Studies      |

    Scenario: User must be able to selects two different studies to compare
        Given The neoDash 'Select studies' tab is selected
        When The user selects the first project in the Select Projects panel
        And The user selects the first study in the Select Base table
        And The user selects a different study in the Select Compare table
        Then The Selected Studies panel displays two different studies

    @manual_test
    Scenario: User must be able to select two studies to compare
        Given The neoDash 'Select studies' tab is selected
        When The user selects version 1 in the Select Base panel
        And The user selects version 1.1 in the Select Compare panel
        Then The following selection is displayed in the Selected Studies panel
            | row     | base                | compare             |
            | TrialID | CDISC DEV-1111      | CDISC DEV-1111      |
            | Date    | 2024-05-08T02:14:18 | 2024-05-08T02:14:36 |
            | Version | 1                   | 1.1                 |
            | Status  | LOCKED              | DRAFT               |
