@REQ_ID:XXX
Feature: Studies - Define Study - Study Structure - Arms, Branches, Cohorts, Elements, Design Matrix - E2E verification

    As a system user,
    I want the system to ensure [Scenario],
    So that I must be able to make complete and consistent specification of study structure, including arms, branches, cohorts, elements and design matrix.

    Background: User is logged in and study has been selected
        Given The user is logged in
        When User selects study with id 'CDISC DEV-9844'
        Then User intercepts the design class request
        And User intercepts the study arms list request

    Scenario: [Test data] User must be able to prepare data through API to conduct the study structure E2E verification
        Given [API] All visit groups uids are fetched
        And [API] All visit groups are removed
        And [API] Study vists uids are fetched for selected study
        And [API] Study visits in selected study are cleaned-up
        And [API] All Activities fotnotes are deleted from selected study
        And [API] All Activities are deleted from selected study
        And [API] All epochs assigned to the selected study are fetched
        And [API] All epochs assigned to the selected study are deleted
        And [API] Get all Study Elements within selected study
        And [API] Delete all Study Elements within selected study
        And [API] Get all Study Arms within selected study
        And [API] Delete all Study Arms within selected study
        And [API] Get all Study Cohorts within selected study
        And [API] Delete all Study Cohorts within selected study
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study

    Scenario: [Create][Arms][Cohorts][Branches] User must be able to define study structure (arms, cohorts, branches) via structure wizard
        Given The page 'study_structure/arms' is opened for current study
        And User waits for the design class request
        And User waits for the study arms list request
        When The plus button is clicked
        And User selects full study structure
        And User continues to next step of study structure stepper
        And New arm is added with type 'Placebo Arm'
        And Users clicks button to add another arm
        And New arm is added with type 'Observational Arm'
        And User continues to next step of study structure stepper
        And New cohort is added
        And Users clicks button to add another cohort
        And New cohort is added
        And Users clicks button to add another cohort
        And New cohort is added
        And User continues to next step of study structure stepper
        And Number of subject field with index 0 is set to 5
        And Number of subject field with index 1 is set to 10
        And Number of subject field with index 2 is set to 15
        And Number of subject field with index 3 is set to 20
        And Number of subject field with index 4 is set to 25
        And Number of subject field with index 5 is set to 30
        And User saves and exits study structure stepper
        Then User searches for 'Test Arm 1'
        And The study arm 1 with type 'Placebo Arm' data is available in the table, including number of participants 30 and connected branches 3
        And User searches for 'Test Arm 2'
        And The study arm 2 with type 'Observational Arm' data is available in the table, including number of participants 75 and connected branches 3
        And The page 'study_structure/cohorts' is opened for current study
        And User searches for 'Cohort Test 1'
        And The study cohort 1 data is visible in the table, including numberOfParticipants 25
        And The study arm 'Test Arm 1' is connected to the cohort
        And The study arm 'Test Arm 2' is connected to the cohort
        And The study branch 'Test Arm 1 Cohort Test 1' is connected to the cohort
        And The study branch 'Test Arm 2 Cohort Test 1' is connected to the cohort
        And User searches for 'Cohort Test 2'
        And The study cohort 2 data is visible in the table, including numberOfParticipants 35
        And The study arm 'Test Arm 1' is connected to the cohort
        And The study arm 'Test Arm 2' is connected to the cohort
        And The study branch 'Test Arm 1 Cohort Test 2' is connected to the cohort
        And The study branch 'Test Arm 2 Cohort Test 2' is connected to the cohort
        And User searches for 'Cohort Test 3'
        And The study cohort 3 data is visible in the table, including numberOfParticipants 45
        And The study arm 'Test Arm 1' is connected to the cohort
        And The study arm 'Test Arm 2' is connected to the cohort
        And The study branch 'Test Arm 1 Cohort Test 3' is connected to the cohort
        And The study branch 'Test Arm 2 Cohort Test 3' is connected to the cohort
        And The page 'study_structure/branches' is opened for current study
        And User searches for 'Test Arm 1 Cohort Test 1'
        And The study branch arm data is visible, including arm name 'Test Arm 1', cohort name 'Cohort Test 1', cohort code 'C1', branch short name 'Arm 1 CT1' and number of participants 5
        And User searches for 'Test Arm 1 Cohort Test 2'
        And The study branch arm data is visible, including arm name 'Test Arm 1', cohort name 'Cohort Test 2', cohort code 'C2', branch short name 'Arm 1 CT2' and number of participants 10
        And User searches for 'Test Arm 1 Cohort Test 3'
        And The study branch arm data is visible, including arm name 'Test Arm 1', cohort name 'Cohort Test 3', cohort code 'C3', branch short name 'Arm 1 CT3' and number of participants 15
        And User searches for 'Test Arm 2 Cohort Test 1'
        And The study branch arm data is visible, including arm name 'Test Arm 2', cohort name 'Cohort Test 1', cohort code 'C1', branch short name 'Arm 2 CT1' and number of participants 20
        And User searches for 'Test Arm 2 Cohort Test 2'
        And The study branch arm data is visible, including arm name 'Test Arm 2', cohort name 'Cohort Test 2', cohort code 'C2', branch short name 'Arm 2 CT2' and number of participants 25
        And User searches for 'Test Arm 2 Cohort Test 3'
        And The study branch arm data is visible, including arm name 'Test Arm 2', cohort name 'Cohort Test 3', cohort code 'C3', branch short name 'Arm 2 CT3' and number of participants 30

Scenario: [Create][Elements] User must be able to define four elements basing on the existing epochs
        Given User intercepts the study elements request
        And The page 'study_structure/elements' is opened for current study
        And User waits for the study elements request
        When The plus button is clicked
        And User continues to next step of study structure stepper
        And User waits for 1 seconds
        And The element type is set to 'No Treatment'
        And The element subtype is set to 'Screening'
        And The element name is set to 'El SCR1'
        And The element short name is set to 'SCR1'
        And User continues to next step of study structure stepper
        Then User searches for 'SCR1'
        Given The plus button is clicked
        And User continues to next step of study structure stepper
        And User waits for 1 seconds
        When The element type is set to 'Treatment'
        And The element subtype is set to 'Treatment'
        And The element name is set to 'El TRT1'
        And The element short name is set to 'TRT1'
        And User continues to next step of study structure stepper
        Then User searches for 'TRT1'
        Given The plus button is clicked
        And User continues to next step of study structure stepper
        And User waits for 1 seconds
        When The element type is set to 'Treatment'
        And The element subtype is set to 'Treatment'
        And The element name is set to 'El TRT2'
        And The element short name is set to 'TRT2'
        And User continues to next step of study structure stepper
        Then User searches for 'TRT2'
        Given The plus button is clicked
        And User continues to next step of study structure stepper
        And User waits for 1 seconds
        When The element type is set to 'No Treatment'
        And The element subtype is set to 'Follow-up'
        And The element name is set to 'El NTRT1'
        And The element short name is set to 'NTRT1'
        And User continues to next step of study structure stepper
        Then User searches for 'NTRT1'

    Scenario: [Create][Design Matrix] User must be able link elements with arms and branches using desgin matrix page
        Given The page 'study_structure/design_matrix' is opened for current study
        And Column 'Run-in' is made visible
        And Column 'Intervention' is made visible
        And User waits for the table
        When The pencil button is clicked
        And User triggers dropdown for element assignment to epoch 'Run-in', branch 'Test Arm 1 Cohort Test 1'
        And 0 element is selected
        And User triggers dropdown for element assignment to epoch 'Run-in', branch 'Test Arm 1 Cohort Test 2'
        And 0 element is selected
        And User triggers dropdown for element assignment to epoch 'Run-in', branch 'Test Arm 1 Cohort Test 3'
        And 0 element is selected
        And User triggers dropdown for element assignment to epoch 'Run-in', branch 'Test Arm 2 Cohort Test 1'
        And 1 element is selected
        And User triggers dropdown for element assignment to epoch 'Run-in', branch 'Test Arm 2 Cohort Test 2'
        And 1 element is selected
        And User triggers dropdown for element assignment to epoch 'Run-in', branch 'Test Arm 2 Cohort Test 3'
        And 1 element is selected
        And User triggers dropdown for element assignment to epoch 'Intervention', branch 'Test Arm 1 Cohort Test 1'
        And 2 element is selected
        And User triggers dropdown for element assignment to epoch 'Intervention', branch 'Test Arm 1 Cohort Test 2'
        And 2 element is selected
        And User triggers dropdown for element assignment to epoch 'Intervention', branch 'Test Arm 1 Cohort Test 3'
        And 2 element is selected
        And User triggers dropdown for element assignment to epoch 'Intervention', branch 'Test Arm 2 Cohort Test 1'
        And 3 element is selected
        And User triggers dropdown for element assignment to epoch 'Intervention', branch 'Test Arm 2 Cohort Test 2'
        And 3 element is selected
        And User triggers dropdown for element assignment to epoch 'Intervention', branch 'Test Arm 2 Cohort Test 3'
        And 3 element is selected
        And User saves changes made in the edition mode
        Then The pop up displays 'Design Matrix updated' 

    Scenario: [Study Overview] User must be able to view the study overview, summing up all defined arms, cohorts, branches, subjects and elements
        Given The page 'study_structure/overview' is opened for current study
        Then The value 'Number of Arm' is displayed for '2' in the study overview
        And The value 'Number of Branch Arms' is displayed for '6' in the study overview
        And The value 'Number of Cohorts' is displayed for '3' in the study overview
        And The value 'Planned number of subjects' is displayed for '105' in the study overview
        And The value 'Number of Study Elements' is displayed for '12' in the study overview
        And The value 'Study Design Class' is displayed for 'Study with cohorts, branches and subpopulations' in the study overview
        And The row 0 in the study structure overview page displays value of subjects 30 for arm 'Test Arm 1'
        And The row 3 in the study structure overview page displays value of subjects 75 for arm 'Test Arm 2'
        And The row 0 in the study structure overview page displays value of subjects 5 for branch 'Test Arm 1 Cohort Test 1'
        And The row 1 in the study structure overview page displays value of subjects 10 for branch 'Test Arm 1 Cohort Test 2'
        And The row 2 in the study structure overview page displays value of subjects 15 for branch 'Test Arm 1 Cohort Test 3'
        And The row 3 in the study structure overview page displays value of subjects 20 for branch 'Test Arm 2 Cohort Test 1'
        And The row 4 in the study structure overview page displays value of subjects 25 for branch 'Test Arm 2 Cohort Test 2'
        And The row 5 in the study structure overview page displays value of subjects 30 for branch 'Test Arm 2 Cohort Test 3'
        And The row 0 in the study structure overview page displays value of subjects 25 for cohort 'Cohort Test 1'
        And The row 1 in the study structure overview page displays value of subjects 35 for cohort 'Cohort Test 2'
        And The row 2 in the study structure overview page displays value of subjects 45 for cohort 'Cohort Test 3'
        And The row 3 in the study structure overview page displays value of subjects 25 for cohort 'Cohort Test 1'
        And The row 4 in the study structure overview page displays value of subjects 35 for cohort 'Cohort Test 2'
        And The row 5 in the study structure overview page displays value of subjects 45 for cohort 'Cohort Test 3'
        And The row 0 in the study structure overview page displays value 'El SCR1' for epoch 'Run-in'
        And The row 0 in the study structure overview page displays value 'El TRT2' for epoch 'Intervention'
        And The row 1 in the study structure overview page displays value 'El SCR1' for epoch 'Run-in'
        And The row 1 in the study structure overview page displays value 'El TRT2' for epoch 'Intervention'
        And The row 2 in the study structure overview page displays value 'El SCR1' for epoch 'Run-in'
        And The row 2 in the study structure overview page displays value 'El TRT2' for epoch 'Intervention'
        And The row 3 in the study structure overview page displays value 'El TRT1' for epoch 'Run-in'
        And The row 3 in the study structure overview page displays value 'El NTRT1' for epoch 'Intervention'
        And The row 4 in the study structure overview page displays value 'El TRT1' for epoch 'Run-in'
        And The row 4 in the study structure overview page displays value 'El NTRT1' for epoch 'Intervention'
        And The row 5 in the study structure overview page displays value 'El TRT1' for epoch 'Run-in'
        And The row 5 in the study structure overview page displays value 'El NTRT1' for epoch 'Intervention'

    Scenario: [Study Design] User must be able to view the study design in the protocol elements
        Given The page 'protocol_elements/Study Design' is opened for current study
        When The 'Study Design' tab is selected
        Then The user is presented with visual representation of designated study structure created for process scenario