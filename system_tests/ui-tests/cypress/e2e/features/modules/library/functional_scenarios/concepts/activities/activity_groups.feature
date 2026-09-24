@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Groups
    As a user, I want to manage every Activity Groups in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activity-groups' page is opened
        And User sets status filter to 'all'
        
    @smoke_test
    Scenario: [Create][Positive case] User must be able to add a new activity group
        When The add activity group button is clicked
        And User waits for 1 seconds
        And The test activity group container is filled with data
        And User intercepts activity group request
        And Form save button is clicked
        And User waits for activity group request
        Then The pop up displays 'Group created'
        And Activity group is searched for and found
        And The newly added activity group is visible in the the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Create][Mandatory fields] User must not be able to save new activity group without filling mandatory fields of 'Group name', 'Sentence case name' and 'Definition'
        When The add activity group button is clicked
        And The Group name and Sentence case name and Definition fields are not filled with data
        And Form save button is clicked
        Then The user is not able to save the acitivity group
        And The message is displayed as 'This field is required' in the mandatory fields

    Scenario: [Create][Sentence case name validation] System must default value for 'Sentence case name' to lower case value of 'Activity group name'
        When The add activity group button is clicked
        And User waits for 1 seconds
        And The user enters a value for Activity group name
        Then The field for Sentence case name will be defaulted to the lower case value of the Activity group name

    Scenario: [Create][Sentence case name validation] System must ensure value of 'Sentence case name' independent of case is identical to the value of 'Activity group name'
        When The add activity group button is clicked
        And The user define a value for Sentence case name and it is not identical to the value of Activity group name
        And Form save button is clicked
        Then The user is not able to save the acitivity group
        And The validation message appears for sentance case name that it is not identical to name

    Scenario: [Actions][New version] User must be able to add a new version for the approved activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is searched for and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'

    Scenario: [Actions][Edit][version 1.0] User must be able to edit and approve new version of activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is searched for and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And The activity group is edited
        And User intercepts activity group request
        And Form save button is clicked
        And User waits for activity group request
        Then The pop up displays 'Group updated'
        And Activity group is searched for and found
        Then The item has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '2.0'

    Scenario: [Actions][Inactivate] User must be able to inactivate the approved version of the activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is searched for and found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '1.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate the inactivated version of the activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity group is inactivated
        And Activity group is searched for and found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Edit][version 0.1] User must be able to edit the drafted version of the activity group
        And [API] Activity group in status Draft exists
        And Activity group is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And The activity group is edited
        And User intercepts activity group request
        And Form save button is clicked
        And User waits for activity group request
        Then The pop up displays 'Group updated'
        And Activity group is searched for and found
        Then The item has status 'Draft' and version '0.2'
        
    Scenario: [Actions][Approve] User must be able to approve the drafted version of the activity group
        And [API] Activity group in status Draft exists
        And Activity group is searched for and found
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Linking] Activity subgroups must remain linked to activity group when activity group has been edited
        And [API] Study Activity is created and approved
        And Subgroup name created through API is found
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And [API] Activity group gets new version
        And User intercepts linked subgroups to group request
        And Overview page for group created via API is opened
        And User waits for linked subgroups to group request
        When The pencil button is clicked
        And The current activity group is edited
        And Form save button is clicked
        And The status displayed on the summary has value 'Draft' and version is '1.2'
        And User waits for 1 seconds
        And The approve button is clicked
        And The status displayed on the summary has value 'Final' and version is '2.0'
        Then The activity subgroups previously linked to that group remain linked

    Scenario: [Actions][Delete] User must be able to Delete the intial created version of the activity group
        And [API] Activity group in status Draft exists
        And Activity group is searched for and found
        When The 'Delete' option is clicked from the three dot menu list
        Then Activity group is searched for and not found

    Scenario: [Cancel][Creation] User must be able to Cancel creation of the activity group
        When The add activity group button is clicked
        And The test activity group container is filled with data
        When Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And Activity group is searched for and not found

    Scenario: [Cancel][Edition] User must be able to Cancel edition of the activity group
        And [API] Activity group in status Draft exists
        And Activity group is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        When The activity group edition form is filled with data
        And Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And Activity group is searched for and not found

    Scenario: [Actions][Availability] User must only have access correct actions depending on item state
        And [API] Activity group in status Draft exists
        And Activity group is searched for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Draft item are displayed
        And [API] Activity group is approved
        And Activity group is searched for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed
        And [API] Activity group is inactivated
        And Activity group is searched for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed

