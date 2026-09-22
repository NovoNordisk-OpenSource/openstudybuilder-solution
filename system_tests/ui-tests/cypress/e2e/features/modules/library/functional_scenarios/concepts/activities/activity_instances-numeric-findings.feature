@REQ_ID:1070683 @skip_on_prv_val
Feature: Library - Concepts - Activities - Activity instances - wizard stepper - numeric findings
    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Feature flag] User must be able to turn on wizard stepper for activity instance creation
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled

    Scenario: [Create][NumericFindings][Existing activity] User must be able to add a new Activity Instance with NumericFindlings as Activity Instance Class
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        Then The Activity Item Classes selection displayed
        And First available value for 'Test Name' is selected
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        Then The Activity Instance Wizard Stepper 'PARAM/PARAMCD' page is displayed
        And Automatically assigned activity instance name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Data specification' page is displayed
        And User intercepts activity instance creation request with strict_mode verification
        And Form save button is clicked
        And User waits for activity instance creation request with strict_mode verification
        And The form is no longer available
        Then The current URL is '/overview'
        And Correct instance overview page is displayed

    Scenario: [Create][NumericFindings][New activity][Overview Page] User must be able to view all selected values in the overview page (instance class, datadomain, category, subcategory, name submission, code submission, unit dimension, standard unit)
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
        And The 'ALCOHOL HABITS' is selected from the Data category field
        And The 'ACUTE KIDNEY INJURY CONDITIONS' is selected from the Data SubCategory field
        Then The Activity Item Classes selection displayed
        And For activity item class 'Test Name' value '1,3-Beta-D-Glucan' is searched and selected
        And Selected Code Submission value is saved
        And For activity item class 'Unit dimension' value 'BMI' is searched and selected
        And For activity item class 'Standardised unit' value 'kg/m2' is selected
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
        Then Activity Item Class 'finding_category' with value 'Alcohol habits' and type 'CT Term' is present in the table
        And Activity Item Class 'finding_subcategory' with value 'AKI Conditions' and type 'Text' is present in the table
        And Activity Item Class 'unit_dimension' with value 'BMI' and type 'CT Term' is present in the table
        And Activity Item Class 'standard_unit' with value 'kg/m2' and type 'CT Term' is present in the table
        And Activity Item Class 'test_name' with value '1,3-Beta-D-Glucan Measurement' and type 'CT Term' is present in the table
        And Activity Item Class 'test_code' with value '1,3-Beta-D-Glucan Measurement' and type 'CT Term' is present in the table

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
        