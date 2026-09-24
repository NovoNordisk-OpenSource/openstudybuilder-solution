@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Study Activities - Updates

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study activities.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [Test Data] User must be able to prepare test data before tests
        Given [API] All Activities are deleted from selected study
    
    Scenario: [Red bell][Activity update] User must be presented with 'red bell' when activity group has been updated
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The red alert badge is not present
        And [API] Activity new version is created
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity is updated
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        Then The red alert badge is present

    Scenario: [Red bell][Activity update] User must be presented with 'red bell' when activity subgroup has been updated
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity group is created
        And [API] Activity group is approved
        And [API] Activity subgroup is created
        And [API] Activity subgroup is approved
        Given [API] Study Activity is created and approved
        And [API] Activity is added to the selected study
        And [API] Activity subgroup is created
        And [API] Activity subgroup is approved
        And [API] Activity subgroup is created
        And [API] Activity subgroup is approved
        And [API] Activity subgroup is created
        And [API] Activity subgroup is approved
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The red alert badge is not present
        And [API] Activity new version is created
        And [API] Activity subgroup in status Draft exists
        And [API] Activity subgroup is approved
        And [API] Activity is updated
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        Then The red alert badge is present

    Scenario: [Red bell][Activity update] User must be presented with 'red bell' when activity name has been updated
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The red alert badge is not present
        And [API] Activity new version is created
        And [API] Activity is updated with new name
        Given The page 'activities/list' is opened for current study
        And The Study Activity is searched for
        Then The red alert badge is present

    Scenario: [Handle update][Accept] User must be able to accept activity updates and no longer see red or yellow alert
        Given The page 'activities/list' is opened for current study
        And The Study Activity is searched for
        When The 'Update activity version' option is clicked for flagged item
        And The user accepts the changes
        And The form is no longer available
        Then The Study Activity is found
        And The yellow alert badge is not present
        And The red alert badge is not present

    Scenario: [Handle update][Decline] User must be able to decline activity updates and see that yellow alert is still present
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        And [API] Activity new version is created
        And [API] Activity is updated with new name
        Given The page 'activities/list' is opened for current study
        And The Study Activity is searched for
        When The 'Update activity version' option is clicked for flagged item
        And The user declines the changes
        Then The yellow alert badge is present

    Scenario: [Handle update][Decline] User must be presented with 'Decline' option when activity status has changed to retired
        Given [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        When [API] Activity is inactivated
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        When The 'Update activity version' option is clicked for flagged item
        Then The 'Decline and keep' button is present

    Scenario: [Red bell][Filtering] User must be able to filter by redbell status
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        And [API] Activity new version is created
        And [API] Activity is updated with new name
        Given The page 'activities/list' is opened for current study
        When The user filters the table by red alert status
        And User waits for the table
        Then The activities with red alert are present 

    Scenario: [Yellow alert][Filtering] User must be able to filter by yellow alert status
        Given The page 'activities/list' is opened for current study
        And The Study Activity is searched for
        When The 'Update activity version' option is clicked for flagged item
        And The user declines the changes
        Given The page 'activities/list' is opened for current study
        When The user filters the table by yellow alert status
        And User waits for the table
        Then The activities with yellow alert are present

    Scenario: [Bulk review][Activity visibility] User must be able to see which activity name, group and subgroup is present in detailed soa
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User search added activity in detailed SoA
        And User clicks eye icon on searched activity level
        And [API] Activity new version is created
        And [API] Activity is updated with new name
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity subgroup in status Draft exists
        And [API] Activity subgroup is approved
        And [API] Activity is updated
        Given The page 'activities/list' is opened for current study
        And The Study Activity is searched for
        And The user opens bulk review changes window
        Then The icon indicates which activity name is present in detailed soa
        And The icon indicates which activity group is present in detailed soa
        And The icon indicates which activity subgroup is present in detailed soa

    @manual_test
    Scenario: User must be able to select group when previously linked group has been removed (multiple groups assigned)
        Given [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        When The activity group is removed from that activity
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        And The user selects new activity group and accepts
        Then The the changes are applied to the activity
