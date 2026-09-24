@REQ_ID:1070683
Feature: Library - Data Collection Standards - CRF Builder - CRF Collections

    As a user, I want to build and manage every CRFs Collection in the library for data collection standards

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to CRF Collections page
        Given The '/library' page is opened
        When The 'CRF Builder' submenu is clicked in the 'Data Collection Standards' section
        And The 'CRF Collections' tab is selected
        Then The current URL is '/library/crf-builder/collections'

    Scenario: [Table][Columns][Names] User must be able to see the data of the CRF Collections tab
        Given The '/library/crf-builder/collections' page is opened
        Then A table is visible with following headers
            | headers   |
            | OID       |
            | Name      |
            | Effective |
            | Obsolete  |
            | Version   |
            | Status    |

    Scenario: [Table][Options] User must be able to see table with correct options
        Given The '/library/crf-builder/collections' page is opened
        Then A table is visible with following options
            | options                                            |
            | add-crf-collection                                 |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | search-field                                       |

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table 
        Given The '/library/crf-builder/collections' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Create][Positive case] User must be able to add a new CRF Collection
        Given The '/library/crf-builder/collections' page is opened
        When The 'add-crf-collection' button is clicked
        And The CRF Collection definition container is filled with data
        And Form save button is clicked
		And The form is no longer available
        Then The pop up displays 'Collection created'
        And Created CRF Collection is found
        Then The CRF Collection is visible in the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Create][Mandatory fields] User must not be able to create CRF Collection without Name provided
        Given The '/library/crf-builder/collections' page is opened
        When The 'add-crf-collection' button is clicked
        And Form save button is clicked
        Then The validation appears for the CRF Collection Name field

    Scenario: [Actions][Edit][version 0.1] User must be able to update CRF Collection in draft status
        Given The '/library/crf-builder/collections' page is opened
        And Created CRF Collection is found
        When The 'Edit' option is clicked from the three dot menu list
        And The CRF Collection metadata are updated
        And Form save button is clicked
		And The form is no longer available
        Then The pop up displays 'Collection updated'
        Then The CRF Collection is visible in the table
        And The item has status 'Draft' and version '0.2'

    Scenario: [Actions][Approve] User must be able to approve CRF Collection in draft status
        Given The '/library/crf-builder/collections' page is opened
        And Created CRF Collection is found
        When The 'Approve' option is clicked from the three dot menu list
        Then The approval popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Inactivate] User must be able to deactivate CRF Collection in final status
        Given The '/library/crf-builder/collections' page is opened
        And Created CRF Collection is found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '2.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate CRF Collection in retired status
        Given The '/library/crf-builder/collections' page is opened
        And Created CRF Collection is found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '3.0'

    Scenario: [Actions][New version] User must be able to create new version of currently approved CRF Collection
        Given The '/library/crf-builder/collections' page is opened
        And Created CRF Collection is found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '3.1'

    Scenario: [Actions][Delete] User must be able to delete CRF Collection in draft status
        And [API] The CRF Collection in draft status exists
        Given The '/library/crf-builder/collections' page is opened
        And Created CRF Collection is found
        When The 'Delete' option is clicked from the three dot menu list
        Then The CRF Collection is no longer available

    @manual_test   
    Scenario: User must be able to read change history of all element
        Given The '/library/crf-builder/collections' page is opened
        When The 'Show history' option is clicked from the three dot menu list
        Then The user is presented with history of changes for all element
        And The history contains timestamps and usernames

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The '/library/crf-builder/collections' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames