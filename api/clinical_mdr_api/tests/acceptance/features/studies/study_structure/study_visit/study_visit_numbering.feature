
@REQ_ID:1074254
Feature: Maintaining Study Visit Numbering in OpenStudyBuilder API

# See shared notes for study visits in file system-tests/cypress/e2e/features/modules/studies/define_study/study_structure/study-visit-intro-notes.txt

   Background: Test user must be able to call the OpenStudyBuilder API
        Given The test user can call the OpenStudyBuilder API

    Rule: As an API user,
        I want the system to ensure [Scenario],
        So that I can make complete and consistent specification of study visits with automatic visit numbering.

    @for_later_release 
    # The definition of this feature is still under the discussion
    Scenario: Visit number and unique visit number must be defined as 0 for the first scheduled visit if this is an information visit
          When the first scheduled visit is defined with the visit type as an 'information visit'
          Then The first scheduled visit within the group is visible with visit number 0 and unique visit number 0


