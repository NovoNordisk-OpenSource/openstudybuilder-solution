@REQ_ID:2383812

Feature: Manage Project in OpenStudyBuilder API

    Background: Test user must be able to call the OpenStudyBuilder API
        Given The test user can call the OpenStudyBuilder API

    Rule: As an API user,
        I want the system to ensure [Scenario],
        So that I can manage the project as expected. 

    Scenario: Create the project
        When create a new project in the database
        Then the newly created project should be found in the database

        Test Coverage:
            |TestFile                                   | TestID                        |
            |/tests/integration/api/test_projects.py    | @TestID:test_get_project      |
            |/tests/integration/api/test_projects.py    | @TestID:test_create_project   |

    Scenario: Edit the project
        Given a new project is created
        When edit the project name to a new one
        Then the Project name should be edited to the new one successfully

        Test Coverage:
            |TestFile                                   | TestID                        |
            |/tests/integration/api/test_projects.py    | @TestID:test_update_project   |

    Scenario: Delete the project
        Given a new project is created
        When delete this project from the database
        Then the project should be deleted from the database successfully

        Test Coverage:
            |TestFile                                   | TestID                        |
            |/tests/integration/api/test_projects.py    | @TestID:test_delete_project   |

    Scenario: Prevent editing of a study-linked project 
        Given there is a study linked to the test project
        Given I edit the test project name to a new one
        Then the editing should not be possible as a study is linked

        Test Coverage:
            |TestFile                                  | TestID                                               |
            |/tests/integration/api/test_projects.py   | @TestID:test_cannot_update_project_used_by_projects  |

    Scenario: Prevent deletion of a study-linked project 
        Given there is a study linked to the test project
        Given I delete this test project from the database
        Then the deletion should not be possible as a study is linked

        Test Coverage:
            |TestFile                                  | TestID                                               |
            |/tests/integration/api/test_projects.py   | @TestID:test_cannot_delete_project_used_by_projects  |