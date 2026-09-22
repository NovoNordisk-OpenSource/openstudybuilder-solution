@REQ_ID:1074254 @manual_test
Feature: Studies - Define Study - Study Structure - Study Visits

     See shared notes for study visits in file study-visit-intro-notes.txt

     As a system user,
     I want the system to ensure [Scenario],
     So that I can make complete and consistent specification of study visits with automatic visit numbering.

     Background: User is logged in and study has been selected
          Given The user is logged in
          And a study with multiple visists of the class 'Scheduled visits' is selected

     Scenario: Visit number and unique visit number must be defined as 1 and 100 for the first scheduled visit
          Given The page 'study_structure/visits' is opened for current study
          And the first scheduled visit is not defined with the visit type as an 'information visit'
          Then The first scheduled visit is visible with visit number 1 and unique visit umber 100

     Scenario: Visit number and unique visit number must be defined as 0 for the first scheduled information visit
          Given The page 'study_structure/visits' is opened for current study
          And The first scheduled visit is created with the visit type as an 'information visit'
          And The visit timing is set to the lowest timing of all existing visit when compared to the Global Anchor time reference
          Then The Information visit should be created with 0 as Visit number
          And No reordering of existing visits should happen

     Scenario: Visit number and unique visit number must Not be defined as 0 for the non-first scheduled information visit
          Given The page 'study_structure/visits' is opened for current study
          And The first scheduled visit is created with the visit type as an 'information visit'
          And The visit timing is Not set to the lowest timing of all existing visit when compared to the Global Anchor time reference
          Then The Information visit should be created with the visit number and unique visit number as other normal visit
          And the reordering of visit number will occur

     Scenario: Visit number and unique visit number of information visit must be changed when lower timing visit is created 
          Given The page 'study_structure/visits' is opened for current study
          And The first scheduled information visit is created with visit 0
          When Create a new non-information study visit and with a ealier timing than the existing information visit
          Then The visit number for the visit 0 information visit must be changed to a number greater than 0
          And The new created visit will have a visit number 1

     Scenario: Visit number and unique visit number must be defined as +1 and +100 for each scheduled visit not being an additional sub-visit in a visit group
          Given The page 'study_structure/visits' is opened for current study
          Then Each scheduled visit has the visit number and unique visit number incremented by 1 and 100 respectfully

     Scenario: Visit number and unique visit number must be defined as the anchor visit in visit group and +10 for each sub-visit in a visit group
          Given The page 'study_structure/visits' is opened for current study
          Then Each sub visit in a visit group has the visit number as the anchor visit in the visit group and unique visit number incremented by 10
          # Note, multiple study visits will exist with the same visit number but differnt unique visit numbers.

     Scenario: User must be able to add a scheduled visit in between other visits with correct numbering recalculated
          Given The page 'study_structure/visits' is opened for current study
          And The new scheduled visit is added in between currently existing visit group
          Then The further scheduled visits have the numbering recalculated to include the new visit

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

