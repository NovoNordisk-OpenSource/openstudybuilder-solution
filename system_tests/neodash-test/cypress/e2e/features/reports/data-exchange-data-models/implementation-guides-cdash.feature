@REQ_ID:NEW
@neodash_tests
Feature: Data Exchange Data Models - Implementation Guides - CDASH

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Data Exchange Data Models' page is opened

    Scenario: User must be able to view model entries in Implementation Guides - CDASH
        Given The neoDash 'Implementation Guides - CDASH' tab is selected
        Then The following set of neoDash reports are displayed
            | report           |
            | Available Guides |
            | Version          |
            | Datasets         |
            | Scenario         |