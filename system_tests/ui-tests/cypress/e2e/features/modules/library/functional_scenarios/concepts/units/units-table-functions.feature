@REQ_ID:1070683
Feature: Library - Concepts - Units
    As a user, I want to manage every Unit in the Concepts Library
    Background: User must be logged in
        Given The user is logged in

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
        Given The '/library/units' page is opened
        Then A table is visible with following headers
            | headers                     |
            | Name                        |
            | Master unit                 |
            | Display unit                |
            | Unit subsets                |
            | UCUM unit                   |
            | CT Submission Values        |
            | Convertible unit            |
            | US conventional unit        |
            | Unit dimension              |
            | Use molecular weight        |
            | Use complex unit conversion |
            | Conversion factor to master |
            | Modified                    |
            | Status                      |
            | Version                     |

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table
        Given The '/library/units' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @smoke_test
    Scenario: [Table][Search][Positive case] User must be able to search created unit
        Given The '/library/units' page is opened
        When [API] First unit for search test is created
        And [API] Second unit for search test is created
        Then One unit is found after performing full name search
        And The existing item is searched for by partial name
        Then More than one result is found

    Scenario: [Table][Search][Negative case] User must be able to search not existing unit and table will correctly filtered
        Given The '/library/units' page is opened
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: [Table][Search][Filtering] User must be able to combine search and filters to narrow table results
        Given The '/library/units' page is opened
        When The user filters table by status 'Final'
        And The existing item is searched for by partial name
        And The item is not found and table is correctly filtered
        And The user changes status filter value to 'Draft'
        And The existing item is searched for by partial name
        Then More than one result is found

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity
        Given The '/library/units' page is opened
        When The existing item in search by lowercased name
        And More than one result is found

    Scenario: [Table][Pagination] User must be able to use table pagination
        Given The '/library/units' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The '/library/units' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
            | name                        |
            | Name                        |
            | Master unit                 |
            | Display unit                |
            | Unit subsets                |
            | UCUM unit                   |
            | CT Submission Values        |
            | Convertible unit            |
            | US conventional unit        |
            | Unit dimension              |
            | Use molecular weight        |
            | Use complex unit conversion |
            | Conversion factor to master |
            | Status                      |
            | Version                     |
    