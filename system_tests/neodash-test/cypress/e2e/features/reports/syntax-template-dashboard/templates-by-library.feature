@REQ_ID:1070684
@REQ_ID:1070686
@neodash_tests
Feature: Syntax Template Dashboard - Templates by Library

    As a user, I want to be able to view and filter template instantiations

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Syntax Template Dashboard' page is opened

    Scenario: User must be able to view the number of templates by library
        Given The neoDash 'Templates by Library' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                      |
            | Template Instantiations by Type and Library |