
@REQ_ID:1074254
Feature: Maintaining Study Visit 0 in OpenStudyBuilder API

# See shared notes for study visits in file system-tests/cypress/e2e/features/modules/studies/define_study/study_structure/study-visit-intro-notes.txt

   Background: Test user must be able to call the OpenStudyBuilder API
        Given The test user can call the OpenStudyBuilder API

    Rule: As an API user,
        I want the system to ensure [Scenario],
        So that I can make complete and consistent specification of study visits 0 with automatic visit numbering and naming.

   Scenario: User must be able to create an information visit with visit 0 if the time value is the lowest
        When The first scheduled visit is created with the visit type as an Information visit
        And The visit timing is set to the lowest timing of all existing visit when compared to the Global Anchor time reference
        Then The Information visit should be created with 0 as Visit number
        And No reordering of existing visits should happen

        Test Coverage:
            |TestFile                                                        | TestID                                         |
            |/tests/integration/api/study_selections/test_study_visits.py    | @TestID:test_visit_0_created_chronologically   |

     Scenario: User must be able to create an information visit without visit 0 if the time value is not the lowest
        When A scheduled visit is created with the visit type as an Information visit
        And The visit timing is Not set to the lowest timing of all existing visit when compared to the Global Anchor time reference
        Then The Information visit should Not be created with 0 as Visit number
        And The reordering of existing visits should happen

        Test Coverage:
            |TestFile                                                        | TestID                                         |
            |/tests/integration/api/study_selections/test_study_visits.py    | @TestID:test_visit_0_created_chronologically   |

    Scenario: User must be able to indirectly edit the existing information visit 0 when a new visit is added with a lower time value
        Given An information visit 0 exists
        When A new non-information visit is created with a lower time value than the existing information visit 0
        Then The existing information visit 0 should be renamed to visit 2 and renumbered to 2
        And The newly created visit should be visit 1

        Test Coverage:
            |TestFile                                                        | TestID                                         |
            |/tests/integration/api/study_selections/test_study_visits.py    | @TestID:test_visit_0_created_chronologically   |

    Scenario: User must be able to edit the study information visit with visit 0 to other visit type
        Given A study inforamtion visit with visit 0 is created
        When This study information visit is edited to be a different visit type
        Then This visit can no longer be Visit 0
        And Reordering will occur of existing visits

        Test Coverage:
            |TestFile                                                        | TestID                                         |
            |/tests/integration/api/study_selections/test_study_visits.py    | @TestID:test_visit_0_edited_chronologically    |

     Scenario: User must be able to edit the study information visit with visit 0 to same visit type
        Given A study inforamtion visit with visit 0 is created
        When This study information visit is edited to the same visit type
        Then This visit should be given the visit number of 0
        When This visit is edited to higher visit timing compare to the Global Anchor time reference
        Then This information visit should not be given the visit number of 0
        Then Reordering of other visits will occur

        Test Coverage:
            |TestFile                                                        | TestID                                         |
            |/tests/integration/api/study_selections/test_study_visits.py    | @TestID:test_visit_0_edited_chronologically    |

    Scenario: User must be able to delete the study information visit with visit 0
        Given A study inforamtion visit with visit 0 is created
        When This study information visit is deleted
        Then No reordering of other visits will occur

        Test Coverage:
            |TestFile                                                        | TestID                                         |
            |/tests/integration/api/study_selections/test_study_visits.py    | @TestID:test_create_visit_0                    |

    Scenario: User must be able to delete the study information visit without visit 0
        Given A study inforamtion visit without visit 0 is created
        When This study information visit is deleted
        Then The reordering of other visits will occur

        Test Coverage:
            |TestFile                                                        | TestID                                         |
            |/tests/integration/api/study_selections/test_study_visits.py    | @TestID:test_visit_0_edited_chronologically    |
