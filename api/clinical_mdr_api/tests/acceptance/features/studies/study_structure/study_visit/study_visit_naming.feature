
@REQ_ID:1074254
Feature: Maintaining Study Visit Naming in OpenStudyBuilder API

# See shared notes for study visits in file system-tests/cypress/e2e/features/modules/studies/define_study/study_structure/study-visit-intro-notes.txt

   Background: Test user must be able to call the OpenStudyBuilder API
        Given The test user can call the OpenStudyBuilder API

    Rule: As an API user,
        I want the system to ensure [Scenario],
        So that I can make complete and consistent specification of study visits with automatic visit naming.

   Scenario: Visit name for repeating visits must be derived as 'Visit ' + [Visit Number]
      Given Study Visits is defined as a "Repeating visit"
      When The visit is created or updated
      And The visit is asigned an automatic visit number
      Then The visit name must be derived as 'Visit ' + [Visit Number]  + '.N'
      And the SDTM visit name as the upper case version of [visit name]
      And The visit short name must be derived as [Abbreviation-Visit-Contact-Mode] + [Visit Number] + '.n' where [Abbreviation-Visit-Contact-Mode] is defined as:
         | Visit Contact Mode | Abbreviation |
         | On Site Visit      | V            |
         | Phone Contact      | P            |
         | Virtual Visit      | O            |


