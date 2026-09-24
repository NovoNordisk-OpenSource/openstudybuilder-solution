@REQ_ID:XXXX
Feature: Administration - Data Completeness Tags
	Background: User must be logged in
		Given The user is logged in

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the Data Completeness Tags page
        Given The '/administration/global-preferences' page is opened
        When The 'Data Completeness Tags' button is clicked
        Then The current URL is '/administration/data-completeness-tags'

    @smoke_test
    Scenario: [Create] User must be able to create a new tag
        And The '/administration/data-completeness-tags' page is opened
        And The user provides new completness tag into the text field
        And The user clicks save button
        Then The data completness tag is created

    Scenario: [Update] User must be able to set a tag to complete
        When User selects study with id 'CDISC DEV-8014'
        And The data completness tag in uncompleted state exists
        And The '/administration/data-completeness-tags' page is opened
        When The user sets the tag to completed for study
        And The '/studies/select_or_add_study/active' page is opened
        Then The data completness tag is visible on study list level for selected study

    Scenario: [Update] User must be able to set a tag to uncompleted
        When User selects study with id 'CDISC DEV-8015'
        And The '/administration/data-completeness-tags' page is opened
        Given The data completness tag in completed state exists for the study
        When The user sets the tag to uncompleted for the study
        And The '/studies/select_or_add_study/active' page is opened
        Then The data completness tag is not on study list level for selected study
    
    Scenario: [Multiple create] User must be able to complete mutliple tags for single study
        When User selects study with id 'CDISC DEV-8016'
        And The '/administration/data-completeness-tags' page is opened
        And The user creates multiple completion tags
        And The user sets multiple tags to completed for selected study
        And The '/studies/select_or_add_study/active' page is opened
        Then All the completed tags are visible for the study        