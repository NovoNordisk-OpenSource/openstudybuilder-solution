@REQ_ID:1070674
Feature: Feature: Library - Code Lists - Dashboard

	Background: User management of Dashboard view
		Given The user is logged in

	Scenario: [Navigation] User must be able to navigate to the Dashboard page and see 'Latest added code lists' table
		Given The '/library' page is opened
		When The 'Dashboard' submenu is clicked in the 'Code Lists' section
		Then The current URL is 'library/ct_dashboard'

	Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
        Given The '/library/ct_dashboard' page is opened
        And A table is visible with following headers
            | headers                 |
			| Library                 |
			| Concept ID              |
			| Sponsor preferred name  |
			| Template parameter      |
			| Name status             |
			| Modified                |
			| Code list name          |
			| Submission value        |
			| Extensible              |
			| Code list status        |
			| Modified                |

	Scenario: [Sections] User must be able to see following sections: Evolution of code lists over time, Term evolutions terms, Latest added code lists
		Given The '/library/ct_dashboard' page is opened
		Then The section with title 'Evolution of code lists over time' is visible
		And The section with title 'Term evolutions / terms:' is visible
		And The section with title 'Latest added code lists' is visible
