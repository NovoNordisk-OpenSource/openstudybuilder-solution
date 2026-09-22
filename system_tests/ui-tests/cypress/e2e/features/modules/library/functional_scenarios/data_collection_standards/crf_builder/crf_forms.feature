@REQ_ID:1070683
Feature: Library - Data Collection Standards - CRF Builder - Forms

    As a user, I want to build and manage data collection forms in the library for data collection standards

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to CRF Builder Forms page
        Given The '/library' page is opened
        When The 'CRF Builder' submenu is clicked in the 'Data Collection Standards' section
        And The 'Forms' tab is selected
        Then The current URL is 'library/crf-builder/forms'

    Scenario: [Table][Columns][Names] User must be able to see the page table with correct columns
        Given The '/library/crf-builder/forms' page is opened
        Then A table is visible with following headers
            | headers              |
            | OID                  |
            | Name                 |
            | Repeating            |
            | Version              |
            | Status               |

    Scenario: [Table][Options] User must be able to see table with correct options
        Given The '/library/crf-builder/forms' page is opened
        Then A table is visible with following options
            | options                                            |
            | add-crf-form                                       |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | search-field                                       |

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table 
        Given The '/library/crf-builder/forms' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Create][Positive case] User must be able to add a new CRF form
        Given The '/library/crf-builder/forms' page is opened
        When The 'add-crf-form' button is clicked
        And The Form definition container is filled with data
        And Form continue button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        And Form save button is clicked
        Then The pop up displays 'Form created'
        And Created CRF form is found

    Scenario: [Actions][Edit][version 0.1] User must be able to update CRF form in draft status
        Given The '/library/crf-builder/forms' page is opened
        And Created CRF form is found
        When The 'Edit' option is clicked from the three dot menu list
        And The Form metadata are updated and saved
        And User goes to Change description step
        And Form save button is clicked
        Then The pop up displays 'Form updated'
        And Created CRF form is found

    Scenario: [Actions][Approve] User must be able to approve CRF form in draft status
        Given The '/library/crf-builder/forms' page is opened
        And Created CRF form is found
        When The 'Approve' option is clicked from the three dot menu list
        Then The approval popup window is displayed
        When Action is confirmed by clicking continue
        And The item has status 'Final' and version '1.0'

    Scenario: [Actions][Inactivate] User must be able to deactivate CRF form in final status
        Given The '/library/crf-builder/forms' page is opened
        And Created CRF form is found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '2.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate CRF form in retired status
        Given The '/library/crf-builder/forms' page is opened
        And Created CRF form is found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '3.0'

    Scenario: [Actions][Edit][version 3.0] User must be able to create new version of currently approved CRF form
        Given The '/library/crf-builder/forms' page is opened
        And Created CRF form is found
        When The 'New version' option is clicked from the three dot menu list
        Then The New version popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Draft' and version '3.1'

    Scenario: [Actions][Delete] User must be able to delete CRF Form in draft status
        Given The '/library/crf-builder/forms' page is opened
        When The 'add-crf-form' button is clicked
        And The Form definition container is filled with data
        And Form continue button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        And Form save button is clicked
        Then Created CRF form is found
        When The 'Delete' option is clicked from the three dot menu list 
        Then The CRF Form is no longer available

    @manual_test  
    Scenario: User must be able to read change history for all element
        Given The '/library/crf-builder/forms' page is opened
        When The 'Show history' option is clicked from the three dot menu list
        Then The user is presented with history of changes for all elements
        And The history contains timestamps and usernames

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The '/library/crf-builder/forms' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames


### Next scenarios support the linking to and from a CRF Form

    @pending_development
    Scenario: [Actions][Browse] User must be able to browse CRF Forms and see related CRF Collections, CRF Item Groups, CRF Items and studies using the CRF Form
        Given The '/library/crf-builder/forms' page is opened
        ### We have multiple options here for how the UI could work, so two options below - to be clarified during UI/UX design
        When The 'Links' option is clicked from the three dot menu list
        When The linked item is clicked in the 'Links' column
        ### We have multiple ways of displaying the related items - to be clarified during UI/UX design
        Then The user is presented with overview of related CRF Collections, CRF Item Groups, CRF Items and studies using the CRF Form