@REQ_ID:2383812
Feature: Library - Admin Definitions - Data Suppliers
    As a user, I want to manage the data suppliers in the Concepts Library UI

    Background:
        Given The user is logged in
        And The '/library/data-suppliers' page is opened 

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the Data Suppliers page
        Given The '/library' page is opened
        When The 'Data Suppliers' submenu is clicked in the 'Admin Definitions' section
        Then The current URL is '/library/data-suppliers'

    Scenario: [Table][Options] User must be able to see table with correct options
        Then A table is visible with following options
            | options                                            |
            | add-data-supplier                                  |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |

    Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
        Then A table is visible with following headers
            | headers               |
            | Name                  |
            | Description           |
            | Order                 |
            | API base URL          |
            | UI base URL           |
            | Default Supplier Type |
            | Origin Source         |
            | Origin Type           |
            | Modified              |
            | Change description    |
            | Version               |
            | Status                |

    Scenario: [Create][Postive case] User must be able to create a new data supplier
        And User waits for the table
        When The 'add-data-supplier' button is clicked
        When The user defines data supplier name, type, description, order, api url, frontend url, origin source and origin type
        And Form save button is clicked
        And The data supplier is found
        Then The data supplier data is visible in the table
        Then The item has status 'Final' and version '1.0'

    Scenario: [Edit][Postive case]User must be able to edit the data supplier
        And User waits for the table
        And The data supplier is found
        And The 'Edit' option is clicked from the three dot menu list
        When The user edits data supplier name, type, description, order, api url, frontend url, origin source and origin type
        And Form save button is clicked
        Then The data supplier data is visible in the table
        Then The item has status 'Final' and version '2.0'

    Scenario: [Edit][State][Postive case] User must be able to inactivate and reactivate data supplier
        And User waits for the table
        And The data supplier is found
        And The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '2.0'
        And The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '2.0'

    Scenario: [Read][History] User must be able to check change history of data supplier
        And User waits for the table
        And The data supplier is found
        When The user intercepts version history request
        And The 'History' option is clicked from the three dot menu list
        When The changes history is presented to the user
