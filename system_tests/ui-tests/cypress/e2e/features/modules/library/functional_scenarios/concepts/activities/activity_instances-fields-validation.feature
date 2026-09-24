@REQ_ID:1070683 @skip_on_prv_val
Feature: Library - Concepts - Activities - Activity instances - wizard stepper - fields validations
    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Feature flag] User must be able to turn on wizard stepper for activity instance creation
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled

    Scenario: [Create][Mandatory fields] User must not be able to continue without selecting activity
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        And Form continue button is clicked
        Then The pop up displays 'You must select an activity from the list'
        And The Activity Instance Wizard Stepper 'Select activity' page is displayed

    Scenario: [Create][Mandatory fields] User must not be able to continue without selecting instance class and data domain
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When First activity is selected from the activity list
        And Form continue button is clicked
        And Form continue button is clicked
        And Required field 'Activity instance class' is highlighted as required
        And Required field 'Data domain' is highlighted as required
        And The Activity Instance Wizard Stepper 'Required' page is displayed

    Scenario: [Create][Mandatory fields] User must not be able to continue without selecting name_submission_value, code_submission_value, unit_dimension and standard_unit for Numeric Findings instance class
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When First activity is selected from the activity list
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        And Form continue button is clicked
        Then Value for required field 'Test Name' is highlighted as required
        And Value for required field 'Test Code' is highlighted as required
        And Value for required field 'Unit dimension' is highlighted as required
        And Value for required field 'Standardised unit' is highlighted as required
        And The Activity Instance Wizard Stepper 'Required' page is displayed

    Scenario: [Create][Mandatory fields] User must be able to see that test_code is automatically populated after selecting test_name
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When First activity is selected from the activity list
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        Then The test_code value is not selected
        And First available value for 'Test Name' is selected
        Then The test_code value is automatically populated

    Scenario: [Create][Mandatory fields] User must be able to continue without selecting data cateogry and subcategory
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When First activity is selected from the activity list
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        And First available value for 'Test Name' is selected
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And Form continue button is clicked
        And The Activity Instance Wizard Stepper 'PARAM/PARAMCD' page is displayed

    Scenario: [Create][Mandatory fields] User must not be able to continue without providing Activity Instance name, case name, topic code, ADaM parameter 
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When First activity is selected from the activity list
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        And First available value for 'Test Name' is selected
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And Form continue button is clicked
        And Customize toggle is turn on
        And Activity Instance Data field 'Activity instance name' is cleared
        And Activity Instance Data field 'Sentence case name' is cleared
        And Activity Instance Data field 'Topic code' is cleared
        And Activity Instance Data field 'ADaM parameter' is cleared
        Then Required field 'Activity instance name' is highlighted as required
        And Required field 'Sentence case name' is highlighted as required
        And Required field 'Topic code' is highlighted as required
        And Required field 'ADaM parameter' is highlighted as required
        Then Form continue button is clicked
        And The Activity Instance Wizard Stepper 'PARAM/PARAMCD' page is displayed

    Scenario: [Create][Mandatory fields] User must be able to continue without providing NCI Preferred Name and NCI Code
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
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
        And Activity Instance Data field 'NCI preferred name' is cleared
        And Activity Instance Data field 'NCI Code' is cleared
        Then Form continue button is clicked
        And The Activity Instance Wizard Stepper 'Data specification' page is displayed

    Scenario: [Create][Sentence case name validation] User must not be able to continue if sentance case name is not identical to instance name (apart from casing)
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
        And The sentance case name is set to different value than instance name
        Then Warning about not matching name and sentence case name is displayed
        And Form continue button is clicked
        And The Activity Instance Wizard Stepper 'PARAM/PARAMCD' page is displayed

    Scenario: [Create][Uniqueness check][Topic code] User must not be able to save instance with topic code that already exists
        Given The '/library/activities/activity-instances' page is opened
        And User waits for the table
        When The already used topic code is saved
        When The Add Activity Instance button is clicked
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
        And The topic code is changed to the already used one
        And Form continue button is clicked
        And Form save button is clicked
        Then Warning about already existing topic code is displayed
        
    Scenario: [Create][Uniqueness check][Name] User must not be able to save instance with name that already exists
        Given The '/library/activities/activity-instances' page is opened
        And User waits for the table
        When The already used instance name is saved
        When The Add Activity Instance button is clicked
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
        And The instance name is changed to the already used one
        And Form continue button is clicked
        And Form save button is clicked
        Then Warning about already existing activity name is displayed

    Scenario: [Create][Mandatory fields] User must not be able to continue without selecting test_code for Numeric Findings instance class
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When First activity is selected from the activity list
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        And The 'AE ADDITIONAL DATA' is selected from the Data category field
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And Form continue button is clicked
        Then Required field 'Code submission value' is highlighted as required
        And Required field 'Name submission value' is highlighted as required
        And The Activity Instance Wizard Stepper 'Required' page is displayed