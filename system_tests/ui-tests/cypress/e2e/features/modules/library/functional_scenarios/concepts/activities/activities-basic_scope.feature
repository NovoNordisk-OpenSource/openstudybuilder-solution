@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activities - Basic Scope
    As a user, I want to manage every Activities in the Concepts Library

    Background: User must be logged in
        Given The user is logged in

    @smoke_test
    Scenario: [Create][Positive case] User must be able to add a new activity with multiple instances allowed
        Given The '/library/activities/activities' page is opened
        When User sets status filter to 'draft'
        And User intercepts request for activity creation
        And The Add activity button is clicked
        And User waits for 1 seconds
        And User selects first activity group
        And User selects first activity subgroup
        And User sets activity name
        And User fills in activity optional data
        And The Multiple instance allowed checkbox is set to 'true'
        And Form save button is clicked
        Then The pop up displays 'Activity created'
        And User waits for activity creation request to finish
        When Activity is searched for and found
        Then The newly added activity is visible in the table
        And The item has status 'Draft' and version '0.1'
        When Open the activity overview page
        Then The Multiple instance allowed field is set to 'Yes'

    Scenario: [Create][Positive case] User must be able to add a new activity with no multiple instances allowed
        Given The '/library/activities/activities' page is opened
        When User sets status filter to 'draft'
        And User intercepts request for activity creation
        And The Add activity button is clicked
        And User selects first activity group
        And User selects first activity subgroup
        And User sets activity name
        And User fills in activity optional data
        And The Multiple instance allowed checkbox is set to 'false'
        And Form save button is clicked
        Then The pop up displays 'Activity created'
        And User waits for activity creation request to finish
        When Activity is searched for and found
        And The newly added activity is visible in the table
        And The item has status 'Draft' and version '0.1'
        When Open the activity overview page
        Then The Multiple instance allowed field is set to 'No'

    Scenario: [Actions][Inactivate] User must be able to inactivate the approved version of the activity
        And [API] Activity in status Draft exists
        And [API] Activity is approved
        And The '/library/activities/activities' page is opened
        And Activity is searched for and found
        When The 'Inactivate' option is clicked from the three dot menu list
        And User sets status filter to 'retired'
        Then The item has status 'Retired' and version '1.0' 

    Scenario: [Actions][Reactivate] User must be able to reactivate the inactivated version of the activity
        And [API] Activity in status Draft exists
        And [API] Activity is approved
        And [API] Activity is inactivated
        And The '/library/activities/activities' page is opened
        And User sets status filter to 'retired'
        And Activity is searched for and found
        When The 'Reactivate' option is clicked from the three dot menu list
        And User sets status filter to 'final'
        Then The item has status 'Final' and version '1.0' 

    Scenario: [Actions][Edit][version 0.1] User must be able to edit the Drafted version of the activity
        And [API] Activity in status Draft exists
        And The '/library/activities/activities' page is opened
        And User sets status filter to 'draft'
        And Activity is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And The activity name is updated
        And User fills in the reason for change
        And Form save button is clicked
        And Activity is searched for and found
        Then The item has status 'Draft' and version '0.2'

    Scenario: [Actions][Approve] User must be able to Approve the drafted version of the activity
        And [API] Activity in status Draft exists
        And The '/library/activities/activities' page is opened
        And User sets status filter to 'draft'
        And Activity is searched for and found
        When The 'Approve' option is clicked from the three dot menu list
        And User sets status filter to 'final'
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Delete] User must be able to Delete the intial created version of the activity
        And [API] Activity in status Draft exists
        And The '/library/activities/activities' page is opened
        And User sets status filter to 'draft'
        And Activity is searched for and found
        When The 'Delete' option is clicked from the three dot menu list
        Then Activity is searched for and not found

    Scenario: [Actions][New version] User must be able to add a new version for the approved activity
        And [API] Activity in status Draft exists
        And [API] Activity is approved
        And The '/library/activities/activities' page is opened
        And Activity is searched for and found
        When The 'New version' option is clicked from the three dot menu list
        And User sets status filter to 'draft'
        Then The item has status 'Draft' and version '1.1'
