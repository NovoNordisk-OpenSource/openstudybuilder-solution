@REQ_ID:1074257
Feature: Studies - Study Attributes

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And A test study is selected

    Scenario: User must be able to navigate to the Study Interventions page
        Given The '/studies' page is opened
        When The 'Study Properties' submenu is clicked in the 'Define Study' section
        And The 'Study Attributes' tab is selected
        Then The current URL is '/studies/Study_000001/study_properties/attributes'

    Scenario: User must be able to see the page table with correct columns and options
        Given The '/studies/Study_000001/study_properties/attributes' page is opened
        Then A table is visible with following headers
            | headers                             |
            | Study intervention type information |
            | Selected values                     |
            | Reason for missing                  |
        
        And The following rows are available in first column
            | values                              |
            | Intervention type		              |
            | Study intent type		              |
            | Add-on to existing treatments       |
            | Control type		                  |
            | Intervention model		          |
            | Study is randomised		          |
            | Stratification factor		          |   
            | Study blinding schema		          |
            | Planned study length                |
    
    Scenario: User must be able to edit the Study Intervention Type
        Given The '/studies/Study_000001/study_properties/attributes' page is opened
        When The study intervention type is edited
        Then The study intervention type data is reflected in the table

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/study_properties/attributes' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/study_properties/attributes' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames