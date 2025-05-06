@REQ_ID:1070683
Feature: Library - Activities Instances with Wizard Stepper (Concepts Library)

    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in
        When The '/administration' page is opened
        And The 'Feature flags' button is clicked
        And Activity instance wizard feature flag is turned on

    Scenario: User must be able to add a new Activity Instance with Wizard Stepper process (positive case)
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When An Activity is selected from the activity list
        And 'continue' button is clicked on form
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        Then The Required Activity Item Classes field is displayed
        When The Required Activity Item Classes field is filled with data
        And 'continue' button is clicked on form
        Then The Activity Instance Wizard Stepper 'PARAM/PARAMCD' page is displayed
        And Automatically assigned activity instance name is saved
        And 'continue' button is clicked on form
        Then The Activity Instance Wizard Stepper 'Data specification' page is displayed
        And 'save' button is clicked on form
        Then Created activity is visible in table

    Scenario: User must be able to search for specific activity and create instance with it
        Given The '/library/activities/activity-instances' page is opened
        And [API] Study Activity is created and approved
        When The Add Activity Instance button is clicked
        And Activity created via API is searched for
        And An Activity is selected from the activity list
        And 'continue' button is clicked on form
        And First value is selected from the Activity instance class field
        And 'continue' button is clicked on form
        And Field 'ADaM parameter' is filled with value 'ADAM'
        And Automatically assigned activity instance name is saved
        And 'continue' button is clicked on form
        And 'save' button is clicked on form
        Then Created activity is visible in table

    Scenario: User must not be able to continue without selecting activity
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        And 'continue' button is clicked on form
        #Then Warning that activity should be selected is displayed - not implemented right now
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed

    Scenario: User must not be able to continue without selecting instance class and domain
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When An Activity is selected from the activity list
        And 'continue' button is clicked on form
        And 'continue' button is clicked on form
        Then Warning is displayed for mandatory field 'Activity instance'

    Scenario: User must not be able to continue without providing Activity Instance name, case name, topic code, adam parameter 
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When An Activity is selected from the activity list
        And 'continue' button is clicked on form
        And First value is selected from the Activity instance class field
        And 'continue' button is clicked on form
        And Mandatory field 'Activity instance name' is cleared
        And Mandatory field 'Sentence case name' is cleared
        And Mandatory field 'Topic code' is cleared
        And Mandatory field 'ADaM parameter' is cleared
        Then Warning is displayed for mandatory field 'Activity instance name'
        And Warning is displayed for mandatory field 'Sentence case name'
        And Warning is displayed for mandatory field 'Topic code'
        And Warning is displayed for mandatory field 'ADaM parameter'

    Scenario: User must not be able to save if sentenace case name is not identical to instance name
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When An Activity is selected from the activity list
        And 'continue' button is clicked on form
        And First value is selected from the Activity instance class field
        And 'continue' button is clicked on form
        And Field 'ADaM parameter' is filled with value 'ADAM'
        And Mandatory field 'Activity instance name' is cleared
        And Mandatory field 'Sentence case name' is cleared
        And Field 'Activity instance name' is filled with value 'TEST'
        And Field 'Sentence case name' is filled with value 'test2'
        And 'continue' button is clicked on form
        And 'save' button is clicked on form
        Then The Activity Instance Wizard Stepper 'Data specification' page is displayed
        And Warning about not matching name and sentence case name is displayed

    Scenario: System must ensure that sentance case name is lowercased version of instance name
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When An Activity is selected from the activity list
        And 'continue' button is clicked on form
        And First value is selected from the Activity instance class field
        And 'continue' button is clicked on form
        Then Sentence case name is lowercased version of instance name

    Scenario: User must not be able to save instance with topic code that already exists
        Given The '/library/activities/activity-instances' page is opened
        When Activity instance is created
        And Second Activity instance with the same topic code is created
        Then Warning about already existing topic code is displayed
        
    Scenario: User must not be able to save instance with name that already exists
        Given The '/library/activities/activity-instances' page is opened
        When Activity instance is created
        And Second Activity instance with the same name is created
        Then Warning about already existing activity name is displayed

    Scenario: System must ensure that Required Activity Item Classes fields have correct validation rules
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When An Activity is selected from the activity list
        And 'continue' button is clicked on form
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        Then The Required Activity Item Classes field is displayed
        And The test_code, test_name, unit_dimention and standard_unit fields are inactive
        And The test_code, test_name, unit_dimention and standard_unit values are empty
        And The test_name value is selected
        Then The test_code value is automatically populated
        And The test_code value is enabled for picking different value
        When The unit_dimension value is selected
        Then The standard_unit value is not automatically populated

    Scenario: User must be able more than one activity item class in Step 3: PARAM/PARAMCD
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        When An Activity is selected from the activity list
        And 'continue' button is clicked on form
        And First value is selected from the Activity instance class field
        And 'continue' button is clicked on form
        And Field 'ADaM parameter' is filled with value 'ADAM'
        And Add activity item class button is clicked
        Then First value is selected from the Activity item class field
        And Add activity item class button is clicked
        Then Second value is selected from the Activity item class field
        And 'save' button is clicked on form

@manual_test @pending_implementation
    Scenario: The new selected fields should display in Step 4: Data specification (can not be tested now, as data is not available)
        Given The '/library/activities/activity-instances' page is opened
        When Fill in correct data in the Step 1, Step 2 and Step 3
        Then The Activity Instance Wizard Stepper step 4: Data specification page is displayed
        Then The two new selected fields: data category and data subcategory are displayed

@manual_test @pending_implementation
    Scenario: Step 2: Optional Attributes field validation with Concentration avlue, without filling in the Optional Attributes field
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        Then The Activity Instance Wizard Stepper step 1: Select Activity page is displayed
        When An Activity is selected from the activity list
        And Click on the CONTINUE button
        Then The Activity Instance Wizard Stepper step 2: Required page is displayed
        When The NemericFindings is selected from the Activity instance class field
        And The LB is selected from the Activity instance class field
        Then The Required Activity Item Classes field is displayed
        When Select "Concentration" value from the unit_dimention value field
        Then The Optional Attributes field is displayed
        When Fill in all data for other fields
        And Leave the Optional Attributes field empty
        And Complete all the rest of Wizard Stepper steps
        Then The newly added Activity Instance item is added in the table
        
@manual_test @pending_implementation
    Scenario: Step 2: Optional Attributes field validation with Concentration avlue, with filling in the Optional Attributes field
        Given The '/library/activities/activity-instances' page is opened
        When The Add Activity Instance button is clicked
        Then The Activity Instance Wizard Stepper step 1: Select Activity page is displayed
        When An Activity is selected from the activity list
        And Click on the CONTINUE button
        Then The Activity Instance Wizard Stepper step 2: Required page is displayed
        When The NemericFindings is selected from the Activity instance class field
        And The LB is selected from the Activity instance class field
        Then The Required Activity Item Classes field is displayed
        When Select "Concentration" value from the unit_dimention value field
        Then The Optional Attributes field is displayed
        When Fill in all data for other fields
        And Fill in the Optional Attributes field with a integer value, like 1
        And Complete all the rest of Wizard Stepper steps
        Then The newly added Activity Instance item is added in the table