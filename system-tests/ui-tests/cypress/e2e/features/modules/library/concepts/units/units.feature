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

    Scenario: User must be able to add a new Unit
        Given The '/library/units' page is opened
        When The new unit is added
        Then Unit is found
        And The newly added unit is visible within the Units table

    Scenario: User must not be able to add a new Unit with already existing name
        Given The '/library/units' page is opened
        And [API] Unit in status Draft exists
        When The new unit with already existing name is added
        Then The validation message appears for already existing unit name

    Scenario: User must not be able to save new unit without mandatory data provided
        Given The '/library/units' page is opened
        When The user tries to create unit without Unit Name, codelist term and library provided
        Then The validation message appears for unit library field
        And The validation message appears for unit name field
        And The validation message appears for codelist term field
        And The form is not closed

    Scenario: User must be able to edit the drafted version of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        And The 'Edit' option is clicked from the three dot menu list
        And The draft unit version is edited and saved with change description
        And Unit is found
        Then The item has status 'Draft' and version '0.2'

    Scenario: User must be able to Approve the drafted version of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: User must be able to inactivate the approved version of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        When [API] Unit is approved
        And Unit is found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '1.0'

    Scenario: User must be able to reactivate the inactivated version of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        When [API] Unit is approved
        When [API] Unit is inactivated
        And Unit is found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: User must be able to add a new version for the approved unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        When [API] Unit is approved
        And Unit is found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'

    Scenario: User must be able to edit and approve new version of unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        When [API] Unit is approved
        And Unit is found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'
        When The 'Edit' option is clicked from the three dot menu list
        And The draft unit version is edited and saved with change description
        Then The item has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '2.0'

    Scenario: User must be able to Cancel creation of the unit
        Given The '/library/units' page is opened
        And Unit mandatory data is filled in
        When Modal window form is closed by clicking cancel button
        And Action is confirmed by clicking continue
        Then The form is no longer available
        And The unit is not saved

    Scenario: User must be able to Cancel edition of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        When The 'Edit' option is clicked from the three dot menu list
        When The unit edition form is filled with data
        And Modal window form is closed by clicking cancel button
        And Action is confirmed by clicking continue
        Then The form is no longer available
        And The unit is not saved

    Scenario: User must only have access to aprove, edit, delete, history actions for Drafted version of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Draft item are displayed

    Scenario: User must only have access to new version, inactivate, history actions for Final version of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        When [API] Unit is approved
        And Unit is found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed

    Scenario: User must only have access to reactivate, history actions for Retired version of the uit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        When [API] Unit is approved
        When [API] Unit is inactivated
        And Unit is found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed

    Scenario: User must be able to search created unit
        Given The '/library/units' page is opened
        When [API] First unit for search test is created
        And [API] Second unit for search test is created
        Then One unit is found after performing full name search
        And More than one item is found after performing partial name search 

    Scenario: User must be able to search not existing unit and table will correctly filtered
        Given The '/library/units' page is opened
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: User must be able to combine search and filters to narrow table results
        Given The '/library/units' page is opened
        When The user filters table by status 'Final'
        And The existing item in status Draft is searched for
        And The item is not found and table is correctly filtered
        And The user changes status filter value to 'Draft'
        Then More than one item is found after performing partial name search

    Scenario: User must be able to search item ignoring case sensitivity
        Given The '/library/units' page is opened
        When The existing item in search by lowercased name
        And More than one result is found

    Scenario: User must be able to use table pagination
        Given The '/library/units' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    @manual_test
    Scenario Outline: User must be able to choose table rows per page
        Given The '/library/units' page is opened
        When The user sets rows per page to 'rows_per_page'
        Then The table is populated with correct data
        Examples:
            | rows_per_page |
            | 5             |
            | 10            |
            | 15            |
            | 25            |
            | 50            |
            | 100           |

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
    