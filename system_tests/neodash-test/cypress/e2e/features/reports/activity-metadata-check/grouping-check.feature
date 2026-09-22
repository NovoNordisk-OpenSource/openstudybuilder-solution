@REQ_ID:1070686
@neodash_tests
Feature: Activity Metadata Check - Grouping Check

    As a user, I want to view activities and their grouped activity instances

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Activity Metadata Check' page is opened

    Scenario: User must be able to view different metrics in Grouping Check
        Given The neoDash 'Grouping Check' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                               |
            | List of Activity Instances Attached to \"Requested\" |
            | Number of Activities Without Grouping                |
            | Number of Activity Instances Without Grouping        |
            | Selected Activity List                               |
            | Activities Without Grouping                          |
            | Activity Instances Without Grouping                  |
            | Activities and their Activity Instances              |
            | Outdated Activities                                  |
            | Activities with Outdated Activity Instances Only     |

    Scenario: User must be able to view number of activities and activity instances with missing grouping
        When The neoDash 'Grouping Check' tab is selected
        Then The panel 'Number of Activity Instances Without Grouping' displays '0'
        And The panel 'Activities Without Grouping' displays 'No Activities without Groupings.'
        And The panel 'Activity Instances Without Grouping' displays 'No Activity Instances without Groupings.'
        And The panel 'Outdated Activities' displays 'No Outdated Activities.'
        And The panel 'Activities with Outdated Activity Instances Only' displays 'No Activities with Only Outdated Activity Instances.'

    Scenario: User must be able to view activities and their groupings of activity instances
        Given The neoDash 'Activity Lib (search Bottom-Up)' tab is selected
        When The user selects 'Albumin' from the 'Select one or more Activities' dropdown
        Given The neoDash 'Grouping Check' tab is selected
        Then The 'Activities and their Activity Instances' report returns a value
