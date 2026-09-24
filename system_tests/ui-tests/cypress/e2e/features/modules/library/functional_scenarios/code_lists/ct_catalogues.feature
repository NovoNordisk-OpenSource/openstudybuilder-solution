@REQ_ID:1070674

Feature: Library - Code Lists - CT Catalogues

	Background: User must be logged in
		Given The user is logged in

	@smoke_test
	Scenario: [Navigation] User must be able to navigate to the CT Catalogues page and see it's content
		Given The '/library' page is opened
		When The 'CT Catalogues' submenu is clicked in the 'Code Lists' section
		And CT data is loaded
		Then The current URL is '/library/ct_catalogues/All'
		And The 'CT Catalogues' title is visible
		And The following tabs are visible
			| tabs 			|
			| All			|
			| ADAM CT       |
			| SEND CT		|
		And The table is loaded
		And The table is visible and not empty

	Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table 
        Given The '/library/ct_catalogues/All' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Pagination] User must be able to use table pagination
        Given The '/library/ct_catalogues/All' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

	Scenario: [Overview] User must be able to open terms for Codelists in CT Catalogue
		Given The '/library/ct_catalogues/All' page is opened
		When The 'SEND CT' tab is selected
		And The id of the first term on the list is saved
		And The 'Show terms' option is clicked from the three dot menu list
		Then The user is redirected to the term page

	Scenario: [Create][New Term] User must be able to add a new term to the Codelist
		Given The '/library/ct_catalogues/All/CTCodelist_000010/terms' page is opened
		When The new term is added
		Then The term page is opened and showing correct data

	Scenario: [Overview][New Term] User must be able to add a new term to the Codelist
		Given The '/library/ct_catalogues/All/CTCodelist_000010/terms' page is opened
		When The term is search for and found
		And User waits for the table
		Then The term data is visible in the table

	Scenario: [Overview] User must be able to see the Codelist Summary for Codelist
		Given The '/library/ct_catalogues/SEND CT/C66729/terms' page is opened
		When The codelist summary is expanded
		Then The codelist summary show following data
			| name               | value                                                                                                                                |
			| Concept ID         | C66729                                                                                                                               |
			| Name               | Route of Administration Response                                                                                                     |
			| Label              | Route of Administration                                                                                                              |
			| Definition	     | A terminology codelist relevant to the pathway by which a substance is administered in order to reach the site of action in the body.|
			| Library            | CDISC                                                                                                                                |
			| Template parameter | No                                                                                                                                   |
			| Extensible         | Yes                                                                                                                                  |
		And Add term button is visible in actions menu

    @smoke_test
	Scenario: [Create][Positive case] User must be able to add a new Codelist
		Given The '/library/ct_catalogues/All' page is opened
		When The new Codelist is added
		Then The new Codelist page is opened and showing correct data
		And The sponsor values should be in status 'Draft' and version '0.1'
		And The attribute values should be in status 'Draft' and version '0.1'

	Scenario: [Actions][Edit] User must be able to edit an existing Codelist
		Given The test Codelist for editing is opened
		When The Codelist sponsor values are edited
		And Form save button is clicked
		And The form is no longer available
		And The Codelist sponsor values are validated
		Then The edited codelist page is showing correct data
		And The sponsor values should be in status 'Final' and version '1.0'
		And The Edit sponsor values button is not visible
		But The Create new sponsor values version button is visible
		And The version history contain the changes of edited Codelist

	@unstable_disabled
	Scenario: [Create][Existing Term] User must be able to add an existing term to the Codelist
		Given The test term in test Codelist is opened
		And The '/library/ct_catalogues/All/C117744/terms' page is opened
		When The existing term is added
		Then The pop up displays 'Term added'

	Scenario: [Actions][Edit][Term] User must be able to edit a term in Codelist
		Given The test term in test Codelist is opened
		When The term sponsor values are edited
		And Form save button is clicked
		And The form is no longer available
		And The term is validated
		Then The edited term page is showing correct data
		And The sponsor values should be in status 'Final' and version '1.0'
		And The Edit sponsor values button is not visible
		But The Create new sponsor values version button is visible

	@pending_implementation
	Scenario: [Actions][Create][Catalogue][Optional fields] User must be able to create codelist without NCI preferred name

	@pending_implementation
	Scenario: [Actions][Create][Catalogue][Optional fields] User must be able to create codelist with Template parameter set to true

	@pending_implementation
	Scenario: [Actions][Create][Catalogue][Optional fields] User must be able to create codelist with Extensible and Ordinal set to true

	@pending_implementation
	Scenario: [Actions][Create][Catalogue][Mandatory fields] User must not be able to create codelist without Codelist name, Submission value and Definition

	@pending_implementation
	Scenario: [Actions][Create][Catalogue][Mandatory fields] User must not be able to create codelist without Sponsor preferred name

	@pending_implementation
	Scenario: [Actions][Create][Catalogue][Mandatory fields] User must not be able to create codelist without Catalogue name 

	Scenario: [Actions][Approve][Catalogue] User must be able to apporve a codelist
		Given The '/library/ct_catalogues/All' page is opened
		When The new Codelist is added
		Given The '/library/ct_catalogues/All' page is opened
        And The codelist is search for and found
        When The 'Edit' option is clicked from the three dot menu list
        And The codelist sponsor values are approved
        And The sponsor values should be in status 'Final' and version '1.0'
        And The codelist attribute values are approved
        And The attribute values should be in status 'Final' and version '1.0'
        Given The '/library/ct_catalogues/All' page is opened
        And The codelist is search for and found
        And The codelist and attributes status is set to 'Final'

	Scenario: [Actions][New version][Catalogue] User must be able to apporve a codelist
		Given The '/library/ct_catalogues/All' page is opened
        And The codelist is search for and found
        When The 'Edit' option is clicked from the three dot menu list
        And The codelist sponsor values new version is created
        And The sponsor values should be in status 'Draft' and version '1.1'
        And The codelist attribute values new version is created
        And The attribute values should be in status 'Draft' and version '1.1'
        Given The '/library/ct_catalogues/All' page is opened
        And The codelist is search for and found
        And The codelist and attributes status is set to 'Draft'

	Scenario: [Actions][Edit][Catalogue] User must be able to edit a sponosor values
        Given The '/library/ct_catalogues/All' page is opened
		When The new Codelist is added
		When The codelist sponsor values edition is triggered
		And The sponsor preffered name is updated
		And Codelist change description is provided
		And Form save button is clicked
		Then The sponsor values should be in status 'Draft' and version '0.2'
		Then The attribute values should be in status 'Draft' and version '0.1'
		And The sponsor preferred name is updated

	Scenario: [Actions][Edit][Catalogue] User must be able to edit a attributes values
        Given The '/library/ct_catalogues/All' page is opened
		When The new Codelist is added
		When The codelist attribute values edition is triggered
		And The code list attributes are updated and change description is provided
		And Code list attrubutes changes are saved
		Then The sponsor values should be in status 'Draft' and version '0.1'
		Then The attribute values should be in status 'Draft' and version '0.2'
		And The codelist attributes updated values are visible

	Scenario: [Actions][Availability][Draft item] User must only have access to edit, show terms, history actions for Drafted version of the codelist
		Given The '/library/ct_catalogues/All' page is opened
        And The codelist is search for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Codelist are displayed

    Scenario: [Actions][Availability][Final item] User must only have access to edit, show terms, history actions for Final version of the codelist
		Given The '/library/ct_catalogues/All' page is opened
        And The codelist is search for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Codelist are displayed

	@pending_development
	Scenario: [Actions][Pairing][Catalogue] User must be able to pair codelist with another codelist by names

	@pending_development
	Scenario: [Actions][Pairing][Catalogue] User must be able to pair codelist with another codelist by codes
