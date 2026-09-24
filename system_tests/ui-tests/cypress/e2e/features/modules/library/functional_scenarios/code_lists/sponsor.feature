@REQ_ID:1070680 @REQ_ID:1070679

Feature: Library - Code Lists - Sponsor
    As a user, I want to verify that the Code Lists - Sponsor page can be displayed correctly and new sponsor can be added to the Librayr successfully.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to the Sponsor page
        Given The '/library' page is opened
        When The 'Sponsor' submenu is clicked in the 'Code Lists' section
        Then The current URL is 'library/sponsor'

    Scenario: [Table][Options] User must be able to see table with correct options
        Given The '/library/sponsor' page is opened
        Then A table is visible with following options
            | options                                            |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
           # | search-with-terms                                               | to be implemented
           # | or-field                                                        | to be implemented

    Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
        Given The '/library/sponsor' page is opened
        And A table is visible with following headers
            | headers                     |
            | Library                     |
            | Sponsor preferred name      |
            | Template parameter          |
            | Code list status            |
            | Name modified               |
            | Concept ID                  |
            | Submission value            |
            | Code list name              |
            | NCI Preferred name          |
            | Extensible                  |
            | Attributes status           |
            | Attributes modified         |

    Scenario: [Table][Pagination] User must be able to use table pagination
        Given The '/library/sponsor' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    @smoke_test
	Scenario: [Create][Positive case] User must be able to add a new Codelist
		Given The '/library/sponsor' page is opened
        And User waits for the table
		When The new Codelist is added
        Given The '/library/sponsor' page is opened
        And The codelist is search for and found
        And The codelist and attributes status is set to 'Draft'

	Scenario: [Actions][Approve] User must be able to add a new Codelist
		Given The '/library/sponsor' page is opened
        And The codelist is search for and found
        When The 'Edit' option is clicked from the three dot menu list
        And The codelist sponsor values are approved
        And The sponsor values should be in status 'Final' and version '1.0'
        And The codelist attribute values are approved
        And The attribute values should be in status 'Final' and version '1.0'
        Given The '/library/sponsor' page is opened
        And The codelist is search for and found
        And The codelist and attributes status is set to 'Final'

    Scenario: [Actions][New version] User must be able to add a new Codelist
		Given The '/library/sponsor' page is opened
        And The codelist is search for and found
        When The 'Edit' option is clicked from the three dot menu list
        And The codelist sponsor values new version is created
        And The sponsor values should be in status 'Draft' and version '1.1'
        And The codelist attribute values new version is created
        And The attribute values should be in status 'Draft' and version '1.1'
        Given The '/library/sponsor' page is opened
        And The codelist is search for and found
        And The codelist and attributes status is set to 'Draft'

    Scenario: [Actions][Availability][Draft item] User must only have access to edit, show terms, history actions for Drafted version of the codelist
		Given The '/library/sponsor' page is opened
        And User waits for the table
		When The new Codelist is added
        Given The '/library/sponsor' page is opened
        And The codelist is search for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Codelist are displayed

     Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The '/library/sponsor' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                         |
        | Library                      |
        | Sponsor preferred name       |
        | Template parameter           |
        | Code list status             |
        | Concept ID                   |
        | Submission value             |
        | Code list name               |
        | NCI Preferred name           |
        | Extensible                   |
        | Attributes status            |

    @pending_development
    Scenario: [Table][Options] User must be able to see table with correct options 
        Given The '/library/sponsor' page is opened
        When The 'Show terms' option is clicked from the three dot menu list
        Then The 'Terms listing' page is shown
        Then A table is visible with following options
            | options                                            |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            
    @pending_development
    Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
        Given The '/library/sponsor' page is opened
        When The 'Show terms' option is clicked from the three dot menu list
        Then The 'Terms listing' page is shown
        And A table is visible with following headers
            | headers                     |
            | Order                       |
            | Submission value            |
            | Added date                  |
            | Removed date                |
            | Library                     |
            | Sponsor name                |
            | Name status                 |
            | Name date                   |
            | Concept ID                  |
            | NCI Preferred name          |
            | Definition                  |
            | Attributes status           |
            | Attributes date             |

    @pending_development
    Scenario: [Table][Pagination] User must be able to use table pagination
        Given The '/library/sponsor' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    @pending_development
    Scenario: User must be able to add existed terms to the selected sponsor
        Given The '/library/sponsor' page is opened
        When Click 'show terms' option from the three dot menu list for a selected sponsor
        Then The 'Code List Summary' page is opened
        When The user clicks on the 'Add term' button
        Then The Add term page is opened
        And The default selection is 'Select an existing one'
        When The user clicks on the 'CONTINUE' button
        Then The 'Select an existing term' page is opened
        When The user selects a term from the list
        And The user clicks on the 'CONTINUE' button
        Then The 'Enter term order and submission value' page is opened
        When The user fills in Submission value and Order fields
        And The user clicks on the 'SAVE' button
        Then The new added term is displayed in the table successfully

    @pending_development
    Scenario: User must give a unique submission value for the newly added term
        Given The '/library/sponsor' page is opened
        When Click 'show terms' option from the three dot menu list for a selected sponsor
        Then The 'Code List Summary' page is opened
        When The user clicks on the 'Add term' button
        Then The Add term page is opened
        And The default selection is 'Select an existing one'
        When The user clicks on the 'CONTINUE' button
        Then The 'Select an existing term' page is opened
        When The user selects a term from the list
        And The user clicks on the 'CONTINUE' button
        Then The 'Enter term order and submission value' page is opened
        When The user fills in the Submission value field with a value that already exists in the table
        Then An error message is displayed indicating that the submission value already exists

    @pending_development
     Scenario: User must be able to add new terms to the selected sponsor
        Given The '/library/sponsor' page is opened
        When Click 'show terms' option from the three dot menu list for a selected sponsor
        Then The 'Code List Summary' page is opened
        When The user clicks on the 'Add term' button
        Then The Add term page is opened
        When The user select 'Create a new one'
        When The user clicks on the 'CONTINUE' button
        Then The 'Manage sponsor term preferred name' page is opened
        When The user fills in the 'Sponsor preferred name' field
        And The user click on the 'Sponsor sentence case name' field
        Then The 'Sponsor sentence case name' field is filled automatically by the small letters of the 'Sponsor preferred name' field
        When The user clicks on the 'CONTINUE' button
        Then The 'Manage term attribute values' page is opened
        When The user fills in NCI preferred name and Definition fields
        And The user clicks on the 'CONTINUE' button
        Then The 'Enter term order and submission value' page is opened
        When The user fills in Submission value and Order fields
        And The user clicks on the 'SAVE' button
        Then The Term Detail page is opened
        And All the filled fields of Term are displayed correctly

    @pending_development
    Scenario: User must enter an integer value in the Order field for the newly added term
        Given The '/library/sponsor' page is opened
        When Click 'show terms' option from the three dot menu list for a selected sponsor
        Then The 'Code List Summary' page is opened
        When The user clicks on the 'Add term' button
        Then The Add term page is opened
        When The user select 'Create a new one'
        When The user clicks on the 'CONTINUE' button
        Then The 'Manage sponsor term preferred name' page is opened
        When The user fills in the 'Sponsor preferred name' field
        And The user click on the 'Sponsor sentence case name' field
        Then The 'Sponsor sentence case name' field is filled automatically by the small letters of the 'Sponsor preferred name' field
        When The user clicks on the 'CONTINUE' button
        Then The 'Manage term attribute values' page is opened
        When The user fills in NCI preferred name and Definition fields
        And The user clicks on the 'CONTINUE' button
        Then The 'Enter term order and submission value' page is opened
        When The user fills in correct Submission value
        And The user fills in the Order field with a non-integer value
        Then An error message is displayed indicating that the Order field must be an integer

    @pending_development
    Scenario: Verify all the mandatory fields are required when adding a new term to the sponsor
        Given The '/library/sponsor' page is opened
        When Click 'show terms' option from the three dot menu list for a selected sponsor
        Then The 'Code List Summary' page is opened
        When The user clicks on the 'Add term' button
        Then The Add term page is opened
        When The user select 'Create a new one'
        When The user clicks on the 'CONTINUE' button
        Then The 'Manage sponsor term preferred name' page is opened
        When The user clicks on the 'CONTINUE' button
        Then An error message is displayed indicating that the 'Sponsor preferred name' field is required
        When The user fills in the 'Sponsor preferred name' field
        And The user clicks on the 'CONTINUE' button
        Then The 'Manage term attribute values' page is opened
        When The user clicks on the 'CONTINUE' button
        Then An error message is displayed indicating that the 'NCI preferred name' field is required
        And An error message is displayed indicating that the 'Definition' field is required
        When The user fills in NCI preferred name and Definition fields
        And The user clicks on the 'CONTINUE' button
        Then The 'Enter term order and submission value' page is opened
        When The user fills in Submission value and Order fields
        When The user clicks on the 'SAVE' button
        Then The error message is displayed indicating that the 'Submission value' field is required
        And The error message is displayed indicating that the 'Order' field is required