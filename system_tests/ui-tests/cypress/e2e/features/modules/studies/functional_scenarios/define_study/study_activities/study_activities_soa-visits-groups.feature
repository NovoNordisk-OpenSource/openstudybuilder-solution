@REQ_ID:xxx @development_only
Feature: Studies - Study Activities - Study Visits groups
    See shared notes for study visits in file study-visit-intro-notes.txt

    Background: User is logged in and study has been selected
        Given The user is logged in
        Given User selects study with id 'CDISC DEV-9880'
        And [API] All visit groups uids are fetched
        And [API] All visit groups are removed
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And The study visits uid array is cleared

    Scenario: [Test data] Test data for testing study visits groups must exists
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] The static visit data is fetched

    Scenario: [Collapse][Range] User must be able to collapse visit in range
        Given [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 4
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, V3, V4'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        And Option for collapsing in 'range' is selected
        And Form save button is clicked
        Then Visits are collapsed as 'V2-V4' in detailed SoA view
        And Visits study weeks are collapsed as '1-4' in detailed SoA view
        And The page 'study_structure/visits' is opened for current study
        And Visits 'V2, V3, V4' have group displayed as 'V2-V4' in table

    Scenario: [Collapse][List] User must be able to collapse visit in list
        Given [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 4
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, V3, V4'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        And Option for collapsing in 'list' is selected
        And Form save button is clicked
        Then Visits are collapsed as 'V2,V3,V4' in detailed SoA view
        And Visits study weeks are collapsed as '1,2,4' in detailed SoA view
        And The page 'study_structure/visits' is opened for current study
        And Visits 'V2, V3, V4' have group displayed as 'V2,V3,V4' in table

    Scenario: [Collapse][Global Anchor Visit] User must be able to collapse global anchor visit
        Given [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V1, V2'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        And Option for collapsing in 'list' is selected
        And Form save button is clicked
        Then Visits are collapsed as 'V1,V2' in detailed SoA view
        And Visits study weeks are collapsed as '0,1' in detailed SoA view
        And The page 'study_structure/visits' is opened for current study
        And Visits 'V1, V2' have group displayed as 'V1,V2' in table

    Scenario: [Collapse][Range][Remove] User must be able to remove range visit group
        Given [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 4
        And [API] Visits group with format 'range' is created
        And The page 'activities/soa' is opened for current study
        And Visit group delete button is clicked
        And Action is confirmed by clicking continue
        Then Visits are no longer collapsed in detailed SoA view
        And Visits study weeks are no longer collapsed in detailed SoA view
        And The page 'study_structure/visits' is opened for current study
        And Visits are no longer grouped in table

    Scenario: [Collapse][List][Remove] User must be able to remove list visit group
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 4
        And [API] Visits group with format 'list' is created
        And The page 'activities/soa' is opened for current study
        And Visit group delete button is clicked
        And Action is confirmed by clicking continue
        Then Visits are no longer collapsed in detailed SoA view
        And Visits study weeks are no longer collapsed in detailed SoA view
        And The page 'study_structure/visits' is opened for current study
        And Visits are no longer grouped in table

    Scenario: [Collapse][Negative case][Inconsecutive visit] User must be able to collapse inconsecutive visits as List
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 4
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, V4'
        And Button for collapsing visits is clicked
        And Option for collapsing in 'list' is selected
        And Form save button is clicked
        Then Visits are collapsed as 'V2,V4' in detailed SoA view
        And Visit group delete button is clicked
        And Action is confirmed by clicking continue
        Then Visits are no longer collapsed in detailed SoA view

    Scenario: [Collapse][Negative case][Epochs] User must not be able to collapse visits from different epochs
        Given [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Intervention'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, V3'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        Then The pop up displays "Given Visits can't be collapsed as they exist in different Epochs"

    Scenario: [Collapse][Negative case][Time reference] User must not be able to collapse visits with different time reference
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Screening', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, V3'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        Then The pop up displays "Visit 'V2' and 'V3' have the following properties different ['visit_type']"

    Scenario: [Collapse][Negative case][Visit type] User must not be able to collapse visits with different visit type
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Informed consent', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, V3'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        Then The pop up displays "Visit 'V2' and 'V3' have the following properties different ['visit_type']"

    Scenario: [Collapse][Negative case][Contact mode] User must not be able to collapse visits with different contact mode
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The dynamic visit data is fetched: contact mode 'Phone Contact', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, P3'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        Then The pop up displays "Visit 'V2' and 'P3' have the following properties different ['visit_contact_mode']"

    Scenario: [Collapse][Negative case][Visit Window] User must not be able to collapse visits with different visit window
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2, minVisitWindow 0, maxVisitWindow 5
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, V3'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        Then The pop up displays "Visit 'V2' and 'V3' have the following properties different ['max_visit_window_value']"

    Scenario: [Collapse][Negative case][Delete visit] User must not be able to delete visit that is part of the visit group
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, V3'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        And Option for collapsing in 'list' is selected
        And Form save button is clicked
        And The page 'study_structure/visits' is opened for current study
        And User search for visit with name 'Visit 2'
        And The 'Delete' option is clicked from the three dot menu list
        Then The pop up displays "The study visit can't be deleted as it is part of visit group V2,V3. The visit group should be uncollapsed first."

    Scenario: [Collapse][Negative case][Edit visit] User must not be able to edit visit epoch if it is part of the visit group
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, V3'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        And Option for collapsing in 'list' is selected
        And Form save button is clicked
        And The page 'study_structure/visits' is opened for current study
        And User search for visit with name 'Visit 2'
        And The 'Edit' option is clicked from the three dot menu list
        And Form continue button is clicked
        And Epoch 'Intervention' is selected for the visit
        And Form continue button is clicked
        And Form save button is clicked
        Then The pop up displays "The study visit can't be edited as it is part of visit group V2,V3. The visit group should be uncollapsed first."

    Scenario: [Collapse][Negative case][Edit visit] User must not be able to edit visit attributes if it is part of the visit group
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And The page 'activities/soa' is opened for current study
        When User selects visits 'V2, V3'
        And User waits for 1 seconds
        And Button for collapsing visits is clicked
        And Option for collapsing in 'list' is selected
        And Form save button is clicked
        And The page 'study_structure/visits' is opened for current study
        And User search for visit with name 'Visit 2'
        And The 'Edit' option is clicked from the three dot menu list
        And Form continue button is clicked
        And Form continue button is clicked
        And Time unit 'days' is selected for the visit
        And Form save button is clicked
        Then The pop up displays "The study visit can't be edited as it is part of visit group V2,V3. The visit group should be uncollapsed first."

    @manual_test
    Scenario: Footnote must be applied to all visits in visit group when collapsing
        Given The page 'activities/soa' is opened for current study
        And Multiple visits are defined for that study
        When User applies a footnote to one of the visits
        And The user collapses multiple visits including visit with footnote
        Then The footnote is applied onto all visits in the visit group