@REQ_ID:987736
Feature: Studies - Study List - Study List - Study Template

    As a user, I want to verify that I can create a new study from an existing study in the Study List page and the data is copied correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Test data] User must be able to create a study with fully defined structure to be used during study creation test
        Given User selects study with id 'CDISC DEV-9882'
        And [API] User fetches term uid for reason for unlocking 'Other'
        And [API] Status of study is checked and unlocked in major version '0' and minor version '1'
        And [API] Study title is set for selected study
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
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for locking 'Study Specification Updates'
        And [API] Status of study is checked and locked in major version '0' and minor version '1'

    Scenario: [Select Template] User must be able to select locked study as a Template
        Given The '/library/template_study' page is opened
        And Study 'CDISC DEV-9882' is searched and found
        When Study is selected as a template
        And User intercepts all available studies request
        Given The 'studies/select_or_add_study' page is opened
        And User waits for the table
        And User waits for available studies request
        And The Add Study button is clicked
        Then The option to create study based on study template is available

    Scenario: [Select Template] User must be able to create a study based on study template
        And User intercepts all available studies request
        Given The 'studies/select_or_add_study' page is opened
        And User waits for available studies request
        And User waits for the table
        And The Add Study button is clicked
        When The user selects to create study from study template
        And New study project id, study number and study acronym are filled in
        And Form save button is clicked
        And The confirmation dilog is no longer available
        And User waits for the table
        And Study is found
        Then The study is visible within the table
        And The page 'activities/list' is opened for current study
        And Activity is searched for and found
        And The page 'study_structure/visits' is opened for current study
        And User search for visit with name 'Visit 1'
        And User search for visit with name 'Visit 2'
        And User search for visit with name 'Visit 3'
        And The page 'activities/soa' is opened for current study
        And User expand table
        And Visit 0 is not selected for the activity
        And Visit 1 is selected for the activity
        And Visit 2 is selected for the activity

    Scenario: [Deselect Template] User must be able to deselect locked study as a Template
        Given The '/library/template_study' page is opened
        And Study 'CDISC DEV-9882' is searched and found
        When Study is deselected as a template
        And User intercepts all available studies request
        Given The 'studies/select_or_add_study' page is opened
        And User waits for available studies request
        And The Add Study button is clicked
        Then The option to create study based on study template is not available

    Scenario: [Select Template][Negative Scenario] User must not be able to select study as a Template if it is not locked
        Given User selects study with id 'CDISC DEV-9882'
        And [API] User fetches term uid for reason for unlocking 'Other'
        And [API] Status of study is checked and unlocked in major version '0' and minor version '1'
        When The '/library/template_study' page is opened
        Then Study 'CDISC DEV-9882' is searched and not found