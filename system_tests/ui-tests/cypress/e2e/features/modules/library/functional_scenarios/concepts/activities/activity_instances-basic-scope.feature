@REQ_ID:1070683 @skip_on_prv_val
Feature: Library - Concepts - Activities - Activity Instances
    As a user, I want to manage every Activity Instances in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activity-instances' page is opened

    Scenario: [Test data] Wizard stepper feature flags are enabled
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled
        When [API] The feature flag 'activity_instance_wizard_stepper_edit_mode' is enabled

    Scenario: [Actions][Approve] User must be able to Approve the drafted version of the Activity Instance Attributes
        And [API] Activity Instance in status Draft exists
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        When The 'Approve attributes' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Approve] User must be able to Approve the drafted version of the Activity Instance Groupings
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        When The 'Approve groupings' option is clicked from the three dot menu list
        Then The activity instance groupings has status 'Final' and version '1.0'

    Scenario: [Actions][Inactivate] User must be able to inactivate the approved version of the Activity Instance
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '1.0'
        Then The activity instance groupings has status 'Retired' and version '1.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate the inactivated version of the Activity Instance
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'
        Then The activity instance groupings has status 'Final' and version '1.0'

    Scenario: [Actions][New version] User must be able to add a new version for the approved Activity Instance Attributes
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        When The 'New version (attributes)' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'

    Scenario: [Actions][New version] User must be able to add a new version for the approved Activity Instance Groupings
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        When The 'New version (groupings)' option is clicked from the three dot menu list
        Then The activity instance groupings has status 'Draft' and version '1.1'

    Scenario: [Actions][Delete] User must be able to Delete the intial created version of the activity Instance
        And [API] Activity Instance in status Draft exists
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        When The 'Delete' option is clicked from the three dot menu list
        Then Activity Instance is searched for and not found
        
    Scenario: [Actions][Edit][version 0.1] User must be able to edit the drafted version of the Activity Instance Attributes
        And [API] Activity Instance in status Draft exists
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        And User waits for 1 seconds
        When The 'Edit attributes' option is clicked from the three dot menu list
        Then The Activity Instance Attributes edition page is displayed

    Scenario: [Actions][Edit][version 0.1] User must be able to edit the drafted version of the Activity Instance Groupings
        And [API] Activity Instance in status Draft exists
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        And User waits for 1 seconds
        When The 'Edit groupings' option is clicked from the three dot menu list
        Then The Activity Instance Groupings edition page is displayed

    @pending_implementation
    Scenario: [Actions][Edit][version 1.1] User must be able to edit and approve new version of Activity Instance
        And [API] Activity Instance is approved
        And [API] Activity Instance new version is created
        And The page is reloaded
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for edition form to open
        And Linked Activity group and subgroup are loaded
        And Form continue button is clicked
        And Form continue button is clicked
        And The user updates instance name
        And User intercepts update instance request
        And Form save button is clicked
        Then The pop up displays 'Activity updated'
        And User waits for activity instance to be updated
        Then The item has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '2.0'

    Scenario: [Actions][Availability] User must only have access correct actions depending on item state
        Given [API] Activity Instance in status Draft exists
        When User sets status filter to 'all'
        And Activity Instance is searched for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Draft Activity Instance are displayed
        And [API] Activity Instance is approved
        And Activity Instance is searched for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Final Activity Instance are displayed
        And [API] Activity Instance is inactivated
        And Activity Instance is searched for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Retired Activity Instance are displayed
