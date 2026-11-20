@REQ_ID:1070683
Feature: Library - Concepts - Activities - Activity instances - wizard stepper - interventions
    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Feature flag] User must be able to turn on wizard stepper for activity instance creation
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled
        When [API] The feature flag 'activity_instance_wizard_stepper_interventions' is enabled

    Scenario: [Create][Interventions][Existing activity] User must be able to add a new Activity Instance with Interventions as Activity Instance Class
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'Interventions' is selected from the Activity instance class field
        And The 'ML' is selected from the Activity instance domain field
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        Then The Activity Instance Wizard Stepper 'Interventions' page is displayed
        And Automatically assigned activity instance name is saved
        And The ADaM param is updated
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Data specification' page is displayed
        And User intercepts activity instance creation request with strict_mode verification
        And Form save button is clicked
        And User waits for activity instance creation request with strict_mode verification
        And The form is no longer available
        Then The current URL is '/overview'
        And Correct instance overview page is displayed

    Scenario: [Create][Interventions][Fields validation] User must be not be presened with required Activity Instance Classes selection
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'Interventions' is selected from the Activity instance class field
        And The 'ML' is selected from the Activity instance domain field
        Then The Activity Item Classes selection is not displayed

    Scenario: [Create][Interventions][Overview Page] User must be able to view all selected values in the overview page (instance class, datadomain, category, subcategory)
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
        When The 'Interventions' is selected from the Activity instance class field
        And The 'EX' is selected from the Activity instance domain field
        And The 'ALCOHOL ABUSE' is selected from the Data category field
        And The 'LONG-ACTING' is selected from the Data SubCategory field
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request 
        And Automatically assigned activity instance name is saved
        And The ADaM param is updated
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
        And The ADaM parameter code displayed on the summary has updated value
        Then Activity Item Class 'intervention_category' with value 'Alcohol Abuse' and type 'CT Term' is present in the table
        And Activity Item Class 'intervention_subcategory' with value 'Long-acting' and type 'CT Term' is present in the table
        And Activity Item Class 'treatment' with value '-' and type 'Text' is present in the table
        And Activity Item Class 'domain' with value 'Exposure Domain' and type 'CT Term' is present in the table

    Scenario: [Create][Approve][Existing activity] User must be able to approve groupings and attributes Activity Instance with Interventions as Activity Instance Class
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'Interventions' is selected from the Activity instance class field
        And The 'ML' is selected from the Activity instance domain field
        And User intecepts preview request
        And Form continue button is clicked
        Then User waits for preview request
        Then The Activity Instance Wizard Stepper 'Interventions' page is displayed
        And Automatically assigned activity instance name is saved
        And The ADaM param is updated
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Data specification' page is displayed
        And User intercepts activity instance creation request with strict_mode verification
        And Form save button is clicked
        And User waits for activity instance creation request with strict_mode verification
        And The form is no longer available
        Then The current URL is '/overview'
        And Correct instance overview page is displayed
        When Activity instance approve attributes button is clicked
        Then The status displayed on the summary for Activity Instance Attributes is 'Final' and version is '1.0'
        When Activity instance approve groupings button is clicked
        Then The status displayed on the summary for Activity Instance Groupings is 'Final' and version is '1.0'