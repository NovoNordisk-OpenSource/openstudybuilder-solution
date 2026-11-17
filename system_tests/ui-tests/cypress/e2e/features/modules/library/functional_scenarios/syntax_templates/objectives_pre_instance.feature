@REQ_ID:1070684
Feature: Library - Syntax Templates - Objectives - Pre-instance
    Background: User must be logged in
        Given The user is logged in

    @smoke_test
    Scenario: [Create][Positive case] User must be able to create Objective Template Pre-instantiation in Parent Template tab
        Given The '/library/objective_templates/parent' page is opened
        And The Add template button is clicked
        And The objective pre-instatiation name is set
        And Form continue button is clicked
        And Form continue button is clicked
        When All Not Applicable checkboxes are checked
        And The Radiobutton with value Yes is selected
        And Form save button is clicked
        And Objective template for pre-instantiation is found by sufix
        When The 'Approve' option is clicked from the three dot menu list
        And Objective template for pre-instantiation is found by sufix
        And The 'Create pre-instantiation' option is clicked from the three dot menu list
        When The pre-instantiation is created from that objective template
        And Form continue button is clicked
        And The Radiobutton with value Yes is selected
        And Form save button is clicked
        Then The pop up displays 'Objective template pre-instantiation added'
        Given The '/library/objective_templates/pre-instances' page is opened
        And User waits for the table
        And User searches for created objective pre-instantiation
        And Created pre-instantiation is visible in the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Delete] User must be able to delete Objective Template Pre-instantiation in Parent Template tab
        Given The '/library/objective_templates/pre-instances' page is opened
        And User waits for the table
        And User searches for created objective pre-instantiation
        And The item has status 'Draft' and version '0.1'
        Given The 'Delete' option is clicked from the three dot menu list
        And User searches for created objective pre-instantiation
        And No results are present the table

    Scenario: [Approve] User must be able to approve the drafted version of Objective Pre-instance Template
        Given The '/library/objective_templates/parent' page is opened
        And The Add template button is clicked
        And The objective pre-instatiation name is set
        And Form continue button is clicked
        And Form continue button is clicked
        When All Not Applicable checkboxes are checked
        And The Radiobutton with value Yes is selected
        And Form save button is clicked
        And Objective template for pre-instantiation is found by sufix
        When The 'Approve' option is clicked from the three dot menu list
        And The 'Create pre-instantiation' option is clicked from the three dot menu list
        When The pre-instantiation is created from that objective template
        And Form continue button is clicked
        And The Radiobutton with value Yes is selected
        And Form save button is clicked
        Then The pop up displays 'Objective template pre-instantiation added'
        Given The '/library/objective_templates/pre-instances' page is opened
        And User waits for the table
        And User searches for created objective pre-instantiation
        Given The 'Approve' option is clicked from the three dot menu list
        When The pop up displays 'Pre-instance is now in Final state'
        Then The item has status 'Final' and version '1.0'

    Scenario: [Inactivate] User must be able to inactivate Objective Pre-instance Template
        Given The '/library/objective_templates/pre-instances' page is opened
        And User waits for the table
        And User searches for created objective pre-instantiation
        Given The 'Inactivate' option is clicked from the three dot menu list
        When The pop up displays 'Pre-Instance inactivated'
        Then The item has status 'Retired' and version '1.0'

    Scenario: [Reactivate] User must be able to reactivate Objective Pre-instance Template
        Given The '/library/objective_templates/pre-instances' page is opened
        And User waits for the table
        And User searches for created objective pre-instantiation
        Given The 'Reactivate' option is clicked from the three dot menu list
        When The pop up displays 'Pre-Instance reactivated'
        Then The item has status 'Final' and version '1.0'

    Scenario: [New version] User must be able to create new version of Objective Pre-instance Template
        Given The '/library/objective_templates/pre-instances' page is opened
        And User waits for the table
        And User searches for created objective pre-instantiation
        Given The 'New version' option is clicked from the three dot menu list
        When The pop up displays 'New version created'
        Then The item has status 'Draft' and version '1.1'

    @manual_test
    Scenario: User must be able to edit an existing Objective Template Pre-instantiation in Pre-instance Template tab

    @manual_test
    Scenario: User must be able to edit indexing properties for the Objective Pre-instantiation Template with a status as 'Final'

    @manual_test
    Scenario: User must be able to test parameter selection for an Objective Pre-instantiation Template
    
    @manual_test
    Scenario: User must not be able to created duplicate of Objective Pre-instance Template with the same template text

    Scenario: User must be able to view history of value and status changes for a selected Objective Pre-instance Template
        Given The '/library/objective_templates/pre-instances' page is opened
        And User waits for the table
        And The 'History' option is clicked from the three dot menu list
        Then The History page is displayed
        And The following column list with values will exist
            | header                 |
            | Sequence number        |
            | Parent template        |
            | Status                 |
            | Version                |
            | Change type            |
            | User                   |
            | From                   |
            | To                     |
        And The history table is not empty
        When The CLOSE button is clicked
        Then The current URL is 'library/objective_templates/pre-instances'
