@REQ_ID:NEW
@neodash_tests
Feature: Data Exchange Data Models - Sponsor Models

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Data Exchange Data Models' page is opened

    Scenario: User must be able to view model entries in Sponsor Models
        Given The neoDash 'Sponsor Models' tab is selected
        Then The following set of neoDash reports are displayed
            | report             |
            | Available Versions |
            | Datasets           |
            | Variables          |

    Scenario: User must be able to view the datasets
        Given The neoDash 'Sponsor Models' tab is selected
        And The user selects 'sdtmig_mastermodel_3.2_NN15' in the 'Available Versions' table
        Then The table title should change to the following
            | no | Table_Name                             |
            | 1  | Datasets - sdtmig_mastermodel_3.2_NN15 |
        And The Datasets - table should display the following
            | uid | label                       | basic_std | purpose    | ig_comment                                                                                                           | xml_path      |
            | PP  | Pharmacokinetics Parameters | true      | Tabulation | Data describing the parameters of the time-concentration curve for PC data (e.g., area under the curve, Cmax, Tmax). | pp.(FileType) |
        Then The table 'Variables - EG - sdtmig_mastermodel_3.2_NN15' displays the following items
            | column    | value            |
            | uid       | CDMS_SUB_EVT_NUM |
            | basic_std | false            |

    Scenario: User must be able to select the datasets
        Given The neoDash 'Sponsor Models' tab is selected
        And The user selects 'sdtmig_mastermodel_3.2_NN15' in the 'Available Versions' table
        And The user selects 'Pharmacokinetics Parameters' in the 'Datasets - sdtmig_mastermodel_3.2_NN15' table
        Then The table 'Variables - PP - sdtmig_mastermodel_3.2_NN15' displays the following items
            | column    | value              |
            | uid       | SRC_FIND_COLL_UNIT |
            | basic_std | false              |