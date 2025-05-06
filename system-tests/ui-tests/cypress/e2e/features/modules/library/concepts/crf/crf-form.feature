@REQ_ID:1070683
Feature: Library - CRF Form

    As a user, I want to manage every CRFs Froms in the Library

    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to CRF Forms page
        Given The '/library' page is opened
        When The 'CRFs' submenu is clicked in the 'Concepts' section
        And The 'Forms' tab is selected
        Then The current URL is 'library/crfs/forms'

    Scenario: User must be able to see the page table with correct columns
        Given The 'library/crfs/forms' page is opened
        Then A table is visible with following headers
            | headers              |
            | OID                  |
            | Name                 |
            | Implementation Notes |
            | Repeating            |
            | Links                |
            | Version              |
            | Status               |
            
    Scenario: User must be able to select visibility of columns in the table 
        Given The '/library/crfs/forms' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to add a new CRF form
        Given The single language CRFs are enabled
        And The 'library/crfs/forms' page is opened
        When The 'add-crf-form' button is clicked
        And The Form definition container is filled with data and saved
        Then The newly added form is visible in the last row of the table

    Scenario: User must be able to update CRF form in draft status
        Given The single language CRFs are enabled
        And The 'library/crfs/forms' page is opened
        And The CRF Form in 'Draft' status exists
        When The 'Edit' action is clicked for the CRF Form
        And The Form metadata are updated and saved
        Then The edited CRF Form is visible within the table

    Scenario: User must be able to approve CRF form in draft status
        Given The 'library/crfs/forms' page is opened
        And The CRF Form in 'Draft' status exists
        When The 'Approve' action is clicked for the CRF Form
        Then The Form status is changed to 'Final' and version is rounded up to full number

    Scenario: User must be able to deactivate CRF form in final status
        Given The 'library/crfs/forms' page is opened
        And The CRF Form in 'Final' status exists
        When The 'Inactivate' action is clicked for the CRF Form
        Then The Form status is changed to 'Retired' and version is incremented by '0'

    Scenario: User must be able to reactivate CRF form in retired status
        Given The 'library/crfs/forms' page is opened
        Given The CRF Form in 'Retired' status exists
        When The 'Reactivate' action is clicked for the CRF Form
        Then The Form status is changed to 'Final' and version is incremented by '0'

    Scenario: User must be able to create new version of currently approved CRF form
        Given The 'library/crfs/forms' page is opened
        And The CRF Form in 'Final' status exists
        When The 'New version' action is clicked for the CRF Form
        Then The Form status is changed to 'Draft' and version is incremented by '0.1'

    Scenario: User must be able to delete CRF Form in draft status
        Given The 'library/crfs/forms' page is opened
        And The CRF Form in draft status with sub 1 version exists
        When The 'Delete' option is clicked from the three dot menu list
        Then The CRF Form is no longer available

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The '/library/crfs/forms' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames