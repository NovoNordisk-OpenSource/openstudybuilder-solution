@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Exports

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study SoA for the protocol.

    Background: User is logged in and study has been selected
        Given The user is logged in
        When User selects study with id 'CDISC DEV-9883'
        
    Scenario: [Test data] User must be able to create test data and enable appropiate feature flags
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1, minVisitWindow -1, maxVisitWindow 1
        When [API] All Activities are deleted from selected study
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] Activity is assigned to the visit 0 in selected study
        And [API] The feature flag 'soa_protocol_lab_table' is enabled

    Scenario: [Export][Protocol][CSV] User must be able to export the data in CSV format
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When User clicks export button
        And User selects 'CSV' format to export the table content
        Then The study specific 'protocol SoA' file without timestamp is downloaded in 'csv' format

    Scenario: [Export][Protocol][EXCEL] User must be able to export the data in JSON format
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When User clicks export button
        And User selects 'EXCEL' format to export the table content
        Then The study specific 'protocol SoA' file without timestamp is downloaded in 'xlsx' format

    Scenario: [Export][Protocol][DOCX] User must be able to export the data in XML format
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        When User clicks export button
        And User selects 'DOCX' format to export the table content
        Then The study specific 'protocol SoA' file without timestamp is downloaded in 'docx' format

    Scenario: [Export][Detailed][CSV] User must be able to export the data in CSV format
        Given The page 'activities/soa' is opened for current study
        And User waits for the table
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        Then The study specific 'detailed SoA' file without timestamp is downloaded in 'csv' format

    Scenario: [Export][Detailed][EXCEL] User must be able to export the data in JSON format
        Given The page 'activities/soa' is opened for current study
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        Then The study specific 'detailed SoA' file without timestamp is downloaded in 'xlsx' format

    Scenario: [Export][Detailed][DOCX] User must be able to export the data in XML format
        Given The page 'activities/soa' is opened for current study
        When User clicks table export button
        And User selects 'DOCX' format to export the table content
        Then The study specific 'detailed SoA' file without timestamp is downloaded in 'docx' format

    Scenario: [Export][Activity List][CSV] User must be able to export the data in CSV format
        Given The page 'activities/list' is opened for current study
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyActivities' file is downloaded in 'csv' format

    Scenario: [Export][Activity List][Json] User must be able to export the data in JSON format
        Given The page 'activities/list' is opened for current study
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyActivities' file is downloaded in 'json' format

    Scenario: [Export][Activity List][Xml] User must be able to export the data in XML format
        Given The page 'activities/list' is opened for current study
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyActivities' file is downloaded in 'xml' format

    Scenario: [Export][Activity List][Excel] User must be able to export the data in EXCEL format
        Given The page 'activities/list' is opened for current study
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyActivities' file is downloaded in 'xlsx' format

        Scenario: [Export][Protocol Lab Table][CSV] User must be able to export the data in CSV format
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol_lab_table' view
        When User clicks export button
        And User selects 'CSV' format to export the table content
        Then The study specific 'protocol_lab_table SoA' file without timestamp is downloaded in 'csv' format

    Scenario: [Export][Protocol Lab Table][EXCEL] User must be able to export the data in JSON format
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol_lab_table' view
        When User clicks export button
        And User selects 'EXCEL' format to export the table content
        Then The study specific 'protocol_lab_table SoA' file without timestamp is downloaded in 'xlsx' format

    Scenario: [Export][Protocol Lab Table][DOCX] User must be able to export the data in XML format
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol_lab_table' view
        When User clicks export button
        And User selects 'DOCX' format to export the table content
        Then The study specific 'protocol_lab_table SoA' file without timestamp is downloaded in 'docx' format