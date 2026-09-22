@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Visits - Special Visits

    See shared notes for study visits in file study-visit-intro-notes.txt

    Background: User is logged in and study has been selected
        Given The user is logged in
        Given User selects study with id 'CDISC DEV-9880'

    Scenario: [Test data] User prepares the study data
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] Global Anchor visit within epoch 'Run-in' exists
        And [API] All visit groups uids are fetched
        And [API] All visit groups are removed
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] The static visit data is fetched
        And The study visits uid array is cleared
        And [API] Global Anchor visit within epoch 'Run-in' exists

    Scenario: [Create][Special visit] User must be able to create special visit for given epoch
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Visit scheduling type is selected as 'SPECIAL_VISIT'
        And Form continue button is clicked
        And Epoch 'Run-in' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Treatment'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Visit 1'
        And Form save button is clicked
        And The pop up displays 'Visit added'
        And User searches for 'V1A'
        And Study visit class is 'Special visit' and the timing is ''
        When Add visit button is clicked
        And Visit scheduling type is selected as 'SPECIAL_VISIT'
        And Form continue button is clicked
        And Epoch 'Run-in' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Treatment'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Visit 1'
        And Form save button is clicked
        And The pop up displays 'Visit added'
        And User searches for 'V1B'
        And Study visit class is 'Special visit' and the timing is ''

    Scenario: [Create][Discontinuation visit] User must be able to create discontinuation special visit for given epoch
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Visit scheduling type is selected as 'SPECIAL_VISIT'
        And Form continue button is clicked
        And Epoch 'Run-in' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Early discontinuation'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Visit 1'
        And Form save button is clicked
        And The pop up displays 'Visit added'
        And User searches for 'V1X'
        And Study visit class is 'Special visit' and the timing is ''

    @BUG_ID:2844670
    Scenario: [EDIT][Special visit] User must be able to edit special visit
        Given User intercepts epochs data
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs data
        And User waits for 1 seconds
        When User searches for 'V1B'
        Then Only one row is present
        And The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And User waits for form data to load
        And Form continue button is clicked
        And Form continue button is clicked
        And Visit description is changed to 'Testing edition'
        And Form save button is clicked
        Then Visit description is displayed in the table as 'Testing edition'