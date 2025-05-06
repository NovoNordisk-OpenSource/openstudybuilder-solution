@REQ_ID:2824916
Feature: Studies - Study Disclosure

    Background: User must be logged in
        Given The user is logged in

    Scenario:  User must be able to navigate to the Study Disclosure page
        Given A test study is selected
        Given The '/studies' page is opened
        When The 'Clinical Transparency' submenu is clicked in the 'View Specifications' section
        Then The current URL is '/studies/Study_000001/study_disclosure'

    Scenario: User must be able to select Identification Pharma CM Specification
        Given The study disclosure page for CDISC DEV-0 is accessed
        And The user selects 'Identification' specification
        Then A table is visible with following headers
            | headers           |
            | StudyBuilder term |
            | PharmaCM term     |
            | Values            |
        And The table display following predefined data
            | column | row | value             |
            | 0      | 0   | Study ID          |
            | 1      | 0   | Unique Study ID   |
            | 0      | 1   | Study Short Title |
            | 1      | 1   | Brief Title       |
            | 0      | 2   | Study Acronym     |
            | 1      | 2   | Acronym           |
            | 0      | 3   | Study Title       |
            | 1      | 3   | Official Title    |
        And The correct study values are presented for Identification

    Scenario: User must be able to select Secondary IDs Pharma CM Specification
        Given The study disclosure page for CDISC DEV-0 is accessed
        And The user selects 'Secondary IDs' specification
        Then A table is visible with following headers
            | headers             |
            | Secondary ID        |
            | Secondary ID Type   |
            | Registry Identifier |
        And The correct study values are presented for Secondary IDs

    ## TODO: Add more test data for proper logic implementation
    # Scenario: User must be able to select Conditions Pharma CM Specification
    #     Given The study disclosure page for CDISC DEV-0 is accessed
    #     And The user selects 'Conditions' specification
    #     Then A table is visible with following headers
    #         | headers           |
    #         | StudyBuilder term |
    #         | PharmaCM term     |
    #         | Values            |
    #     And The correct study values are presented for Conditions

    Scenario: User must be able to select Design Pharma CM Specification
        Given The study disclosure page for CDISC DEV-0 is accessed
        And The user selects 'Design' specification
        Then A table is visible with following headers
            | headers           |
            | StudyBuilder term |
            | PharmaCM term     |
            | Values            |
        And The table display following predefined data
            | column | row | value                      |
            | 0      | 0   | Study Type                 |
            | 1      | 0   | Study Type                 |
            | 0      | 1   | Study Intent Type          |
            | 1      | 1   | Primary Purpose            |
            | 0      | 2   | Study Phase Classification |
            | 1      | 2   | Study Phase                |
            | 0      | 3   | Intervention Model         |
            | 1      | 3   | Interventional Study Model |
            | 0      | 4   | Number of Arms             |
            | 1      | 4   | Number of Arms             |
            | 0      | 5   | Study is randomised        |
            | 1      | 5   | Allocation                 |
        And The correct study values are presented for Design

    Scenario: User must be able to select Interventions Pharma CM Specification
        Given The study disclosure page for CDISC DEV-0 is accessed
        And The user selects 'Interventions' specification
        Then A table is visible with following headers
            | headers     |
            | Arm Title   |
            | Type        |
            | Description |
        And The correct study values are presented for Interventions

    Scenario: User must be able to select Outcome Measures Pharma CM Specification
        Given The study disclosure page for CDISC DEV-0 is accessed
        And The user selects 'Outcome Measures' specification
        Then A table is visible with following headers
            | headers         |
            | Outcome Measure |
            | Time Frame      |
            | Description     |
        And The correct study values are presented for Outcome Measures

    Scenario: User must be able to download XML
        Given The study disclosure page for CDISC DEV-0 is accessed
        When The user clicks on Download XML button
        Then The correct file is downloaded
        And The file is XML valid
