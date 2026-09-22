@REQ_ID:1070683
Feature: Library - Concepts - Activities - Activity instances - wizard stepper - edit
    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Test data][Feature flag] User must be able to turn on wizard stepper feature flags and create instance to use for edit tests
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled
        When [API] The feature flag 'activity_instance_wizard_stepper_edit_mode' is enabled
        And [API] Study Activity is created and approved
        And User saves activity name created via API
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        And Activity created via API is searched for
        When First activity is selected from the activity list
        And Form continue button is clicked
        When The 'NumericFindings' is selected from the Activity instance class field
        And The 'MK' is selected from the Activity instance domain field
        And The 'ALCOHOL HABITS' is selected from the Data category field
        And The 'ACUTE KIDNEY INJURY CONDITIONS' is selected from the Data SubCategory field
        Then The Activity Item Classes selection displayed
        And First available value for 'Test Name' is selected
        And First available value for 'Unit dimension' is selected
        And First available value for 'Standardised unit' is selected
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request 
        And Add activity item class button is clicked
        Then Value 'Location' is selected for 0 Activity item class field
        And Automatically assigned activity instance name is saved
        And Form continue button is clicked
        And Add activity item class button is clicked
        Then Value 'Position' is selected for 0 Activity item class field
        And User intecepts activity groupings request
        And User intecepts activity items request
        And User intercepts activity instance creation request with strict_mode verification
        And Form save button is clicked

    Scenario: [Edit][Attributes] User must be able to edit instance Data Category and Data Subcategory
        Given The '/library/activities/activity-instances' page is opened
        And User sets status filter to 'all'
        And User waits for the table
        And User searches for created activity instance
        And Created activity instance is displayed in the first table row
        When The 'Edit attributes' option is clicked from the three dot menu list
        And The '24 HOUR URINE COLLECTION' is selected from the Data category field
        And The 'ACS ECG CHANGES' is selected from the Data SubCategory field
        And Form continue button is clicked
        And Form continue button is clicked
        And User intecepts activity groupings request
        And User intecepts activity items request
        And The Change description is provided
        And Form save button is clicked
        And The form is no longer available
        Then The current URL is '/overview'
        And User waits for activity groupings request
        And User waits for activity items request
        Then Activity Item Class 'finding_category' with value '24 Hour Urine Collection' and type 'CT Term' is present in the table
        And Activity Item Class 'finding_subcategory' with value 'ACS ECG Changes' and type 'Text' is present in the table

    Scenario: [Edit][Attributes] User must be able to edit instance Name and Sentance case name
        Given The '/library/activities/activity-instances' page is opened
        And User sets status filter to 'all'
        And User waits for the table
        And User searches for created activity instance
        And Created activity instance is displayed in the first table row
        When The 'Edit attributes' option is clicked from the three dot menu list
        And Form continue button is clicked
        And The instance name and sentence case name are updated
        And Form continue button is clicked
        And User intecepts activity groupings request
        And User intecepts activity items request
        And The Change description is provided
        And Form save button is clicked
        And The form is no longer available
        Then The current URL is '/overview'
        And User waits for activity groupings request
        And User waits for activity items request
        Then The instance name displayed on the summary has updated value
        And The Sentence case name displayed on the summary has updated value
        
    Scenario: [Edit][Attributes] User must be able to edit instance NCI Code and NCI Name
        Given The '/library/activities/activity-instances' page is opened
        And User sets status filter to 'all'
        And User waits for the table
        And User searches for created activity instance
        And Created activity instance is displayed in the first table row
        When The 'Edit attributes' option is clicked from the three dot menu list
        And Form continue button is clicked
        And The NCI name is set
        And The NCI code is set
        And Form continue button is clicked
        And User intecepts activity groupings request
        And User intecepts activity items request
        And The Change description is provided
        And Form save button is clicked
        And The form is no longer available
        Then The current URL is '/overview'
        And User waits for activity groupings request
        And User waits for activity items request
        Then The NCI Concept ID displayed on the summary has updated value
        And The NCI Concept Name displayed on the summary has updated value

    Scenario: [Edit][Attributes] User must be able to edit instance ADaM parameter
        Given The '/library/activities/activity-instances' page is opened
        And User sets status filter to 'all'
        And User waits for the table
        And User searches for created activity instance
        And Created activity instance is displayed in the first table row
        When The 'Edit attributes' option is clicked from the three dot menu list
        And Form continue button is clicked
        And The ADaM param is updated
        And Form continue button is clicked
        And User intecepts activity groupings request
        And User intecepts activity items request
        And The Change description is provided
        And Form save button is clicked
        And The form is no longer available
        Then The current URL is '/overview'
        And User waits for activity groupings request
        And User waits for activity items request
        Then The ADaM parameter code displayed on the summary has updated value

    Scenario: [Edit][Attributes] User must be able to edit Data specification Activity Item Classes
        Given The '/library/activities/activity-instances' page is opened
        And User sets status filter to 'all'
        And User waits for the table
        And User searches for created activity instance
        And Created activity instance is displayed in the first table row
        When The 'Edit attributes' option is clicked from the three dot menu list
        And Form continue button is clicked
        And Form continue button is clicked
        Then For Activity item class 'Position' value 'Standing' is selected
        And User intecepts activity groupings request
        And User intecepts activity items request
        And The Change description is provided
        And Form save button is clicked
        And The form is no longer available
        Then The current URL is '/overview'
        And User waits for activity groupings request
        And User waits for activity items request
        Then Activity Item Class 'position' with value "Standing, Fowler's Position" and type 'CT Term' is present in the table

    Scenario: [Edit][Attributes] User must be able to edit Data specification Activity Instance Data
        Given The '/library/activities/activity-instances' page is opened
        And User sets status filter to 'all'
        And User waits for the table
        And User searches for created activity instance
        And Created activity instance is displayed in the first table row
        When The 'Edit attributes' option is clicked from the three dot menu list
        And Form continue button is clicked
        And Form continue button is clicked
        Then The Required for Activity checkbox is checked
        And User intecepts activity groupings request
        And User intecepts activity items request
        And The Change description is provided
        And Form save button is clicked
        And The form is no longer available
        Then The current URL is '/overview'
        And User waits for activity groupings request
        And User waits for activity items request
        Then The Required for activity displayed on the summary has value 'Yes'

    Scenario: [Edit][Attributes] User must not be able to edit instance class and domain
        Given The '/library/activities/activity-instances' page is opened
        And User sets status filter to 'all'
        And User waits for the table
        And User searches for created activity instance
        And Created activity instance is displayed in the first table row
        When The 'Edit attributes' option is clicked from the three dot menu list
        Then The input with value 'NumericFindings' is disabled
        And The input with value 'MK -' is disabled

    Scenario: [Edit][Attributes] User must not be able to edit instance topic code
        Given The '/library/activities/activity-instances' page is opened
        And User sets status filter to 'all'
        And User waits for the table
        And User searches for created activity instance
        And Created activity instance is displayed in the first table row
        When The 'Edit attributes' option is clicked from the three dot menu list
        And Form continue button is clicked
        Then The input with value 'Topic code' is disabled

    Scenario: [Edit][Attributes] User must not be able to edit PARAM/PARAMCD Activty Item Classes
        Given The '/library/activities/activity-instances' page is opened
        And User sets status filter to 'all'
        And User waits for the table
        And User searches for created activity instance
        And Created activity instance is displayed in the first table row
        When The 'Edit attributes' option is clicked from the three dot menu list
        And Form continue button is clicked
        Then The activity item class with its value is disabled

    @pending_implementation
    Scenario: [Edit][Groupings] User must be able to edit activity instance groupings
        