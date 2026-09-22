@REQ_ID:NEW
@neodash_tests
Feature: Data Exchange Data Models - Implementation Guides - Excl. CDASH

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Data Exchange Data Models' page is opened

    Scenario: User must be able to view model entries in Implementation Guides - Excl. CDASH
        Given The neoDash 'Implementation Guides - Excl. CDASH' tab is selected
        Then The following set of neoDash reports are displayed
            | no | report                              |
            | 0  | Available Guides                    |
            | 1  | Versions -                          |
            | 2  | Datasets -                          |
            | 3  | Variables -                         |
            | 4  | Sponsor Model                       |
            | 5  | Sponsor Model Version of Variable : |

    Scenario: User must be able to select from the available models
        Given The neoDash 'Implementation Guides - Excl. CDASH' tab is selected
        And The user selects 'SDTMIG__AP' in the 'Available Guides' table
        Then The table title should change to the following
            | no | Table_Name            |
            | 1  | Versions - SDTMIG__AP |
        And The Versions - table should display the following
            | version        | implements |
            | SDTMIG-AP v1.0 | SDTM v1.4  |

    Scenario: User must be able to select from the available versions
        Given The neoDash 'Implementation Guides - Excl. CDASH' tab is selected
        And The user selects 'SDTMIG__AP' in the 'Available Guides' table
        And The user selects 'SDTMIG-AP v1.0' in the 'Versions - SDTMIG__AP' table
        Then The table title should change to the following
            | no | Table_Name                |
            | 2  | Datasets - SDTMIG-AP v1.0 |
        And The Datasets table should display the following
            | dataset  | implements |
            | APDM     |            |
            | APRELSUB |            |

    Scenario: User must be able to select from the available datasets
        Given The neoDash 'Implementation Guides - Excl. CDASH' tab is selected
        And The user selects 'SDTMIG__AP' in the 'Available Guides' table
        And The user selects 'SDTMIG-AP v1.0' in the 'Versions - SDTMIG__AP' table
        And The user selects 'APRELSUB' in the 'Versions - SDTMIG__AP' table
        Then The table title should change to the following
            | no | Table_Name           |
            | 3  | Variables - APRELSUB |
        And The Variables - table should display the following
            | variable | label                         | description                                                                                                                                                                                  | dataType | length | role       | codelist | implements |
            | STUDYID  | Study Identifier              | Unique identifier for a study.                                                                                                                                                               | Char     |        | Identifier |          |            |
            | APID     | Associated Persons Identifier | Identifier for a single associated person, a group of associated persons, or a pool of associated persons. If APID identifies a pool, POOLDEF records must exist for each associated person. | Char     |        | Identifier |          |            |

    @pending_implementation
    Scenario: User must be able to select from the available variables
        Given The neoDash 'Implementation Guides - Excl. CDASH' tab is selected
        And The user selects 'SDTMIG__AP' in the 'Available Guides' table
        And The user selects 'SDTMIG-AP v1.0' in the 'Versions - SDTMIG__AP' table
        And The user selects 'APRELSUB' in the 'Versions - SDTMIG__AP' table
        And The user clicks 'Sponsor Model' on the following Guide Variable
            | variable | label            | description                    | dataType | length | role       | codelist | implements |
            | STUDYID  | Study Identifier | Unique identifier for a study. | Char     |        | Identifier |          |            |
        Then The table title should change to the following
            | no | Table_Name                                  |
            | 5  | Sponsor Model Version of Variable : STUDYID |