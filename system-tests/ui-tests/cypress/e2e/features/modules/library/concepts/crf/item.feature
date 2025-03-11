@REQ_ID:1070683
Feature: Library - CRF Items

    As a user, I want to manage every CRF Item in the Library

    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to the CRF Items page
        Given The '/library' page is opened
        When The 'CRFs' submenu is clicked in the 'Concepts' section
        And The 'Items' tab is selected
        Then The current URL is '/library/crfs/items'

    Scenario: User must be able to see the data of the CRF Items tab
        Given The 'library/crfs/items' page is opened
        Then A table is visible with following headers
            | headers              |
            | OID                  |
            | Name                 |
            | Description          |
            | Implementation Notes |
            | Type                 |
            | Length               |
            | SDS Var Name         |
            | Links                |
            | Version              |
            | Status               |
            
    Scenario: User must be able to select visibility of columns in the table 
        Given The '/library/crfs/items' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to add an Item
        Given The single language CRFs are enabled
        And The 'library/crfs/items' page is opened
        When The 'add-crf-item' button is clicked
        And The CRF Item definition container is filled with data and saved
        Then The newly added CRF Item is visible in the last row of the table

    Scenario: User must be able to update an existing Item
        Given The single language CRFs are enabled
        And The 'library/crfs/items' page is opened
        And The CRF Item in 'Draft' status exists
        When The 'Edit' action is clicked for the CRF Item
        And The CRF Item metadata are updated and saved
        Then The edited CRF Item is visible within the table

    Scenario: User must be able to approve an Item in draft status
        Given The 'library/crfs/items' page is opened
        And The CRF Item in 'Draft' status exists
        When The 'Approve' action is clicked for the CRF Item
        Then The CRF Item status is changed to 'Final' and version is rounded up to full number

    Scenario: User must be able to inactivate currently active Item
        Given The 'library/crfs/items' page is opened
        And The CRF Item in 'Final' status exists
        When The 'Inactivate' action is clicked for the CRF Item
        Then The CRF Item status is changed to 'Retired' and version is incremented by '0'

    Scenario: User must be able to reactivate currently retired Item
        Given The 'library/crfs/items' page is opened
        And The CRF Item in 'Retired' status exists
        When The 'Reactivate' action is clicked for the CRF Item
        Then The CRF Item status is changed to 'Final' and version is incremented by '0'

    Scenario: User must be able to create a new version of an Item
        Given The 'library/crfs/items' page is opened
        And The CRF Item in 'Final' status exists
        When The 'New version' action is clicked for the CRF Item
        Then The CRF Item status is changed to 'Draft' and version is incremented by '0.1'

    Scenario: User must be able to delete CRF Item in draft status
        Given The 'library/crfs/items' page is opened
        And The CRF Item in draft status with sub 1 version exists
        When The 'Delete' action is clicked for the CRF Item
        Then The CRF Item is no longer available

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The '/library/crfs/items' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames