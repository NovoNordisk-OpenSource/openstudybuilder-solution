@REQ_ID:1070679
Feature: Library - Code Lists - Trial Summary Parameters - UI Structure

    As a user, I want to verify that the Trial Summary Parameters visibility elements are displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Table][Options] User must be able to see table with correct options
        Given The '/library/trial_summary_parameters' page is opened
        Then A table is visible with following options
            | options               |
            | search-field          |
            | filters-button        |
            | columns-layout-button |
            | table-export-button   |

    Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
        Given The '/library/trial_summary_parameters' page is opened
        And A table is visible with following headers
            | headers                |
            | Library                |
            | Sponsor name           |
            | NCI preferred term     |
            | Code subm value        |
            | Concept ID             |
            | Definition             |
            | Required level         |
            | Semantic data type     |
            | Response code list     |
            | Cardinality            |
            | Valid null flavor      |
            | Notes                  |
            | OSB page reference     |
            | OSB field name         |
            | Name status            |
            | Name modified by       |
            | Name date              |
            | Attributes status      |
            | Attributes modified by |
            | Attributes date        |

    Scenario: [Actions][Availability] User must be able to see available actions for a Trial Summary Parameter row
        Given The '/library/trial_summary_parameters' page is opened
        When The item actions button is clicked
        Then The following actions are available
            | actions              |
            | View or edit details |
            | Open CT history      |
            | Open sponsor history |

    Scenario: [Overview][Header][Visibility] User must be able to see the header information on the overview page
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        Then The page header shows the CT term name with 'Library' and 'Concept ID'

    Scenario: [Overview][Term sponsor values][Visibility] User must be able to see the Term sponsor values section fields
        Given The Trial Summary Parameter details page is opened
        Then The 'Term sponsor values' section is visible with the following fields
            | field              |
            | Sponsor name       |
            | Sentence case name |
            | OSB field name     |
            | OSB page reference |
            | Response code list |
            | Required level     |
            | Cardinality        |
            | Status             |
            | Version            |
            | Modified by        |
            | Modified           |

    Scenario: [Overview][Term attributes values][Visibility] User must be able to see the Term attributes values section fields
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        Then The 'term-attributes' section is visible with the following fields
            | field              |
            | Concept ID         |
            | NCI preferred name |
            | Definition         |
            | Status             |
            | Version            |
            | Modified by        |
            | Modified           |

    Scenario: [Overview][CT codelists context][Visibility] User must be able to see the CT term codelists context section
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        Then The codelist context table is visible

    Scenario: [Overview][CT codelists context][Table][Columns][Names] User must be able to see the CT term codelists context table columns
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        Then The 'codelists-context-table' table is visible with the following headers
            | headers                   |
            | Term library              |
            | Codelist name             |
            | Codelist concept ID       |
            | Codelist submission value |
            | Submission value          |
            | Order                     |
            | Modified                  |

    Scenario: [Overview][CT codelists context][Table][Options] User must be able to see the CT term codelists context table options
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        Then The codelist context table is visible
