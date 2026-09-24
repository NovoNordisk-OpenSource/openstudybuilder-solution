@REQ_ID:1070683
@neodash_tests
Feature: Activity Library Dashboard - Activity Lib (Search Bottom-Up)

    As a user, I want to browse activities and activity instances in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in

    Scenario: User must be able to view groupings of activites and their instances
        Given The neoDash 'Activity Lib (Search Bottom-Up)' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                    |
            | Search Activity                           |
            | Number of Groups for Selected Activity    |
            | Number of Subgroups for Selected Activity |
            | Groups for Selected Activity/Activities   |
            | Activity Instance Detail                  |

    Scenario: User must be able to select activities and display their groups and sub-groups
        Given The neoDash 'Activity Lib (Search Bottom-Up)' tab is selected
        When The user selects a value from the 'Select one or more Activities' dropdown
        Then The 'Number of Groups for Selected Activity' report returns a value
        And The 'Number of Subgroups for Selected Activity' report returns a value
        And The 'Groups for Selected Activity/Activities' report returns a value

    Scenario: From the selected activities, the user must be able to select an activity instance and display its details
        Given The neoDash 'Activity Lib (Search Bottom-Up)' tab is selected
        When The user selects a value from the 'Select one or more Activities' dropdown
        And The user click SHOWN DETAIL in the 'Groups for Selected Activity/Activities' table
        Then The 'Activity Instance Detail' report returns a value



