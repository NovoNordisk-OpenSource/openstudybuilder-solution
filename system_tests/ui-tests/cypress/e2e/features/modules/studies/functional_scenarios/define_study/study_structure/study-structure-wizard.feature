@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure Wizard

    As a system user,
    I want the system to ensure [Scenario],
    So that I must be able to make complete and consistent specification of study structure.

    Background: User is logged in and study has been selected
        Given The user is logged in
        Given User selects study with id 'CDISC DEV-9877'
        Given User intercepts the design class request
        And User intercepts the study arms list request
        Then The page 'study_structure/arms' is opened for current study
        Given User waits for the design class request
        And User waits for the study arms list request

    Scenario: [Test data] User must be able to delete all existing arms and cohorts before tests start
        And [API] Get all Study Arms within selected study
        And [API] Delete all Study Arms within selected study
        And [API] Get all Study Cohorts within selected study
        And [API] Delete all Study Cohorts within selected study

    Scenario: [Create][Arm] User must be able to create arms using stepper wizard
        And The plus button is clicked
        And User selects full study structure
        And User continues to next step of study structure stepper
        When New arm is added with type 'Placebo Arm'
        When Users clicks button to add another arm
        When New arm is added with type 'Observational Arm'
        When Users clicks button to add another arm
        And New arm is added with type 'Investigational Arm'
        And User saves and exits study structure stepper
        Then User searches for 'Test Arm 1'
        And User searches for 'Test Arm 2'
        And User searches for 'Test Arm 3'

    Scenario: [Edit][Arm] User must be able to edit arms using stepper wizard
        And The pencil button is clicked
        When The first arm data is edited
        And User saves and exits study structure stepper
        Then User searches for 'Test Arm 1 Update'
        And The new study arm data is updated in the table

    Scenario: [Remove][Arm] User must be able to remove arms using stepper wizard
        When The pencil button is clicked
        And First arm is removed
        And Action is confirmed by clicking continue
        And User waits for 1 seconds
        And User saves and exits study structure stepper
        Then User searches for 'Test Arm 1 Update' and confirms no results returned

    Scenario: [Create][Cohort] User must be able to create cohorts using stepper wizrd
        Given User intercepts the design class request
        Given The page 'study_structure/cohorts' is opened for current study
        Given User waits for the design class request
        And The pencil button is clicked
        And New cohort is added
        And Users clicks button to add another cohort
        And New cohort is added
        And Users clicks button to add another cohort
        And New cohort is added
        And User saves and exits study structure stepper
        Then User searches for 'Cohort Test 1'
        And The new study cohort data is available in the table
        Then User searches for 'Cohort Test 2'
        Then User searches for 'Cohort Test 3'

    Scenario: [Edit][Cohort] User must be able to edit cohorts using stepper wizard
        Given User intercepts the design class request
        Given The page 'study_structure/cohorts' is opened for current study
        Given User waits for the design class request
        And The pencil button is clicked
        When The first cohort data is edited
        And User saves and exits study structure stepper
        Then User searches for 'Cohort Test 1 Update'
        Then The new study cohort data is updated in the table

    Scenario: [Remove][Cohort] User must be able to remove cohorts using stepper wizard
        Given The page 'study_structure/cohorts' is opened for current study
        And User intercepts study cohorts request
        When The pencil button is clicked
        And User waits for study cohorts request
        And First cohort is removed
        And Action is confirmed by clicking continue
        And User waits for 1 seconds
        And User saves and exits study structure stepper
        Then User searches for 'Cohort Test 1 Update' and confirms no results returned

    Scenario: [Branches][No of Participants] User must be able to define number of participants in branches using stepper wizard
        Given User intercepts the design class request
        Given The page 'study_structure/branches' is opened for current study
        Given User waits for the design class request
        And The pencil button is clicked
        When Number of subject for arm 1 is set to 20
        And Number of subject for arm 2 is set to 50
        And User continues to next step of study structure stepper
        Then The number of participants are correctly assigned to the branches

    Scenario: [Branches][No of Participants] User must be able to copy number of participants in branche to all other branches/rows
        Given User intercepts the design class request
        Given The page 'study_structure/branches' is opened for current study
        Given User waits for the design class request
        And The pencil button is clicked
        When Number of subject for arm 1 is set to 10
        When The user copies the number of participants to all rows
        And User continues to next step of study structure stepper
        Then The number of participants is updated in each row

