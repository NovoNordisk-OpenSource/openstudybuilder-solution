@REQ_ID:1070683
@neodash_tests
Feature: Activity Library Dashboard - Search Activity Instance

    As a user, I want to browse activities and activity instances in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in

    Scenario: User must be able to view activity instances
        Given The neoDash 'Search Activity Instance' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                 |
            | Select Activity Instance (One or More) |
            | Detail of Selected Instances           |

    Scenario: User must be able to select one or more activites instances and get a detailed view of the instances selected
        Given The neoDash 'Search Activity Instance' tab is selected
        When The user selects a value from the 'ai' dropdown
        Then The 'Detail of Selected Instances' report returns a value
