@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Shared Study Activities Placeholder

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: [TestData] Old placeholder activity workflow feature flag is enabled
        Then [API] The feature flag 'streamline_placeholder_activities' is disabled

    Scenario: [Update][Positive Case][Shared Activity Request] User must be able to accept changes to activity request copied from other study
        And User selects study with id 'CDISC DEV-9876'
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Unsubmitted Requested Activity
        And [API] Requested Activity is added to the study
        And User selects study with id 'CDISC DEV-9879'
        Given The page 'activities/list' is opened for current study
        And User intercepts available studies request
        When Study activity add button is clicked
        And Activity from studies is selected
        And User waits for available studies request
        And User selects study 'CDISC DEV-9876'
        And Form continue button is clicked
        And Activity placeholder is searched for
        And The first matching activity is selected
        And Form save button is clicked
        And The form is no longer available
        And The Study Activity is found
        And The 'Edit' option is clicked from the three dot menu list
        And User updates Activity Placeholder name
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And User selects study with id 'CDISC DEV-9876'
        And The page 'activities/list' is opened for current study
        And Old The Study Activity is found
        And The 'Update activity version' option is clicked for flagged item
        And The user is presented with the changes to request
        And Modal window 'Accept' button is clicked
        And The form is no longer available
        Then The Study Activity is found

    Scenario: [Update][Positive Case][Shared Activity Request] User must be able to decline and keep changes to activity request copied from other study
        And User selects study with id 'CDISC DEV-9879'
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The 'Edit' option is clicked from the three dot menu list
        And User updates Activity Placeholder name
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And User selects study with id 'CDISC DEV-9876'
        And The page 'activities/list' is opened for current study
        And Old The Study Activity is found
        And The 'Update activity version' option is clicked for flagged item
        Then The user is presented with the changes to request
        And Modal window 'Decline and keep' button is clicked
        And The form is no longer available
        Then Old The Study Activity is found

    Scenario: [Update][Positive Case][Shared Activity Request] User must be able to remove activity request copied from other study
        And User selects study with id 'CDISC DEV-9876'
        Given The page 'activities/list' is opened for current study
        And Old The Study Activity is found
        When The 'Remove Activity' option is clicked for flagged item
        And Action is confirmed by clicking continue
        Then The Old study Activity Placeholder is not available

    Scenario: [Positive Case][Shared Activity Request] User must be able to approve activity request created from placeholder
        Given User selects study with id 'CDISC DEV-9876'
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Submitted Requested Activity
        And [API] Requested Activity is added to the study
        When The '/library/activities/requested-activities' page is opened
        Then The Study Activity is found
        When The 'Handle placeholder request' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And The request continue button is clicked
        And The activity request approval form is filled with definition
        And The sponsor continue button is clicked
        And The confirm continue button is clicked
        Then The Study Activity is not found
        And The page 'activities/list' is opened for current study
        Then The Study Activity is found
        When The 'Update to approved activity' option is clicked for flagged item
        And Modal window 'Accept' button is clicked
        And The item actions button is clicked
        Then The form is no longer available
        And 'Update to approved activity' action is not available

    Scenario: [Update][Positive Case][Shared Activity Request] User must not be notified of changes when SoA group has been updated
        Given User selects study with id 'CDISC DEV-9876'
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Unsubmitted Requested Activity
        And [API] Requested Activity is added to the study
        And User selects study with id 'CDISC DEV-9879'
        And [API] Requested Activity is added to the study
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And User edits Activity SoA group to 'HIDDEN'
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And User selects study with id 'CDISC DEV-9876'
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The red alert badge is not present

    Scenario: [Update][Positive Case][Shared Activity Request] User must not be notified of changes when Data Collection flag has been updated
        Given User selects study with id 'CDISC DEV-9879'
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The 'Edit' option is clicked from the three dot menu list
        And Data collection flag is checked
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And User selects study with id 'CDISC DEV-9876'
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The red alert badge is not present

    Scenario: [Update][Positive Case][Shared Activity Request] User must not be notified of changes when Rationale for activity request has been updated
        Given User selects study with id 'CDISC DEV-9879'
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The 'Edit' option is clicked from the three dot menu list
        And User sets Activity rationale
        And Modal window 'Save' button is clicked
        And The form is no longer available
        Given User selects study with id 'CDISC DEV-9876'
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The red alert badge is not present

    @pending_implementation
    Scenario: [Create][Positive case] System must select 'Multiple instances allowed' true as default for placeholder requests
        Given The activity placeholder request is created
        Then The checkbox 'Multiple instances allowed' is set true by default