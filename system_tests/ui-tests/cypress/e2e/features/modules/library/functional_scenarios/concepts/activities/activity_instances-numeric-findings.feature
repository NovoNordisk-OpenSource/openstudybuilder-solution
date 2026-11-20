@REQ_ID:1070683
Feature: Library - Concepts - Activities - Activity instances - wizard stepper - numeric findings
    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Feature flag] User must be able to turn on wizard stepper for activity instance creation
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled

    Scenario: [Create][NumericFindings][New activity][Overview Page] User must be able to view all selected values in the overview page (instance class, datadomain, category, subcategory, name submission, code submission, unit dimension, standard unit)
        And [API] User fetches instace class uid for 'NumericFindings'
        And [API] User fetches test_name and test_code uids for 'LB'
        And [API] User fetches test_name and test_code terms uids for 'LB'
        And [API] Study Activity is created and approved
        And User saves activity name created via API
        And The homepage is opened
        And User sets row page to 10 in the settings menu
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        And Activity created via API is searched for
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        And [API] User fetches type of finding_category
        And [API] User fetches name of category by its submission value 'ALCOHOL HABITS'
        And The 'ALCOHOL HABITS' is selected from the Data category field
        And [API] User fetches type of finding_subcategory
        And [API] User fetches name of subcategory by its submission value 'ACUTE KIDNEY INJURY CONDITIONS'
        And The 'ACUTE KIDNEY INJURY CONDITIONS' is selected from the Data SubCategory field
        Then The Activity Item Classes selection displayed
        And [API] User fetches type of test_name
        And [API] User fetches name of test_name by its submission value '1,3-Beta-D-Glucan'
        And For activity item class 'Test Name' value '1,3-Beta-D-Glucan' is searched and selected
        And Selected Code Submission value is saved
        And [API] User fetches type of test_code
        And [API] User fetches name of test_code by its submission value
        And [API] User fetches type of unit_dimension
        And Activity item class unit_dimension value is set with sumbission value 'BMI'
        And [API] User fetches type of standard_unit
        And Activity item class standard_unit value is set to 'kg/m2'
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request 
        And Automatically assigned activity instance name is saved
        And Form continue button is clicked
        And User intecepts activity groupings request
        And User intecepts activity items request
        And User intercepts activity instance creation request with strict_mode verification
        And Form save button is clicked
        And User waits for activity instance creation request with strict_mode verification
        And The form is no longer available
        Then The current URL is '/overview'
        And Correct instance overview page is displayed
        And User waits for activity groupings request
        And User waits for activity items request
        Then Category is present in the table with selected values
        And Subcategory is present in the table with selected values
        And Unit dimension Item Class is present in the table with selected values
        And Standard Unit Item Class is present in the table with selected values
        And Test Name Item Class is present in the table with selected values
        And Test Code Item Class is present in the table with selected values

    Scenario: [Cancel][Creation] User must be able to cancel activity instance creation
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        When First activity is selected from the activity list
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        And First available value for 'Test Name' is selected
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        And Customize toggle is turn on
        And The instance name is changed to custom one
        And Form continue button is clicked
        When Fullscreen wizard is closed by clicking cancel button
        And Action is confirmed by clicking continue
        Then The form is no longer available
        And Activity instance is not visible in table

    Scenario: [Create][NumericFindings][Activity Item Class Flags] User must be able to see only filtered values based on selected Activity Instance Class and Data Domain 
        And [API] Study Activity is created and approved
        And User saves activity name created via API
        And The homepage is opened
        And User sets row page to 10 in the settings menu
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        And Activity created via API is searched for
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'MK' is selected from the Activity instance domain field
        Then The Activity Item Classes selection displayed
        And First available value for 'Test Name' is selected
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        And Add activity item class button is clicked
        Then Only values for Numeric Findings and MK as data domain are displayed for Activity Item Class selection in the Step 3
        Then Value 'Directionality' is selected for 0 Activity item class field
        And Form continue button is clicked
        And Add activity item class button is clicked
        Then Only values for Numeric Findings and MK as data domain are displayed for Activity Item Class selection in the Step 4
        