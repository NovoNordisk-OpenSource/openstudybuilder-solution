@REQ_ID:2824916
Feature: Studies - View Specification - Clinical Transparency

    Background: User must be logged in
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the Study Disclosure page
        Given The '/studies' page is opened
        When The 'Clinical Transparency' submenu is clicked in the 'View Specifications' section
        Then The current URL is '/study_disclosure'

    Scenario: [Table][Columns][Names][Data] User must be able to select Identification Pharma CM Specification
        Given User selects study with id 'CDISC DEV-0'
        And The page 'study_disclosure' is opened for current study
        And The user selects 'Identification' specification
        Then A table is visible with following headers
            | headers           |
            | OpenStudyBuilder term |
            | PharmaCM term     |
            | Values            |
        And The table display following predefined data
            | row | column            | value             |
            | 0   | OpenStudyBuilder term | Study ID          |
            | 0   | PharmaCM term     | Unique Study ID   |
            | 1   | OpenStudyBuilder term | Study Short Title |
            | 1   | PharmaCM term     | Brief Title       |
            | 2   | OpenStudyBuilder term | Study Acronym     |
            | 2   | PharmaCM term     | Acronym           |
            | 3   | OpenStudyBuilder term | Study Title       |
            | 3   | PharmaCM term     | Official Title    |
        And The correct study values are presented for Identification

    Scenario: [Table][Columns][Names][Data] User must be able to select Secondary IDs Pharma CM Specification
        Given User selects study with id 'CDISC DEV-0'
        And The page 'study_disclosure' is opened for current study
        And The user selects 'Secondary IDs' specification
        Then A table is visible with following headers
            | headers             |
            | Secondary ID        |
            | Secondary ID Type   |
            | Registry Identifier |
        And The correct study values are presented for Secondary IDs

    ## TODO: Add more test data for proper logic implementation
    # Scenario: User must be able to select Conditions Pharma CM Specification
    #     Given User selects study with id 'CDISC DEV-0'
    #     And The page 'study_disclosure' is opened for current study
    #     And The user selects 'Conditions' specification
    #     Then A table is visible with following headers
    #         | headers           |
    #         | OpenStudyBuilder term |
    #         | PharmaCM term     |
    #         | Values            |
    #     And The correct study values are presented for Conditions

    Scenario: [Table][Columns][Names][Data] User must be able to select Design Pharma CM Specification
        Given User selects study with id 'CDISC DEV-0'
        And The page 'study_disclosure' is opened for current study
        And The user selects 'Design' specification
        Then A table is visible with following headers
            | headers           |
            | OpenStudyBuilder term |
            | PharmaCM term     |
            | Values            |
        And The table display following predefined data
            | row | column                 | value                      |
            | 0   | OpenStudyBuilder term  | Study Type                 |
            | 0   | PharmaCM term          | Study Type                 |
            | 1   | OpenStudyBuilder term  | Study Intent Type          |
            | 1   | PharmaCM term          | Primary Purpose            |
            | 2   | OpenStudyBuilder term  | Study Phase Classification |
            | 2   | PharmaCM term          | Study Phase                |
            | 3   | OpenStudyBuilder term  | Intervention Model         |
            | 3   | PharmaCM term          | Interventional Study Model |
            | 4   | OpenStudyBuilder term  | Number of Arms             |
            | 4   | PharmaCM term          | Number of Arms             |
            | 5   | OpenStudyBuilder term  | Study is randomised        |
            | 5   | PharmaCM term          | Allocation                 |
        And The correct study values are presented for Design

    Scenario: [Table][Columns][Names][Data] User must be able to select Interventions Pharma CM Specification
        Given User selects study with id 'CDISC DEV-0'
        And The page 'study_disclosure' is opened for current study
        And The user selects 'Interventions' specification
        Then A table is visible with following headers
            | headers     |
            | Arm Title   |
            | Type        |
            | Description |
        And The correct study values are presented for Interventions

    Scenario: [Table][Columns][Names][Data] User must be able to select Outcome Measures Pharma CM Specification
        Given User selects study with id 'CDISC DEV-0'
        And The page 'study_disclosure' is opened for current study
        And The user selects 'Outcome Measures' specification
        Then A table is visible with following headers
            | headers         |
            | Outcome Measure |
            | Time Frame      |
            | Description     |
        And The correct study values are presented for Outcome Measures

    Scenario: [Export][Xml] User must be able to download XML
        Given User selects study with id 'CDISC DEV-0'
        And The page 'study_disclosure' is opened for current study
        When The user clicks on Download XML button
        Then The correct file is downloaded
        And The file is XML valid
