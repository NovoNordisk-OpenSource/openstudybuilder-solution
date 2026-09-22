@REQ_ID:1070683
Feature: Library - Data Collection Standards - CRF Builder - Items

    As a user, I want to build and manage every CRF Item in the library for data collection standards

    Background: User must be logged in
        Given The user is logged in
        And The homepage is opened

    Scenario: [Navigation] User must be able to navigate to the CRF Items page
        Given The '/library' page is opened
        When The 'CRF Builder' submenu is clicked in the 'Data Collection Standards' section
        And The 'Items' tab is selected
        Then The current URL is '/library/crf-builder/items'

    Scenario: [Table][Columns][Names] User must be able to see the data of the CRF Items tab
        Given The '/library/crf-builder/items' page is opened
        Then A table is visible with following headers
            | headers              |
            | OID                  |
            | Name                 |
            | Type                 |
            | Length               |
            | SDS Var Name         |
            | Version              |
            | Status               |

    Scenario: [Table][Options] User must be able to see table with correct options
        Given The '/library/crf-builder/items' page is opened
        Then A table is visible with following options
            | options                                            |
            | add-crf-item                                       |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | search-field                                       |

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table 
        Given The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And User waits for the table
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Create][Positive case]User must be able to add an Item
        Given The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        When The 'add-crf-item' button is clicked
        And The CRF Item name is set
        And The CRF Item oid is set
        And The CRF Item datatype is set as 'integer'
        And Form continue button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        And Form save button is clicked
        And User waits for the table
        And Created CRF Item is found
        Then The CRF Item is visible in the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Actions][Edit][version 0.1] User must be able to update an existing Item
        Given The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And Created CRF Item is found
        When The 'Edit' option is clicked from the three dot menu list
        And The CRF Item datatype is set as 'integer'
        And The CRF Item name is updated
        And The CRF Item oid is updated
        And User goes to Change description step
        And Form save button is clicked
        And User waits for the table
        Then The CRF Item is visible in the table
        And The item has status 'Draft' and version '0.2'

    Scenario: [Actions][Approve] User must be able to approve an Item in draft status
        Given The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And User waits for the table
        And Created CRF Item is found
        When The 'Approve' option is clicked from the three dot menu list
        And The item has status 'Final' and version '1.0'

    Scenario: [Actions][Inactivate] User must be able to inactivate currently active Item
        Given The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And User waits for the table
        And Created CRF Item is found
        When The 'Inactivate' option is clicked from the three dot menu list
        And The item has status 'Retired' and version '2.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate currently retired Item
        Given The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And User waits for the table
        And Created CRF Item is found
        When The 'Reactivate' option is clicked from the three dot menu list
        And The item has status 'Final' and version '3.0'

    Scenario: [Actions][New version] User must be able to create a new version of an Item
        Given The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And User waits for the table
        And Created CRF Item is found
        When The 'New version' option is clicked from the three dot menu list
        Then The New version popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Draft' and version '3.1'

    Scenario: [Actions][Delete] User must be able to delete CRF Item in draft status
        And [API] CRF Item is created
        Given The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And User waits for the table
        And The CRF Item created via API is searched and found
        When The 'Delete' option is clicked from the three dot menu list
        Then The CRF Item created via API is searched and not found

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And Created CRF Item is found
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames