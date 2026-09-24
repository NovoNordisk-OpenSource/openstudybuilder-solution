@REQ_ID:1070679
Feature: Library - Code Lists - Sponsor - Show Terms
    AAs a user, I want to verify that the Terms page can be displayed correctly and filter functionality works as expected.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to the Terms page
        Given The '/library' page is opened
        When The 'Terms' submenu is clicked in the 'Code Lists' section
        Then The current URL is 'library/terms'

    Scenario: [Table][Options] User must be able to see table with correct options
        Given The '/library/terms' page is opened
        Then A table is visible with following options
            | options                                            |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |

    Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
        Given The '/library/terms' page is opened
        And A table is visible with following headers
            | headers                     |
            | Library                     |
            | Sponsor name                |
            | Name status                 |
            | Name date                   |
            | Concept ID                  |
            | Code list names             |
            | Code list submission values |
            | Submission values           |
            | NCI Preferred name          |
            | Definition                  |
            | Attributes status           |
            | Attributes date             |

    @unstable_disabled        
    Scenario: [Table][Pagination] User must be able to use table pagination
        Given The '/library/terms' page is opened
        And User waits for the table
        When The user switches pages of the table
        Then The table page presents correct data
                                                          