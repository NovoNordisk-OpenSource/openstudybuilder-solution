@REQ_ID:1070683
@neodash_tests
Feature: Activity Library Dashboard - Activity Lib (Search Top-Down)

    As a user, I want to search activities based on class,sub-class, group and sub-group
    and see the the activity details

    Background: User must be logged into the dashboard
        Given The user is logged in

    Scenario: User must be able to view activites and their instances
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                                                   |
            | Guide                                                                    |
            | Activity Class                                                           |
            | Activity Subclass                                                        |
            | Activity Group                                                           |
            | Activity Subgroup                                                        |
            | Number of Activities (Instances per Activity, when Subgroup is Selected) |
            | List of Activities                                                       |
            | Activity in Tabular Format                                               |
            | Activity as a Graph View (Logical View)                                  |
            | Activity as a Graph View (Physical View)                                 |
            | Select Instance                                                          |
            | Instance Detail                                                          |
            | Instance (Logical View)                                                  |

    Scenario: User must be able to view report values for a selected activity and instance
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'NumericFinding' from the 'activityinstanceclassvalue_name_subtype' dropdown
        And The user selects 'Laboratory Assessments' from the 'activitygroupvalue_name' dropdown
        And The user selects 'Urinalysis' from the 'activitysubgroupvalue_name' dropdown
        Then The 'Number of Activities (Instances per Activity, when Subgroup is Selected)' report returns a value
        And The 'List of Activities' report returns a value
        When The user selects a value in the 'List of Activities' table
        And The 'Activity in Tabular Format' report returns a value
        And The 'Select Instance' report returns a value
        When The user selects a value in the 'Select Instance' table
        And The 'Instance Detail' report returns a value

    Scenario: User must be able to search for activities based on class and sub-class
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'NumericFinding' from the 'activityinstanceclassvalue_name_subtype' dropdown
        And The user resets the Activity Group selector to blank
        And The user resets the Activity Sub-group selector to blank
        And The histogram is presenting the groups and activities

    Scenario: User must be able to search for activities based on group and sub-group
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'NumericFinding' from the 'activityinstanceclassvalue_name_subtype' dropdown
        And The user selects 'Laboratory Assessments' from the 'activitygroupvalue_name' dropdown
        And The user selects 'Urinalysis' from the 'activitysubgroupvalue_name' dropdown
        Then The 'Number of Activities (Instances per Activity, when Subgroup is Selected)' report returns a value

    Scenario: User must be able to display activity detail when selecting an activity
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'NumericFinding' from the 'activityinstanceclassvalue_name_subtype' dropdown
        And The user selects 'Laboratory Assessments' from the 'activitygroupvalue_name' dropdown
        And The user resets the Activity Sub-group selector to blank
        And The user selects a value in the 'List of Activities' table
        Then The 'Activity in Tabular Format' report returns a value


