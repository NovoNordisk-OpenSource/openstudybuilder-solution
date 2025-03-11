@REQ_ID:1074254
Feature: Studies - Study Arms

    As a system user,
    I want the system to ensure [Scenario],
    So that I must be able to make complete and consistent specification of study arms.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: User must be able to navigate to Study Arms page using side menu
        Given The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Arms' tab is selected
        Then The current URL is 'studies/Study_000001/study_structure/arms'

    Scenario: User must be able to see the Study Arms table with options listed in this scenario
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add study arm                                                   |
            | Columns                                                         |
            | Export                                                          |
            | Show version history                                            |
            | Add select boxes to table to allow selection of rows for export |

        # And The search field is available in the table - disabled for MVP
        And A table is visible with following headers
            | headers             |
            | #                   |
            | Type                |
            | Arm name            |
            | Arm short name      |
            | Randomisation group |
            | Arm code            |
            | Number of subjects  |
            | Connected Branches  |
            | Description         |
            | Colour              |
            | Modified            |
            | Modified by         |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    Scenario: User must be able to add a new Study Arm
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        When The new study arm form is filled and saved
        Then The new study arm is visible within the study arms table

   Scenario: User must be able to edit an existing Study Arm
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        And The Study Arm exists within the study
        When The arm data is edited and saved
        Then The study arm with updated values is visible within the study arms table

    # Scenario: Arm code default value must be populated from Randomisation Group
    #     Given The '/studies/Study_000001/study_structure/arms' page is opened
    #     When The Randomisation Group is populated in the Add New Arm form
    #     And no value is specified for the field Arm Code
    #     Then The Arm code field is populated with value from Randomisation group field

    Scenario Outline: User must not be able to provide value other than positive integer for Number of subjects
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        And The value '<number>' is entered for the field Number of subjects in the Study Arms form
        Then The validation appears under the field in the Study Arms form

        Examples:
            | number |
            | -1     |
            | 0      |
            | -10    |

    Scenario: User must not be able to create a Study Arm without Arm Name and Arm Short Name provided in the Study Arms form
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        When The Arm name field is not populated
        And The Arm short name field is not populated
        And The 'save-button' button is clicked
        Then The required field validation appears for the '2' empty fields
        And The form is not closed

    Scenario: User must not be able to create two Arms within one study using the same Arm name
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        When The Study Arm is created with given name
        And Another Study Arm is created with the same arm name
        Then The system displays the message "Value 'Test Arm Name' in field Arm name is not unique for the study"
        And The form is not closed

    Scenario: User must not be able to create two Arms within one study using the same Arm short name
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        When The Study Arm is created with given short name
        And Another Study Arm is created with the same arm short name
        Then The system displays the message "Value 'Test Short Name' in field Arm short name is not unique for the study"
        And The form is not closed

    Scenario: User must not be able to create two Arms within one study using the same Arm randomisation group
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        When The Study Arm is created with given randomisation group
        And Another Study Arm is created with the same randomisation group
        Then The system displays the message "Value 'Test Randomisation Group' in field Arm Randomization code is not unique for the study"
        And The form is not closed

    # Scenario Outline: User must not be able to use text longer than specified in this scenario for Study Arms form
    #     Given The '/studies/Study_000001/study_structure/arms' page is opened
    #     When For the '<field>' a text longer than '<length>' is provided in the Study Arms form
    #     Then The message "This field must not exceed " '<length>' " characters" is displayed

    #     Examples:
    #         | field          | length |
    #         | arm-name       | 200    |
    #         | arm-short-name | 20     |
    # | arm-randomisation-group | 20     |  Comments from Mikkel: This requirement is under disucssion, will be updated later.

    Scenario: User must not be able to use text longer than 20 characters for the Study Arm Arm Code field in the Study Arms form
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        When In the Study Arms form randomistaion group is provided
        And The study arm code is updated to exceed 20 characters
        Then The message 'This field must not exceed 20 characters' is displayed

    @manual_test
    Scenario: User must be presented with the warning message when deleting Study Arm
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        And The study arm related to study branch arm and study design cell exists
        When The delete button is clicked for the study arm related to those elements
        Then The warning message appears 'Removing this Study Arm will remove all related Study Cells and Branches'

    @manual_test
    Scenario: User must be able to delete all related items to Study Arm when Study arm is removed
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        And The study arm related to study branch arm and study design cell exists
        When The the study arm related to those elements is removed
        Then That study arm no longer exists
        And Related study design cells are deleted
        And Related study branch arms are deleted

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/study_structure/arms' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames