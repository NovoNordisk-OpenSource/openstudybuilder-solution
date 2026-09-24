@REQ_ID:NEW
@neodash_tests
Feature: Data Exchange Data Models - Models

    As a user, I want to be able view infromation about the models

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Data Exchange Data Models' page is opened

    Scenario: User must be able to view model entries in Models
        Given The neoDash 'Models' tab is selected
        Then The following set of neoDash reports are displayed
            | no | report              |
            | 0  | Available Models    |
            | 1  | SDTM Model Versions |
            | 2  | Classes - SDTM v2.0 |
            | 3  | SDTM v2.0 Impl. by: |
            | 4  | Variable Classes -  |

    Scenario: User must be able to view the available models
        Given The neoDash 'Models' tab is selected
        Then The following models are available in the Available Models table
            | model        |
            | FBDE         |
            | NN-VEEVA-EDC |
            | SDTM         |


    Scenario: User must be able to select from the available models
        Given The neoDash 'Models' tab is selected
        And The user selects 'SDTM' in the 'Available Models' table
        Then The table title should change to the following
            | no | Table_Name          |
            | 1  | SDTM Model Versions |
        And The Versions table should display the following
            | version   |
            | SDTM v2.0 |
            | SDTM v1.8 |
            | SDTM v1.7 |
            | SDTM v1.6 |
            | SDTM v1.5 |

    Scenario: User must be able to select from the available versions
        Given The neoDash 'Models' tab is selected
        And The user selects 'SDTM' in the 'Available Models' table
        And The user selects 'SDTM v1.7' in the 'SDTM Model Versions' table
        Then The table title should change to the following
            | no | Table_Name          |
            | 2  | Classes - SDTM v1.7 |
            | 4  | SDTM v1.7 Impl. by  |
        And The Classes table should display the following
            | class                 |
            | General__Observations |
            | Interventions         |
            | Events                |
            | Findings              |
            | Findings__About       |
        And The Impl. by card should display the following
            | text                        |
            | SDTMIG-MD v1.1\nSDTMIG v3.3 |

    Scenario: User must be able to select from the available classes
        Given The neoDash 'Models' tab is selected
        And The user selects 'SDTM' in the 'Available Models' table
        And The user selects 'SDTM v1.7' in the 'SDTM Model Versions' table
        And The user selects 'Findings' in the 'Classes - SDTM v1.7' table
        Then The table title should change to the following
            | no | Table_Name                  |
            | 3  | Variable Classes - Findings |
        And The Variable Classes table should display the following
            | variable | label                                    | role              | length | qualifies | origin   |
            | --TESTCD | Short Name of Measurement, Test, or Exam | Topic             |        |           | Findings |
            | --TEST   | Name of Measurement, Test, or Exam       | Synonym Qualifier |        | --TESTCD  | Findings |
            | --MODIFY | Modified Term                            | Synonym Qualifier |        | --ORRES   | Findings |
