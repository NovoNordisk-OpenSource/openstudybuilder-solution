@REQ_ID:1070686
@neodash_tests
Feature: Activity Metadata Check - Readme

    As a user, I want to be able to ensure activity metadata within StudyBuilder is mapped correctly

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Activity Metadata Check' page is opened

    Scenario: User must be able to read a small guide of the Activity Metadata Check
        Given The neoDash 'ReadMe' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                        |
            | Guide                                         |
            | List of Missing Mandatory Items for Instances |
            | Grouping Check                                |
            | Missing Grouping                              |
