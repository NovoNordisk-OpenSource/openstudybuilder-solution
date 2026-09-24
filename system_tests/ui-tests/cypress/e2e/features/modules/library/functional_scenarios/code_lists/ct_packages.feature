@REQ_ID:1070674

Feature: Library - Code Lists - CT Packages

	Background: User must be logged in
		Given The user is logged in

	@smoke_test
	Scenario: [Navigation] User must be able to navigate to the CT Packages page and see it's content
		Given The '/library' page is opened
		When The 'CT Packages' submenu is clicked in the 'Code Lists' section
		Then The current URL is 'library/ct_packages'
		And The 'CT Packages' title is visible
		And The timeline is visible
		And The table is loaded
		And The table is visible and not empty
		And The following tabs are visible
			| tabs 			|
			| ADAM CT       |
			| SEND CT		|

	Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table
		Given The '/library/ct_packages' page is opened
		And CT Package data is loaded
		When The first column is selected from Select Columns option for table with actions
		Then The table contain only selected column and actions column

    Scenario: [Table][Pagination] User must be able to use table pagination
		Given User sets row page to 5 in the settings menu
        And The '/library/ct_packages' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

	# Scenario Outline: User must be able to filter the table by text fields
	# 	Given The '/library/ct_packages' page is opened
	# 	And CT Package data is loaded
	# 	When The user filters field '<name>'
	# 	Then The table is filtered correctly

	# 	Examples:
	# 		| name                   |
	# 		| Library                |
	# 		| Sponsor preferred name |
	# 		| Template parameter     |
	# 		| Code list status       |
	# 		| Concept ID             |
	# 		| Code list name         |
	# 		| NCI Preferred name     |
	# 		| Extensible             |
	# 		| Attributes status      |

	
	Scenario: [Overview] User must be able to see the term within the Codelist existing in CT Package
		Given The '/library/ct_packages/SEND CT/SEND CT 2021-12-17' page is opened
		And CT Package data is loaded
		Then The 'C111113' row contains following values
			| column                 | value                    |
			| Concept ID             | C111113                  |
			| Sponsor preferred name | SEND Domain Abbreviation |
			| Submission value       | SDOMAIN                  |

	Scenario: [Overview] User must be able to open the term CT Package
		Given The '/library/ct_packages/SEND CT' page is opened
		And CT Package data is loaded
		And The id of the first term on the list is saved
		And The 'Show terms' option is clicked from the three dot menu list
		Then The user is redirected to the term page

	Scenario: [Overview] User must be able to view the Codelist summary for given Codelist in CT Package
		Given The '/library/ct_packages/SEND CT/SEND CT 2014-09-26/C66729/terms' page is opened
		When The codelist summary is expanded
		Then The codelist summary show following data
			| name               | value                                                                                                                                |
			| Concept ID         | C66729                                                                                                                               |
			| Name               | Route of Administration Response                                                                                                     |
			| Label              | Route of Administration                                                                                                              |
			| Definition         | A terminology codelist relevant to the pathway by which a substance is administered in order to reach the site of action in the body.|
			| Library            | CDISC                                                                                                                                |
			| Template parameter | No                                                                                                                                   |
			| Extensible         | Yes                                                                                                                                  |
		And Add term button is visible in actions menu