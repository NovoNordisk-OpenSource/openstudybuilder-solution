@REQ_ID:NEW
@neodash_tests
Feature: Data Exchange Data Models - Implementation Guides - ADaM

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Data Exchange Data Models' page is opened

    Scenario: User must be able to view model entries in Implementation Guides - ADaM
        Given The neoDash 'Implementation Guides - ADaM' tab is selected
        Then The following set of neoDash reports are displayed
            | report           |
            | Available Guides |
            | Version          |
            | Data Structures  |
            | Variable Sets    |
            | Variables        |