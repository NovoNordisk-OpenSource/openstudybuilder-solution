@REQ_ID:1070683
Feature: Library - Units
    As a user, I want to manage every Unit in the Concepts Library
    Background: User must be logged in
        Given The user is logged in
    
    Scenario: User must be able to navigate to the Units page
        Given The '/library' page is opened
        When The 'Units' submenu is clicked in the 'Concepts' section
        Then The current URL is '/library/units'

    Scenario: User must be able to see the columns list on the main page as below
        Given The '/library/units' page is opened
        Then A table is visible with following headers
            | headers                     |
            | Library                     |
            | Name                        |
            | Master unit                 |
            | Display unit                |
            | Unit subsets                |
            | UCUM unit                   |
            | CT Unit terms               |
            | Convertible unit            |
            | SI unit                     |
            | US conventional unit        |
            | Unit dimension              |
            | Legacy code                 |
            | Use molecular weight        |
            | Use complex unit conversion |
            | Conversion factor to master |
            | Modified                    |
            | Status                      |
            | Version                     |

    Scenario: User must be able to select visibility of columns in the table
        Given The '/library/units' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @manual_test
    Scenario Outline: User must be able to filter the table by text fields
        Given The '/library/units' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
            | name                        |
            | Library                     |
            | Name                        |
            | Master unit                 |
            | Display unit                |
            | Unit subsets                |
            | UCUM unit                   |
            | CT Unit terms               |
            | Convertible unit            |
            | SI unit                     |
            | US conventional unit        |
            | Unit dimension              |
            | Legacy code                 |
            | Molecular weight            |
            | Conversion factor to master |
            # | Modified                    |
            | Status                      |
            | Version                     |

    Scenario: User must be able to add a new Unit
        Given The '/library/units' page is opened
        When The new unit is added
        And The newly added unit is visible within the Units table

    Scenario: User must not be able to save new unit without name provided
        Given The '/library/units' page is opened
        When The user tries to create unit without Unit Name provided
        Then The validation appears for Unit Name field
        And The form is not closed

    Scenario: User must not be able to save new unit without Unit codelist term provided
        Given The '/library/units' page is opened
        When The user tries to create unit without Unit codelist term provided
        Then The validation appears for Unit codelist term field
        And The form is not closed

    Scenario: User must be able to edit the drafted version of the unit
        Given The '/library/units' page is opened
        When Unit in Draft status is created
        When The 'Edit' action is clicked for the Unit
        When The draft unit version is edited and saved with change description
        Then The Unit status is kept as 'Draft' and version is incremented by '0.1'

    Scenario: User must be able to Approve the drafted version of the unit
        Given The '/library/units' page is opened
        When Unit in Draft status is created
        When The 'Approve' action is clicked for the Unit
        Then The Unit status is changed to 'Final' and version is rounded up to full number

    Scenario: User must be able to inactivate the approved version of the unit
        Given The '/library/units' page is opened
        When The 'Inactivate' action is clicked for the Unit
        Then The Unit status is changed to 'Retired' and version remain unchanged

    Scenario: User must be able to reactivate the inactivated version of the unit
        Given The '/library/units' page is opened
        When The 'Reactivate' action is clicked for the Unit
        Then The Unit status is changed to 'Final' and version remain unchanged

    Scenario: User must be able to add a new version for the approved unit
        Given The '/library/units' page is opened
        When The 'New version' action is clicked for the Unit
        Then The Unit status is changed to 'Draft' and version is incremented by '0.1'

    Scenario Outline: User must be able to filter the table by text fields
        Given The '/library/units' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                        |
        | Library                     |
        | Name                        |
        | Master unit                 |
        | Display unit                |
        | Unit subsets                |
        | UCUM unit                   |
        | CT Unit terms               |
        | Convertible unit            |
        | SI unit                     |
        | US conventional unit        |
        | Unit dimension              |
        | Legacy code                 |
        | Use molecular weight        |
        | Use complex unit conversion |
        | Conversion factor to master |
        | Status                      |
        | Version                     |

