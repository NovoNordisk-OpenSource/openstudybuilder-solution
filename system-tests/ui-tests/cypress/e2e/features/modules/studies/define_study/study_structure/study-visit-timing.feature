@REQ_ID:1074254 @manual_test
Feature: Studies - Study Visit Timing

    See shared notes for study visits in file study-visit-intro-notes.txt

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of timing for study visits.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected


    Scenario Outline: User must be able to select visit time unit only for first defined visit
        Given No visits has been defined for the study
        When The user is defining first visit in the study with the time unit as 'unit'
        Then The every next study visit for that study is using the same time unit

        Examples:
            | unit  |
            | day   |
            | week  |
            | year  |
            | days  |
            | weeks |
            | years |


    # Terms for Time Reference is shared with Visit Types, for Visit Types that can represent a Time reference
    # This will be the base visit for all time calculation
    Scenario: Each study have a global anchor visit having time span value set as 0 and visit type must the same as the time reference
        Given no visit have been defined as a global anchor visit with the time referencespan value set as 0
        When a visit is defined as a global anchor visit with the time reference span value set as 0
        Then the the visit type must be set to the same value as the time reference

    # E.g. a 2nd Baseline, Ranodmisation etc.
    # First additional time reference visit must refer time to the global anchor visits
    Scenario: Each study can have aditional unique time reference visits
        Given a visit have been defined as a global anchor visit with the time reference span value set as 0
        When study visits is being defined
        Then additional time reference visits can be defined
        And these must have a time reference span value different than 0
        And the time reference must be different than the visit type
        And the time reference must refer to an existing reference visit or the global anchor visit

    # Define and refine rules.
    Scenario: Each study can have a set of sub-visits each having time reference to the anchor visit in visit group visit initiating the series of sub-visits
        Given a scheduled visit has been defined as the anchor visit in visit group
        When additional sub-visits are defined
        Then these sub visit must have their time reference defined to the anchor visit in this visit group

    # It should not be possible to refer to a time reference visit not defined for the study (e.g. baseline 2 is only an option if this is defined for the study)
    Scenario: A scheduled study visit can either refer to the global anchor visit, previous vist or a defined reference time visit for the study
        When scheduled study visits is being defined
        Then the study visit can have a time reference to the global anchor visit, previous vist or a defined reference time visit for the study

    #Scenario: Each scheduled study visit will be related to an absolute or relative TimePoint
    # Not sure if this scenario is needed or coverred above
    ###########################################################
    ###### Following section describe the time calculation

    Scenario: Each Unscheduled visit or Non-visit defined for the study must not have a reference time defined
        When an Unscheduled visit or Non-visit is defined for the study
        Then it must not be possible to define a time reference, time value and time unit
        And overall time will not be derived

    Scenario: The scheduled study visit defined as the global anchor visit must get the absolute duration time as 0
        When the scheduled global anchor visit is defined with time 0
        Then the time point must be time 0
        And the Study duration days value '0'
        And the Study duration days name '0 Days'
        And the Study duration weeks value '0'
        And the Study duration weeks name '0 Weeks'
        And the Study day value '1'
        And the Study day name 'Day 1'
        And the Study week value '1'
        And the Study week name 'Week 1'

    #### We need to clarify rounding using ceil/floor - as multiple visits then can get the same time value!!!

    # Derive overall time as relationship to StudyDay, StudyWeek, StudyDurationDay, StudyDurationWeek

    Scenario Outline: Each scheduled study visit having an absolute time reference to the global anchor visit must get the overall time derived
        When a scheduled visit is defined with time different from 0
        And an absolute time refefrence to the global anchor visit at time 0
        And the scheduled visit is not a repeating visit
        Then the time point must be the defined <Timing> value in the defined <Time unit> with reference to the global anchor visit
        And the <Study duration days value> is derived as the defined time value converted to days
        And the <Study duration days name> is derived as <Study duration days value> + ' days'
        And the <Study duration weeks value> is derived as the defined time value converted to weeks
        And the <Study duration weeks name> is derived as <Study duration weeks value> + ' weeks'
        And the <Study day value> is derived as <Study duration days value> if value is less than 0 or <Study duration days value> + 1 if value is equal or greather than 0
        And the <Study day name> is derived as 'Day ' + <Study day value>
        And the <Study week value> is derived as <Study duration weeks value> if value is less than 0 or <Study duration weeks value> + 1 if value is equal or greather than 0
        And the <Study week name> is derived as 'Week ' + <Study week value>
        And the <Study week name> is derived as 'Week ' + <Study duration weeks value>
        Examples:
            | Timing | Time unit | Study duration days value | Study duration days name | Study duration weeks value | Study duration weeks name | Study day value | Study day name | Study week value | Study week name | Week in study |
            | -14    | days      | -14                       | -14 days                 | -2                         | -2 weeks                  | -14             | Day -14        | -2               | Week -2         | Week -2       |
            | -1     | days      | -1                        | -1 days                  | 0                          | 0 weeks                   | -1              | Day -1         | -1               | Week -1         | Week 0        |
            | 0      | days      | 0                         | 0 days                   | 0                          | 0 weeks                   | 1               | Day 1          | 1                | Week 1          | Week 0        |
            | 1      | days      | 1                         | 1 days                   | 0                          | 0 weeks                   | 2               | Day 2          | 1                | Week 1          | Week 0        |
            | 14     | days      | 14                        | 14 days                  | 2                          | 2 weeks                   | 15              | Day 15         | 3                | Week 3          | Week 2        |


    Scenario: Each scheduled study visit having a relative time reference must get the overall absolute time calculated
        When a scheduled visit is defined with time different from 0
        And a relative time refefrence to another visit having a specified time value
        And the scheduled visit is not a repeating visit
        Then the time point must be the defined <Timing> value in the defined <Time unit> with reference to the time reference visit
        And the <Study duration days value> is derived as the defined time value converted to days + the <Reference Study duration days value> from the time reference visit
        And the <Study duration days name> is derived as <Study duration days value> + ' days'
        And the <Study duration weeks value> is derived as <Study duration days value> converted to weeks
        And the <Study duration weeks name> is derived as <Study duration weeks value> + ' weeks'
        And the <Study day value> is derived as <Study duration days value> if value is less than 0 or <Study duration days value> + 1 if value is equal or greather than 0
        And the <Study day name> is derived as 'Day ' + <Study day value>
        And the <Study week value> is derived as <Study duration weeks value> if value is less than 0 or <Study duration weeks value> + 1 if value is equal or greather than 0
        And the <Study week name> is derived as 'Week ' + <Study week value>
        Examples:
            | Timing | Time unit | Reference Study duration days value | Study duration days value | Study duration days name | Study duration weeks value | Study duration weeks name | Study day value | Study day name | Study week value | Study week name | Week in study |
            | -14    | days      | 7                                   | -7                        | -7 days                  | -1                         | -1 weeks                  | -7              | Day -7         | -1               | Week -1         | Week -1       |
            | 0      | days      | 7                                   | 7                         | 7 days                   | 1                          | 1 weeks                   | 8               | Day 8          | 2                | Week 2          | Week 1        |
            | 14     | days      | 7                                   | 21                        | 21 days                  | 3                          | 3 weeks                   | 22              | Day 22         | 4                | Week 4          | Week 3        |

    @Release1.7
    Scenario: Each scheduled repeating study visit having an absolute time reference to the global anchor visit must get the overall start time derived
        When a scheduled repeating visit is defined with time different from 0
        And an absolute time refefrence to the global anchor visit at time 0
        Then the starting time point must be the defined time value in the defined time unit with reference to the global anchor visit
        And the time point must be flagged as an repeating time point
        And the Study duration days value is derived as the defined time value converted to days
        And the Study duration days name is derived as [Study duration days value] + ' Days' + '(repeating' + [repeating-frequency] + ')'
        # i.e. study day name can be: "Day 57 (repeating weekly)" or if repeating frequency not is defined: "Day57 (repeating)"
        And the Study duration weeks value is derived as the defined time value converted to weeks
        And the Study duration weeks name is derived as [Study duration weeks value] + ' Weeks' + '(repeating' + [repeating-frequency] + ')'
        And the Study day value is derived as [Study duration days value] if value is less than 0 or [Study duration days value] + 1 if value is equal or greather than 0
        And the Study day name is derived as 'Day ' + [Study day value] + '(repeating' + [repeating-frequency] + ')'
        And the Study week value is derived as [Study duration weeks value] if value is less than 0 or [Study duration weeks value] + 1 if value is equal or greather than 0
        And the Study week name is derived as 'Week ' + [ Study week value] + '(repeating' + [repeating-frequency] + ')'

    @Release1.7
    Scenario: Each scheduled repeating study visit having a relative time reference must get the overall absolute time calculated
        When a scheduled repeating visit is defined with time different from 0
        And a relative time refefrence to another visit having a specified time value
        Then the starting time point must be the defined time value in the defined time unit with reference to the time reference visit
        And the time point must be flagged as an repeating time point
        And the Study duration days value is derived as the defined time value converted to days + the [Study duration days value] from the time reference visit
        And the Study duration days name is derived as [Study duration days value] + ' Days' + '(repeating' + [repeating-frequency] + ')'
        And the Study duration weeks value is derived as [Study duration days value] converted to weeks
        And the Study duration weeks name is derived as [Study duration weeks value] + ' Weeks' + '(repeating' + [repeating-frequency] + ')'
        And the Study day value is derived as [Study duration days value] if value is less than 0 or [Study duration days value] + 1 if value is equal or greather than 0
        And the Study day name is derived as 'Day ' + [Study day value] + '(repeating' + [repeating-frequency] + ')'
        And the Study week value is derived as [Study duration weeks value] if value is less than 0 or [Study duration weeks value] + 1 if value is equal or greather than 0
        And the Study week name is derived as 'Week ' + [ Study week value] + '(repeating' + [repeating-frequency] + ')'


###? we need to define if we also add a short study day/week name holding a short version to be used in the SoA time row.