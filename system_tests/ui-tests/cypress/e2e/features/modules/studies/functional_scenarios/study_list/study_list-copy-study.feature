@REQ_ID:987736 @development_only
Feature: Studies - Study List - Study List - Copy Study

    As a user, I want to verify that I can create a new study from an existing study in the Study List page and the data is copied correctly.

    Background: User must be logged in
        Given The user is logged in
        And The 'studies/select_or_add_study' page is opened
        And User intercepts all available studies request
        And User waits for available studies request

    Scenario: [Test data] User must be able to create a study with fully defined structure to be used during study creation test
        Given User selects study with id 'CDISC DEV-9866'
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
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

    Scenario: [Copy][Study selection] User must be able to select which study to use for structury copying
        Given The Add Study button is clicked
        And The user selects to create study from existing study
        And New study project id, study number and study acronym are filled in
        And Form continue button is clicked
        Then The user is presented study selection dropdown

    Scenario: [Copy][Preview] User must be able to preview structure of copied study
        Given The Add Study button is clicked
        And The user selects to create study from existing study
        And New study project id, study number and study acronym are filled in
        And Form continue button is clicked
        And The user intercepts study statistics request
        When The user selects study to use for copy
        Then The user is presented with visual representation of designated study structure

    Scenario: [Copy][Arms category] User must be able to select Arms category
        Given The Add Study button is clicked
        And The user selects to create study from existing study
        And New study project id, study number and study acronym are filled in
        And Form continue button is clicked
        And The user intercepts study statistics request        
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        Then The 'Branches' category with 'branch_count' derived from source study is presented for selection

    Scenario: [Copy][Branches category] User must be able to select Branches category
        Given The Add Study button is clicked
        And The user selects to create study from existing study
        And New study project id, study number and study acronym are filled in
        And Form continue button is clicked
        And The user intercepts study statistics request     
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        When The user selects 'Branches' category to be copied
        Then The 'Cohorts' category with 'cohort_count' derived from source study is presented for selection

    Scenario: [Copy][Cohorts category] User must be able to select Cohorts category
        Given The Add Study button is clicked
        And The user selects to create study from existing study
        And New study project id, study number and study acronym are filled in
        And Form continue button is clicked
        And The user intercepts study statistics request
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        When The user selects 'Branches' category to be copied
        When The user selects 'Cohorts' category to be copied
        Then The 'Cohorts' category with 'cohort_count' derived from source study is presented for selection

    Scenario: [Copy][Epochs category] User must be able to select Epochs category
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
        Then The 'Include footnotes' option is visible under 'Epochs' category showing appropiate 'epoch_footnote_count' number
        Then The 'Study visits' category with 'visit_count' derived from source study is presented for selection
    
    Scenario: [Copy][Visits category] User must be able to select Study Visits category
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
        Then The 'Include footnotes' option is visible under 'Study visits' category showing appropiate 'visit_footnote_count' number
        Then The 'Elements' category with 'element_count' derived from source study is presented for selection

    Scenario: [Copy][Elements category] User must be able to select elements category
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
        When The user selects 'Elements' category to be copied
        Then The Design matrix category is presented for selection
        
    Scenario: [Create][Positive case] User must be able to copy study structure after correctly filling the form
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
        When The user selects 'Elements' category to be copied
        When The user selects 'Design matrix' category to be copied
        When User intercepts cloning request
        And Form save button is clicked
        And User waits for cloning request
        Then The new study is created with selected data

    Scenario: [Create][Mandatory fields] User must not be able to copy study structure without selecting any category to copy
        Given The Add Study button is clicked
        And The user selects to create study from existing study
        And New study project id, study number and study acronym are filled in
        And Form continue button is clicked
        And The user intercepts study statistics request
        When The user selects study to use for copy
        And Form save button is clicked
        Then The pop up displays 'You must select something to copy'

    Scenario: [Create][Mandatory fields] User must not be able to use existing study number for new study
        Given The Add Study button is clicked
        And The user selects to create study from existing study
        And The user selects study project and uses existing study number
        And The user intercepts study statistics request
        And Form continue button is clicked
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        And Form save button is clicked
        Then The pop up displays "Study with Study Number '9876' already exists."
