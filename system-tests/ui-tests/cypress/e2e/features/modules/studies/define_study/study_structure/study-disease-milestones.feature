@REQ_ID:1074254
Feature: Studies - Study Disease Milestones

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study elements.

    Background: User is logged in and the test study is selected
        Given The user is logged in
        And A test study is selected

    Scenario: Navigation to Study Disease Milestones page
        Given The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Disease Milestones' tab is selected
        Then The current URL is '/studies/Study_000001/study_structure/disease_milestones'

    Scenario: User must be able to see the Study Disease Milestones table with options listed in this scenario
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add disease milestone                                           |
            | Columns                                                         |
            | Add select boxes to table to allow selection of rows for export |
        And A table is visible with following headers
            | headers              |
            | #                    |
            | Type                 |
            | Definition           |
            | Repetition indicator |
            | Modified             |
            | Modified by          |

    ##To uncomment after library part has been finished
    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    Scenario: User can add a new Study Disease Milestone
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        When The new Study Disease Milestone is added
        Then The new Study Disease Milestone is visible within the study disease milestones table

    Scenario: User can edit the Study Disease Milestones
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        And The test Study Disease Milestones exists
        When The Study Disease Milestones is edited
        Then The Study Disease Milestones with updated values is visible within the table

    Scenario: User must not be able to add or edit study disease milestones without Disease Milestone Type provided
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        When The user tries to close the form without Disease Milestone Type provided
        Then The validation appears under that field in the Disease Milestones form
        And The form is not closed

    #Not implemented
    # Scenario: User must not be able to add or edit study disease milestones without Repetition Indicator provided
    #     Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
    #     When The Add or Edit Study Disease Milestones button is clicked
    #     And The Repetition Indicator field is empty
    #     And The save button in the Add or Edit Study Disease Milestones form is clicked
    #     Then The required field validation appears for that field
    #     And The Add or Edit Study Disease Milestones form is not closed

    Scenario: User must not be able to create two Study Disease Milestones within one study using the same Disease Milestone Type
        Given The test Study Disease Milestones exists
        And The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        When New Disease Milestone Type is created with the same Disease Milestone Type
        Then The system displays the message "in field Type is not unique for the study"
        And The form is not closed

    Scenario: Deleting an existing Study Disease Milestones is possible
        Given The test Study Disease Milestones exists
        And The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        When The delete action is clicked for the test Study Disease Milestones
        And The continue is clicked in confirmation popup
        Then The test Study Disease Milestones is no longer available

    Scenario: User must be able to export the data in CSV format
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        And The user exports the data in 'CSV' format
        Then The study specific 'DiseaseMilestones' file is downloaded in 'csv' format

    Scenario: User must be able to export the data in JSON format
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        And The user exports the data in 'JSON' format
        Then The study specific 'DiseaseMilestones' file is downloaded in 'json' format

    Scenario: User must be able to export the data in XML format
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        And The user exports the data in 'XML' format
        Then The study specific 'DiseaseMilestones' file is downloaded in 'xml' format

    Scenario: User must be able to export the data in EXCEL format
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        And The user exports the data in 'EXCEL' format
        Then The study specific 'DiseaseMilestones' file is downloaded in 'xlsx' format

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/study_structure/disease_milestones' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames