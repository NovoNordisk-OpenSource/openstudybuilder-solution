@REQ_ID:1074254 @manual_test
Feature: Studies - Study Visit Sub Numbering

   See shared notes for study visits in file study-visit-intro-notes.txt

   As a system user,
   I want the system to ensure [Scenario],
   So that I can make complete and consistent specification of study sub visits with automatic sub visit numbering.

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And A test study is selected

   Scenario: The Anchor visit in a visit group created for a sequence of sub-visits must get visit number increased by 1 and unique visit number by 100 from previous visit
      Given some study visits has been defined for the study
      When the user creates the anchor visit for a a sequence of sub-visits
      And the new visit is defined to have automatic visit numbering
      Then the new visit will get the visit number as the visit number from the previous visit with automatic numbering + 1
      And the new visit will get the unique visit number as the (visit number * 100) + 10

   Scenario: The additional sub-visit for a visit group created in chronological sequence of sub-visits must get visit number from initiating sub visit and unique visit number increased by 10
      Given study sub-visits has been defined for the study
      When the user creates an additional sub-visit in the chronological sequence of sub-visits
      And the new visit is defined to have automatic visit numbering
      Then the new visit will get the visit number as the visit number from the visit with automatic numbering initiating the sequence of sub-visits
      And the new visit will get the unique visit number as the (visit number * 100) + 10

   Scenario: The additional sub-visit for a visit group created within the sequence of sub-visits must get visit number from initiating sub visit, unique visit number increased by 10, following sub-visit must be renumbered
      Given study sub-visits has been defined for the study
      When the user creates an additional sub-visit within the existing sequence of sub-visits
      And the new visit is defined to have automatic visit numbering
      Then the new visit will get the visit number as the visit number from the visit with automatic numbering initiating the sequence of sub-visits
      And the new visit will get the unique visit number as the unique visit number from the previous sub-visit with automatic numbering + 10
      And the following sub-visits with automatic numbering will get their unique visit number to be the previous value + 10

   Scenario: The removal of sub-visit in a visit group within the sequence of sub-visits must renumber following sub-visits
      Given a sequence of study sub-visits has been defined for the study
      When the user removes (delete) a sub-visit within the existing sequence of sub-visits
      And the visit is defined to have automatic visit numbering
      Then the following sub-visits with automatic numbering will get their unique visit number to be the previous value - 10

   Scenario: When the number of sub-visits within a visit group becomes greater than 9 then sub-visits must be renumbered in steps by 5
      Given 9 study sub-visits has been defined within a sequence of sub-visits for the study
      When the user adds an additional sub-visit within the existing sequence of sub-visits
      And the new visit is defined to have automatic visit numbering
      Then all unique visit numbers within the existing sequence of sub-visits with automatic numbering must be incremented in steps by 5 instead of 10

   Scenario: When adding sub-visits within a visit group of sub-visits greater than 9 then sub-visits must be numbered in steps by 5
      Given more than 9 study sub-visits has been defined within a sequence of sub-visits for the study
      When the user adds an additional sub-visit within the existing sequence of sub-visits
      And the new visit is defined to have automatic visit numbering
      Then the unique visit number for the new sub-visits (and following sub-visits with automatic numbering if applicable) must be incremented by 5

