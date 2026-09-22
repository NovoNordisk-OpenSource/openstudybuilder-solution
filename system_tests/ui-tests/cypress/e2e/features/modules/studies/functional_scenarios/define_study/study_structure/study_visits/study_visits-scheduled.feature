@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Visits

    See shared notes for study visits in file study-visit-intro-notes.txt

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study visits.

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: [Create][Pre-condition] User must not be able to add a new Study Visit when no Study Epoch has been defined
        Given User selects study with id 'CDISC DEV-9876'
        When The page 'study_structure/visits' is opened for current study
        When The 'add-visit' button is clicked
        Then The user is prompted with a notification message "To add visits, you need to difine the epochs first. Would you like to define epochs?"
        And The 'Add epoch' button is visible
        And The 'Cancel' button is visible

    Scenario: [Create][Mandatory fields] User must not be able to create an visit without epoch selected
        When User selects study with id 'CDISC DEV-0'
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And User waits for 3 seconds
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        Then The validation appears for missing study period

    Scenario: [Create][Mandatory fields] User must not be able to create an visit without type, contact mode, time reference and timing defined
        When User selects study with id 'CDISC DEV-0'
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And User waits for 3 seconds
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And First available epoch is selected
        And Form continue button is clicked
        And Form save button is clicked
        Then The validation appears for missing visit type
        And The validation appears for missing contact mode
        And The validation appears for missing time reference
        And The validation appears for missing visit timing
    
    Scenario: [Create][Fields check] User must not be able to select time referece for an anchor visit
        When User selects study with id 'CDISC DEV-9880'
        And [API] All visit groups uids are fetched
        And [API] All visit groups are removed
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And User waits for 3 seconds
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Run-in' is selected for the visit
        And Form continue button is clicked
        And Anchor visit checkbox is checked
        Then Time Reference for anchor visit is disabled for edition

    Scenario: [Create][First visit][Visit window warning] User must be presented with waring regarding visit window selection
        When User selects study with id 'CDISC DEV-9880'
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Run-in' is selected for the visit
        And Form continue button is clicked
        Then Warning about visit window unit selection is displayed

    Scenario: [Create][Not first visit][Visit window warning] User must be presented with waring regarding visit window selection
        When User selects study with id 'CDISC DEV-0'
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And First available epoch is selected
        And Form continue button is clicked
        Then Warning about visit window unit selection is displayed

    @smoke_test
    Scenario: [Create][Anchor visit][Positive case] User must be able to create an anchor visit
        When User selects study with id 'CDISC DEV-9880'
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Run-in' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Randomisation'
        And Contact mode is selected as 'On Site Visit'
        And Time unit 'day' is selected for the visit
        And Anchor visit checkbox is checked
        When Form save button is clicked
        Then The new Anchor Visit is visible within the Study Visits table

    @manual_test
    Scenario: [Create] User must be able to create an information visit with visit 0
        When User selects study with id 'CDISC DEV-0'
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And The page 'study_structure/visits' is opened for current study
        Given User selects study with id 'CDISC DEV-9876'
        And The epoch exists in selected study
        And The page 'study_structure/visits' is opened for current study
        And The first scheduled visit is created with the visit type as an Information visit
        And The visit timing is set to the lowest timing of all existing visit when compared to the Global Anchor time reference
        Then The Information visit should be created with 0 as Visit number
        And No reordering of existing visits should happen

    Scenario: [Create][Anchor visit][Negative case] User must not be able to create an anchor visit if one already exists
        When User selects study with id 'CDISC DEV-9880'
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Run-in' is selected for the visit
        And Form continue button is clicked
        And User waits for 1 seconds
        Then The Anchor visit checkbox is disabled

    Scenario: [Actions][Edit] User must be able to edit the study visit
        When User selects study with id 'CDISC DEV-9880'
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        When The page 'study_structure/visits' is opened for current study
        When User searches for 'V2'
        And The 'Edit' option is clicked from the three dot menu list
        And Form continue button is clicked
        And Form continue button is clicked
        And Visit description is changed to 'Testing edition'
        And Form save button is clicked
        Then Visit description is displayed in the table as 'Testing edition'

    Scenario: [Actions][Edit][Fields check] User must be able to update study visit epoch
        When User selects study with id 'CDISC DEV-9880'
        When The page 'study_structure/visits' is opened for current study
        When User searches for 'V2'
        And The 'Edit' option is clicked from the three dot menu list
        And Form continue button is clicked
        Then The study epoch field is enabled for editing

    @pending_implementation
    Scenario: User must not be able to update study epoch without updating the timing to correct chronological order
        Given The '/studies/Study_000002/study_structure/visits' page is opened
        And There are at least 3 visits created for the study
        When The user tries to update last treatment visit epoch to Screening without updating the timing
        Then The pop up displays "The following visit can't be created as the next Epoch Name 'Treatment' starts at the '1' Study Day"

    @manual_test
    Scenario: User must be able to edit the study information visit with visit 0 to other visit type
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A study information visit with visit 0 is created
        When This study information visit is edited to be a different visit type
        Then This visit can no longer be Visit 0
        And Reordering will occur of existing visits

    @manual_test
    Scenario: User must be able to edit the study information visit with visit 0 to same visit type
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A study information visit with visit 0 is created
        When This study information visit is edited to the same visit type
        Then This visit should be given the visit number of 0
        When This visit is edited to higher visit timing compare to the Global Anchor time reference
        Then Reordering of other visits will occur

    Scenario: [Actions][Delete] User must be able to delete the study visit
        When User selects study with id 'CDISC DEV-9880'
        When The page 'study_structure/visits' is opened for current study
        And The 'Delete' option is clicked from the three dot menu list
        Then The pop up displays 'Visit deleted'

    @manual_test
    Scenario: User must be able to delete the study information visit with visit 0
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A study information visit with visit 0 is created
        When This study information visit is deleted
        Then No reordering of other visits will occur

    @manual_test
    Scenario: User must be able to delete the study information visit without visit 0
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A study information visit without visit 0 is created
        When This study information visit is deleted
        Then The reordering of other visits will occur

    Scenario: [Create][Study Vists][Same Day Visits] User must be able to define two visits with same visit day in the same epoch
        Given User selects study with id 'CDISC DEV-9876'
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1, minVisitWindow -1, maxVisitWindow 1
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        And Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Run-in' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Pre-screening'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Global anchor visit'
        And Visit timing 7 is selected for the visit
        And User intercepts create visit request
        When Form save button is clicked
        Then The study visit is created

    Scenario: [Create][Study Vists][Same Day Visits] User must be able to define two visits with same visit day in the neighboring epoch
        Given User selects study with id 'CDISC DEV-9876'
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1, minVisitWindow -1, maxVisitWindow 1
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        And Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Intervention' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Pre-screening'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Global anchor visit'
        And Visit timing 7 is selected for the visit
        And User intercepts create visit request
        When Form save button is clicked
        Then The study visit is created

    Scenario: [Create][Study Vists][Same Day Visits] User must be able to define more than two visits with same visit day in the same epoch
        Given User selects study with id 'CDISC DEV-9876'
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1, minVisitWindow -1, maxVisitWindow 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1, minVisitWindow -1, maxVisitWindow 1
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        And Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Run-in' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Pre-screening'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Global anchor visit'
        And Visit timing 7 is selected for the visit
        When Form save button is clicked
        Then The pop up displays 'Visit added'

    Scenario: [Create][Study Vists][Same Day Visits] User must be able to define more than two visits with same visit day in the neighboring epoch
        Given User selects study with id 'CDISC DEV-9876'
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1, minVisitWindow -1, maxVisitWindow 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1, minVisitWindow -1, maxVisitWindow 1
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        And Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Intervention' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Pre-screening'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Global anchor visit'
        And Visit timing 7 is selected for the visit
        When Form save button is clicked
        Then The pop up displays 'Visit added'

