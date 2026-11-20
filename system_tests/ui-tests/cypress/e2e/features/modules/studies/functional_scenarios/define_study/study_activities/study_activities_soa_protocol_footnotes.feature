@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Schedule of Activities - Protocol - Footnotes

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study SoA footnotes.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9884'

    # Scenario: [Test data] User must be able to create test data
        # And [API] All visit groups uids are fetched
        # And [API] All visit groups are removed
        # When [API] Study vists uids are fetched for selected study
        # When [API] Study visits in selected study are cleaned-up
        # And [API] All Activities fotnotes are deleted from selected study
        # Given [API] All Activities are deleted from selected study
        # And [API] All epochs assigned to the selected study are fetched
        # And [API] All epochs assigned to the selected study are deleted
        # Given [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        # And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        # And [API] The static visit data is fetched
        # And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        # And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        # And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        # And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        # And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        # And [API] Get SoA Group 'INFORMED CONSENT' id
        # And [API] Get class uid for activity instance creation
        # And [API] Group and subgroup are created and approved to be used for activity creation
        # And [API] Activity with data collection set to 1 and 'FirstActivity' included in the name is created and approved
        # And [API] The activity instance with name 'FirstInstance_API_' and isRequriedForActivity set to true is created and approved
        # And [API] Activity is added to the selected study
        # And [API] Activity is assigned to the visit 0 in selected study
        # And [API] Activity is assigned to the visit 1 in selected study
        # And [API] Activity with data collection set to 1 and 'SecondActivity' included in the name is created and approved
        # And [API] The activity instance with name 'SecondInstance_API_' and isRequriedForActivity set to true is created and approved
        # And [API] Activity is added to the selected study
        # And [API] Activity is assigned to the visit 1 in selected study
        # And [API] Activity with data collection set to 1 and 'MissingInstance' included in the name is created and approved
        # And [API] Activity is added to the selected study
        # And [API] Activity is assigned to the visit 0 in selected study
        # And [API] Activity with data collection set to 0 and 'NoDataCollection' included in the name is created and approved
        # And [API] Activity is added to the selected study
        # And [API] Activity is assigned to the visit 0 in selected study
        # And [API] Activity with data collection set to 1 and 'RequiredForActivity' included in the name is created and approved
        # And [API] The activity instance with isRequriedForActivity set to true is created and approved
        # And [API] Activity is added to the selected study
        # And [API] Activity with data collection set to 1 and 'DefaultForActivity' included in the name is created and approved
        # And [API] The activity instance with isDefaultForActivity set to true is created and approved
        # And [API] Activity is added to the selected study
        # And [API] User gets data of activity with name 'Albumin', group 'Laboratory Assessments', subgroup 'Urinalysis'
        # And [API] Activity is added to the selected study
        # And [API] Activity is assigned to the visit 0 in selected study
        # And [API] Activity is assigned to the visit 1 in selected study
        # And [API] User gets data of activity with name 'Albumin', group 'Laboratory Assessments', subgroup 'Biochemistry'
        # And [API] Activity is added to the selected study
        # And [API] Activity is assigned to the visit 0 in selected study
        # And [API] Activity is assigned to the visit 1 in selected study
        # And [API] Get SoA Group 'BIOMARKERS' id
        # When [API] Create Submitted Requested Activity
        # And [API] Requested Activity is added to the study
        # When [API] Create Unsubmitted Requested Activity
        # And [API] Requested Activity is added to the study

    Scenario: User must be informed when no footnotes are defined
        Given [API] All Activities fotnotes are deleted from selected study
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        And The 'manage-footnotes-button' button is clicked
        Then The manage footnotes dialog contains 'No footnotes have been added to this study yet.'

    Scenario: User must be guided through cells selection for footnote creation
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The 'manage-footnotes-button' button is clicked
        And The 'create-footnotes-button' button is clicked
        Then The manage footnotes dialog contains "Click on the cells in the protocol you want the new footnote to be added to. Click a selected cell again to deselect it."

    Scenario: User must be able to select cells for creation of footnotes
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The 'manage-footnotes-button' button is clicked
        When The 'create-footnotes-button' button is clicked
        And The user selects cells for footnote creation
        Then The selected cells are highlighted for footnote creation
        And The manage footnotes dialog contains 'Selected cells: 2'

    Scenario: [Footnotes][Create][Scratch] User must be able to create footnote from scratch
        Given [API] All Activities fotnotes are deleted from selected study
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The 'manage-footnotes-button' button is clicked
        When The 'create-footnotes-button' button is clicked
        When The user selects option to create a footnote from 'scratch'
        When The user creates a footnote from scratch
        Then The footnote is successfully created from scratch

    Scenario: [Footnotes][Create][Standards] User must be able to create footnote from standards
        Given [API] All Activities fotnotes are deleted from selected study
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The 'manage-footnotes-button' button is clicked
        When The 'create-footnotes-button' button is clicked
        When The user selects option to create a footnote from 'standards'
        When The user creates a footnote from standards
        Then The footnote is successfully created from standards

    Scenario: [Footnotes][Create][Studies] User must be able to create footnote from studies
        Given [API] All Activities fotnotes are deleted from selected study
        Given [API] The footnote exists for study '9885'
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The 'manage-footnotes-button' button is clicked
        When The 'create-footnotes-button' button is clicked
        When The user selects option to create a footnote from 'studies'
        When The user creates a footnote from studies
        Then The footnote is successfully created from studies

    Scenario: User must be able to link footnote to Activity Group
        Given [API] All Activities fotnotes are deleted from selected study
        And [API] The footnote exists for current study
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The user opens link dialog for the "StudyActivityGroup"
        And The user selects footnote
        Then The footnote is successfully linked

    Scenario: User must be able to link footnote to Activity Subgroup
        Given [API] All Activities fotnotes are deleted from selected study
        And [API] The footnote exists for current study
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The user opens link dialog for the "StudyActivitySubGroup"
        And The user selects footnote
        Then The footnote is successfully linked

    Scenario: User must be able to link footnote to Activity
        Given [API] All Activities fotnotes are deleted from selected study
        And [API] The footnote exists for current study
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The user opens link dialog for the "StudyActivitySchedule"
        And The user selects footnote
        Then The footnote is successfully linked

    Scenario: User must be able to link footnote to Epoch
        Given [API] All Activities fotnotes are deleted from selected study
        And [API] The footnote exists for current study
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The user opens link dialog for the study epoch
        And The user selects footnote
        Then The footnote is successfully linked

    Scenario: User must be able to link footnote to Visit
        Given [API] All Activities fotnotes are deleted from selected study
        And [API] The footnote exists for current study
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The user opens link dialog for the study visit
        And The user selects footnote
        Then The footnote is successfully linked

    Scenario: User must be able to edit footnote
        Given [API] All Activities fotnotes are deleted from selected study
        And [API] The footnote exists for current study
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The user opens link dialog for the study visit
        And The user selects footnote
        And The 'close-footnotes-button' button is clicked
        And The 'manage-footnotes-button' button is clicked
        And The user intercepts SoA Footnotes 'edit' request
        And The footnote is edited
        Then The footnote is successfully updated and the link remains

    Scenario: User must be able to delete footnote
        Given [API] All Activities fotnotes are deleted from selected study
        And [API] The footnote exists for current study
        When The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When The user opens link dialog for the study visit
        And The user selects footnote
        And The 'close-footnotes-button' button is clicked
        And The 'manage-footnotes-button' button is clicked
        And The user intercepts SoA Footnotes 'delete' request
        And The footnote is deleted
        Then The footnote is successfully deleted