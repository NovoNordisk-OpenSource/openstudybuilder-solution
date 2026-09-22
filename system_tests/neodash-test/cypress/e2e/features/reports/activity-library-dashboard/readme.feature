@REQ_ID:1070683
@neodash_tests
Feature: Activity Library Dashboard - ReadMe

    As a user, I want to get an overview of the number of activities and instances in the library

    Background: User must be logged into the dashboard
        Given The user is logged in

    Scenario: User must be able to view basic statistics of the activities
        Given The neoDash 'ReadMe' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                                   |
            | Guide                                                    |
            | Groupings of Activities                                  |
            | Number of Activities and Instances                       |
            | Number of Activities and Instances by Group and Subgroup |
            | Number of Activities and Instances by Type and Subtype   |



