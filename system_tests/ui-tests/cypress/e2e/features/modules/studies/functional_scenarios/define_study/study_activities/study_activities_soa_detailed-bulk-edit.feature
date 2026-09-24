@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Schedule of Activities - Detailed - Bulk Edit

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study SoA.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [TestData] User creates data for Bulk scenarios
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And Activity name is added to the list
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And Activity name is added to the list

    Scenario: [Bulk][Edit] User must be able to open bulk edit activities form on Detailed SoA
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User search for 0 activity on the list
        And Activity checkbox is checked for 0 activity on the list
        And The user selects 'Bulk Edit Activities' action after clicking Bulk actions
        Then The bulk edit view is presented to user allowing to update Activity Group and Visits for selected activities

    Scenario: [Bulk][Mandory fields] User must not be able to bulk edit without selecting Activity Group and Visit
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User search for 0 activity on the list
        And Activity checkbox is checked for 0 activity on the list
        And The user selects 'Bulk Edit Activities' action after clicking Bulk actions
        And Form save button is clicked
        Then The validation appears for Activity Group field in bulk edit form

    Scenario: [Bulk][Delete] User must be able to bulk delete activities on Detailed SoA
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User search for 0 activity on the list
        And Activity checkbox is checked for 0 activity on the list
        And The user selects 'Bulk Remove Activities' action after clicking Bulk actions
        When Batch request is intercepted
        And Action is confirmed by clicking continue
        Then The activities are removed from the study
        
    @manual_test @pending_implementation 
    Scenario: User must be able to bulk edit activities on Detailed SoA
        Given At least '2' activites are present in the selected study
        Given The page 'activities/soa' is opened for current study
        When The user edits activities in bulk
        And User intercepts bulk edit request
        And Action is confirmed by clicking save
        Then The data for bulk edited activities is updated

    @manual_test @pending_implementation 
    Scenario: User must be able to remove selection of activity on the form for bulk edit in Detailed SoA
        Given At least '2' activites are present in the selected study
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User search study activity
        And Activity checkbox is checked for 0 activity on the list
        And The user selects 'Bulk Edit Activities' action after clicking Bulk actions
        And The user removes selection of one of Activities on the form
        Then The selection disappears from the form
        