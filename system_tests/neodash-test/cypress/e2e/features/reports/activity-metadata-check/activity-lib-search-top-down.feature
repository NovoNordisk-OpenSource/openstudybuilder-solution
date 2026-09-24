@REQ_ID:1070686
@neodash_tests
Feature: Activity Metadata Check - Activity Lib (search top-down)

    As a user, I want to search activities based on class, subclass, group and subgroup
    and see the the activity details

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Activity Metadata Check' page is opened

    Scenario: User must be able to view different metrics in Activity Lib (search top-down)
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
            | Activity in Tabular Format -                                             |
            | Activity as a Graph View (Logical View) -                                |
            | Activity as a Graph View (Physical View) -                               |
            | Select Instance -                                                        |
            | Instance Detail -                                                        |
            | Instance (Logical View) -                                                |

    Scenario: User must be able to search for activities based on class and subclass
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'NumericFinding' from the 'activityinstanceclassvalue_name_subtype' dropdown
        And The user resets the 'activitygroupvalue_name' selector to blank
        And The user resets the 'activitysubgroupvalue_name' selector to blank
        And The histogram is presenting the groups and activities

    Scenario: User must be able to search for activities based on group and subgroup
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'NumericFinding' from the 'activityinstanceclassvalue_name_subtype' dropdown
        And The user selects 'Laboratory Assessments' from the 'activitygroupvalue_name' dropdown
        And The user selects 'Coagulation Parameters' from the 'activitysubgroupvalue_name' dropdown
        And The histogram displays number of instances per activity
            | activity                           | instances |
            | Prothrombin Intl. Normalized Ratio | 1         |
            | Prothrombin Tim                    | 1         |

    Scenario: User must be able to display activity detail when selecting an activity
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'NumericFinding' from the 'activityinstanceclassvalue_name_subtype' dropdown
        And The user resets the 'activitygroupvalue_name' selector to blank
        And The user resets the 'activitysubgroupvalue_name' selector to blank
        And The user selects a value in the 'List of Activities' table
        Then The Activity in tabular format table returns a value

    Scenario: User must be able to display activity instance detail when selecting an activity instance for an activity
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'NumericFinding' from the 'activityinstanceclassvalue_name_subtype' dropdown
        And The user selects 'Laboratory Assessments' from the 'activitygroupvalue_name' dropdown
        And The user selects 'Biochemistry' from the 'activitysubgroupvalue_name' dropdown
        And The user selects a value in the 'List of Activities' table
        Then The Activity in tabular format table returns a value
        When The user selects a value in the 'Select Instance' table
        Then The Instance detail table returns a value
