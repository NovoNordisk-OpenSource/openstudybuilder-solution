@REQ_ID:1070674
@neodash_tests

Feature: Codelist/Terms History - ReadMe

    As a user, I want to browse codelists and their versions of terms in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Codelist / Terms history' page is opened

    Scenario: User must be able to read a small guide of the Codelist/Terms History
        Given The neoDash 'ReadMe' tab is selected
        Then The following set of neoDash reports are displayed
            | report |
            | Guide  |


