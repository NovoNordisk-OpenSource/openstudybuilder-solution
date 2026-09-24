@REQ_ID:<new>
Feature: Maintaining Study Controlled Terminology Standard Versions in OpenStudyBuilder API

    Background: Test user must be able to call the OpenStudyBuilder API
        Given The test user can call the OpenStudyBuilder API

    Rule: As an API user,
        I want the system to ensure [Scenario], 
        So that I can effectively maintain and manage controlled terminology versions for study data standards.

    Scenario: User must be able to retrieve Study Data Standard Versions of Controlled Terminology via API
        When The Study Data Standard Versions of Controlled Terminology API endpoint is called
        Then The API should respond correctly with the Study Data Standard Versions of Controlled Terminology

        Test Coverage:
            |TestFile                                                                           | TestID                                                             |
            |/tests/integration/api/study_selections/test_study_standard_version.py             | @TestID:test_study_standard_version_crud_operations                |

    Scenario: User must be able to add a Study Data Standard Versions of Controlled Terminology via API
        When The Study Data Standard Versions of Controlled Terminology API endpoint is to add a Study Data Standard Versions
        Then The API response should indicate the successful addition of the Study Data Standard Versions

        Test Coverage:
            |TestFile                                                                           | TestID                                                             |
            |/tests/integration/api/study_selections/test_study_standard_version.py             | @TestID:test_study_standard_version_crud_operations                |

    Scenario: User must not be able to add a second Study Data Standard Versions of Controlled Terminology via API
        When The Study Data Standard Versions of Controlled Terminology API endpoint is to add a Controlled Terminology Version
        Then The API response should indicate the message "Already exists a Standard Version for the study"

        Test Coverage:
            |TestFile                                                                           | TestID                                                             |
            |/tests/integration/api/study_selections/test_study_standard_version.py             | @TestID:test_study_standard_version_crud_operations                |

    Scenario: User must be able to edit the Study Data Standard Versions of Controlled Terminology via API
        When The Study Data Standard Versions of Controlled Terminology API endpoint is called to edit a Study Data Standard Versions
        Then The API response should reflect the changes made to the Study Data Standard Versions

        Test Coverage:
            |TestFile                                                                           | TestID                                                             |
            |/tests/integration/api/study_selections/test_study_standard_version.py             | @TestID:test_study_standard_version_crud_operations                |

    Scenario: User must be able to delete a Study Data Standard Versions of Controlled Terminology via API
        When The Study Data Standard Versions of Controlled Terminology API endpoint is called to delete a Study Data Standard Versions
        Then The API response should confirm the removal of the Study Data Standard Versions

        Test Coverage:
            |TestFile                                                                           | TestID                                                             |
            |/tests/integration/api/study_selections/test_study_standard_version.py             | @TestID:test_study_standard_version_crud_operations                |

    Scenario: User must be able to retrieve change history of Study Data Standard Versions of Controlled Terminology via API
        When The Study Data Standard Versions of Controlled Terminology API endpoint is called to retrieve the change history
        Then The API response should include the version history with correct information

        Test Coverage:
            |TestFile                                                                           | TestID                                                             |
            |/tests/integration/api/study_selections/test_study_standard_version.py             | @TestID:test_get_standard_version_data_for_specific_study_version  |

    Scenario: User must be able to retrieve change history of selected Study Data Standard Versions of Controlled Terminology via API
        When The Study Data Standard Versions of Controlled Terminology API endpoint is called for a specific element
        Then The API response should include the history of changes for that element with correct information

        Test Coverage:
            |TestFile                                                                           | TestID                                                            |
            |clinical_mdr_api/tests/integration/api/study_selections/test_study_visits.py       | @TestID:test_study_visist_version_selecting_ct_package            |
            |clinical_mdr_api/tests/integration/api/study_selections/test_study_activities.py   | @TestID:test_study_activity_version_selecting_ct_package          |
            |clinical_mdr_api/tests/integration/api/study_selections/test_study_arms.py         | @TestID:test_study_arm_type_version_selecting_ct_package          |
            |clinical_mdr_api/tests/integration/api/study_selections/test_study_criteria.py     | @TestID:test_study_criteria_version_selecting_ct_package          |
            |clinical_mdr_api/tests/integration/api/study_selections/test_study_elements.py     | @TestID:test_study_element_version_selecting_ct_package           |
            |clinical_mdr_api/tests/integration/api/study_selections/test_study_endpoints.py    | @TestID:test_study_endpoint_version_selecting_ct_package          |
            |clinical_mdr_api/tests/integration/api/study_selections/test_study_epochs.py       | @TestID:test_study_epoch_version_selecting_ct_package             |
            |clinical_mdr_api/tests/integration/api/study_selections/test_study_objectives.py   | @TestID:test_study_objective_version_selecting_ct_package         |
            |clinical_mdr_api/tests/integration/api/test_studies.py                             | @TestID:test_study_metadata_version_selecting_ct_package          |