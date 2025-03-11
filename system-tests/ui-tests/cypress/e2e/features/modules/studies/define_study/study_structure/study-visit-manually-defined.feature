@REQ_ID:1074254 @pending_implementation
Feature: Studies - Study Visit

   See shared notes for study visits in file study-visit-intro-notes.txt

   As a system user,
   I want the system to ensure [Scenario],
   So that I can make complete and consistent specification of study visits.

   Background: User is logged in and study has been selected
      Given the user is logged in
      And a test study is selected


   Scenario: Visit name for Manual visits must be defined manually
      Given Study Visits is defined as a "Manually defined visit"
      When the visit is created or updated
      Then the visit number must be assigned manually by user input
      And the unique visit number must be assigned manually by user input
      And the visit name must be assigned manually by user input
      And the SDTM visit name as the upper case version of [visit name]

   Scenario: Visit number must support a decimal number data type
      Given study visit is defined as a "Manually defined visit"
      When the visit number is defined or updated
      Then the visit number must support a decimal number (float) data type

   Scenario: Unique visit number must support an integer number data type
      Given study visit is defined as a "Manually defined visit"
      When the unique visit number is defined or updated
      Then the unique visit number must support an integer data type

   Scenario Outline: Visit name, short name, number and unique number for manually defined study visits must be unique
      Given the '/studies/Study_000001/study_structure/visits' page is opened
      When a study visit is created or updated
      And the study visit is defined as a "Manually defined visit"
      And the <study visit field> is defined with a test value that already exist for the study
      Then the system displays the message "Value \"test value\" in field "<study visit field>" is not unique for the study"
      And the study visit values are not saved
      And The form is not closed
      Examples:
         | study visit field   |
         | Visit name          |
         | Visit short name    |
         | Visit number        |
         | Unique visit number |

   Scenario Outline: Visit name, short name, number and unique number for non-manually defined study visits must be unique
      Given the '/studies/Study_000001/study_structure/visits' page is opened
      When a study visit is created or updated
      And the study visit is not defined as a "Manually defined visit"
      And the <study visit field> is defined with a derived or preset test value that already exist for a manually defined study visit
      Then the system displays the message "Value \"test value\" in field "<study visit field>" is not unique for the study as a manually defined value exist. Change the manually defined value before this visit can be defined."
      And the study visit values are not saved
      And The form is not closed
      Examples:
         | study visit field   |
         | Visit name          |
         | Visit short name    |
         | Visit number        |
         | Unique visit number |

   Scenario: Visit number for manually defined study visits must be in cronological order by study visit timing
      Given the '/studies/Study_000001/study_structure/visits' page is opened
      When a study visit is created or updated
      And the study visit is defined as a "Manually defined visit"
      And the test visit number is not defined in cronological order by study visit timing
      Then the system displays the message "Value \"test visit number\" in field visit number is not defined in cronological order by study visit timing"
      And the study visit values are not saved
      And The form is not closed

   Scenario: Unique visit number for manually defined study visits must be in cronological order by study visit timing
      Given the '/studies/Study_000001/study_structure/visits' page is opened
      When a study visit is created or updated
      And the study visit is defined as a "Manually defined visit"
      And the test unique visit number is not defined in cronological order by study visit timing
      Then the system displays the message "Value \"test unique visit number\" in field unique visit number is not defined in cronological order by study visit timing"
      And the study visit values are not saved
      And The form is not closed
