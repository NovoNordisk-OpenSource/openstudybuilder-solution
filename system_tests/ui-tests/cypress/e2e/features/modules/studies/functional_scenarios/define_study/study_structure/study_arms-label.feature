@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Manually Defined Study Arms

    As a system user,
    I want the system to ensure [Scenario],
    So that I must be able to make complete and consistent specification of study arms.

    Background: User is logged in and study has been selected
        Given The user is logged in
        Given User selects study with id 'CDISC DEV-9878'
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

    Scenario: [Create][Default Label Value] User must be able to see that by default arm label is empty
        And The plus button is clicked
        When User select manual study structure
        And User continues to next step of study structure stepper
        Then The Arm label is empty by default

    Scenario: [Create][Postive case] User must be able to add arm with study label
        And The plus button is clicked
        When User select manual study structure
        And User continues to next step of study structure stepper
        And New arm is added with type 'Placebo Arm'
        And User provides the study arm label
        And User saves and exits study structure stepper
        Then User searches for 'Test Arm 1'
        And The study arm label value is visible in the table

    Scenario: [Edit][Postive case] User must be able to edit study label via wizard
        When The pencil button is clicked
        And User continues to next step of study structure stepper
        And User provides the study arm label
        And User saves and exits study structure stepper
        Then User searches for 'Test Arm 1'
        And The study arm label value is visible in the table

    Scenario: [Create][Postive case] User must be able to add arm without study label
        Given [API] Get all Study Arms within selected study
        And [API] Delete all Study Arms within selected study
        Given User intercepts the design class request
        And User intercepts the study arms list request
        Then The page 'study_structure/arms' is opened for current study
        Given User waits for the design class request
        And User waits for the study arms list request
        And The plus button is clicked
        And User select manual study structure
        And User continues to next step of study structure stepper
        And New arm is added with type 'Placebo Arm'
        And User saves and exits study structure stepper
        Then User searches for 'Test Arm 1'
        And The study arm label value is empty

    Scenario: [Edit][Postive case] User must be able to edit study label via form window
        Given User searches for 'Test Arm 1'
        When The 'Edit' option is clicked from the three dot menu list
        And User provides the study arm label
        And Form save button is clicked
        Then User searches for 'Test Arm 1'
        And The study arm label value is visible in the table

    Scenario: [Character limit] User must be add arm label with max 40 character length
        Given [API] Get all Study Arms within selected study
        And [API] Delete all Study Arms within selected study
        Given User intercepts the design class request
        And User intercepts the study arms list request
        Then The page 'study_structure/arms' is opened for current study
        Given User waits for the design class request
        And User waits for the study arms list request
        And The plus button is clicked
        And User select manual study structure
        And User continues to next step of study structure stepper
        And User provides the study arm label with 41 characters
        Then The validation message appears for arm label 'This field must not exceed 40 characters'
        And New arm is added with type 'Placebo Arm'
        And User provides the study arm label with 40 characters
        And User saves and exits study structure stepper
        Then User searches for 'Test Arm 1'
        And The study arm label value is visible in the table
