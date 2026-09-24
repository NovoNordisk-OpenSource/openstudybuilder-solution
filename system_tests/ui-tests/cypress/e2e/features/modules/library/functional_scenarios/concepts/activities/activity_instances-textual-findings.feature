@REQ_ID:1070683
Feature: Library - Concepts - Activities - Activity instances - wizard stepper - textual findings
    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Feature flag] User must be able to turn on wizard stepper for activity instance creation
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled
        When [API] The feature flag 'activity_instance_wizard_stepper_textual_findings' is enabled

    Scenario: [Create][TextualFindings][Existing activity] User must be able to add a new Activity Instance with TextualFindings as Activity Instance Class
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'TextualFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        Then The Activity Item Classes selection displayed
        And First available value for 'Test Name' is selected
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

    Scenario: [Create][TextualFindings][Mandatory Item Classes] User must not be able to add a new Activity Instance with TextualFindings as Activity Instance Class if Test Name and Test Code is not selected
        Given The '/library/activities/activity-instances' page is opened
        And User intercepts available activities requests
        When The Add Activity Instance button is clicked
        And User waits for available activities requests
        Then The Activity Instance Wizard Stepper 'Select activity' page is displayed
        When First activity is selected from the activity list
        And Selected Activity name is saved
        And Form continue button is clicked
        Then The Activity Instance Wizard Stepper 'Required' page is displayed
        When The 'TextualFindings' is selected from the Activity instance class field
        And The 'LB' is selected from the Activity instance domain field
        Then The Activity Item Classes selection displayed
        And Form continue button is clicked
        Then Value for required field 'Test Name' is highlighted as required
        And Value for required field 'Test Code' is highlighted as required
        And Item classes unit_dimension and standardised unit are not displayed
        And The Activity Instance Wizard Stepper 'Required' page is displayed
        