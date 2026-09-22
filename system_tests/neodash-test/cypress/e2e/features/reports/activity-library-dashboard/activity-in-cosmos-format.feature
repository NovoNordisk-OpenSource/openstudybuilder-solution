@REQ_ID:1070683
@neodash_tests
Feature: Activity Library Dashboard - Activity in COSMOS Format

    As a user, I want to browse activities and activity instances in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in

    Scenario: User must be able to view activites in CDISC COSMOS format
        Given The neoDash 'Activity in COSMOS Format' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                         |
            | Limit List (Search Activity Subgroup)          |
            | Select Activity                                |
            | Selected Activity                              |
            | Activity as COSMOS BC Concept                  |
            | Select CDISC SDTM Version                      |
            | Select Instance                                |
            | Activity as COSMOS SDTM Dataset Specialization |

    Scenario: User must be able to select an activity and view it in CDISC COSMOS BC Concept yaml format
        Given The neoDash 'Activity in COSMOS Format' tab is selected
        When The user selects a value from the 'ActivitySubGroupValue' dropdown
        And The user selects a value in the 'Select Activity' table
        And The user selects a value in the 'Select CDISC SDTM Version' table
        And The user selects a value in the 'Select Instance' table
        Then The Activity as COSMOS BC Concept displays the activity in a yaml format
        And The Activity as COSMOS SDTM datasetspecialization displays the activity in a yaml format
