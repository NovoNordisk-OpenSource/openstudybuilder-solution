@REQ_ID:2383812

Feature: Library - Admin Definitions - Projects

    Background: A Clinical Programme is existed
        Given The user is logged in

    Scenario: User must be able to use column selection option
        Given The '/library/projects' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @smoke_test
    Scenario: [Create][Postive case] User must be able to create a new project
        Given The '/library/clinical_programmes' page is opened
        Given A Clinical Programme is created
        And Form save button is clicked
        Given The '/library/projects' page is opened
        When Click on the + button to create a new project
        And User waits for 1 seconds
        When Select an existing clinical programme
        And Input a project name, project number and description
        And Form save button is clicked
        Then The pop up displays 'Project added'
        And Test project is found

    Scenario: [Actions][Edit] User must be able to edit the none study-linked project
        Given The '/library/clinical_programmes' page is opened
        Given A Clinical Programme is created
        And Form save button is clicked
        Given The '/library/projects' page is opened
        And Click on the + button to create a new project
        And Select an existing clinical programme
        And Input a project name, project number and description
        And Form save button is clicked
        And Test project is found
        When The 'Edit' option is clicked from the three dot menu list
        When Update the project name to a new one
        And Form save button is clicked
        Then The pop up displays 'Project updated'
        And Test project is found

    Scenario: [Actions][Delete] User must be able to delete the none study-linked project
        Given The '/library/clinical_programmes' page is opened
        Given A Clinical Programme is created
        And Form save button is clicked
        Given The '/library/projects' page is opened
        And Click on the + button to create a new project
        And Select an existing clinical programme
        And Input a project name, project number and description
        And Form save button is clicked
        And Test project is found
        When The 'Delete' option is clicked from the three dot menu list
        When Action is confirmed by clicking continue
        Then The pop up displays 'Project deleted'
        And Test project is no longer available

    Scenario: [Actions][Edit][Negative case] User must Not be able to edit a study-linked project
        Given The '/library/projects' page is opened
        And Test project with linked study is found
        When The 'Edit' option is clicked from the three dot menu list
        When User tries to update project name
        And Form save button is clicked
        Then The pop up displays 'Cannot update Project'

    Scenario: [Actions][Delete][Negative case]User must Not be able to delete a study-linked project
        Given The '/library/projects' page is opened
        And Test project with linked study is found
        When The 'Delete' option is clicked from the three dot menu list
        When Action is confirmed by clicking continue
        Then The pop up displays 'Cannot delete Project'