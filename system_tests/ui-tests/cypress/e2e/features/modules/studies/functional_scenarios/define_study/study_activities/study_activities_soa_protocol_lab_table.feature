@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Schedule of Activities - Protocol - Lab Table

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study SoA for the protocol.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [Test data] User must be able to create test data and enable appropiate feature flags
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] The feature flag 'soa_protocol_lab_table' is enabled

    Scenario: [Navigation] User must be able to navigate to Protocol SoA - Lab table page using side menu
        Given The '/studies' page is opened
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        And The 'Schedule of Activities' tab is selected
        And User switches to the 'protocol_lab_table' view
        Then The current URL is '/activities/soa'
