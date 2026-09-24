@REQ_ID:New
Feature: Support compatibility with DDF/USDM API standard

    Background: Test user must be able to call the OpenStudyBuilder API and test data exist
        Given The test user can call the OpenStudyBuilder API
        Given a test study identified by <uid> is available holding test data

    Rule: As an API user,
        I want the system to support API compatibility with the DDF USDM standard,
        So that I can use this API for integration with USDM compatible systems.

        Scenario Outline: Generate DDF USDM for a study
            When The GET API endpoint '/ddf/v4/studyDefinitions/<study_id>' is called for the test study <uid>
            Then The API must return a DDF USDM compatible JSON response
            Examples:
                | TestFile                                         | TestID                 |
                | /tests/integration/api/ddf/test_usdm_mappings.py | @TestID:test_ddf_study |

