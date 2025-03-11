@REQ_ID:2383812

Feature: Library - Manage Clinical Programmes

    Background: User is logged in
        Given The user is logged in

    Scenario: User must be able to create a new clinical programme
        Given The '/library/clinical_programmes' page is opened
        When Click on the + button to create a new clinical programme
        Then The pop-up window is opened to indicate to add a new clinical programme
        When Input a clinical programme name
        And The SAVE button is clicked
        Then The pop up displays 'Clinical programme added'
        And The newly created clinical programme is shown in the table

    Scenario: User must be able to edit the none project-linked clinical programme
        Given The '/library/clinical_programmes' page is opened
        And A test clinical programme exists and is not linked to any project
        When Click on 'Edit' option from the three dot menu beside this test clinical programme
        Then The pop-up window is opened to indicate to update the clicnical programme name
        When Update the clinical programme name to a new one
        And The SAVE button is clicked
        Then The pop up displays 'Clinical programme updated'
        And The updated clinical programme is shown in the table

    Scenario: User must be able to delete the none project-linked clinical programme
        Given The '/library/clinical_programmes' page is opened
        And A test clinical programme exists and is not linked to any project
        When Click on 'Delete' option from the three dot menu beside this test clinical programme
        Then The pop-up window is opened to indicate that this clinical programme will be deleted
        When The CONTINUE button is clicked
        Then The pop up displays 'Clinical programme deleted'
        And The deleted clinical programme is not shown anymore in the table