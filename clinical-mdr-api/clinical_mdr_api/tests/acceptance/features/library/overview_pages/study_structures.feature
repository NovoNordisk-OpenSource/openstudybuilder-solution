@REQ_ID:xxx

Feature: Manage and maintain Study Structure Overview Pages in Clinical MDR API

    Background: Test user must be able to call the Clinical MDR API and the test data exists
        Given The test user can call the Clinical MDR API

Scenario: User must be able to get all the studies when calling the API endpoint '/studies/structure-overview'
    When the user calls the API endpoint '/studies/structure-overview'
    Then the response must include all studies

Test Coverage:
    |TestFile                               | TestID                                            |
    |/tests/integration/api/test_studies.py | @TestID: test_get_study_structure_overview        |

Scenario: User must be able to get correct headers when calling the API endpoint '/studies/structure-overview/headers'
    When the user calls the API endpoint '/studies/structure-overview/headers'
    Then the response must contain correct headers and with correct values for each header

Test Coverage:
    |TestFile                               | TestID                                            |
    |/tests/integration/api/test_studies.py | @TestID: test_get_study_structure_overview_headers|

Scenario: User must be able to use the column filters to filter out the correct value
    When the users calls the API endpoint '/studies/structure-overview'
    And calls the filter function
    Then the response should contain the correct value

Test Coverage:
    |TestFile                               | TestID                                            |
    |/tests/integration/api/test_studies.py | @TestID: test_filtering_wildcard                  |

Scenario: The grouping functionality of the structure overview page must be able to work
    When the user calls the API endpoint '/studies/structure-overview'
    And the study structure is the same across multiple studies
    Then the response must contain the StudyID only once with all studies

Test Coverage:
    |TestFile                               | TestID                                            |
    |/tests/integration/api/test_studies.py | @TestID: test_study_structure_overview_grouping   |