@REQ_ID:3459562
Feature: Study - Manage Study - Study Data Suppliers
    As a user, I want to manage the data suppliers in the Study

    Background:
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [Test data] User must be able to enabler feature flags and delete all existing data suppliers for given study
        Then [API] The feature flag 'study_data_suppliers' is enabled
        Then [API] The feature flag 'study_data_suppliers_create_from_study' is enabled
        And [API] All data suppliers are removed from selected study

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the List Study Data Supplier tab in the Study Data Suppliers page
        Given The '/studies' page is opened
        When The 'Study Data Suppliers' submenu is clicked in the 'Manage Study' section
        And The 'Overview' tab is selected
        Then The current URL is '/data-suppliers'

    Scenario: [Table][Columns][Names] User must be able to see the Study Data Supplier Overview table with correct columns
        Given The '/studies' page is opened
        When The 'Study Data Suppliers' submenu is clicked in the 'Manage Study' section
        And The 'List Study Data Supplier' tab is selected
        And A table is visible with following headers
            | headers                  |
            | #                        |
            | Study Data Supplier Type |
            | Data supplier name       |
            | Blinded                  |
            | Description              |
            | Library                  |
            | Origin Type              |
            | Origin Source            |
            | UI base URL              |
            | API base URL             |
            | Modified                 |
            | Modified by              |

    Scenario: [Create New][Positive case] User must be able to create a new data supplier in Study
        Given The page 'data-suppliers' is opened for current study
        And The 'Overview' tab is selected
        And User intercepts data supplier request
        When The pencil button is clicked
        Then The Edit Study Data Supplier page is opened
        And User waits for data supplier request
        And User initiate adding value for data supplier type 'EDC System'
        And User clicks ADD USER DEFINED DATA SUPPLIER button
        Then The Add User Defined Data Supplier form is opened
        When User fills in data supplier name
        And Form save button is clicked
        Then The form is no longer available
        When The Save button is clicked
        Then The newly added value should be visible for data supplier type 'EDC System'
        When The 'List Study Data Supplier' tab is selected
        And Data supplier is searched and found
        Then The newly added value should be displayed in the table with for data supplier type 'EDC System'

    Scenario: [Add Existing one][Positive case] User must be able to add one existing data supplier to the data supplier type
        Given The page 'data-suppliers' is opened for current study
        And The 'Overview' tab is selected
        And User intercepts data supplier request
        When The pencil button is clicked
        Then The Edit Study Data Supplier page is opened
        And User waits for data supplier request
        And User initiate adding value for data supplier type 'EDC System'
        And User saves data supplier value with index 0
        And User selects data supplier value from previous step
        When The Save button is clicked
        Then The newly added value should be visible for data supplier type 'EDC System'
        When The 'List Study Data Supplier' tab is selected
        And Data supplier is searched and found
        Then The newly added value should be displayed in the table with for data supplier type 'EDC System'
     
    Scenario: [Remove][Positive case] User must be able to remove the data supplier from data supplier type in study
        Given The page 'data-suppliers' is opened for current study
        And The 'Overview' tab is selected
        And User intercepts data supplier request
        When The pencil button is clicked
        Then The Edit Study Data Supplier page is opened
        And User waits for data supplier request
        And User saves first available value of data supplier type 'EDC System'
        When User clicks remove button for previously selected value for data supplier type 'EDC System'
        Then The value is removed from the data supplier type 'EDC System'
        When The Save button is clicked
        Then The value is removed from the overview for data supplier type 'EDC System'
        When The 'List Study Data Supplier' tab is selected
        Then User defined data supplier is searched and not found

      Scenario: [Add Existing multiple][Positive case] User must be able to add multiple existing data suppliers to the same data supplier type
        And [API] All data suppliers are removed from selected study
        Given The page 'data-suppliers' is opened for current study
        And The 'Overview' tab is selected
        And User intercepts data supplier request
        When The pencil button is clicked
        Then The Edit Study Data Supplier page is opened
        And User waits for data supplier request
        And User initiate adding value for data supplier type 'EDC System'
        And User saves data supplier value with index 0
        And User selects data supplier value from previous step
        And User defocus from field
        And User initiate adding value for data supplier type 'EDC System'
        And User saves data supplier value with index 1
        And User selects data supplier value from previous step
        When The Save button is clicked
        Then Both values are displayed on the overview page for data supplier type 'EDC System'
        When The 'List Study Data Supplier' tab is selected
        Then Both values are searched and correct data is displayed in the table for data supplier type 'EDC System'
        
    Scenario: [Add Existing][Positive case] User must be able to add same existing data supplier to the different data supplier type
        And [API] All data suppliers are removed from selected study
        Given The page 'data-suppliers' is opened for current study
        And The 'Overview' tab is selected
        And User intercepts data supplier request
        When The pencil button is clicked
        Then The Edit Study Data Supplier page is opened
        And User waits for data supplier request
        And User initiate adding value for data supplier type 'EDC System'
        And User finds one of the user defined values for data supplier
        Then User selects data supplier value from previous step
        And User initiate adding value for data supplier type 'Lab Data Exchange Files'
        And User finds one of the user defined values for data supplier
        Then User selects data supplier value from previous step
        When The Save button is clicked
        Then The newly added value should be visible for data supplier type 'EDC System'
        And The newly added value should be visible for data supplier type 'Lab Data Exchange Files'
        When The 'List Study Data Supplier' tab is selected
        And Data supplier is searched and found
        And The newly added value should be displayed in the table with for data supplier type 'EDC System'
        And Data supplier type 'Lab Data Exchange Files' is searched and found
        And The newly added value should be displayed in the table with for data supplier type 'Lab Data Exchange Files'
