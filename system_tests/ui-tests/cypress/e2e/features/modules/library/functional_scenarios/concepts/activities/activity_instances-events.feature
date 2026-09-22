@REQ_ID:1070683
Feature: Library - Concepts - Activities - Activity instances - wizard stepper - events
    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Feature flag] User must be able to turn on wizard stepper for activity instance creation
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled
        When [API] The feature flag 'activity_instance_wizard_stepper_events' is enabled

    Scenario: [Create][Events][Existing activity] User must be able to add a new Activity Instance with Events as Activity Instance Class
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'Events' is selected from the Activity instance class field
        And The 'DE' is selected from the Activity instance domain field
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        Then The Activity Instance Wizard Stepper 'OCCDS' page is displayed
        And Automatically assigned activity instance name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Data specification' page is displayed
        And User intercepts activity instance creation request with strict_mode verification
        And Form save button is clicked
        And User waits for activity instance creation request with strict_mode verification
        And The form is no longer available
        Then The current URL is '/overview'
        And Correct instance overview page is displayed

    Scenario: [Create][Events][Fields validation] User must be not be presened with required Activity Instance Classes selection
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'Events' is selected from the Activity instance class field
        And The 'DE' is selected from the Activity instance domain field
        Then The Activity Item Classes selection is not displayed

    Scenario: [Create][Events][Fields validation] User must be not be presened with ADaM Paramter code input
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'Events' is selected from the Activity instance class field
        And The 'DE' is selected from the Activity instance domain field
        And Form continue button is clicked
        Then ADaM parameter code input should not exists

    Scenario: [Create][Events][Overview Page] User must be able to view all selected values in the overview page (instance class, datadomain, category, subcategory)
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
        When The 'Events' is selected from the Activity instance class field
        And The 'AE' is selected from the Activity instance domain field
        And The 'ADVERSE EVENT' is selected from the Data category field
        And The 'ACQUIRED' is selected from the Data SubCategory field
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
        Then Activity Item Class 'event_category' with value 'Adverse Event' and type 'CT Term' is present in the table
        And Activity Item Class 'event_subcategory' with value 'Acquired' and type 'CT Term' is present in the table
        And Activity Item Class 'domain' with value 'Adverse Event Domain' and type 'CT Term' is present in the table