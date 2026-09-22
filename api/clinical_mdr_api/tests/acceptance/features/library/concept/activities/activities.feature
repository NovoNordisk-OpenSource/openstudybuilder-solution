@REQ_ID:1070683

Feature: Manage Library Concept Activities in OpenStudyBuilder API

    As a API user, I want to manage the Activities in the Concepts Library API endpoints

    Background: Test user must be able to call the OpenStudyBuilder API and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get all the studies when calling the API endpoint '/studies/structure-overview'
        When the user calls the API endpoint '/studies/structure-overview'
        Then the response must include all studies

    Test Coverage:
        |TestFile                                                      | TestID                              |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_get_activity          |

    Scenario: User must be able to get activity details
        When the user requests to get the details of an activity with a specific UID
        Then the response should include the following attributes for the activity:
            | Library            |
            | Activity group     |
            | Activity subgroup  |
            | Activity name      |
            | Sentence case name |
            | Synonyms           |     
            | NCI Concept ID     |
            | NCI Concept Name   |
            | Abbreviation       |
            | Data collection    |
            | Legacy usage       |
            | Modified           |
            | Modified by        |
            | Status             |
            | Version            |

    Test Coverage:
        |TestFile                                                      | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_get_activity                            |

    Scenario: User must be able to create a new activity
        Given the user provides the necessary details for a new activity
        When the user attempts to create a new activity
        Then the system should verify the uniqueness of the activity name and perform the necessary actions to add the activity
        And the system should reject the creation if an activity with the same name already exists

    Test Coverage:
        |TestFile                                                      | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_create_activity_unique_name_validation  |

        

    Scenario: User must be able to get all versions of activities
        When the user requests to get all versions of activities
        Then the response should include details of all versions of activities, sorted by start date descending

    Test Coverage:
        |TestFile                                                      | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_get_activity_versions                   |

    Scenario: User must be able to filter versions of activities
        When the user requests to filter versions of activities
        Then the response should include only the versions of activities that match the specified filter

    Test Coverage:
        |TestFile                                                      | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_filtering_versions_wildcard             |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_filtering_versions_exact                |

    Scenario: User must be able to get activity overview
        When the user requests to get the overview of an activity
        Then the response should include the overview details of the activity in the specified format

    Test Coverage:
        |TestFile                                                      | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_activity_cosmos_overview                |