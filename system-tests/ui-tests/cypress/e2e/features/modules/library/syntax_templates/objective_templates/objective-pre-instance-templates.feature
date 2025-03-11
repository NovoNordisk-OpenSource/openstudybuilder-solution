@REQ_ID:1070684
Feature: Library - Objective template Pre-Instantiations
    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to see the Parent Objective template table with listed columns
        Given The '/library/objective_templates/pre-instances' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: User must be able to select visibility of columns in the table 
        Given The '/library/objective_templates/pre-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to add a new Objective Template Pre-instantiation in Parent Template tab
        Given The '/library/objective_templates/parent' page is opened
        When The new objective to be used as pre-instantiation is added in the library
        When The 'Approve' action is clicked for the created objective template for pre-instantiation
        When The pre-instantiation is created from that objective template
        Then The pop up displays 'Objective template pre-instantiation added'
        And The newly added Objective Template Pre-instantiation is visible as a new row in the table

    @manual_test
    Scenario: User must be able to edit an existing Objective Template Pre-instantiation in Pre-instance Template tab
        Given The test objective pre-instance template exists with a status as 'Draft'
        When The 'Edit' action is clicked for the objective pre-instantiation
        And The objective pre-instantiation metadata is updated
        Then The updated Objective is visible within the table

    @manual_test
    Scenario: User must be able to edit indexing properties for the Objective Pre-instantiation Template with a status as 'Final'
        Given The test objective parent template exists with a status as 'Final'
        When The 'Edit indexing' is selected from the three dot menu list
        Then The 'Edit indexing properties' container fields are re-selected and saved
        And The pop-up snack displayed with a value as 'Indexing properties updated'

    @manual_test
    Scenario: User must be able to test parameter selection for an Objective Pre-instantiation Template
        Given The '/library/objective_templates' page is opened
        And an Objective Template Pre-instantiation is being added or edited
        When the user select Template Parameter values on the 'Test parameter values' page step
        Then a rich text representation of Objective Template instantiation is displayed with selected parameter values in green text
        And non-selected parameters the parameter is displayed in yellow text
        And the resolving Objective Template instantiation is displayed in plain black text in separate field

    @manual_test
    Scenario: User must not be able to created duplicate of Objective Pre-instance Template with the same template text
        Given The '/library/objective_templates' page is opened
        And an Objective Pre-instance Template is being added or edited
        When the user select 'Continue'
        And the values for Objective Pre-instance Template text is a duplicate of an existing Objective Pre-instance Template
        Then a notification must be given to the user stating this is a duplicate Objective Pre-instance Template that not can be made
        And the page cannot be saved

    @manual_test
    Scenario: User must be able to delete an existing Objective Template Pre-instantiation in Sponsor standards tab
        Given The test Objective Pre-instantiation Template exists with a status as 'Draft'
        And Objective Pre-instantiation Template version is below version 1.0
        When The 'Delete' action button is clicked on an Objective Template Pre-instantiation row
        Then The pop up displays 'Pre-instantiation deleted'
        And The deleted Objective Template Pre-instantiation is no longer visible as a row in the table

    @manual_test
    Scenario: User must be able to approve the drafted version of Objective Pre-instance Template
        Given The test Objective Pre-instance Template exists with a status as 'Draft'
        When The'Approve' option is clicked from the three dot menu list
        Then The pop up displays 'Pre-instance Template is now in Final state'
        And The status of the template displayed as 'Final'

    @manual_test
    Scenario: User must be able to add a new version for the Objective Pre-instance Template with a status as 'Final'
        Given The test Objective Pre-instance Template exists with a status as 'Final' with an incremented value as an example '1.0'
        When The 'New version' button is clicked from the three dot menu list
        Then The pop up displays 'New version created'
        And The approved Objective Pre-instance Template is created as Draft version with an incremented value as an example '1.1'

    @manual_test
    Scenario: User must be able to inactivate the Objective Pre-instance Template with a status as 'Final'
        Given The test Objective Pre-instance Template exists with a status as 'Final'
        When The 'inactivate' button is clicked from the three dot menu list
        Then The pop-up snack displayed with a value as 'Pre-instance Template in-activated'
        And The Objective Pre-instance Template is displayed with a status as 'Retired' with the same version as before

    @manual_test
    Scenario: User must be able to reactivate the Objective Pre-instance Template with a status as 'Retired'
        Given The test Objective Parent Template exists with a status as 'Retired'
        When The 'reactivate' button is clicked from the three dot menu list
        Then The pop-up snack displayed with a value as 'Pre-instance Template reactivated'
        And The Objective Pre-instance Template is displayed with a status as 'Final' with the same version as before

    @manual_test
    Scenario: User must be able to view history of value and status changes for Objective Pre-instance Templates
        Given the '/library/objective_templates' page is opened
        And the 'Pre-instance Template' tab is selected
        When The 'View Page History' is clicked
        Then The 'History for templates' window is displayed with the following column list with values
            | Column | Header             |
            | 1      | Uid                |
            | 2      | Sequence number    |
            | 3      | Partent Template   |
            | 4      | Template           |
            | 5      | Status             |
            | 6      | Version            |
            | 7      | Change description |
            | 8      | Change type        |
            | 9      | User               |
            | 10     | From               |
            | 11     | To                 |
        And latest 10 rows of the history is displayed

    @manual_test
    Scenario: User must be able to view history of value and status changes for a selected Objective Pre-instance Template
        Given The test objective template exists
        When The 'History' option is clicked from the three dot menu list
        Then The 'History for template [uid]' window is displayed with the following column list with values
            | Column | Header             |
            | 1      | Sequence number    |
            | 2      | Partent Template   |
            | 3      | Template           |
            | 4      | Status             |
            | 5      | Version            |
            | 6      | Change description |
            | 7      | Change type        |
            | 8      | User               |
            | 9      | From               |
            | 10     | To                 |

    @manual_test
    Scenario: User must be able to read change history of output
        Given the '/library/objective_templates' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given the '/library/objective_templates' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames