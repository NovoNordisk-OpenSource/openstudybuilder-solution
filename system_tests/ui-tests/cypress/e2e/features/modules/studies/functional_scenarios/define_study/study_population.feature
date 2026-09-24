@REQ_ID:1074255
Feature: Studies - Define Study - Study Population

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    @smoke_test
    Scenario: [Navigation] Opening the page
        Given The '/studies' page is opened
        When The 'Study Population' submenu is clicked in the 'Define Study' section
        Then The current URL is '/population'

    Scenario: [Table][Columns][Names][Data] User must be able to see the page table with correct columns
        Given The page 'population' is opened for current study
        Then A table is visible with following headers
            | headers                      |
            | Study population information |
            | Selected values              |
            | Reason for missing           |
        And The table display following predefined data
            | row | column                        | value                               |
            | 0   | Study population information  | Therapeutic area                    |
            | 1   | Study population information  | Study disease, condition or indicat |
            | 2   | Study population information  | Stable disease minimum duration     |
            | 3   | Study population information  | Healthy subject indicator           |
            | 4   | Study population information  | Diagnosis group                     |
            | 5   | Study population information  | Relapse criteria                    |
            | 6   | Study population information  | Total number of subjects            |
            | 7   | Study population information  | Rare disease indicator              |
            | 8   | Study population information  | Sex of study participants           |
            | 9   | Study population information  | Planned minimum age of study partic |
            | 10  | Study population information  | Planned maximum age of study partic |
            | 11  | Study population information  | Paediatric study indicator          |
            | 12  | Study population information  | Paediatric investigation plan indic |
            | 13  | Study population information  | Paediatric post-market study indica |

    Scenario: [Actions][Edit] User must be able to edit the Study Population
        Given The page 'population' is opened for current study
        When The edit content button is clicked
        When The population is edited
        And Form save button is clicked
        And The form is no longer available
        Then The population data is reflected in the table

    @manual_test
    Scenario: User must be able to read change history of output
        Given The page 'population' is opened for current study
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The page 'population' is opened for current study
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames
