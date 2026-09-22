@REQ_ID:1074254
Feature: Maintaining Study Visit Manually Define in OpenStudyBuilder API

# See shared notes for study visits in file system-tests/cypress/e2e/features/modules/studies/define_study/study_structure/study-visit-intro-notes.txt

   Background: Test user must be able to call the OpenStudyBuilder API
        Given The test user can call the OpenStudyBuilder API
        
   Scenario: Visit name for manually defined visits must be defined manually
      Given Study Visits is defined as a "Manually defined visit"
      When The visit is created or updated
      Then The visit number must be assigned manually by user input
      And The unique visit number must be assigned manually by user input
      And The visit name must be assigned manually by user input
      And The SDTM visit name as the upper case version of visit name

      Examples:
            |TestFile                                                    | TestID                                   |
            |/tests/integration/api/study_selections/test_study_visit.py | @TestID:test_manually_defined_visit      |

   Scenario: Visit number must support a decimal number data type
      Given Study Visits is defined as a "Manually defined visit"
      When The visit number is defined or updated
      Then The visit number must support a decimal number "float" data type

            Examples:
            |TestFile                                                    | TestID                                   |
            |/tests/integration/api/study_selections/test_study_visit.py | @TestID:test_manually_defined_visit      |

   Scenario: Unique visit number must support an integer number data type
      Given Study Visits is defined as a "Manually defined visit"
      When The unique visit number is defined or updated
      Then the unique visit number must support an integer data type

            Examples:
            |TestFile                                                    | TestID                                   |
            |/tests/integration/api/study_selections/test_study_visit.py | @TestID:test_manually_defined_visit      |

   Scenario Outline: Visit name, short name, number and unique number for manually defined study visits must be unique
      When A study visit is created or updated
      And The study visit is defined as a "Manually defined visit"
      And The <study visit field> is defined with a test value that already exist for the study
      Then The system displays the message "Value 'test value' in field "<study visit field>" is not unique for the study."
         Examples:
         | study visit field   |
         | Visit name          |
         | Visit short name    |
         | Visit number        |
         | Unique visit number |

            Examples:
            |TestFile                                                    | TestID                                   |
            |/tests/integration/api/study_selections/test_study_visit.py | @TestID:test_manually_defined_visit      |

   Scenario Outline: Visit name, short name, number and unique number for non-manually defined study visits must be unique
      When A study visit is created or updated
      And The study visit is not defined as a "Manually defined visit"
      And The <study visit field> is defined with a derived or preset test value that already exist for a manually defined study visit
      Then The system displays the message "Value 'test value' in field "<study visit field>" is not unique for the study as a manually defined value exist. Change the manually defined value before this visit can be defined."

         Examples:
         | study visit field   |
         | Visit name          |
         | Visit short name    |
         | Visit number        |
         | Unique visit number |

         Examples:
            |TestFile                                                    | TestID                                   |
            |/tests/integration/api/study_selections/test_study_visit.py | @TestID:test_non_manually_defined_visit  |

   Scenario: Visit number for manually defined study visits must be in chronological order by study visit timing
      When A study visit is created and defined as a "Manually defined visit"
      And The test visit number is not defined in chronological order by study visit timing
      Then The system displays the message "Value 'test visit number' in field visit number is not defined in chronological order by study visit timing."

      Examples:
            |TestFile                                                    | TestID                                                                     |
            |/tests/integration/api/study_selections/test_study_visit.py | @TestID:test_manually_defined_visit_in_chronological_order_by_visit_timing |

      
   Scenario: Unique visit number for manually defined study visits must be in chronological order by study visit timing
      When A study visit is created or updated
      And The study visit is defined as a "Manually defined visit"
      And The test unique visit number is not defined in chronological order by study visit timing
      Then The system displays the message "Value 'test unique visit number' in field unique visit number is not defined in chronological order by study visit timing."

      Examples:
            |TestFile                                                    | TestID                                                                      |
            |/tests/integration/api/study_selections/test_study_visit.py | @TestID:test_manually_defined_visit_in_chronological_order_by_visit_timing  |


 