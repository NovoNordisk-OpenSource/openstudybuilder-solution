@REQ_ID:1070679
Feature: Library - Code Lists - Sponsor CT Packages

    Background: User must be logged in
        Given The user is logged in

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the Sponsor CT Packages page
        Given The '/library' page is opened
        When The 'Sponsor CT Packages' submenu is clicked in the 'Code Lists' section
        Then The current URL is 'library/sponsor-ct-packages'

    # Disabled due to already existing packages in tests env
    # Scenario: User must be able to create first Sponsor CT Package
    #     Given The '/library/sponsor-ct-packages' page is opened
    #     When The Create First One button is pressed on the Sponsor CT Package page
    #     And The Sponsor CT Package form is populated and saved
    #     And Form save button is clicked
    #     Then The table presents created Sponsor CT Package

    Scenario: [Create][Negative case] User must not be able to create multiple Sponsor CT Packages for the same date
        Given [API] User fetches first available package on ADAM CT
        And [API] User creates a package if it doesn not exists
        And The '/library/sponsor-ct-packages' page is opened
        When Sponsor CT Package is created for the same date as already existing one
        And Action is confirmed by clicking save
        Then The pop up displays 'A Sponsor CTPackage already exists for this date'

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the columns list of Sponsor CT Package for a selected CDISC CT Package
        Given The '/library/sponsor-ct-packages' page is opened
        Then A table is visible with following options
            | options                                            |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |

        And A table is visible with following headers
            | headers                |
            | Library                |
            | Sponsor preferred name |
            | Template parameter     |
            | Code list status       |
            | Name modified          |
            | Concept ID             |
            | Submission value       |
            | Code list name         |
            | NCI Preferred name     |
            | Extensible             |
            | Attributes status      |
            | Attributes modified    |
