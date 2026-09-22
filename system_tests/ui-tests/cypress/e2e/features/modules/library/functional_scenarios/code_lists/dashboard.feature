@REQ_ID:1070674 @pending_implementation

Feature: Feature: Library - Code Lists - Dashboard

	Background: User management of Dashboard view
		Given The user is logged in

	Scenario: [Navigation] User must be able to navigate to the Dashboard page and see 'Latest added code lists' table
		Given The '/library' page is opened
		When The 'Dashboard' submenu is clicked in the 'Code Lists' section
		Then The current URL is 'library/ct_dashboard'
		And The 'Code Lists and Terms Dashboard' title is visible
		And The following column lists are visible under 'Latest added code lists' table
			| Library                 |
			| Concept ID              |
			| Sponsor preferred name  |
			| Name status             |
			| Modified                |
			| Code list name          |
			| Submission value        |
			| Extensible              |
			| Code list status        |
			| Modified                |

	Scenario: [Navigation] User must be able to navigate to the Dashboard page and see it's content
		Given The '/library' page is opened
		When The 'Dashboard' submenu is clicked in the 'Code Lists' section
		Then The current URL is 'library/ct_dashboard'
		And The 'Code Lists and Terms Dashboard' title is visible on the left top panel of the window
		And The following titles are visible with printed values
    """
      # of catalogues: <>
	  # of pacakages: <>

	  # of code list in CDISC library: <>
	  # of code list in Sponsor library: <>

	  # of terms in CDISC library: <>
	  # of terms in Sponsor library: <>

	  Code list evolution/code lists: <>
	  Mean # of evolution/terms: <>

    """

	Scenario: [Overview] User must be able to see the 'Evolution of code lists over time' bar chart table
		Given The '/library' page is opened
		When The 'Dashboard' submenu is clicked in the 'Code Lists' section
		Then The current URL is 'library/ct_dashboard'
		And The 'Evolution of code lists over time' bar chart dashboard view visible with Years on x-axis and visible with numbercount on y-axis
		And The charts are colour coded with a reference as 'Added' are Dark blue in colour, 'Updated' are Green in colour and 'Deleted' are Red in colour

	Scenario: [Overview] User must be able to click the 'Evolution of code lists over time' Bar chart reference 'Added'
		Given The 'Dashboard' submenu is clicked in the 'Code Lists' section 
		And The 'Code Lists and Terms Dashboard' page is visible
		When The blue color coded bar reference 'Added' is clicked in the 'Evolution of code lists over time' chart table 
		Then The blue colour coded bar charts are disappeared from the chart table

	Scenario: [Overview] User must be able to click the 'Evolution of code lists over time' Bar chart reference 'Updated'
		Given The 'Dashboard' submenu is clicked in the 'Code Lists' section 
		And The 'Code Lists and Terms Dashboard' page is visible
		When The green color coded bar reference 'Updated' is clicked in the 'Evolution of code lists over time' chart table
		Then The green colour coded bar charts are disappeared from the chart table

	Scenario: [Overview] User must be able to click the 'Evolution of code lists over time' Bar chart reference 'Deleted'
		Given The 'Dashboard' submenu is clicked in the 'Code Lists' section 
		And The 'Code Lists and Terms Dashboard' page is visible
		When The red color coded bar reference 'Deleted' is clicked in the 'Evolution of code lists over time' chart table
		Then The red colour coded bar charts are disappeared from the chart table

	Scenario: [Overview] User must be able to see the 'Terms evolutions/terms' bar chart table
		Given The '/library' page is opened
		When The 'Dashboard' submenu is clicked in the 'Code Lists' section
		Then The current URL is 'library/ct_dashboard'
		And The 'Terms evolutions/terms' bar chart dashboard view visible with Years on x-axis and visible with numbercount on y-axis
		And The charts are colour coded with a reference as 'Added' are Dark blue in colour, 'Updated' are Green in colour and 'Deleted' are Red in colour

	Scenario: [Overview] User must be able to click the 'Terms evolutions/terms' Bar chart reference 'Added'
		Given The 'Dashboard' submenu is clicked in the 'Code Lists' section 
		And The 'Code Lists and Terms Dashboard' page is visible
		When The blue color coded bar reference 'Added' is clicked in the 'Terms evolutions/terms' chart table 
		Then The blue colour coded bar charts are disappeared from the chart table

	Scenario: [Overview] User must be able to click the 'Terms evolutions/terms' Bar chart reference 'Updated'
		Given The 'Dashboard' submenu is clicked in the 'Code Lists' section 
		And The 'Code Lists and Terms Dashboard' page is visible
		When The green color coded bar reference 'Updated' is clicked in the 'Terms evolutions/terms' chart table
		Then The green colour coded bar charts are disappeared from the chart table

	Scenario: [Overview] User must be able to click the 'Terms evolutions/terms' Bar chart reference 'Deleted'
		Given The 'Dashboard' submenu is clicked in the 'Code Lists' section 
		And The 'Code Lists and Terms Dashboard' page is visible
		When The red color coded bar reference 'Deleted' is clicked in the 'Terms evolutions/terms' chart table
		Then The red colour coded bar charts are disappeared from the chart table