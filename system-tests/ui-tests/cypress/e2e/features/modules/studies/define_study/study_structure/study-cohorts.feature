@REQ_ID:1074254
Feature: Studies - Study Cohorts

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study cohorts.

    Background: User is logged in
        Given The user is logged in

    Scenario: User must be able to navigate to Study Cohorts page using side menu
        Given A test study is selected
        And The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Cohorts' tab is selected
        Then The current URL is 'studies/Study_000001/study_structure/cohorts'

    Scenario: User must be able to see the Study Cohorts table with options listed in this scenario
        Given A test study is selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add Study Cohort                                                |
            | Columns                                                         |
            | Add select boxes to table to allow selection of rows for export |
        #And The search field is available in the table
        And A table is visible with following headers
            | headers            |
            | #                  |
            | Arm name           |
            | Branch Arm name    |
            | Cohort Name        |
            | Cohort Short Name  |
            | Cohort Code        |
            | Number of subjects |
            | Description        |
            | Colour             |
            | Modified           |
            | Modified by        |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    Scenario: User must be able to create a new study cohort
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The form for new study cohort is filled and saved
        Then The study cohort is visible within the table

    Scenario: User must be able to edit the Study Cohort
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The study cohort is edited
        Then The study cohort with updated values is visible within the table

    Scenario: User must be able to edit the Arm and Branch Arm while editing the Study Cohort
        # Given A study with Study Arms has been selected
        Given A test study is selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The study cohort is edit form is opened
        Then The fields of Arm and Branch arms in the cohort edit form are active for editing

    Scenario Outline: User must not be able to provide value other than positive integer for Number of subjects
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The value '<number>' is entered for the field Number of subjects in the Study Cohorts form
        Then The validation appears under the field in the Study Cohorts form

        Examples:
            | number |
            | -123   |
            | -1     |
            | 0      |

    Scenario: User must not be able to provide a value for number of subjects higher than the number defined for the study arm
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The value entered for the field Number of subjects is higher than the value defined for the selected study arm in the Study Cohorts form
        Then The message 'Number of subjects in a cohort cannot exceed total number of subject in the study' is displayed

    Scenario: User must not be able to create a Study Cohort without providing necessary data as in this scenario
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The form for new study cohort is filled
        And The Cohort name field is not populated
        And The Cohort short name field is not populated
        And The Cohort code field is not populated
        And The 'save-button' button is clicked
        Then The form is not closed

    Scenario: User must not be able to create two Cohorts within one study using the same Cohort name
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The Study Cohort is created with given cohort name
        And Another Study Cohort is created with the same cohort name
        Then The system displays the message "Value 'Cohort Test Name' in field Cohort Name is not unique for the study"
        And The form is not closed

    Scenario: User must not be able to create two Cohorts within one study using the same Cohort short name
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The Study Cohort is created with given cohort short name
        And Another Study Cohort is created with the same cohort short name
        Then The system displays the message "Value 'CH Test Short Name' in field Cohort Short Name is not unique for the study"
        And The form is not closed

    Scenario: User must not be able to create two Cohorts within one study using the same Cohort code
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The Study Cohort is created with given cohort code
        And Another Study Cohort is created with the same cohort code
        Then The system displays the message "Value '88' in field Cohort code is not unique for the study"
        And The form is not closed

    Scenario Outline: User must not be able to use text longer than specified in this scenario for Study Cohorts form
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When For the '<field>' a text longer than '<length>' is provided in the Study Cohorts form
        Then The message "This field must not exceed <length> characters" is displayed

        Examples:
            | field                   | length |
            | study-cohort-name       | 200    |
            | study-cohort-short-name | 20     |

    Scenario: User must not be able to create a Cohort with code less than 1
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When For the 'study-cohort-code' a '0' value is provided in Study Cohort form
        Then The message "Value can't be less than 1" is displayed

    Scenario: User must not be able to create a Cohort with code bigger than 99
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/cohorts' page is opened
        When For the 'study-cohort-code' a '100' value is provided in Study Cohort form
        Then The message "Value must be less than 99" is displayed


    @manual_test
    Scenario: User must be able to remove the Study Cohort
        Given The '/studies/Study_000001/study_structure/cohorts' page is opened
        And The test Study Cohort is available
        When The delete action is clicked for the test Study Cohort
        Then The test Study Cohort is no longer available
        And related Study Design Cell selections are cascade deleted

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/study_structure/cohorts' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames