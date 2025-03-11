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

    Scenario: User must be able to see the page buttons
        Given The '/studies/protocol_process' page is opened
        Then The following buttons are visible
            | buttons           |
            | Select study     |
            | Add New Study    |
            | Study Structure  |
            | Study Purpose    |
            | Study Population |
            | Study Activities |

    Scenario: User must be able to use the Select Study button
        Given The '/studies/protocol_process' page is opened
        When The 'Select study' button is clicked in Protocol Process page
        Then The 'Select study ID or acronym' form is opened

    Scenario: User must be able to use the New Study Study button
        Given The '/studies/protocol_process' page is opened
        When The 'Add New Study' button is clicked in Protocol Process page
        Then The current URL is 'studies/select_or_add_study'

    Scenario Outline: User must be able to use the Study Structure button
        Given A test study is selected
        And The '/studies/protocol_process' page is opened
        When The 'Study Structure' button is clicked in Protocol Process page
        And The '<link>' is clicked in the dropdown
        Then The current URL is '<url>'

        Examples:
            | link           | url                                                |
            | Study Arms     | studies/Study_000001/study_structure/arms          |
            | Study Epochs   | studies/Study_000001/study_structure/epochs        |
            | Study Elements | studies/Study_000001/study_structure/elements      |
            | Study Visits   | studies/Study_000001/study_structure/visits        |
            | Design Matrix  | studies/Study_000001/study_structure/design_matrix |

    Scenario Outline: User must be able to use the Study Purpose button
        Given A test study is selected
        And The '/studies/protocol_process' page is opened
        When The 'Study Purpose' button is clicked in Protocol Process page
        And The '<link>' is clicked in the dropdown
        Then The current URL is '<url>'

        Examples:
            | link        | url                                           |
            | Study Title | studies/Study_000001/study_title              |
            | Objectives  | studies/Study_000001/study_purpose/objectives |
            | Endpoints   | studies/Study_000001/study_purpose/endpoints  |

    Scenario Outline: User must be able to use the Study Population button
        Given A test study is selected
        And The '/studies/protocol_process' page is opened
        When The 'Study Population' button is clicked in Protocol Process page
        And The '<link>' is clicked in the dropdown
        Then The current URL is '<url>'

        Examples:
            | link                   | url                                                              |
            | Study Population       | studies/Study_000001/population                                  |
            | Inclusion Criteria     | studies/Study_000001/selection_criteria/Inclusion%20Criteria     |
            | Exclusion Criteria     | studies/Study_000001/selection_criteria/Exclusion%20Criteria     |
            | Run-in Criteria        | studies/Study_000001/selection_criteria/Run-in%20Criteria        |
            | Randomisation Criteria | studies/Study_000001/selection_criteria/Randomisation%20Criteria |
            | Dosing Criteria        | studies/Study_000001/selection_criteria/Dosing%20Criteria        |
            | Withdrawal Criteria    | studies/Study_000001/selection_criteria/Withdrawal%20Criteria    |


    Scenario Outline: User must be able to use the Study Activites button
        Given A test study is selected
        And The '/studies/protocol_process' page is opened
        When The 'Study Activities' button is clicked in Protocol Process page
        And The '<link>' is clicked in the dropdown
        Then The current URL is '<url>'

        Examples:
            | link             | url                                      |
            | Study Activities | studies/Study_000001/activities/list     |
            | Detailed SoA     | studies/Study_000001/activities/soa |