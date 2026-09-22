@REQ_ID:NEW
@neodash_tests
Feature: Data Exchange Data Models - Catalogues

    As a user, I want to be able to explore Data Exchange Data Models

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Data Exchange Data Models' page is opened

    Scenario: User must be able view model overviews in Catalogues
        Given The neoDash 'Catalogues' tab is selected
        Then The following set of neoDash reports are displayed
            | no | report                                                |
            | 0  | Physical Data Model - Excluding Catalogue for Clarity |
            | 1  | Catalogues, Models and Versions                       |