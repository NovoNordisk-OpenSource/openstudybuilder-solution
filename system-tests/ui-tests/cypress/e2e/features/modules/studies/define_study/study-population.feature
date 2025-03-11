@REQ_ID:1074255
Feature: Studies - Study Population

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: Opening the page
        Given The '/studies' page is opened
        When The 'Study Population' submenu is clicked in the 'Define Study' section
        Then The current URL is '/studies/Study_000001/population'

    Scenario: User must be able to see the page table with correct columns
        Given The '/studies/Study_000001/population' page is opened
        Then A table is visible with following headers
            | headers                      |
            | Study population information |
            | Selected values              |
            | Reason for missing           |
        And The following rows are available in first column
            | values                              |
            | Therapeutic area                    |
            | Study disease, condition or indicat |
            | Stable disease minimum duration     |
            | Healthy subject indicator           |
            | Diagnosis group                     |
            | Relapse criteria                    |
            | Total number of subjects            |
            | Rare disease indicator              |
            | Sex of study participants           |
            | Planned minimum age of study partic |
            | Planned maximum age of study partic |
            | Paediatric study indicator          |
            | Paediatric investigation plan indic |
            | Paediatric post-market study indica |

    Scenario: User must be able to edit the Study Population
        Given The '/studies/Study_000001/population' page is opened
        When The population is edited
        Then The population data is reflected in the table

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/population' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/population' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames
