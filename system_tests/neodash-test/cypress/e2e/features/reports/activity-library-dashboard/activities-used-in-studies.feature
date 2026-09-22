@REQ_ID:1070683
@neodash_tests
Feature: Activity Library Dashboard - Activities used in Studies

    As a user, I want to browse activities and activity instances in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in

    Scenario: User must be able to view activites used in studies
        Given The neoDash 'Activities Used in Studies' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                           |
            | Select One or More Activities                    |
            | Studies Using Selected Activities - Select Study |
            | Operator                                         |
            | Show Only Latest                                 |
            | Study Selection                                  |
            | Study Description                                |
            | Objectives/Endpoints                             |
            | SoA (Activity Instances)                         |
            
    Scenario: User must be able to select one or more activites and get a list of studies in which they have been included in the SoA
        Given The neoDash 'Activities Used in Studies' tab is selected
        When The user selects 'Albumin' from the 'study_activity' dropdown
        And The user selects one study by clicking the Trial ID in the table 'Studies Using Selected Activities - Select Study'
        Then The 'Study Selection' report returns a value
        And The 'Study Description' report returns a value
        And The 'Objectives/Endpoints' report returns a value
        And The 'SoA (Activity Instances)' report returns a value


