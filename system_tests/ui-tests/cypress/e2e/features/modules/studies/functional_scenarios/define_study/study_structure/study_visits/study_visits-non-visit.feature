@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Visits - Non Visit

    See shared notes for study visits in file study-visit-intro-notes.txt

    Background: User is logged in and study has been selected
        Given The user is logged in
        Given User selects study with id 'CDISC DEV-9880'

    Scenario: [Create][Non visit] User must be able to create non visit for given study
        And [API] All visit groups uids are fetched
        And [API] All visit groups are removed
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Visit scheduling type is selected as 'NON_VISIT'
        And Form continue button is clicked
        And Epoch 'Basic' is selected for the visit
        And Form continue button is clicked
        And User waits for 1 seconds
        And Form save button is clicked
        And The pop up displays 'Visit added'
        When User searches for 'Non-visit'
        Then Study visit class is 'Non visit' and the timing is ''

    @BUG_ID:2776541
    Scenario: [EDIT][Special visit] User must not be able to edit non visit number
        When The page 'study_structure/visits' is opened for current study
        When User searches for 'Non-visit'
        And The 'Edit' option is clicked from the three dot menu list
        And Form continue button is clicked
        And Form continue button is clicked 
        Then Visit number field is disabled