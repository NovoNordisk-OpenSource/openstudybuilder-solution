@REQ_ID:1070679
Feature: Library - Sponsor CT Packages

    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to the Sponsor CT Packages page
        Given The '/library' page is opened
        When The 'Sponsor CT Packages' submenu is clicked in the 'Code Lists' section
        Then The current URL is 'library/sponsor-ct-packages'

    # Disabled due to already existing packages in tests env
    # Scenario: User must be able to create first Sponsor CT Package
    #     Given The '/library/sponsor-ct-packages' page is opened
    #     When The Create First One button is pressed on the Sponsor CT Package page
    #     And The Sponsor CT Package form is populated and saved
    #     Then The table presents created Sponsor CT Package

    Scenario: User must be able to see the columns list of Sponsor CT Package for a selected CDISC CT Package
        Given The '/library/sponsor-ct-packages' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Columns                                                         |
            | Export                                                          |
            | Add select boxes to table to allow selection of rows for export |

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

Scenario: User must not be able to create multiple Sponsor CT Packages for the same date
    Given The '/library/sponsor-ct-packages' page is opened
    When Sponsor CT Package is created for the same date as already existing one
    Then The pop up displays 'A sponsor CTPackage already exists for this date'
