@REQ_ID:1074260
Feature: Manage and Maintain Study SOA preferences functionality in OpenStudyBuilder API

# All the scenarios in this Gherkin specification, with flowchart (SoA), will include testing Protocal SoA, Detailed SoA and Operational SoA. 

    Background: Test user must be able to call the OpenStudyBuilder API and test data exist
        Given The test user can call the OpenStudyBuilder API
        Given A test study identified by 'uid' is available holding test data

    Scenario Outline: User must be able to request for the flowchart (SoA) with preferred time unit as day
        When The user requests for the flowchart (SoA) with preferred time unit as day
        Then The user receives the flowchart with study day view

            Test Coverage:
            |TestFile                                                        | TestID                               |
            |/tests/integration/api/service/test_study_flowchart.py          | @TestID:test_get_flowchart_table     |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart               |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart_docx          |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart_html          |

    Scenario Outline: User must be able to request for the flowchart (SoA) with preferred time unit as week
        When The user requests for the flowchart (SoA) with preferred time unit as week
        Then The user receives the flowchart with study week view

            Test Coverage:
            |TestFile                                                        | TestID                               |
            |/tests/integration/api/service/test_study_flowchart.py          | @TestID:test_get_flowchart_table     |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart               |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart_docx          |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart_html          | 
