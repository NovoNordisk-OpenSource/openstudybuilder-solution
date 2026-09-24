@REQ_ID:1741028
@neodash_tests
Feature: Activity Instance Export

    As a user, I want to export activity instance items in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Activity Instance Export' page is opened

    Scenario: User must be able to view the Activity Instance Export report panels
        Given The neoDash 'New page' tab is selected
        Then The following set of neoDash reports are displayed
            | report                    |
            | Activity items            |
            | Select Activity Instances |

    Scenario: User must be able to select an activity instance from the ActivityInstanceValue name dropdown and view its items
        Given The neoDash 'New page' tab is selected
        When The user selects an activity instance from the 'ActivityInstanceValue name' dropdown
        Then The Activity items table returns values
