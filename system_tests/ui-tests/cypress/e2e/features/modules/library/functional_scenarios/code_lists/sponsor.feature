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

    Scenario: [Table][Pagination] User must be able to use table pagination
        Given The '/library/sponsor' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    @pending_development
    Scenario: [Add term][Existing] User must be able to add existed terms to the selected sponsor

    @pending_development
    Scenario: [Add term][New] User must be able to add new terms to the selected sponsor

    @pending_development
    Scenario: [Add term][New][Fields validation] User must give an unique submission value of new term

    @pending_development
    Scenario: [Add term][New][Fields validation] User must give an integer value for order of new term
