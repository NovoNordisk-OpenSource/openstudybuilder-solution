@REQ_ID:1074260
Feature: Maintaining Study Protocol SoA in OpenStudyBuilder API

    Background: Test user must be able to call the OpenStudyBuilder API and test data exist
        Given The test user can call the OpenStudyBuilder API
        Given a test study identified by 'uid' is available holding test data


    Rule: As an API user,
        I want the system to support display of the Protocol SoA,
        So that I can use this view for overview of the study data specification.

        Scenario Outline: The Study activities/Protocol SoA can show/hide epochs and SoA milestone
            When The PATCH API endpoint '/studies/<uid>/soa-preferences' is called with different value of show_epochs and show_milestones
            Then The API must return the correct value of show_epochs and show_milestones.

            Examples:
                | PATCH Request                   | GET Response                  |
                | show_epochs   | show_milestones | show_epochs | show_milestones |
                | true          | true            | true        | true            |
                | true          | false           | true        | false           |
                | false         | true            | false       | true            |
                | false         | false           | false       | false           |

                # Test Coverage:
                | TestFile                                                   | TestID                              |
                | /tests/integration/api/study/test_study_soa_preferences.py | @TestID: test_patch_soa_preferences |
                | /tests/integration/api/study/test_study_soa_preferences.py | @TestID: test_get_soa_preferences   |


        Scenario Outline: User must be able to request for the Protocol SoA with "baseline shown as time 0"
            When The user requests for the Protocol SoA with "Baseline shown as time 0"
            Then The user receives the Protocol SoA with "baseline shown as time 0"

                # Test Coverage:
                | TestFile                                                        | TestID                                    |
                | /tests/integration/api/study/test_study_soa_preferences.py      | @TestID: test_patch_soa_preferences       |
                | /tests/integration/api/study/test_study_soa_preferences.py      | @TestID: test_get_soa_preferences         |


