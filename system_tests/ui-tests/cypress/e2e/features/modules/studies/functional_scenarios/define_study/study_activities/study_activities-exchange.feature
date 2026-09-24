@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Exchange Activity

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study activities.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'
        And [API] All Activities are deleted from selected study

    Scenario: [TestData] Old placeholder activity workflow feature flag is disabled and test data is prepared
        Then [API] The feature flag 'streamline_placeholder_activities' is enabled
        #When User clears list of exchanged activities
        Given [API] Activity in status Draft exists
        And [API] Activity is approved
        And Name of Activity from Library for exchaning placeholder is saved
        Given [API] Activity in status Draft exists
        And [API] Activity is approved
        And Name of Activity from Library for exchaning placeholder is saved
        Given User selects study with id 'CDISC DEV-9881'
        And [API] Study Activity is created and approved
        And Name of Activity from Library for exchaning placeholder is saved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] Study Activity is created and approved
        And Name of Activity from Library for exchaning placeholder is saved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] Get SoA Group 'BIOMARKERS' id

    Scenario: [Actions][Exchange Activity] User must be able to exchange submitted activity placeholder with more than activity from library
        When [API] Create Submitted Requested Activity
        And [API] Requested Activity is added to the study
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        When The 'Exchange Activity' option is clicked from the three dot menu list
        And Form continue button is clicked
        And User waits for the table
        And 1 Activity for exchanging the placeholder is searched for
        And User sets SoA Group as 'INFORMED CONSENT' for first matching activity
        And 2 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'INFORMED CONSENT' for first matching activity
        And Form save button is clicked
        And The form is no longer available
        Then The Study Activity is not found
        And 1 Activity that exchanged the placeholder is found in Study Activities table
        And 2 Activity that exchanged the placeholder is found in Study Activities table
        
    Scenario: [Actions][Exchange Activity] User must be able to exchange not submitted activity placeholder with more than activity from library
        When [API] Create Unsubmitted Requested Activity
        And [API] Requested Activity is added to the study
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        When The 'Exchange Activity' option is clicked from the three dot menu list
        And Form continue button is clicked
        And User waits for the table
        And 1 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'INFORMED CONSENT' for first matching activity
        And 2 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'INFORMED CONSENT' for first matching activity
        And Form save button is clicked
        And The form is no longer available
        Then The Study Activity is not found
        And 1 Activity that exchanged the placeholder is found in Study Activities table
        And 2 Activity that exchanged the placeholder is found in Study Activities table

    Scenario: [Actions][Exchange Activity] User must be able to exchange submitted activity placeholder with more than activity from study
        When [API] Create Submitted Requested Activity
        And [API] Requested Activity is added to the study
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And User intercepts available studies request
        When The 'Exchange Activity' option is clicked from the three dot menu list
        And Activity from studies is selected
        And User waits for available studies request
        And User selects study 'CDISC DEV-9881'
        And Form continue button is clicked
        And User waits for the table
        And 3 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And 4 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And Form save button is clicked
        And The form is no longer available
        Then The Study Activity is not found
        And 3 Activity that exchanged the placeholder is found in Study Activities table
        And 4 Activity that exchanged the placeholder is found in Study Activities table

    Scenario: [Actions][Exchange Activity] User must be able to exchange not submitted activity placeholder with more than activity from library
        When [API] Create Unsubmitted Requested Activity
        And [API] Requested Activity is added to the study
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And User intercepts available studies request
        When The 'Exchange Activity' option is clicked from the three dot menu list
        And Activity from studies is selected
        And User waits for available studies request
        And User selects study 'CDISC DEV-9881'
        And Form continue button is clicked
        And User waits for the table
        And 3 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And 4 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And Form save button is clicked
        And The form is no longer available
        Then The Study Activity is not found
        And 3 Activity that exchanged the placeholder is found in Study Activities table
        And 4 Activity that exchanged the placeholder is found in Study Activities table

    Scenario: [Actions][Exchange Activity] User must not be able to exchange activity with more than activity from library
        And [API] Study Activity is created and approved
        And [API] Activity is added to the selected study
        Given The page 'activities/list' is opened for current study
        When The Study Activity is found
        When The 'Exchange Activity' option is clicked from the three dot menu list
        And Form continue button is clicked
        And User waits for the table
        And 1 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And 2 Activity for exchanging the placeholder is searched for
        And User waits for the table
        Then The 2 activity is disabled for selection

    Scenario: [Actions][Exchange Activity] User must not be able to exchange activity with more than activity from study
        And [API] Study Activity is created and approved
        And [API] Activity is added to the selected study
        Given The page 'activities/list' is opened for current study
        When The Study Activity is found
        And User intercepts available studies request
        When The 'Exchange Activity' option is clicked from the three dot menu list
        And Activity from studies is selected
        And User waits for available studies request
        And User selects study 'CDISC DEV-9881'
        And Form continue button is clicked
        And User waits for the table
        And 3 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And 4 Activity for exchanging the placeholder is searched for
        And User waits for the table
        Then The 4 activity is disabled for selection

    Scenario: [Actions][Exchange Activity] User must be able to exchange activity placeholder with more than one activity in the Detailed SoA
        When [API] Create Submitted Requested Activity
        And [API] Requested Activity is added to the study
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When Action 'Exchange Activity' is selected for activity added to study via API
        And Form continue button is clicked
        And User waits for the table
        And 1 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'INFORMED CONSENT' for first matching activity
        And 2 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'INFORMED CONSENT' for first matching activity
        And Form save button is clicked
        And The form is no longer available
        And Detailed SoA table is loaded
        And Placeholder is no longer available
        And 1 Activity that exchanged the placeholder is found in table
        And 2 Activity that exchanged the placeholder is found in table

    Scenario: [Actions][Exchange Activity] User must be able to exchange activity with one activity from study in the Detailed SoA
        And [API] Study Activity is created and approved
        And [API] Activity is added to the selected study
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User search added activity in detailed SoA
        And User intercepts available studies request
        When Action 'Exchange Activity' is selected for activity added to study via API
        And Activity from studies is selected
        And User waits for available studies request
        And User selects study 'CDISC DEV-9881'
        And Form continue button is clicked
        And User waits for the table
        And 3 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And Form save button is clicked
        And The page is reloaded
        And Detailed SoA table is loaded
        And User expand table
        Then The 3 selected activity replaces previous activity in study
        Then The Activity is not visible in the SoA

    Scenario: [Actions][Exchange Activity] User must be able to exchange activity with one activity from library in the Detailed SoA
        And [API] Study Activity is created and approved
        And [API] Activity is added to the selected study
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User search added activity in detailed SoA
        And User intercepts available studies request
        When Action 'Exchange Activity' is selected for activity added to study via API
        And Form continue button is clicked
        And User waits for the table
        And 1 Activity for exchanging the placeholder is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'INFORMED CONSENT' for first matching activity
        And Form save button is clicked
        And The page is reloaded
        And Detailed SoA table is loaded
        And User expand table
        Then The 1 selected activity replaces previous activity in study
        Then The Activity is not visible in the SoA