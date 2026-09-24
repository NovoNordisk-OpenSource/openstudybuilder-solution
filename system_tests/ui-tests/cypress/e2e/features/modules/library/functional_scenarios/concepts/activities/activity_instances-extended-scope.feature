@REQ_ID:1070683 @skip_on_prv_val
Feature: Library - Concepts - Activities - Activity instances - Wizard Stepper - Extended Scope
    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Feature flag] User must be able to turn on wizard stepper for activity instance creation
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled

    Scenario: [Create][Selected Activity] User must be able to see which activity has been selected in the first step
        And [API] Study Activity is created and approved
        And User saves activity name created via API
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        And Activity created via API is searched for
        When First activity is selected from the activity list
        And Form continue button is clicked
        Then User can see which activity was selected in the previous step

    Scenario: [Create][Requested Activity] User must not be able to see submitted requested activity
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Submitted Requested Activity
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        When Activity placeholder is searched for
        Then No results are returned in the form table

    Scenario: [Create][Requested Activity] User must not be able to see unsubmitted requested activity
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Unsubmitted Requested Activity
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        When Activity placeholder is searched for
        Then No results are returned in the form table

    Scenario: [Create][Naming] User must presented with adjusted activity instance naming based on selected activity
        And [API] Study Activity is created and approved
        And User saves activity name created via API
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
        And First available value for 'Test Name' is selected
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And Selected Code Submission value is saved
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        Then Sentence case name is lowercased version of instance name
        Then Activity Instance Name is identical to selected Activity Name
        And Topic code is uppercased version of Activity Instance Name with _ instead of spaces
        And ADaM parameter code is four first letters of selected Code submission value of Activity Item Class

    Scenario: [Create][Naming] User must presented with adjusted activity instance naming after checking Data From Research Lab checkbox
        And [API] Study Activity is created and approved
        And User saves activity name created via API
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
        And First available value for 'Test Name' is selected
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And Selected Code Submission value is saved
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        And Customize toggle is turn off
        And Data from research lab is checked
        Then Activity Instance Name have Research added to it
        And Sentence case name is lowercased version of instance name
        And Topic code have _RESEARCH added to it
        And ADaM parameter code have X added to it

    Scenario: [Create][Item classes][Optional] User must be able more than one activity item class in Step 3: PARAM/PARAMCD
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        And First available value for 'Test Name' is selected
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        And Automatically assigned activity instance name is saved
        And Add activity item class button is clicked
        Then Value 'Method' is selected for 0 Activity item class field
        And Add activity item class button is clicked
        Then Value 'Specimen' is selected for 1 Activity item class field
        And Form continue button is clicked
        And User intercepts activity instance creation request with strict_mode verification
        And Form save button is clicked
        And User waits for activity instance creation request with strict_mode verification
        And The form is no longer available
        Then The current URL is '/overview'
        
    Scenario: [Create][Item classes][Optional] User must be able more than one activity item class in Step 4: Data Specification
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        And First available value for 'Test Name' is selected
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        And Automatically assigned activity instance name is saved
        And Form continue button is clicked
        And Add activity item class button is clicked
        Then Value 'Method' is selected for 0 Activity item class field
        And Add activity item class button is clicked
        Then Value 'Specimen' is selected for 1 Activity item class field
        And User intercepts activity instance creation request with strict_mode verification
        And Form save button is clicked
        And User waits for activity instance creation request with strict_mode verification
        And The form is no longer available
        Then The current URL is '/overview'
        And Correct instance overview page is displayed