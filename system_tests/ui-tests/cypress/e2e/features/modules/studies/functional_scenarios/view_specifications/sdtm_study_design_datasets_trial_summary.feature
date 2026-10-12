@REQ_ID:1074254
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
        Given The '/library/trial_summary_parameters' page is opened
        When The plus button is clicked
        And User selects first library for trial summary parameter
        And User fills trial summary parameter sponsor name with random, unique value
        And User fills trial summary parameter submission code value with random, unique value
        And User fills trial summary parameter submission name value with random, unique value
        And User selects 'Optional' as required level for trial summary parameter
        And User fills trial summary parameter order as '1'
        And User fills trial summary parameter defintion as 'E2E Trial Summary Parameter definition'
        And User selects 'other_study_attributes' as osb name for trial summary parameter
        And Form save button is clicked
        And The new Trial Summary Parameter is visible in the table
        And The 'View or edit details' option is clicked from the three dot menu list
        And The osb field name has value 'other_study_attributes'
        And User clicks approve term sponsor values
        And User clicks approve term attributes values
        Given The page 'study_properties/other_study_attributes' is opened for current study
        And User clicks add other study attributes button
        And The form is opened and visible
        And User selects created term as optional parameter
        And User selects null flavor as 'Asked but unknown'
        And User removes required other study attribute
        And Form save button is clicked
        And The page 'sdtm_study_design_datasets/tab-5' is opened for current study
        Then The table is visible and not empty
        And The new Trial Summary Parameter is visible in the table
