@REQ_ID:987736 @pending_implementation
Feature: Studies - Manage the study definition core attributes

    Background: User must be logged in
        Given The user is logged in

    Scenario:  User must be able to navigate to the Study Core Attributes page
        Given The '/studies' page is opened
        When The 'Study' submenu is clicked in the 'Manage Studies' section
        And the 'Study Core Attributes' tab is selected
        Then The current URL is '/studies/Study_000001/core_attributes'

    Scenario: User must be able to see the Study Core Attibutes page form with correct fields
        Given The '/studies/Study_000001/core_attributes' page is opened
        Then A form is visible with following fields
            | column | header             |
            | 1      | Clinical programme |
            | 2      | Project ID         |
            | 3      | Project name       |
            | 4      | Study ID           |
            | 5      | Stuby number       |
            | 6      | Study acronym      |
            | 7      | Modified           |
            | 8      | Modified by        |


    #### Alowed actions based on state and status - Covered by Actions section

    # Scenario: User must see an enabled Edit button when the Study status is 'Draft'
    #     Given The '/studies/Study_000001/core_attributes' page is opened
    #     Then A page form is visible with the following options
    #         | Edit    |
    #         | Histroy |

    # Scenario: User must see an enabled Delete button when the Study status is 'Draft' and the study have newer been released or locked
    #     Given The '/studies/Study_000001/core_attributes' page is opened
    #     Then A page form is visible with the option
    #         | Delete |


    #### Actions

    Scenario: User must be able to edit a Study
        Given The '/studies/Study_000001/core_attributes' page is opened
        And A study in draft status is selected
        When The 'Edit' option is selected on the page
        And The Study is updated and saved
        Then The pop up displays 'Study updated'
        And The updated study data is present in the core attributes table

    Scenario: User must be able to delete a Study
        Given The '/studies/Study_000001/core_attributes' page is opened
        And A study in draft status with no release or lock history and ready to be deleted is selected 
        When The 'Delete' option is selected on the page
        Then The pop up displays 'Study updated'
        And The page tab 'Deleted Studies' is displayed
        And The deleted study is listed in the table of deleted studies


    ### History

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/core_attributes' page is opened
      When The user opens version history
      Then The user is presented with version history of the output containing timestamp and username

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/core_attributes' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernamesv


