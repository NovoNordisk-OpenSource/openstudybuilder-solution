@REQ_ID:1070683

Feature: Library - Concepts - Activities - Requested Activities
    As a user, I want to manage Requested Activities in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in

    Scenario: [TestData] Old placeholder activity workflow feature flag is enabled
        Then [API] The feature flag 'streamline_placeholder_activities' is disabled
        
    Scenario: [Create] User must not be able to create activity request from library level
        Given The '/library/activities/requested-activities' page is opened
        Then The add activity request button is not available

    Scenario: [Actions][New version] User must be able to add a new version for the approved activity request
        Given The '/library/activities/requested-activities' page is opened
        And [API] Requested activity in status Draft exists
        And [API] Requested activity is approved
        And Requested activity is found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'

    Scenario: [Actions][Inactivate] User must be able to inactivate the approved version of the activity request
        Given The '/library/activities/requested-activities' page is opened
        And [API] Requested activity in status Draft exists
        And [API] Requested activity is approved
        And Requested activity is found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '1.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate the inactivated version of the activity request
        Given The '/library/activities/requested-activities' page is opened
        And [API] Requested activity in status Draft exists
        And [API] Requested activity is approved
        And [API] Requested activity is inactivated
        And Requested activity is found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Approve] User must be able to Approve the drafted version of the activity request
        Given The '/library/activities/requested-activities' page is opened
        And [API] Requested activity in status Draft exists
        And Requested activity is found
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    @manual_test
    Scenario: User must be able to handle and approve an activity placeholder request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Final
        When The 'Handle placeholder request' option is clicked from the three dot menu list
        And The activity request is approved
        Then The new activity request is saved with a status as 'Retired'
        And The activity request appears as available activity in the study
        And The activity appears in sponsor library

    @manual_test
    Scenario: User must be able to handle and reject an activity placeholder request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Final
        When The 'Handle placeholder request' option is clicked from the three dot menu list
        And The activity request is rejected
        Then The new activity request is saved with a status as 'Retired'
        And The activity request appears as rejected for study

    Scenario: [Actions][Availability] User must only have access correct actions depending on item state
        Given The '/library/activities/requested-activities' page is opened
        And [API] Requested activity in status Draft exists
        And Requested activity is found
        And The item actions button is clicked
        Then 'Approve' action is available
        And 'History' action is available
        And 'Edit' action is not available
        And [API] Requested activity is approved
        And Requested activity is found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed
        Then 'Handle placeholder request' action is available
        And [API] Requested activity is inactivated
        And Requested activity is found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed

    Scenario: [Overview Page] User must able to see the linked study on the activity placeholder overview page
        Given User selects study with id 'CDISC DEV-9876'
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Unsubmitted Requested Activity
        And [API] Requested Activity is added to the study
        And The '/library/activities/activities' page is opened
        And The Study Activity is found
        Then The Library value is set to 'Requested'
        And User goes to study activity overview page by clicking its name
        Then The Library displayed on the summary has value 'Requested'
        And The Study ID displayed on the summary has value 'CDISC DEV-9876'

    Scenario: [Overview Page] User must able unlink study from the activity placeholder and see the change on the overview page
        Given User selects study with id 'CDISC DEV-9876'
        When The page 'activities/list' is opened for current study 
        And The Study Activity is found
        When The 'Remove Activity' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        Then The pop up displays 'Study activity deleted'
        And The '/library/activities/activities' page is opened
        And The Study Activity is found
        Then The Library value is set to 'Requested'
        And User goes to study activity overview page by clicking its name
        Then The Library displayed on the summary has value 'Requested'
        And The Study ID displayed on the summary has value '-'

    Scenario: [Archive] User must able to archive requested activity
        Given User selects study with id 'CDISC DEV-9876'
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Unsubmitted Requested Activity
        And [API] Requested Activity is added to the study
        And The '/library/activities/activities' page is opened
        And The Study Activity is found
        Then The Library value is set to 'Requested'
        Given User toggles on the Archived Library
        Then The Study Activity is not found
        When The page 'activities/list' is opened for current study 
        And The Study Activity is found
        When The 'Remove Activity' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        Then The pop up displays 'Study activity deleted'
        And [API] Unsubmitted requested Activity is archived
        And The '/library/activities/activities' page is opened
        Then The Study Activity is not found
        Given User toggles on the Archived Library
        Then The Study Activity is found
        Then The Library value is set to 'Archived'
        And User goes to study activity overview page by clicking its name
        Then The Library displayed on the summary has value 'Archived'
        And The Study ID displayed on the summary has value '-'

    Scenario: [Archive] User must not be able to inactivate archived activity
        And The '/library/activities/activities' page is opened
        Given User toggles on the Archived Library
        Then The Study Activity is found
        And The 'Inactivate' option is clicked from the three dot menu list
        Then The pop up displays "Library isn't editable."

    Scenario: [Archive] User must not be able to create new version of archived activity
        And The '/library/activities/activities' page is opened
        Given User toggles on the Archived Library
        Then The Study Activity is found
        And The 'New version' option is clicked from the three dot menu list
        Then The pop up displays "Library isn't editable."

    Scenario: [Archive] User must not be able to inactivate archived activity from the overview page
        And The '/library/activities/activities' page is opened
        Given User toggles on the Archived Library
        Then The Study Activity is found
        And User goes to study activity overview page by clicking its name
        When The inactivate button is clicked
        Then The pop up displays "Library isn't editable."

    Scenario: [Archive] User must not be able to create new version of archived activity from the overview page
        And The '/library/activities/activities' page is opened
        Given User toggles on the Archived Library
        Then The Study Activity is found
        And User goes to study activity overview page by clicking its name
        When The new version plus button is clicked
        Then The pop up displays "Library isn't editable."