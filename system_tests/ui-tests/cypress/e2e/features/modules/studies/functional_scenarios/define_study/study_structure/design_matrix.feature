@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Design Matrix

    As a system user,
    I want the system to ensure to [Scenario],
    So that I can make complete and consistent study design specifications.

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [Test data] Data needed for verfication of design specification is created
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] Uid of study type 'Investigational Arm' is fetched
        And [API] The Study Arm exists within selected study
        And [API] Uids are fetched for element subtype 'Run-in'
        And [API] Element is created for the current study
        And [API] Uids are fetched for element subtype 'Treatment'
        And [API] Element is created for the current study
        
    Scenario: [Navigation] User must be able to open the page for Study Design Matrix
        And The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Design Matrix' tab is selected
        Then The current URL is '/study_structure/design_matrix'

    Scenario: [Table][Columns][Names] User must be able to see the page structure for Study Design Matrix
        Given The page 'study_structure/design_matrix' is opened for current study
        And Column 'Run-in' is made visible
        And Column 'Intervention' is made visible
        Then A table is visible with following headers
            | headers          |
            | Study Arm        |
            | Branches         | 
            | Run-in           |
            | Intervention     |

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The page 'study_structure/design_matrix' is opened for current study
        And Column 'Run-in' is made visible
        And Column 'Intervention' is made visible
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario: [Assign Elements] User must be able to assign study elements to epochs
        And User sets row page to 10 in the settings menu
        Given The page 'study_structure/design_matrix' is opened for current study
        And Column 'Run-in' is made visible
        And Column 'Intervention' is made visible
        And User waits for the table
        And The pencil button is clicked
        Then User triggers dropdown for element assignment to epoch 'Run-in'
        And 0 element is selected
        Then User triggers dropdown for element assignment to epoch 'Intervention'
        And 1 element is selected
        And User saves changes made in the edition mode
        Then The pop up displays 'Design Matrix updated' 

    Scenario: [Transition rules] User must be able to set transition rules
        And User sets row page to 10 in the settings menu
        Given The page 'study_structure/design_matrix' is opened for current study
        And Column 'Run-in' is made visible
        And Column 'Intervention' is made visible
        And User waits for the table
        When Transion rules are enabled
        And The pencil button is clicked
        Then User open transition rules edit mode for epoch 'Run-in'
        And Transition rules edit window is opened
        And User sets transition rule
        When Form save button is clicked
        And User saves changes made in the edition mode
        Then The pop up displays 'Design Matrix updated'
        And Transition rule is visible in the table for epoch 'Run-in'
        
    Scenario: [Transition rules] User must be able to toggle transition rule on and off
        And User sets row page to 10 in the settings menu
        Given The page 'study_structure/design_matrix' is opened for current study
        And Column 'Run-in' is made visible
        And Column 'Intervention' is made visible
        And User waits for the table
        When Transion rules are enabled
        Then Transition rule is visible in the table for epoch 'Run-in'
        When Transion rules are disabled
        Then Transition rule is not visible in the table for epoch 'Run-in'

    Scenario: [Transition rules] User must be able to see transition rules in the SDTM Study Design Datasets Trial Arms
        Given The page 'sdtm_study_design_datasets/tab-0' is opened for current study
        And User waits for the table
        Then Transition rule is searched
        And The transition rule is visible in the correct table column

    Scenario: [Transition rules] User must be able to see warning if transition rule exceeds 200 characters
        And User sets row page to 10 in the settings menu
        Given The page 'study_structure/design_matrix' is opened for current study
        And Column 'Run-in' is made visible
        And Column 'Intervention' is made visible
        And User waits for the table
        When Transion rules are enabled
        And The pencil button is clicked
        Then User open transition rules edit mode for epoch 'Run-in'
        And The transition rule is changed to have 201 characters
        Then The warning message about transition rule exceeding 200 characters is displayed
        When Form save button is clicked
        And The form is not closed
        Then The transition rule is changed to have 200 characters
        When Form save button is clicked
        And User saves changes made in the edition mode
        Then The pop up displays 'Design Matrix updated'
        And Transition rule is visible in the table for epoch 'Run-in'
        Given The page 'sdtm_study_design_datasets/tab-0' is opened for current study
        And User waits for the table
        Then Transition rule is searched
        And The transition rule is visible in the correct table column
