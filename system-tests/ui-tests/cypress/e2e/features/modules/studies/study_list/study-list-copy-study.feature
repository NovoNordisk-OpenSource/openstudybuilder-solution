@REQ_ID:987736
Feature: Studies - Study List of Create Study from Existing Study

    As a user, I want to verify that I can create a new study from an existing study in the Study List page and the data is copied correctly.

    Background: User must be logged in
        Given The user is logged in

    @manual_test
    Scenario: User must be able to add a new study from an existing study (positive case)
        Given The '/studies/select_or_add_study/active' page is opened
        When I clicked on the Add button
        Then The Add Study from Existing Study page is displayed
        When I select the "Create a study from an existing study" option
        Then The Copy Study page is displayed
        When I fill in project ID, study number and study acronym fields with data
        And I click on the CONTINUE button
        Then The "Select what to copy" page is displayed
        When I select the study ID from the dropdown list
        Then The "Preview of study" panel for the selected study is displayed
        And The "What to you want to copy?" section is displayed
        And The section should include "Arms", "Cohorts", "Elements", and "Epochs" categories
        When I select "Arms" category
        Then The sub-category "Branchs" is visible
        When I select "Branchs" sub-category
        And I select "Epochs" category
        Then The sub-part "Include footnotes" is displayed
        And The sub-catogory "Study visits" is visible
        When I select the sub-part "Include footnotes" under the "Epochs"
        And I select "Study visits"
        Then The sub-part "Include footnotes" is displayed
        When I select the sub-part "Include footnotes" under the "Study Visits"
        And I select "Cohorts" and "Elements" categories
        Then The "Design matrix" option is displayed
        When I select "Design matrix" option
        And I click on the SAVE button
        Then The new study is created successfully
        And The study is visible within the table

    @manual_test
    Scenario: User must be able to add a new Study from an existing Study without selecting any options (negative case)
        Given The '/studies/select_or_add_study/active' page is opened
        When I clicked on the Add button
        Then The Add Study from Existing Study dialog is displayed
        When I select the "Create a study from an existing study" option
        Then The Copy Study page is displayed
        When I fill in project ID, study number and study acronym fields with data
        And I click on the CONTINUE button
        Then The "Select what to copy" page is displayed
        When I pick up the study ID from the dropdown list
        Then The "Preview of study" panel for the selected study is displayed
        And The "What to you want to copy?" section is displayed
        And It must include "Arms", "Cohorts", "Elements", and "Epochs" categories
        When I do not select any categories
        And I click on the SAVE button
        Then The new study is created successfully
        And The study is visible within the table

    @manual_test
    Scenario: The "Design matrix" option will not display when do not select "Branchs" sub-category
        Given The '/studies/select_or_add_study/active' page is opened
        When I select the option of creating a new study from an existing study and fill in all mandatory data
        And I pick up the study ID from the dropdown list
        Then The "What to you want to copy?" section is displayed
        When I select "Arms" and do not select the sub-category "Branchs"
        And I select "Cohorts", "Elements", and "Epochs" categories
        Then The "Design matrix" option will not displayed




    



