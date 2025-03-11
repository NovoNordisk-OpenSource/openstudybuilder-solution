@REQ_ID:<new> @pending_implementation
Feature: Studies - Study Data Exchange Standard Versions

    Background: User must be logged in
        Given The user is logged in

    Scenario:  User must be able to navigate to the Study Data Standard Versions of Data Exchange Standards page
        Given A test study is selected
        Given The '/studies' page is opened
        When The 'Data Standard Versions' submenu is clicked in the 'Manage Study' section
        And The 'Data Exchange' tab is selected
        Then The current URL is '/studies/Study_000001/data_standard_versions/data_exchange'

    Scenario: User must be able to see the Study Data Standard Versions of Data Exchange Standards table with correct columns
        Given A test study is selected
        Given The '/studies/Study_000001/data_standard_versions/data_exchange' page is opened
        And A table is visible with following headers
            | headers                       |
            | Data model catalogue          |
            | Data model version            |
            | Data model IG version         |
            | Sponsor data model IG version |
            | Description                   |
            | Modified                      |
            | Modified by                   |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/study_data_standards/data_exchange_versions' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    @pending_implementation
    Scenario: User must be able to add a Study Data Exchange Standard Versions
        Given The '/studies/Study_000001/study_data_standards/data_exchange_versions' page is opened
        When A Data Exchange Standard Version is added
        Then The Data Exchange Standard Version data is reflected in the table
    @pending_implementation
    Scenario: User must be able to edit the Study Data Exchange Standard Versions
        Given The '/studies/Study_000001/study_data_standards/data_exchange_versions' page is opened
        When The Data Exchange Standard Version is edited
        Then The Data Exchange Standard Version data is reflected in the table
    @pending_implementation
    Scenario: User must be able to delete a Study Data Exchange Standard Versions
        Given The '/studies/Study_000001/study_data_standards/data_exchange_versions' page is opened
        When A Data Exchange Standard Version is deleted
        Then The Data Exchange Standard Version data is removed from the table
    @pending_implementation
    Scenario: User must be able to read change history of Study Data Exchange Standard Versions
        Given The '/studies/Study_000001/study_data_standards/data_exchange_versions' page is opened
        When The user opens show version history
        Then The user is presented with version history of the output containing timestamp and username
    @pending_implementation
    Scenario: User must be able to read change history of selected Study Data Exchange Standard Version
        Given The '/studies/Study_000001/study_data_standards/data_exchange_versions' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames