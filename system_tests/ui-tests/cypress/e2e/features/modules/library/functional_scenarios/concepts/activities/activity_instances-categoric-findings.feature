@REQ_ID:1070683
Feature: Library - Concepts - Activities - Activity instances - wizard stepper - events
    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Feature flag] User must be able to turn on wizard stepper for activity instance creation
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled
        When [API] The feature flag 'activity_instance_wizard_stepper_categoric_findings' is enabled

    Scenario: [Create][Categoric Findings][Existing activity] User must be able to add a new Activity Instance with Categoric Findings as Activity Instance Class
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'CategoricFindings' is selected from the Activity instance class field
        And The 'EG' is selected from the Activity instance domain field
        And First available value and codelist for 'Test Name' are selected
        And First available value and codelist for 'Test Code' are selected
        And First available value and codelist for 'Categoric Finding Original result' are selected
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

    Scenario: [Create][Categoric Findings][Overview page] User must be able to see all selected values on overview page of Activity Instance with Categoric Findings as Instance Class
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'CategoricFindings' is selected from the Activity instance class field
        And The 'EG' is selected from the Activity instance domain field
        And The '24 HOUR URINE COLLECTION' is selected from the Data category field
        And The 'ACS ECG CHANGES' is selected from the Data SubCategory field
        And For activity item class 'Test Name', codelist 'Holter ECG Test Name' value 'Pacemaker' is searched and selected
        And For activity item class 'Test Code', codelist 'Holter ECG Test Code' value 'PACEMAKR' is searched and selected
        And For activity item class 'Categoric Finding Original result', codelist 'No Yes Response' value 'Not Applicable' is searched and selected
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        Then The Activity Instance Wizard Stepper 'PARAM/PARAMCD' page is displayed
        And Automatically assigned activity instance name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Data specification' page is displayed
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
        Then The Activity instance class displayed on the summary has value 'CategoricFindings'
        And Activity Item Class 'finding_category' with value '24 Hour Urine Collection' and type 'CT Term' is present in the table
        And Activity Item Class 'finding_subcategory' with value 'ACS ECG Changes' and type 'Text' is present in the table
        And Activity Item Class 'domain' with value 'Electrocardiogram Domain' and type 'CT Term' is present in the table
        And Activity Item Class 'test_code' with value 'Pacemaker ECG Assessment' and type 'CT Term' is present in the table
        And Activity Item Class 'test_name' with value 'Pacemaker ECG Assessment' and type 'CT Term' is present in the table

    Scenario: [Create][Categoric Findings][Existing activity] User must be able to add a new Activity Instance with Categoric Findings as Activity Instance Class and domain that does not require codelist selection
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'CategoricFindings' is selected from the Activity instance class field
        And The 'FA' is selected from the Activity instance domain field
        And First available value for 'Test Name' is selected
        And First available value for 'Test Code' is selected
        And First available value and codelist for 'Categoric Finding Original result' are selected
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

    Scenario: [Create][Categoric Findings][Mandatory fields] User must not be able to add a new Activity Instance with Categoric Findings if Test Name and Test Code are not selected
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'CategoricFindings' is selected from the Activity instance class field
        And The 'EG' is selected from the Activity instance domain field
        And User waits for 1 seconds
        And Form continue button is clicked
        Then Value for required field 'Test Name' is highlighted as required
        And Value for required field 'Test Code' is highlighted as required
        Then The Activity Instance Wizard Stepper 'Required' page is displayed

    Scenario: [Create][Categoric Findings][Mandatory fields] User must not be able to add a new Activity Instance with Categoric Findings if Categoric Finding Original result is not selected
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'CategoricFindings' is selected from the Activity instance class field
        And The 'EG' is selected from the Activity instance domain field
        And User waits for 1 seconds
        And Form continue button is clicked
        Then Value for required field 'Categoric Finding Original result' is highlighted as required
