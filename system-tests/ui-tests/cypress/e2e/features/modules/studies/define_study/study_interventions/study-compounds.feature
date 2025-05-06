@REQ_ID:1074257
@pending_development
Feature: Studies - Study Compounds

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: User must be able to navigate to the Studies Design page
        Given The '/studies' page is opened
        When The 'Study Interventions' submenu is clicked in the 'Define Study' section
        And The 'Study Compounds' tab is selected
        Then The current URL is '/studies/Study_000001/study_interventions/study_compounds'

    Scenario: User must be able to see the page table with correct columns
        Given The '/studies/Study_000001/study_interventions/study_compounds' page is opened
        Then A table is visible with following headers
            | headers                        |
            | #                              |
            | Type of treatment              |
            | Reason For Missing             |
            | Compound                       |
            | Sponsor Compound               |
            | Is INN                         |
            | Substance (UNII)               |
            | Pharmacological Class (MED-RT) |
            | Compound Alias                 |
            | Preferred Alias                |
            | Strength                       |
            | Pharmaceutical Dosage form     |
            | Route of administration        |
            | Dispensed in                   |
            | Delivery Device                |
            | Half-life                      |
            | Lag-time                       |
            | Compound Number (long)         |
            | Compound Number (short)        |
            | Analyte Number                 |
            | Compound Definition            |
            | Alias Definition               |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/study_interventions/study_compounds' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    Scenario: User must be able to add a complete Study Compound
        Given The '/studies/Study_000001/study_interventions/study_compounds' page is opened
        When The study compound is added
        Then The study compound is available in the table

    Scenario: User must be able to edit the Study Compound
        Given The study compound is available in the test study
        And The '/studies/Study_000001/study_interventions/study_compounds' page is opened
        When The study compound is edited
        Then The updated study compound is available in the table

    Scenario: User must be able to delete the Study Compound
        Given The study compound is available in the test study
        And The '/studies/Study_000001/study_interventions/study_compounds' page is opened
        When The study compound is deleted
        Then The study compound is no longer available