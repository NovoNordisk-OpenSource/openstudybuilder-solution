@REQ_ID:987736 @development_only
Feature: Studies - Study List - Copy Study - Study activities and schedules

    As a user, I want to clone a study including study activity groupings, study activities, instances, and activity schedules.

    Background: User must be logged in
        Given The user is logged in
        And The '/studies/select_or_add_study/active' page is opened

    Scenario: [Create][Positive case][Study activities][Schedules] User must be able to copy study including study activities and schedules
        Given User selects study with id 'CDISC DEV-9866'
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        Given The study visits uid array is cleared
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] Uid of study type 'Investigational Arm' is fetched
        And [API] The Study Arm with name 'Arm1' exists within selected study
        And [API] The Study Branch is created within selected study
        And [API] The Study Cohort is created within selected study
        And [API] Uids are fetched for element subtype 'Run-in'
        And [API] Element is created for the current study
        And [API] Link Study Element to Epoch and Study Arm within selected study
        And [API] Uids are fetched for element subtype 'Treatment'
        And [API] Element is created for the current study
        And [API] The Study Arm with name 'Arm2' exists within selected study
        And [API] The Study Arm with name 'Arm3' exists within selected study
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1, minVisitWindow -1, maxVisitWindow 1
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Intervention'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2, minVisitWindow 3, maxVisitWindow 7
        And [API] All Activities are deleted from selected study
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] Activity is assigned to the visit 0 in selected study
        And [API] Activity is assigned to the visit 1 in selected study
        And The '/studies/select_or_add_study/active' page is opened
        Given The Add Study button is clicked
        And The user selects to create study from existing study
        And New study project id, study number and study acronym are filled in
        And Form continue button is clicked
        And The user intercepts study statistics request
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        When The user selects 'Branches' category to be copied
        When The user selects 'Cohorts' category to be copied
        When The user selects 'Epochs' category to be copied
        When The user selects 'Study visits' category to be copied
        When The user selects 'Study activities' category to be copied
        When The user selects 'Schedules' category to be copied
        When The user selects 'Elements' category to be copied
        When The user selects 'Design matrix' category to be copied
        When User intercepts study clone request verifying structure and activity clone flags
        And Form save button is clicked
        And User waits for cloning request
        Then The study clone response is successful with submitted metadata
