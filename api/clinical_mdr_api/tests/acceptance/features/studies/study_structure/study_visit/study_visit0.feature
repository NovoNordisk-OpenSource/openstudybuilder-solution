
@REQ_ID:1074254
Feature: Maintaining Study Visit 0 in OpenStudyBuilder API

# See shared notes for study visits in file system-tests/cypress/e2e/features/modules/studies/define_study/study_structure/study-visit-intro-notes.txt

   Background: Test user must be able to call the OpenStudyBuilder API
        Given The test user can call the OpenStudyBuilder API

    Rule: As an API user,
        I want the system to ensure [Scenario],
        So that I can make complete and consistent specification of study visits 0 with automatic visit numbering and naming.

   Scenario: User must be able to create an information visit with visit 0
        When The first scheduled visit is created with the visit type as an Information visit
        And The visit timing is set to the lowest timing of all existing visit when compared to the Global Anchor time reference
        Then The Information visit should be created with 0 as Visit number
        And No reordering of existing visits should happen

    Scenario: User must be able to edit the study information visit with visit 0 to other visit type
        Given A studty inforamtion visit with visit 0 is created
        When This study information visit is edited to be a different visit type
        Then This visit can no longer be Visit 0
        And Reordering will occur of existing visits

     Scenario: User must be able to edit the study information visit with visit 0 to same visit type
        Given A studty inforamtion visit with visit 0 is created
        When This study information visit is edited to the same visit type
        Then This visit should be given the visit number of 0
        When This visit is edited to higher visit timing compare to the Global Anchor time reference
        Then Reordering of other visits will occur

    Scenario: User must be able to delete the study information visit with visit 0
        Given A studty inforamtion visit with visit 0 is created
        When This study information visit is deleted
        Then No reordering of other visits will occur

    Scenario: User must be able to delete the study information visit without visit 0
        Given A studty inforamtion visit without visit 0 is created
        When This study information visit is deleted
        Then The reordering of other visits will occur

