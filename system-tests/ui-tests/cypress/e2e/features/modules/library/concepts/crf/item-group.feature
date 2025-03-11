@REQ_ID:1070683
Feature: Library - CRF Item Group

    As a user, I want to manage every CRF Item Group in the Library

    Background: User is logged in the system
        Given The user is logged in

    Scenario: User must be able to navigate to the Items Group page
        Given The '/library' page is opened
        When The 'CRFs' submenu is clicked in the 'Concepts' section
        And The 'Item Groups' tab is selected
        Then The current URL is '/library/crfs/item-groups'

    Scenario: User must be able to see the data of the CRF Item Group tab
        Given The 'library/crfs/item-groups' page is opened
        Then A table is visible with following headers
            | headers              |
            | OID                  |
            | Name                 |
            | Description          |
            | Implementation Notes |
            | Repeating            |
            | Links                |
            | Version              |
            | Status               |
            
    Scenario: User must be able to select visibility of columns in the table 
        Given The '/library/crfs/item-groups' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to add an Item Group
        Given The single language CRFs are enabled
        And The 'library/crfs/item-groups' page is opened
        When The 'add-crf-item-group' button is clicked
        And The CRF Item Group definition container is filled with data and saved
        # Then The pop up displays 'Item Group has been created'
        And The newly added CRF Item Group is visible in the last row of the table

    #Done after study design merges - commands for the validations included there
    # Scenario: User must not be able to create CRF Item Group without Name provided
    #     Given The 'library/crfs/item-groups' page is opened
    #     And The CRF Item Group definition is filled without name provided and the next button is clicked
    #     Then The validation appears for the 'crf-form-name' field

    Scenario: User must be able to update an existing a Item Group
        Given The single language CRFs are enabled
        And The 'library/crfs/item-groups' page is opened
        And The CRF Item Group in 'Draft' status exists
        When The 'Edit' action is clicked for the CRF Item Group
        And The CRF Item Group metadata are updated and saved
        # Then The pop up displays 'Item Group has been saved'
        And The edited CRF Item Group is visible within the table

    Scenario: User must be able to approve an Item Group in draft status
        Given The 'library/crfs/item-groups' page is opened
        And The CRF Item Group in 'Draft' status exists
        When The 'Approve' action is clicked for the CRF Item Group
        # Then The pop up displays 'Item Group has been approved'
        And The CRF Item Group status is changed to 'Final' and version is rounded up to full number


    Scenario: User must be able to inactivate currently active Item Group
        Given The 'library/crfs/item-groups' page is opened
        And The CRF Item Group in 'Final' status exists
        When The 'Inactivate' action is clicked for the CRF Item Group
        # Then The pop up displays 'Item Group has been inactivated'
        And The CRF Item Group status is changed to 'Retired' and version is incremented by '0'

    Scenario: User must be able to reactivate currently retired Item Group
        Given The 'library/crfs/item-groups' page is opened
        And The CRF Item Group in 'Retired' status exists
        When The 'Reactivate' action is clicked for the CRF Item Group
        # Then The pop up displays 'Item Group has been inactivated'
        And The CRF Item Group status is changed to 'Final' and version is incremented by '0'

    Scenario: User must be able to create a new version of an Item Group
        Given The 'library/crfs/item-groups' page is opened
        And The CRF Item Group in 'Final' status exists
        When The 'New version' action is clicked for the CRF Item Group
        # Then The pop up displays 'New version has been created'
        And The CRF Item Group status is changed to 'Draft' and version is incremented by '0.1'

    Scenario: User must be able to delete CRF Item Group in draft status
        Given The 'library/crfs/item-groups' page is opened
        And The CRF Item Group in draft status with sub 1 version exists
        When The 'Delete' action is clicked for the CRF Item Group
        Then The CRF Item Group is no longer available

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The 'library/crfs/item-groups' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames