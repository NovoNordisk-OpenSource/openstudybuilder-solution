@REQ_ID:1074274
Feature: Studies - Protocol Process

    As a User I want to see the process map in form of buttons linking to necessary pages

    Background: User must be logged in
        Given The user is logged in

    #hidden feature
    #Scenario: User must be able to navigate to the Protocol Process page
    #    Given The '/studies' page is opened
    #    When The 'Protocol Process' submenu is clicked in the 'Process Overview' section
    #    Then The current URL is 'studies/protocol_process'

    Scenario: [Navigation][Buttons] User must be able to see the page buttons
        Given The '/studies/protocol_process' page is opened
        Then The following buttons are visible
            | buttons           |
            | Select study     |
            | Add New Study    |
            | Study Structure  |
            | Study Purpose    |
            | Study Population |
            | Study Activities |

    Scenario: [Navigation][Select Study] User must be able to use the Select Study button
        Given The '/studies/protocol_process' page is opened
        When User clicks button 'Select study'
        Then The 'Select a study' form is opened

    Scenario: [Navigation][New Study] User must be able to use the New Study Study button
        Given The '/studies/protocol_process' page is opened
        When User clicks button 'Add New Study'
        Then The current URL is 'studies/select_or_add_study'

    Scenario Outline: [Navigation][Study Structure] User must be able to use the Study Structure button
        Given User selects study with id 'CDISC DEV-9876'
        And The '/studies/protocol_process' page is opened
        When User clicks button 'Study Structure'
        And The '<link>' is clicked in the dropdown
        Then The current URL is '<url>'

        Examples:
            | link           | url                                                |
            | Study Arms     | /study_structure/arms          |
            | Study Epochs   | /study_structure/epochs        |
            | Study Elements | /study_structure/elements      |
            | Study Visits   | /study_structure/visits        |
            | Design Matrix  | /study_structure/design_matrix |

    Scenario Outline: [Navifation][Study Purpose] User must be able to use the Study Purpose button
        Given User selects study with id 'CDISC DEV-9876'
        And The '/studies/protocol_process' page is opened
        When User clicks button 'Study Purpose'
        And The '<link>' is clicked in the dropdown
        Then The current URL is '<url>'

        Examples:
            | link        | url                                           |
            | Study Title | /study_title              |
            | Objectives  | /study_purpose/objectives |
            | Endpoints   | /study_purpose/endpoints  |

    Scenario Outline: [Navigation][Study Population] User must be able to use the Study Population button
        Given User selects study with id 'CDISC DEV-9876'
        And The '/studies/protocol_process' page is opened
        When User clicks button 'Study Population'
        And The '<link>' is clicked in the dropdown
        Then The current URL is '<url>'

        Examples:
            | link                   | url                                                              |
            | Study Population       | /population                                  |
            | Inclusion Criteria     | /selection_criteria/Inclusion%20Criteria     |
            | Exclusion Criteria     | /selection_criteria/Exclusion%20Criteria     |
            | Run-in Criteria        | /selection_criteria/Run-in%20Criteria        |
            | Randomisation Criteria | /selection_criteria/Randomisation%20Criteria |
            | Dosing Criteria        | /selection_criteria/Dosing%20Criteria        |
            | Withdrawal Criteria    | /selection_criteria/Withdrawal%20Criteria    |


    Scenario Outline: [Navigation][Study Activities] User must be able to use the Study Activites button
        Given User selects study with id 'CDISC DEV-9876'
        And The '/studies/protocol_process' page is opened
        When User clicks button 'Study Activities'
        And The '<link>' is clicked in the dropdown
        Then The current URL is '<url>'

        Examples:
            | link             | url                                      |
            | Study Activities | /activities/list     |
            | Detailed SoA     | /activities/soa |