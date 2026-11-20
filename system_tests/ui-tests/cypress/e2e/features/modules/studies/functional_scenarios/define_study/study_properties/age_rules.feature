@REQ_ID:1074254
Feature: Studies - Define Study - Study Properties - Age Rules

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to Study Age Rules page using side menu
        And The '/studies' page is opened
        When The 'Study Properties' submenu is clicked in the 'Define Study' section
        And The 'Age Rules' tab is selected
        Then The current URL is '/study_properties/age_rules'

    Scenario: [Table][Columns][Names] User must be able to see the Study Age Rules table with following columns
        Given The page 'study_properties/age_rules' is opened for current study
        Then A table is visible with following headers
            | headers              |
            | Age rule information |
            | Selected values      |
        And The table display following predefined data
            | row | column               | value                |
            | 0   | Age rule information | Age at baseline rule |
            | 1   | Age rule information | Age group rule       |


    Scenario: [Table][Options] User must be able to see the Study Age Rules table with following options
        Given The page 'study_properties/age_rules' is opened for current study
        And A table is visible with following options
            | options      |
            | edit-content |
            | History      |

    Scenario: [Actions][Edit] User must be able to select Age rules for study
        Given [API] The selected study age rules are cleared
        Given The page 'study_properties/age_rules' is opened for current study
        When The 'edit-content' button is clicked
        And The user defines age rules
        And Form save button is clicked
        Then The table display following predefined data
            | row | column          | value                    |
            | 0   | Selected values | Age at Baseline Rule 2   |
            | 1   | Selected values | Age with 1 decimal digit |

    Scenario: [Actions][Edit] User must be able to clear Age rules for study
        Given [API] User gets rule code for Age At Baseline with name 'Age at Baseline Rule 3'
        Given [API] User gets rule code for Age Rule with name 'Age with 1 decimal digit' 
        Given [API] The age rules are defined for current study
        Given The page 'study_properties/age_rules' is opened for current study
        When The 'edit-content' button is clicked
        And The age rules are cleared
        And Form save button is clicked
        Then The table display following predefined data
            | row | column          | value |
            | 0   | Selected values |       |
            | 1   | Selected values |       |
