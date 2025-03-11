@REQ_ID:1070683
Feature: Library - CRF Tree

    As a user, I want to view and manage CRF Tree in the Library

    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to CRF Tree page
        Given The '/library' page is opened
        When The 'CRFs' submenu is clicked in the 'Concepts' section
        And The 'CRF Tree' tab is selected
        Then The current URL is 'library/crfs/crf-tree'

    Scenario: User must be able to see the table of the CRF Tree
        Given The 'library/crfs/crf-tree' page is opened
        Then A table is visible with following headers
            | headers                                 |
            | Templates / Forms / ItemGroups / Items  |
            | Reference attributes                    |
            | Definition attributes                   |
            | Status                                  |
            | Version                                 |
            | Link                                    |

    @manual_test
    Scenario: User must be able to create CRF Tree by linking CRF Elements together - Item to Item Group, Item Group to Form, Form to Template
        Given The CRF Template in 'Final' status exists in database
        And The CRF Form in 'Final' status exists in database
        And The CRF Item Group in 'Final' status exists in database
        And The CRF Item in 'Final' status exists in database
        And The '/library/crfs/crf-tree' page is opened
        When The CRF Form is linked to CRF Template
        And The CRF Item Group is linked to CRF Form
        And The CRF Item is linked to CRF Item Group
        Then The CRF Form is displayed underneath the linked CRF Template
        And The CRF Item Group is displayed underneath the linked CRF Form
        And The CRF Item is displayed underneath the linked CRF Item Group

    @manual_test
    Scenario: User check the Mandatory checkbox for the CRF Form
        Given The CRF Tree consisting of Template, Form, Item Group and Item exists
        And The '/library/crfs/crf-tree' page is opened
        When The Mandatory checkbox is checked for given CRF Form
        Then The given CRF Form is now Mandatory

    @manual_test
    Scenario: User check the Mandatory checkbox for the CRF Item Group
        Given The CRF Tree consisting of Template, Form, Item Group and Item exists
        And The '/library/crfs/crf-tree' page is opened
        When The Mandatory checkbox is checked for given CRF Item Group
        Then The given CRF Item Group is now Mandatory

    @manual_test
    Scenario: User check the Mandatory checkbox for the CRF Item
        Given The CRF Tree consisting of Template, Form, Item Group and Item exists
        And The '/library/crfs/crf-tree' page is opened
        When The Mandatory checkbox is checked for given CRF Item
        Then The given CRF Item is now Mandatory

    @manual_test
    Scenario: User must be able to see the CRF Form as Repeating in the CRF Tree
        Given The CRF Tree consisting of Template, Form, Item Group and Item exists
        And The given CRF Form is set as Repeating
        And The '/library/crfs/crf-tree' page is opened
        Then The given CRF Form has tick-mark in the Repeating column

    @manual_test
    Scenario: User must be able to see the CRF Item Group as Repeating in the CRF Tree
        Given The CRF Tree consisting of Template, Form, Item Group and Item exists
        And The given CRF Item Group is set as Repeating
        And The '/library/crfs/crf-tree' page is opened
        Then The given CRF Item Group has tick-mark in the Repeating column
