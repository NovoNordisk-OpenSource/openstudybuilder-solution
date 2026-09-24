@REQ_ID:1074260
Feature: Maintaining Study Operational SOA in OpenStudyBuilder API

    Background: Test user must be able to call the OpenStudyBuilder API and test data exist
        Given The test user can call the OpenStudyBuilder API
        Given a test study identified by 'uid' is available holding test data


    Rule: As an API user,
        I want the system to support display of the Operational SoA,
        So that I can use this view for overview of the study data specification.

        Scenario: Support display of Operational SoA
        # Gherkin to be made


    Rule: As an API user,
        I want the system to support download of Operational SoA in .csv and Excel file formats,
        So that I can use the files for reviews and downstream integrations.

        Scenario Outline: Download of collections by visits of study activity instances in Excel file format
            When The GET API endpoint '/studies/<uid>/operational-soa-exports' is called with Accept header 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' to download Operational SoA in Excel file format
            Then The API must return the following columns with one row for each collection of an study activity instance by a visit
                | column | header            |
                | 1      | Study number      |
                | 2      | Study version     |
                | 3      | SoA group         |
                | 4      | Activity group    |
                | 5      | Activity subgroup |
                | 6      | Epoch             |
                | 7      | Visit             |
                | 8      | Activity          |
                | 9      | Activity instance |
                | 10     | Topic code        |
                | 11     | Param code        |
            Examples:
            |TestFile                                                        | TestID                       |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_soa_exports     |


        Scenario Outline: Download of collections by visits of study activity instances in .csv file format
            When The GET API endpoint '/studies/<uid>/operational-soa-exports' is called with Accept header 'text/csv' to download Operational SoA in .csv file format
            Then The API must return the following columns with one row for each collection of an study activity instance by a visit
                | column | header            |
                | 1      | study_number      |
                | 2      | study_version     |
                | 3      | soa_group         |
                | 4      | activity_group    |
                | 5      | activity_subgroup |
                | 6      | epoch             |
                | 7      | visit             |
                | 8      | activity          |
                | 9      | activity_instance |
                | 10     | topic_code        |
                | 11     | param_code        |

            Examples:
            |TestFile                                                        | TestID                       |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_soa_exports     |

    Rule: As an API user,
        I want the system to support download of Operational SoA in DOCX file format,
        So that I can use the matrix representation in DOCX to review the Operational SoA.

        Scenario: Download of collections by visits of study activity instances in DOCX file format
            When The GET API endpoint '/studies/<uid>/operational-soa' is called to download Operational SoA in DOCX format
            Then The API must return the following columns with one row for each study activity instance by a visit
                | column | header                                                                                 |
                | 1      | Study number                                                                           |
                | 2      | Activities (SoA group, Activity group, Activity subgroup, Activity, Activity Instance) |
                | 3      | Topic Code                                                                             |
                | 4      | Param code                                                                             |
                | 3      | Epoch Visit Day/Week Window                                                            |
                | 4+     | <Study Epoch>                                                                          |
                | 4+     | <Study Visit>   
                
            Examples:
            |TestFile                                                        | TestID                                |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart_docx           |
                                                                    

