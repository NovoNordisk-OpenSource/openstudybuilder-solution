@REQ_ID:1070686
@neodash_tests
Feature: Activity Metadata Check - Full Path of Missing Items

    As a user, I want to search the full path of activities with missing items
    and see the the activity details

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Activity Metadata Check' page is opened

    Scenario: User must be able to view different metrics in Full Path of Missing Items
        Given The neoDash 'Full Path of Missing Items' tab is selected
        Then The following set of neoDash reports are displayed
            | report              |
            | Search              |
            | Activity Class      |
            | Activity Subclass   |
            | Results (Mandatory) |
            | Results (All)       |

    Scenario: User must be able to select activity class and subclass to view results
        Given The neoDash 'Full Path of Missing Items' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'NumericFindings' from the 'activityinstanceclassvalue_name_subtype' dropdown
        Then The panel 'Results (Mandatory)' displays 'Activity Group'
        And The panel 'Results (Mandatory)' displays 'NumericFindings'
