@REQ_ID:1070683 @skip_on_prv_val

Feature: Library - Concepts - Activities - Activity Subgroups

    As a user, I want to manage every Activity Subgroups in the Concepts Library
    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activity-subgroups' page is opened
        And User sets status filter to 'all'

    @smoke_test
    Scenario: [Create][Positive case] User must be able to add a new activity subgroups
        When The Add activity subgroup button is clicked
        And User waits for 1 seconds
        And The activity subgroup form is filled with data
        And User intercepts activity subgroup request
        And Form save button is clicked
        And User waits for activity subgroup request
        Then The pop up displays 'Subgroup created'
        And Activity subgroup is searched for and found
        Then The newly added activity subgroup is visible in the the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Create][Mandatory fields] User must not be able to save new activity subgroup without filling mandatory fields of 'Group name', 'Subgroup name', 'Sentence case name' and 'Definition'
        When The Add activity subgroup button is clicked
        And The Activity Subgroup name, Sentence case name and Definition fields are not filled with data
        And Form save button is clicked
        Then The user is not able to save the acitivity subgroup
        And The validation appears for missing subgroup
        And The validation appears for missing subgroup name
        And The validation appears for missing subgroup definition

    Scenario: [Create][Sentence case name validation] System must default value for 'Sentence case name' to lower case value of 'Activity subgroup name'
        When The Add activity subgroup button is clicked
        And User waits for 1 seconds
        And The user enters a value for Activity subgroup name
        Then The field for Sentence case name will be defaulted to the lower case value of the Activity subgroup name

    Scenario: [Create][Sentence case name validation] System must ensure value of 'Sentence case name' independent of case is identical to the value of 'Activity subgroup name'
        When The Add activity subgroup button is clicked
        And The user define a value for Sentence case name and it is not identical to the value of Activity subgroup name
        And Form save button is clicked
        Then The user is not able to save the acitivity subgroup
        And The validation message appears for sentance case name that it is not identical to name

    Scenario: [Actions][New version] User must be able to add a new version for the approved activity subgroup
        And [API] Activity subgroup in status Draft exists
        And [API] Activity subgroup is approved
        And Activity subgroup is searched for and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'

    Scenario: [Actions][Edit][version 1.0] User must be able to edit and approve new version of activity subgroup
        And [API] Activity subgroup in status Draft exists
        And [API] Activity subgroup is approved
        And Activity subgroup is searched for and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And The activity subgroup edition form is filled with data
        And User intercepts activity subgroup request
        And Form save button is clicked
        And User waits for activity subgroup request
        Then The pop up displays 'Subgroup updated'
        And Activity subgroup is searched for and found
        Then The item has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '2.0'

    Scenario: [Linkage] Activity groups and activity instances must remain linked to activity subgroup when activity subgroup has been edited
        And [API] Study Activity is created and approved
        And Group name created through API is found
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And [API] Activity subgroup gets new version
        And Overview page for subgroup created via API is opened
        When The pencil button is clicked
        And The current activity subgroup is edited
        And Form save button is clicked
        Then The pop up displays 'Subgroup updated'
        Then The status displayed on the summary has value 'Draft' and version is '1.2'
        And User waits for 1 seconds
        When The approve button is clicked
        Then The status displayed on the summary has value 'Final' and version is '2.0'
        Then The activity groups previously linked to that subgroup remain linked

    Scenario: [Actions][Inactivate] User must be able to inactivate the approved version of the activity subgroup
        And [API] Activity subgroup in status Draft exists
        And [API] Activity subgroup is approved
        And Activity subgroup is searched for and found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '1.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate the inactivated version of the activity subgroup
        And [API] Activity subgroup in status Draft exists
        And [API] Activity subgroup is approved
        And [API] Activity subgroup is inactivated
        And Activity subgroup is searched for and found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Edit][version 0.1] User must be able to edit the drafted version of the activity subgroup
        And [API] Activity subgroup in status Draft exists
        And Activity subgroup is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        Then The activity subgroup edition form is filled with data
        And User intercepts activity subgroup request
        And Form save button is clicked
        And User waits for activity subgroup request
        Then The pop up displays 'Subgroup updated'
        And Activity subgroup is searched for and found
        And The item has status 'Draft' and version '0.2'

    Scenario: [Actions][Approve] User must be able to approve the drafted version of the activity subgroup
        And [API] Activity subgroup in status Draft exists
        And Activity subgroup is searched for and found
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Delete] User must be able to Delete the intial created version of the activity subgroup
        And [API] Activity subgroup in status Draft exists
        And Activity subgroup is searched for and found
        When The 'Delete' option is clicked from the three dot menu list
        Then Activity subgroup is searched for and not found
    
    Scenario: [Cancel][Creation] User must be able to Cancel creation of the activity subgroup
        Given The Add activity subgroup button is clicked
        And The activity subgroup form is filled with data
        When Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And Activity subgroup is searched for and not found

    Scenario: [Cancel][Edition] User must be able to Cancel edition of the activity subgroup
        And [API] Activity subgroup in status Draft exists
        And Activity subgroup is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        When The activity subgroup edition form is filled with data
        And Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And Activity subgroup is searched for and not found
    
    Scenario: [Actions][Availability] User must only have access correct actions depending on item state
        When [API] Activity subgroup in status Draft exists
        And Activity subgroup is searched for and found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Draft item are displayed
        And [API] Activity subgroup is approved
        And Activity subgroup is searched for and found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed
        And [API] Activity subgroup is inactivated
        And Activity subgroup is searched for and found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed

    @BUG_ID:2813782
    Scenario: [History] User must be presented with correct values in history table
        When The user opens version history of activity subgroup
        Then The version history displays correct data for activity subgroup

