@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Visits

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study visits.

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: [Create][Study Vists][Unscheduled] User must be presented with correct visit name and visit type when creating unscheduled visit
        Given User selects study with id 'CDISC DEV-9876'
        And [API] The epoch with type 'No Treatment' and subtype 'Basic' exists in selected study
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        And Add visit button is clicked
        And Visit scheduling type is selected as 'UNSCHEDULED_VISIT'
        And Form continue button is clicked
        And User waits for the Basic epoch for unscheduled visit to load
        When Form continue button is clicked
        Then User is presented with correct unscheduled visit name
        And User is presented with visit start rule set as 'Unplanned unscheduled'

    Scenario: [Create][Study Vists][Unscheduled] User must be set visit start rule for unscheduled visit
        Given User selects study with id 'CDISC DEV-9876'
        And [API] The epoch with type 'No Treatment' and subtype 'Basic' exists in selected study
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        And Add visit button is clicked
        And Visit scheduling type is selected as 'UNSCHEDULED_VISIT'
        And Form continue button is clicked
        And User waits for the Basic epoch for unscheduled visit to load
        When Form continue button is clicked
        Then User must be able to set vist start rule as 'Custom start rule'
        And Form save button is clicked
        When User searches for 'Unscheduled'
        And The 'Edit' option is clicked from the three dot menu list
        And Form continue button is clicked
        And Form continue button is clicked
        And User is presented with visit start rule set as 'Custom start rule'