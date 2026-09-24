@REQ_ID:1070684
@REQ_ID:1070686
@neodash_tests
Feature: Syntax Template Dashboard - Readme

    As a user, I want to be able to explore different syntax templates

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Syntax Template Dashboard' page is opened

    Scenario: User must be able to read a small guide of the Syntax Template
        Given The neoDash 'ReadMe' tab is selected
        Then The following set of neoDash reports are displayed
            | report |
            | Guide  |










