@REQ_ID:1074258 @manual_test
Feature: Studies - Study Objectives

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And A test study is selected

    Scenario: User must be able to navigate to the Study Objectives page
        Given The '/studies' page is opened
        When The 'Study Purpose' submenu is clicked in the 'Define Study' section
        And The 'Study Objectives' tab is selected
        Then The current URL is '/studies/Study_000001/study_purpose/objectives'

    Scenario: User must be able to see the page table with correct columns
        Given The '/studies/Study_000001/study_purpose/objectives' page is opened
        Then A table is visible on the 'Study Objectives' tab with following options
            | option                                                          |
            | Add study objective                                             |
            | Filters                                                         |
            | Columns                                                         |
            | Download                                                        |
            | History                                                         |
            | Select rows control                                             |
            | Add select boxes to table to allow selection of rows for export |
            | Reorder content control                                         |
        And The search field is available in the table
        Then A table is visible with following headers
            | headers         |
            | #               |
            | Objective level |
            | Objective       |
            | Endpoint count  |
            | Modified        |
            | Modified by     |

    Scenario: User must be able to add a study objective as a copy from other existing studies
        And The '/studies/Study_000001/study_purpose/objectives' page is opened
        When the user select to add a study objective
        And The objective is selected from other studies
        # These can both be based on a sponsor standard template or a user denied template
        And The test study is selected to copy objective from
        And The objective is selected from selected study
        And the form is saved
        Then The added study objective is visible within the table with correct data

    Scenario: User must be able to select studies when adding study objectives from other studies

    Scenario: User must be able to select study objectives from other studies when adding study objectives from other studies

    Scenario: User must be able to add a study objective based on an existing base objective template or pre-instantiated objective template
        Given The '/studies/Study_000001/study_purpose/objectives' page is opened
        When the user select to add a study objective
        And The objective is created from existing template
        And base objective template or pre-instantiated template is selected
        And Template Parameters are selected
        And The objective level is selected 
        And the form is saved
        Then The added study objective is visible within the table with correct data

    Scenario: User must be able to select Objective Templates and Pre-Instantiated Objective Templates when study objectives are add from templates

    Scenario: User must be able to select Template Parameters when adding new study objectives from standard or user defined templates

    Scenario: User must see pre-selected template parameter values when adding new study objectives based on pre-instantiated syntax templates

    Scenario: User must be able add a study objective created from from scratch
        Given The '/studies/Study_000001/study_purpose/objectives' page is opened
        When the user select to add a study objective
        And The objective is created from scratch
        # This will become a user defined template
        And the objective template is defined
        And Template Parameters are selected
        And The objective level is selected
        And the form is saved
        Then The added study objective is visible within the table with correct data

    Scenario: User must be able to edit a study objective based on a sponsor standard objective template

    Scenario: User must be able to edit a study objective based on a user defined objective template

    Scenario: User must be able to edit the template text on a study objective based on a sponsor standard objective template

    Scenario: User must be able to edit template parameter values when editing study objectives based on standard or user defined templates

    Scenario: User must be able to reorder study objectives

    Scenario: User must be able to delete a study objective

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/study_purpose/objectives' page is opened
      When The user opens version history
      Then The user is presented with version history of the output containing timestamp and username

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/study_purpose/objectives' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames