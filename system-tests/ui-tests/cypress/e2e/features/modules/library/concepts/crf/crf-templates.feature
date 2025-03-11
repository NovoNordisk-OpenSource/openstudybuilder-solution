@REQ_ID:1070683
Feature: Library - CRF Templates

    As a user, I want to manage every CRFs Template in the Library

    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to CRF Templates page
        Given The '/library' page is opened
        When The 'CRFs' submenu is clicked in the 'Concepts' section
        And The 'CRF Templates' tab is selected
        Then The current URL is 'library/crfs/templates'

    Scenario: User must be able to see the data of the CRF Templates tab
        Given The 'library/crfs/templates' page is opened
        Then A table is visible with following headers
            | headers   |
            | OID       |
            | Name      |
            | Effective |
            | Obsolete  |
            | Version   |
            | Status    |
            
    Scenario: User must be able to select visibility of columns in the table 
        Given The '/library/crfs/templates' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to add a new CRF Template
        Given The single language CRFs are enabled
        And The 'library/crfs/templates' page is opened
        When The 'add-crf-template' button is clicked
        And The CRF Template definition container is filled with data and saved
        Then The newly added CRF Template is visible in the last row of the table

    Scenario: User must not be able to create CRF Template without Name provided
        Given The single language CRFs are enabled
        And The 'library/crfs/templates' page is opened
        When The 'add-crf-template' button is clicked
        And The CRF Template definition container is filled without name provided
        And The 'save-button' button is clicked
        Then The validation appears for the CRF Template Name field

    Scenario: User must be able to update CRF Template in draft status
        Given The single language CRFs are enabled
        And The 'library/crfs/templates' page is opened
        And The CRF Template in 'Draft' status exists
        When The 'Edit' action is clicked for the CRF Template
        And The CRF Template metadata are updated and saved
        Then The edited CRF Template is visible within the table

    Scenario: User must be able to approve CRF Template in draft status
        Given The 'library/crfs/templates' page is opened
        And The CRF Template in 'Draft' status exists
        When The 'Approve' action is clicked for the CRF Template
        Then The CRF Template status is changed to 'Final' and version is rounded up to full number

    Scenario: User must be able to deactivate CRF Template in final status
        Given The 'library/crfs/templates' page is opened
        And The CRF Template in 'Final' status exists
        When The 'Inactivate' action is clicked for the CRF Template
        Then The CRF Template status is changed to 'Retired' and version is incremented by '0'

    Scenario: User must be able to reactivate CRF Template in retired status
        Given The 'library/crfs/templates' page is opened
        And The CRF Template in 'Retired' status exists
        When The 'Reactivate' action is clicked for the CRF Template
        Then The CRF Template status is changed to 'Final' and version is incremented by '0'

    Scenario: User must be able to create new version of currently approved CRF Template
        Given The 'library/crfs/templates' page is opened
        And The CRF Template in 'Final' status exists
        When The 'New version' action is clicked for the CRF Template
        Then The CRF Template status is changed to 'Draft' and version is incremented by '0.1'

    Scenario: User must be able to delete CRF Template in draft status
        Given The 'library/crfs/templates' page is opened
        And The CRF Template in draft status with sub 1 version exists
        When The 'Delete' action is clicked for the CRF Template
        Then The CRF Template is no longer available

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The 'library/crfs/templates' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames