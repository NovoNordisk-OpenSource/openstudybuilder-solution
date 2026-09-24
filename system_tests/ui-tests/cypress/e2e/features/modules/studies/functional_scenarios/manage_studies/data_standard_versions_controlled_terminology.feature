@REQ_ID:2866939
@pending_development
Feature: Studies - Manage Studies - Data Standard Versions - Controlled Terminology

    Background: User must be logged in
        Given The user is logged in

    Scenario:  User must be able to navigate to the Study Data Standard Versions of Controlled Terminology page
        Given User selects study with id 'CDISC DEV-9876'
        Given The '/studies' page is opened
        When The 'Data Standard Versions' submenu is clicked in the 'Manage Study' section
        And The 'Controlled Terminology' tab is selected
        Then The current URL is '/data_standard_versions/controlled_terminology'

    Scenario: User must be able to see the Study Data Standard Versions of Controlled Terminology table with correct columns
        Given User selects study with id 'CDISC DEV-9876'
        Given The page 'data_standard_versions/controlled_terminology' is opened for current study
        And A table is visible with following headers
            | headers            |
            | CT catalogue       |
            | CDISC CT package   |
            | Sponsor CT package |
            | Description        |
            | Modified           |
            | Modified by        |

    Scenario: User must be able to use column selection option
        Given The page 'data_standard_versions/controlled_terminology' is opened for current study
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to add a Study Controlled Terminology Versions
        Given The page 'data_standard_versions/controlled_terminology' is opened for current study
        When A Controlled Terminology Version is added
        And Form save button is clicked
        Then The Controlled Terminology Version data is reflected in the table

    Scenario: User must be able to edit the Study Controlled Terminology Versions
        Given The page 'data_standard_versions/controlled_terminology' is opened for current study
        When The 'Edit' option is clicked from the three dot menu list
        When The Controlled Terminology Version is edited
        And Form save button is clicked
        Then The edited Controlled Terminology Version data is reflected in the table

    Scenario: User must be able to delete a Study Controlled Terminology Versions
        Given The page 'data_standard_versions/controlled_terminology' is opened for current study
        When The 'Delete' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        Then The Controlled Terminology Version data is removed from the table

    Scenario: User must be able to read change history of Study Controlled Terminology Versions
        Given The page 'data_standard_versions/controlled_terminology' is opened for current study
        When The user opens show version history
        Then The user is presented with version history of the output containing timestamp and username

    Scenario: User must be able to read change history of selected Study Controlled Terminology Version
        Given The page 'data_standard_versions/controlled_terminology' is opened for current study
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames