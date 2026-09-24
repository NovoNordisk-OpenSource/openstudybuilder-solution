@REQ_ID:2383812

Feature: Library - Admin Definitions - Clinical Programmes

    Background: User is logged in
        Given The user is logged in

    @smoke_test
    Scenario: [Create][Positive case] User must be able to create a new clinical programme
        Given The '/library/clinical_programmes' page is opened
        When Click on the + button to create a new clinical programme
        When Input a clinical programme name
        And Form save button is clicked
        Then The pop up displays 'Clinical programme added'
        And Clinical programme is found

    Scenario: [Actions][Edit] User must be able to edit the none project-linked clinical programme
        Given The '/library/clinical_programmes' page is opened
        And Click on the + button to create a new clinical programme
        And Input a clinical programme name
        And Form save button is clicked
        And Clinical programme is found
        When The 'Edit' option is clicked from the three dot menu list
        When Update the clinical programme name to a new one
        And Form save button is clicked
        Then The pop up displays 'Clinical programme updated'
        And Clinical programme is found

    Scenario: [Actions][Delete] User must be able to delete the none project-linked clinical programme
        Given The '/library/clinical_programmes' page is opened
        And Click on the + button to create a new clinical programme
        And Input a clinical programme name
        And Form save button is clicked
        And Clinical programme is found
        When The 'Delete' option is clicked from the three dot menu list
        When Action is confirmed by clicking continue
        Then The pop up displays 'Clinical programme deleted'
        And Clinical programme is no longer available

    Scenario: [Action][Edit][Negative case] User must Not be able to edit the project-linked clinical programme
        Given The '/library/clinical_programmes' page is opened
        When Click on the + button to create a new clinical programme
        And Input a clinical programme name
        And Form save button is clicked
        And The '/library/projects' page is opened
        And Click on the + button to create a new project
        When Create project and link it to the programme
        And Form save button is clicked
        And The '/library/clinical_programmes' page is opened
        And Clinical programme is found
        And The 'Edit' option is clicked from the three dot menu list
        And User tries to update programme name
        And Form save button is clicked
        Then The pop up displays 'Cannot update Clinical Programme'

    Scenario: [Action][Delete][Negative case] User must Not be able to delete the project-linked clinical programme
        Given The '/library/clinical_programmes' page is opened
        And Clinical programme is found
        When The 'Delete' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        Then The pop up displays 'Cannot delete Clinical Programme'