@REQ_ID:1074254
Feature: Studies - Study Branches

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study branch arms.

    Background: User is logged in
        Given The user is logged in

    Scenario: User must be able to navigate to Study Branches page using side menu
        Given A test study is selected
        Given The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Branches' tab is selected
        Then The current URL is 'studies/Study_000001/study_structure/branches'

    Scenario: User must be able to see the Study Branches table with options listed in this scenario
        Given A test study is selected
        Given The '/studies/Study_000001/study_structure/branches' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add Branch Arm                                                  |
            | Columns                                                         |
            | Add select boxes to table to allow selection of rows for export |
        And A table is visible with following headers
            | headers               |
            | #                     |
            | Arm name              |
            | Branch arm name       |
            | Branch arm short name |
            | Randomisation group   |
            | Branch Code           |
            | Number of subjects    |
            | Description           |
            | Colour                |
            | Modified              |
            | Modified by           |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000004/study_structure/branches' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    Scenario: User must be informed that no Study Arms are available
        Given A study without Study Arms has been selected
        And The '/studies/Study_000004/study_structure/branches' page is opened
        Then The table display the note "No data available - Create Study Arm first"

    Scenario: User must be able to create a new study arm when creating a branch for study without arms
        Given A study without Study Arms has been selected
        And The '/studies/Study_000004/study_structure/branches' page is opened
        When The 'add-study-branch-arm' button is clicked
        And The user clicks on Add Study Arm button in the information popup
        Then The current URL is 'studies/Study_000004/study_structure/arms'

    Scenario: User must be able to create a new study arm branch for existing arm
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        And The form for new study branch arm is filled and saved
        Then The study branch arm is visible within the table

    # Scenario: System must update the relationship to Study Design Cell when initial Study Branch Arm for a Study Arm is created
    #     Given A study with Study Arms has been selected
    #     And The '/studies/Study_000001/study_structure/branches' page is opened
    #     And no existing Study Branch Arm is related to the selected Study Arm
    #     And the selected Study Arm have Study Design Cell relationships to Study Elements for a Study Epochs
    #     When The new Study Branch Arm is added
    #     Then The new Study Design Cell selections changes their relationship from the Study Arm to the created Study Branch Arm

    Scenario: User must be able to edit the Study Branch Arm
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        When The study branch arm is edited
        Then The study branch arm with updated values is visible within the table

    Scenario: User must not be able to change the Study Arm for created Study Branch Arm
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        When The new Study Branch Arm with selected Study Arm is added
        Then The edit form for the branch arm has the Arm name field disabled

    #TODO: Input fields not hosting values
    # Scenario: Branch arm code default value must be populated from Randomisation Group
    #     Given A study with Study Arms has been selected
    #     Given The '/studies/Study_000001/study_structure/branches' page is opened
    #     When The Randomisation Group is populated in the Add New Branch Arm form
    #     And No value is specified for the field Branch Arm Code
    #     Then The Branch Arm code field is populated with value from Randomisation group field

    Scenario Outline: User must not be able to provide value other than positive integer for Number of subjects
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        And The value '<number>' is entered for the field Number of subjects in the Study Branch Arms form
        Then The validation appears under the field in the Study Branch Arms form

        Examples:
            | number |
            | -123   |
            | -1     |
            | 0      |

    Scenario: User must not be able to provide a value for number of subjects higher than the number defined for the study arm
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        And The value entered for the field Number of subjects is higher than the value defined for the selected study arm in the Study Branch Arms form
        Then The message 'Number of subjects in a branch cannot exceed total number of subjects in the arm' is displayed

    Scenario: User must not be able to create a Study Branch Arm without Study Arm selected
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        When The Study Arm field is not populated in the Study Branch Arms form
        And The Branch Arm name field is not populated
        And The Branch Arm short name field is not populated
        And The 'save-button' button is clicked
        Then The required field validation appears for the '3' empty fields
        And The form is not closed

    Scenario: User must not be able to create two Branch Arms within one study using the same Branch Arm name
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        When The Study Branch Arm is created with given branch arm name
        And Another Study Branch Arm is created with the same arm name
        Then The system displays the message "Value 'BA Test Arm Name' in field Branch Arm Name is not unique for the study"
        And The form is not closed

    Scenario: User must not be able to create two Branch Arms within one study using the same Branch Arm short name
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        When The Study Branch Arm is created with given branch arm short name
        And Another Study Branch Arm is created with the same branch arm short name
        Then The system displays the message "Value 'BA Test Short Name' in field Branch Arm Short Name is not unique for the study"
        And The form is not closed

    Scenario: User must not be able to create two Branch Arms within one study using the same Randomisation group
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        When The Study Branch Arm is created with given branch arm randomisation group
        And Another Study Branch Arm is created with the same randomisation group
        Then The system displays the message "Value 'BA Randomisation' in field Branch Arm Randomization code is not unique for the study"
        And The form is not closed

    Scenario: User must not be able to create two Branch Arms within one study using the same Branch code
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        When The Study Branch Arm is created with given branch code
        And Another Study Branch Arm is created with the same branch code
        Then The system displays the message "Value 'BA Test Branch Code' in field Branch Arm Code is not unique for the study"
        And The form is not closed

    # #TODO: Invoking value to type long 
    # Scenario Outline: User must not be able to use text longer than specified in this scenario for Study Branch Arms form
    #     Given A study with Study Arms has been selected
    #     And The '/studies/Study_000001/study_structure/branches' page is opened
    #     When For the '<field>' a text longer than '<length>' is provided in the Study Branch Arms form
    #     Then The message "This field must not exceed '<length>' characters" is displayed

    #     Examples:
    #         | field                       | length |
    #         | study-branch-arm-name       | 200    |
    #         | study-branch-arm-short-name | 20     |
    # # | study-branch-arm-randomisation-group | 20     | Comments from Mikkel: This requirement is under disucssion, will be updated later.

    Scenario: User must not be able to use text longer than 20 characters for the Study Arm Arm Code field in the Study Arms form
        Given A study with Study Arms has been selected
        And The '/studies/Study_000001/study_structure/branches' page is opened
        When For the Branch Code a text longer than 20 characters is provided in the Study Branch Arms form
        Then The message 'This field must not exceed 20 characters' is displayed

    Scenario: User must be able to export the data in CSV format
        Given The '/studies/Study_000001/study_structure/branches' page is opened
        And The user exports the data in 'CSV' format
        Then The study specific 'StudyBranches' file is downloaded in 'csv' format

    Scenario: User must be able to export the data in JSON format
        Given The '/studies/Study_000001/study_structure/branches' page is opened
        And The user exports the data in 'JSON' format
        Then The study specific 'StudyBranches' file is downloaded in 'json' format

    Scenario: User must be able to export the data in XML format
        Given The '/studies/Study_000001/study_structure/branches' page is opened
        And The user exports the data in 'XML' format
        Then The study specific 'StudyBranches' file is downloaded in 'xml' format

    Scenario: User must be able to export the data in EXCEL format
        Given The '/studies/Study_000001/study_structure/branches' page is opened
        And The user exports the data in 'EXCEL' format
        Then The study specific 'StudyBranches' file is downloaded in 'xlsx' format


    @manual_test
    Scenario: User must be able to remove the Study Branch Arm
        Given The '/studies/Study_000001/study_structure/branches' page is opened
        And The test Study Branch Arm is available
        When The delete action is clicked for the test Study Branch Arm
        Then The test Study Branch Arm is no longer available
        And related Study Design Cell selections are cascade deleted

    @manual_test
    Scenario: User must be presented with the warning message when removing the last Study Branch Arm
        Given The '/studies/Study_000001/study_structure/branches' page is opened
        And The test study branch arm is available
        And The test study arm is related to study design cell
        When The delete action is clicked for the 'To be removed' study arm
        Then The warning message appears 'Removing this Study Branch Arm will remove all related Study Cells'

    @manual_test
    Scenario: Deleting last Study Branch Arm for a Study Arm must update relationship to Study Design Cell
        Given a Study Arm has been defined for the study
        And only one Study Branch Arm exist related to this Study Arm
        And the Study Branch Arm have Study Design Cell relationships to Study Elements for a Study Epochs
        When The delete action is clicked for the Study Branch Arm
        Then The Study Design Cell selections will change their relationship from the Study Branch Arm to the related Study Arm

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/study_structure/branches' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/study_structure/branches' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames