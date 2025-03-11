@REQ_ID:2383812

Feature: Library - Manage project

    Background: A Clinical Programme is existed
        Given The user is logged in

    Scenario: User must be able to use column selection option
        Given The '/library/projects' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to create a new project
        Given A Clinical Programme is created
        Given The '/library/projects' page is opened
        When Click on the + button to create a new project
        Then The pop-up window is opened to indicate to add a new project
        When Select an existed clinical programme
        And Input a project name, project number and description
        And Click on SAVE button
        Then The pop up displays 'Project added'
        And The newly created project is shown in the table

    Scenario: User must be able to edit the none study-linked project
        Given A Clinical Programme is created
        Given The '/library/projects' page is opened
        And A test project exists and is not linked to any study
        When Click on 'Edit' option from the three dot menu beside this test project
        Then The pop-up window is opened to indicate to update the project
        When Update the project name to a new one
        And Click on SAVE button
        Then The pop up displays 'Project updated'
        And The updated project is shown in the table

    Scenario: User must be able to delete the none study-linked project
        Given A Clinical Programme is created
        Given The '/library/projects' page is opened
        And A test project exists and is not linked to any study
        When Click on 'Delete' option from the three dot menu beside this test project
        Then The pop-up window is opened to indicate this project will be deleted
        When Click on CONTINUE button
        Then The pop up displays 'Project deleted'
        And The deleted project is not shown anymore in the table