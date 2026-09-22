@REQ_ID:TBD
Feature: Studies - View Specifications - SDTM Study Design Datasets - Trial Summary

    Background: User must be logged in
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the SDTM Study Design Datasets Trial Summary tab
        Given The '/studies' page is opened
        When The 'SDTM Study Design Datasets' submenu is clicked in the 'View Specifications' section
        And The 'Trial Summary' tab is selected
        Then The current URL is '/sdtm_study_design_datasets/tab-5'

    Scenario: [Table][Columns][Names] User must be able to see Trial Summary table columns
        Given The page 'sdtm_study_design_datasets/tab-5' is opened for current study
        Then A table is visible with following headers
            | headers                            |
            | Study Identifier                   |
            | Domain Abbreviation                |
            | Sequence Number                    |
            | Group ID                           |
            | Trial Summary Parameter Short Name |
            | Trial Summary Parameter            |
            | Parameter Value                    |
            | Parameter Null Flavor              |
            | Parameter Value Code               |
            | Name of the Reference Terminology   |
            | Version of the Reference Terminology|

    Scenario: [Table][Options] User must be able to see table options for Trial Summary
        Given The page 'sdtm_study_design_datasets/tab-5' is opened for current study
        Then A table is visible with following options
            | options             |
            | search-field        |
            | table-export-button |

    Scenario: [Table][Data][Visibility] User must be able to see Trial Summary Parameters data for the study
        Given A Trial Summary Parameter mapped to Other Study Attributes is created through the UI
        And The page 'sdtm_study_design_datasets/tab-5' is opened for current study
        Then The table is visible and not empty
        And The created Trial Summary Parameter is visible in the table
