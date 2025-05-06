@REQ_ID:1070674

Feature: Library - CT Catalogues

	Background: User must be logged in
		Given The user is logged in

	Scenario: User must be able to navigate to the CT Catalogues page and see it's content
		Given The '/library' page is opened
		And Log that step was executed
		When The 'CT Catalogues' submenu is clicked in the 'Code Lists' section
		And CT data is loaded
		And Log that step was executed
		Then The current URL is '/library/ct_catalogues/All'
		And Log that step was executed
		And The 'CT Catalogues' title is visible
		And Log that step was executed
		And The following tabs are visible
			| tabs 			|
			| ADAM CT       |
			| CDASH CT      |
			| COA CT        |
			| DEFINE-XML CT |
			| PROTOCOL CT   |
			| QRS CT        |
			| QS-FT CT      |
			| SDTM CT       |
			| SEND CT       |
		And The table is visible and not empty

	Scenario: User must be able to select visibility of columns in the table 
        Given The '/library/ct_catalogues/All' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to use table pagination
        Given The '/library/ct_catalogues/All' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

	Scenario: User must be able to open terms for Codelists in CT Catalogue
		Given The '/library/ct_catalogues/All' page is opened
		When The 'SEND CT' tab is selected
		And The 'Show terms' option is clicked from the three dot menu list
		Then The URL should contain 'C106482' ID

	Scenario: User must be able to open see the terms for Codelists in CT Catalogue
		Given The '/library/ct_catalogues/All/C85839/terms' page is opened
		Then The 'C92362' row contains following values
			| column                | value                                                        |
			| Library               | CDISC                                                        |
			| Concept ID            | C92362                                                       |
			| Sponsor name          | AUC All Normalized by Body Mass Index                        |
			| Name submission value | AUC All Norm by BMI                                          |
			| NCI Preferred name    | AUC All Normalized by Body Mass Index                        |
			| Code submission value | AUCALLB                                                      |
			| Definition            | The area under the curve (AUC) from the time of dosing to th |

	Scenario: User must be able to see the Codelist Summary for Codelist
		Given The '/library/ct_catalogues/SEND CT/C66729/terms' page is opened
		When The codelist summary is expanded
		Then The codelist summary show following data
			| name               | value                                                                                                                                |
			| Concept ID         | C66729                                                                                                                               |
			| Name               | Route of Administration Response                                                                                                     |
			| Label              | Route of Administration                                                                                                              |
			| Definition	     | A terminology codelist relevant to the pathway by which a substance is administered in order to reach the site of action in the body.|
			| Library            | CDISC                                                                                                                                |
			| Template parameter | Yes                                                                                                                                  |
			| Extensible         | Yes                                                                                                                                  |
		And Add term button is visible in actions menu

	Scenario: User must be able to add a new Codelist
		Given The '/library/ct_catalogues/All' page is opened
		When The new Codelist is added
		Then The new Codelist page is opened and showing correct data
		And The sponsor values should be in status 'Draft' and version '0.1'
		And The attribute values should be in status 'Draft' and version '0.1'

	Scenario: User must be able to edit an existing Codelist
		Given The test Codelist for editing is opened
		When The Codelist sponsor values are edited
		And The Codelist sponsor values are validated
		Then The edited codelist page is showing correct data
		And The sponsor values should be in status 'Final' and version '1.0'
		And The Edit sponsor values button is not visible
		But The Create new sponsor values version button is visible
		And The version history contain the changes of edited Codelist

	Scenario: User must be able to add a new term to the Codelist
		Given The '/library/ct_catalogues/All/C117744/terms' page is opened
		When The new term is added
		Then The term page is opened and showing correct data

	Scenario: User must be able to add an existing term to the Codelist
		Given The test term in test Codelist is opened
		And The '/library/ct_catalogues/All/C117744/terms' page is opened
		When The existing term is added
		Then The pop up displays 'Term added'

	Scenario: User must be able to edit a term in Codelist
		Given The test term in test Codelist is opened
		When The term sponsor values are edited
		And The term is validated
		Then The edited term page is showing correct data
		And The sponsor values should be in status 'Final' and version '1.0'
		And The Edit sponsor values button is not visible
		But The Create new sponsor values version button is visible