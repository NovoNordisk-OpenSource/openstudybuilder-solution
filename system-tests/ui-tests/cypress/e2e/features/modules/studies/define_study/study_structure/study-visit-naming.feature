@REQ_ID:1074254 @manual_test
Feature: Studies - Study Visit Naming

   See shared notes for study visits in file study-visit-intro-notes.txt

   As a system user,
   I want the system to ensure [Scenario],
   So that I can make complete and consistent specification of study visits with automatic visit naming.

   Background: User is logged in and study has been selected
      Given The user is logged in
      And A test study is selected

   Scenario: Visit name for single visits must be derived as 'Visit ' + [Visit Number]
      Given Study Visits is defined as a "Single visit"
      When The visit is created or updated
      And The visit is asigned an automatic visit number
      Then The visit name must be derived as 'Visit ' + [Visit Number]
      And the SDTM visit name as the upper case version of [visit name]
      And The visit short name must be derived as [Abbreviation-Visit-Contact-Mode] + [Visit Number] where [Abbreviation-Visit-Contact-Mode] is defined as:
         | Visit Contact Mode | Abbreviation |
         | On Site Visit      | V            |
         | Phone Contact      | P            |
         | Virtual Visit      | O            |
   # How can we get these abbreviations into the database?
   # Currently hardcoded - parked for later
   # NOTE: Visit contact mode must not impact visit numbering

   # NOTE, visit name is the same as above - visit short name will include abbreviated version of visit sub label
   ### Newly added: automatic naming of visit sub-label
   Scenario: Visit name for visit in sequence of sub-visits must be derived as 'Visit ' + [Visit Number] + [Visit sub-label]
      Given Study Visits is defined as a "First visit in sequence of sub-visits" or "Additional sub-visit"
      When The visit is created or updated
      And The visit is asigned an automatic visit number
      Then The visit name must be derived as 'Visit ' + [Visit Number]
      And The visit sub-label must be derived as 'Day ' + the relative TimePoint in days when < 0 or relative TimePoint in days + 1 when >= 0
      And The visit sub-label abbrevation must be derived as 'D' + the relative TimePoint in days when < 0 or relative TimePoint in days + 1 when >= 0
      And the SDTM visit name as the the upper case version of [Visit name] + ' ' + [Visit sub-label]
      And The visit short name must be derived as [Abbreviation-Visit-Contact-Mode] + [Visit Number] + [Visit sub-label abbrevation] Where [Abbreviation-Visit-Contact-Mode] is defined as:
         | Visit Contact Mode | Abbreviation |
         | On Site Visit      | V            |
         | Phone Contact      | P            |
         | Virtual Visit      | O            |
   # all additional subvisit within a sub visit cluster / group must have a relative visit time reference, and this will control
   # naming of all visit sub-label will then be automatically derived

   Scenario: Visit name for repeating visits must be derived as 'Visit ' + [Visit Number]
      Given Study Visits is defined as a "Repeating visit"
      When The visit is created or updated
      And The visit is asigned an automatic visit number
      Then The visit name must be derived as 'Visit ' + [Visit Number]  + '.n'
      And the SDTM visit name as the upper case version of [visit name]
      And The visit short name must be derived as [Abbreviation-Visit-Contact-Mode] + [Visit Number] + '.n' where [Abbreviation-Visit-Contact-Mode] is defined as:
         | Visit Contact Mode | Abbreviation |
         | On Site Visit      | V            |
         | Phone Contact      | P            |
         | Virtual Visit      | O            |

   Scenario: Visit name for unscheduled visits must be set to 'Visit 29999'
      Given Study Visits is defined as a "Unscheduled visits"
      When The visit is created or updated
      Then The visit is asigned 29999 as the visit number
      And The visit name must be set as 'Visit 29999'
      And the SDTM visit name as the upper case version of [visit name]

   Scenario: Visit name for non-visit must be set to 'Visit 29500'
      Given Study Visits is defined as a "Non visits"
      When The visit is created or updated
      Then The visit is asigned 29500 as the visit number
      And The visit name must be set as 'Visit 29500'
      And the SDTM visit name as the upper case version of [visit name]

   Scenario: Visit name for special visits must be set as the reference visit
      Given Study Visits is defined as a "Special visits"
      When The visit is created or updated with a time reference to an existing scheduled visit
      Then The visit is asigned the same visit numbers as the reference visit
      And The visit name must be set as the reference visit
      And The short visit name must be set as the short visit name + a running letter (as A, B, C,etc.)
      And the SDTM visit name as the upper case version of [visit name]


#? Below scenarious seem to be redundant with feature file study-visit-timing.feature
   Scenario: Study Duration Days
      Given Study Visits is defined with a Time reference and a Time Point (Time span and Time unit)
      When The visit is created or updated
      Then The derived value for Study Duration Days must be calculated as the value for Study Duration Days for the visit of the time reference time + the time span value specified for the study visit converted into days time unit.
      And the study duration days label is derived as [study duration days] + ' days'

   Scenario: Study Duration Weeks
      Given Study Visits is defined with a Time reference and a Time Point (Time span and Time unit)
      When The visit is created or updated
      Then The derived value for Study Duration Weeks must be calculated as the value for Study Duration Weeks for the visit of the time reference time + the time span value specified for the study visit converted into weeks time unit.
      And the study duration weeks label is derived as [study duration weeks] + ' weeks'

   Scenario: Study Day
      Given Study Visits is defined with a Time reference and a Time Point (Time span and Time unit)
      When The visit is created or updated
      Then The derived value for study day is equal to the derived [study duration days] if value is less than 0
      And The derived value for study day is equal to the derived [study duration days] + 1 if value is greater than or equal 0
      And the study day label is derived as 'Day ' + [study day]

   Scenario: Study Week
      Given Study Visits is defined with a Time reference and a Time Point (Time span and Time unit)
      When The visit is created or updated
      Then The derived value for study week is equal to the derived [study duration weeks] if value is less than 0
      And The derived value for study week is equal to the derived [study duration weeks] + 1 if value is greater than or equal 0
      And the study week label is derived as 'Week ' + [study day]
