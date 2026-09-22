@REQ_ID:2383812

Feature: Manage Clinical Programmes in OpenStudyBuilder API

    Background: Test user must be able to call the OpenStudyBuilder API
        Given The test user can call the OpenStudyBuilder API

    Rule: As an API user,
        I want the system to ensure [Scenario],
        So that I can manage the clinical programmes as expected. 

    Scenario: Create the clinical programme
        When Create a new clinical programme in the database
        Then the clinical programme should be created successfully in the database

        Test Coverage:
            |TestFile                                              | TestID                                   |
            |/tests/integration/api/test_clinical_programmes.py    | @TestID:test_get_clinical_programme      |
            |/tests/integration/api/test_clinical_programmes.py    | @TestID:test_create_clinical_programme   |

    Scenario: Edit the clinical programme
        Given a new clinical programme is created
        When edit the clinical programme name to a new one
        Then the clinical programme should be edited successfully

        Test Coverage:
            |TestFile                                              | TestID                                   |
            |/tests/integration/api/test_clinical_programmes.py    | @TestID:test_update_clinical_programme   |

    Scenario: Delete the clinical programme
        Given a new clinical programme is created
        When delete this newly created clinical programme from the database
        Then the newly created clinical programme should be deleted successfully

        Test Coverage:
            |TestFile                                              | TestID                                   |
            |/tests/integration/api/test_clinical_programmes.py    | @TestID:test_delete_clinical_programme   |

    Scenario: Prevent editing of project-linked clinical programme
        Given there is a project linked to the test clinical programme
        When I attempt to edit the test clinical programme 
        Then the editing should not be possible as a project is linked to it

        Test Coverage:
            |TestFile                                              | TestID                                                             |
            |/tests/integration/api/test_clinical_programmes.py    | @TestID:test_cannot_update_clinical_programme_used_by_projects     |

    Scenario: Prevent deletion of project-linked clinical programme
        Given there is a project linked to the test clinical programme
        When I attempt to delete the test clinical programme 
        Then the deletion should not be possible as a project is linked to it

        Test Coverage:
            |TestFile                                              | TestID                                                             |
            |/tests/integration/api/test_clinical_programmes.py    | @TestID:test_cannot_delete_clinical_programme_used_by_projects     |