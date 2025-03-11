@REQ_ID:1074254 @manual_test
Feature: Studies - Study Visit Numbering

     See shared notes for study visits in file study-visit-intro-notes.txt

     As a system user,
     I want the system to ensure [Scenario],
     So that I can make complete and consistent specification of study visits with automatic visit numbering.

     Background: User is logged in and study has been selected
          Given The user is logged in
          And a study with multiple visists of the class 'Scheduled visits' is selected

     Scenario: Visit number and unique visit number must be defined as 1 and 100 for the first scheduled visit
          When The '/studies/Study_000001/study_structure/visits' page is opened
          And the first scheduled visit is not defined with the visit type as an 'information visit'
          Then The first scheduled visit is visible with visit number 1 and unique visit umber 100

     Scenario: Visit number and unique visit number must be defined as 0 for the first scheduled information visit
          When The '/studies/Study_000001/study_structure/visits' page is opened
          And The first scheduled visit is created with the visit type as an 'information visit'
          And The visit timing is set to the lowest timing of all existing visit when compared to the Global Anchor time reference
          Then The Information visit should be created with 0 as Visit number
          And No reordering of existing visits should happen

     Scenario: Visit number and unique visit number must Not be defined as 0 for the non-first scheduled information visit
          When The '/studies/Study_000001/study_structure/visits' page is opened
          And The first scheduled visit is created with the visit type as an 'information visit'
          And The visit timing is Not set to the lowest timing of all existing visit when compared to the Global Anchor time reference
          Then The Information visit should be created with the visit number and unique visit number as other normal visit
          And the reordering of visit number will occur

     Scenario: Visit number and unique visit number of information visit must be changed when lower timing visit is created 
          Given The '/studies/Study_000001/study_structure/visits' page is opened
          And The first scheduled information visit is created with visit 0
          When Create a new non-information study visit and with a ealier timing than the existing information visit
          Then The visit number for the visit 0 information visit must be changed to a number greater than 0
          And The new created visit will have a visit number 1

     Scenario: Visit number and unique visit number must be defined as +1 and +100 for each scheduled visit not being an additional sub-visit in a visit group
          When The '/studies/Study_000001/study_structure/visits' page is opened
          Then Each scheduled visit has the visit number and unique visit number incremented by 1 and 100 respectfully

     Scenario: Visit number and unique visit number must be defined as the anchor visit in visit group and +10 for each sub-visit in a visit group
          When The '/studies/Study_000001/study_structure/visits' page is opened
          Then Each sub visit in a visit group has the visit number as the anchor visit in the visit group and unique visit number incremented by 10
          # Note, multiple study visits will exist with the same visit number but differnt unique visit numbers.

     Scenario: User must be able to add a scheduled visit in between other visits with correct numbering recalculated
          When The '/studies/Study_000001/study_structure/visits' page is opened
          And The new scheduled visit is added in between currently existing visit group
          Then The further scheduled visits have the numbering recalculated to include the new visit
