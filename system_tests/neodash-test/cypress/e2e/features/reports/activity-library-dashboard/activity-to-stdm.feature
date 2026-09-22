@REQ_ID:1070683
@neodash_tests
Feature: Activity Library Dashboard - Activity to SDTM

    As a user, I want to browse activities and activity instances in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in

    Scenario: User must be able to view activites mapped to SDTM
        Given The neoDash 'Activity to SDTM' tab is selected
        Then The following set of neoDash reports are displayed
            | report                      |
            | Limit List of Activities    |
            | Select Activity Instance    |
            | Select SDTM Version         |
            | Activity Mapped to SDTM     |
            | Activity with Links to SDTM |

    Scenario: User must be able to select an activity instance and SDTM version and see how the activity instance items are mapped to SDTMIG variables
        Given The neoDash 'Activity to SDTM' tab is selected
        When The user selects a value from the 'ActivitySubGroupValue name' dropdown
        And The user selects a value in the 'Select Activity Instance' table
        And The user selects a value in the 'Select SDTM Version' table
        Then The 'Activity Mapped to SDTM' report returns a value
        And The 'Activity with Links to SDTM' report returns a value
