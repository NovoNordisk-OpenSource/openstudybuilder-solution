@REQ_ID:1074257
Feature: Studies - Define Study - Study Interventions - Study Compound Dosings

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [Test data] Study compunds feature flag is enabled, data for compound creation is fetched and existing compounds are deleted
        Then [API] The feature flag 'compounds_studies' is enabled
        And The study compounds data is cleaned for testing purspose
        And [API] Study compound simple data is fetched
        And [API] Study compound alias data is fetched
        And [API] Study compound medical product data is fetched
        And [API] Study compound type of treatment data is fetched is created
        Given [API] Study compound is created

    Scenario: [Navigaion] User must be able to navigate to the Study Compound Dosings page
        Given The '/studies' page is opened
        When The 'Study Interventions' submenu is clicked in the 'Define Study' section
        And The 'Study Compound Dosings' tab is selected
        Then The current URL is '/study_interventions/study_compound_dosings'

    Scenario: [Table][Columns][Names] User must be able to see the page table with correct columns
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        Then A table is visible with following headers
            | headers             |
            | #                   |
            | Study element       |
            | Compound name       |
            | Medicinal product   |
            | Compound alias name |
            | Preferred alias     |
            | Dose value          |
            | Dose frequency      |

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Create] User must be able to create a study compound dosings
        Given [API] Uids are fetched for element subtype 'Treatment'
        And [API] Element is created for the current study
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When The user clicks add study compund dosing
        And The user select first study element
        And Form continue button is clicked
        And The user select first compund
        And Form continue button is clicked
        And The user select first dose value
        And The user select first dose frequency
        And The user intercepts study compund dosings create request
        When Form save button is clicked
        Then The study compound dosing is present in the compound dosings table

    Scenario: [Edit] User must be able to edit a study compound dosing
        Given The study compound dosing data is cleaned for testing purspose
        Given [API] Study compound data is fetched
        And [API] Study compound dosing is created
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        And User searches the compound dosing by the uid
        When The 'Edit' option is clicked from the three dot menu list
        And The user select last study element
        And Form continue button is clicked
        And The user select last compund
        And Form continue button is clicked
        And The user select last dose value
        And The user select last dose frequency
        When The user intercepts study compund dosings update request
        When Form save button is clicked
        Then The study compound dosing is present in the compound dosings table

    Scenario: [Create][Form behaviour][Compound Dosings][Element] Element data is automatically populated when selecting study compound
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        And The user intercepts study elements request
        When The user clicks add study compund dosing
        And The user select first study element
        Then The Element data is automatically populated

    Scenario: [Create][Form behaviour][Compound Dosings][Compound] Compound data is automatically populated when selecting study compound
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        And The user intercepts study compunds request
        And The user clicks add study compund dosing
        And The user select first study element
        And Form continue button is clicked
        When The user select first compund
        Then The Compound data is automatically populated

    Scenario: [Create] User must not be able to create a study compound dosing without the study element selected
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When The user clicks add study compund dosing
        And Form continue button is clicked
        Then The user cannot save the form

    Scenario: [Create] User must not be able to create a study compound without the study compound selected
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When The user clicks add study compund dosing
        And The user select first study element
        And Form continue button is clicked
        And Form continue button is clicked
        Then The user cannot save the form

    Scenario: [Create] User must be able to create a study compound without the dosing selected
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When The user clicks add study compund dosing
        And The user select first study element
        And Form continue button is clicked
        And The user select first compund
        And Form continue button is clicked
        When Form save button is clicked
        Then The pop up displays 'Study compound dosing added'

    Scenario: [Create][Composition] User must be able to create a study compound dosing with a composition value
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When The user clicks add study compund dosing
        And The user select first study element
        And Form continue button is clicked
        And The user select first compund
        And Form continue button is clicked
        And The user enters 'Test composition' in the composition field
        And The user intercepts study compund dosings create request
        When Form save button is clicked
        Then The study compound dosing is present in the compound dosings table

    Scenario: [Create][Composition] User must be able to create a study compound dosing without a composition value
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When The user clicks add study compund dosing
        And The user select first study element
        And Form continue button is clicked
        And The user select first compund
        And Form continue button is clicked
        Then The composition field is empty
        When Form save button is clicked
        Then The pop up displays 'Study compound dosing added'

    Scenario: [Delete] User must be able to delete a study compound
        Given The study compound dosing data is cleaned for testing purspose
        Given [API] Study compound data is fetched
        And [API] Study compound dosing is created
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        And User searches the compound dosing by the uid
        When The 'Delete' option is clicked from the three dot menu list
        And The user intercepts study compound dosing delete request
        And Action is confirmed by clicking continue
        Then The study compound dosing is removed
        And The pop up displays 'Study compound dosing deleted'

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCompoundDosings' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCompoundDosings' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCompoundDosings' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The page 'study_interventions/study_compound_dosings' is opened for current study
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyCompoundDosings' file is downloaded in 'xlsx' format

