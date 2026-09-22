@REQ_ID:1074254
Feature: Maintaining Study Repeating Visit in OpenStudyBuilder API

# See shared notes for study visits in file system-tests/cypress/e2e/features/modules/studies/define_study/study_structure/study-visit-intro-notes.txt

   Background: Test user must be able to call the OpenStudyBuilder API
        Given The test user can call the OpenStudyBuilder API

    Rule: As an API user,
        I want the system to ensure [Scenario],
        So that I can make complete and consistent specification of study repeating visits with automatic visit numbering and naming.

   Scenario: User must be able to create a repeating visit with correct number and name
        When A repeating visit is created
        Then The visit number should be chronological 
        And The visit name and visit short name should follow visit naming rules

        Test Coverage:
            |TestFile                                                        | TestID                                      |
            |/tests/integration/api/study_selections/test_study_visits.py    | @TestID:test_create_repeating_visit         |

    Scenario: User must be able to create a repeating visit with daily, weekly and monthly frequency
        When Creat a repeating visit and set it to daily frequency
        Then This reapting visit is created with daily fequency
        When Creat a repeating visit and set it to weekly frequency
        Then This reapting visit is created with weekly fequency
        When Creat a repeating visit and set it to monthly frequency
        Then This reapting visit is created with monthly frequency

        Test Coverage:
            |TestFile                                                        | TestID                                      |
            |/tests/integration/api/study_selections/test_study_visits.py    | @TestID:test_create_repeating_visit         |
