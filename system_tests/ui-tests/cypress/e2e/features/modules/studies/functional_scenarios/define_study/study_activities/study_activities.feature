@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Study Activities - Basic Scope

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study activities.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to Study Activity page using side menu
        And User selects study with id 'CDISC DEV-9876'
        And The '/studies' page is opened
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        Then The current URL is '/activities/soa'

    @smoke_test
    Scenario: [Add][From Study] User must be able to add a Study Activity from an existing study
        And User selects study with id 'CDISC DEV-9881'
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        And User selects study with id 'CDISC DEV-9876'
        Given The page 'activities/list' is opened for current study
        And User intercepts available studies request
        When Study activity add button is clicked
        And Activity from studies is selected
        And User waits for available studies request
        And User selects study 'Empty study'
        And Form continue button is clicked
        And User selects first activity available for selection
        And Data of selected activity is saved
        And SoA group assigned to the selected activity is saved
        And Form save button is clicked
        Then The pop up displays 'Study activity added'
        And The Study Activity is found
        Then The Study Activity name, group and subgroup are visible in table
        And The Study Activity Library is displayed as 'Sponsor' in the table

    @smoke_test
    Scenario: [Add][From Library] User must be able to add a Study Activity from the library
        Given The page 'activities/list' is opened for current study
        When Study activity add button is clicked
        And Activity from library is selected
        And Form continue button is clicked
        And User selects first activity available for selection
        And User selects SoA group as 'INFORMED CONSENT' for selected activity
        And Data of selected activity is saved
        And Form save button is clicked
        Then The pop up displays 'Study activity added'
        And The Study Activity is found
        Then The Study Activity name, group and subgroup are visible in table
        And The Study Activity SoA Group is displayed as 'INFORMED CONSENT' in the table
        And The Study Activity Library is displayed as 'Sponsor' in the table

    Scenario: [Actions][Delete][Activity] User must be able to delete a Study Activity
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        Given The page 'activities/list' is opened for current study
        And Activity is searched for and found
        When The 'Remove Activity' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        Then Activity is searched for and not found

    Scenario: [Actions][Edit][version 0.1][Activity] User must be able to edit a Study Activity
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        Given The page 'activities/list' is opened for current study
        And Activity is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And User edits Activity SoA group to 'EFFICACY'
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And Activity is searched for and found
        Then The Study Activity SoA Group is displayed as 'EFFICACY' in the table

    Scenario: [Fields Validation][From Study] User must not be able to create Study Activity from studies without study selected
        Given The page 'activities/list' is opened for current study
        When Study activity add button is clicked
        When Activity from studies is selected
        And Form continue button is clicked
        Then The validation appears and Create Activity form stays on Study Selection

    Scenario: [Fields Validation][From Study] User must be able to select existing study by its id when adding study activity
        Given The page 'activities/list' is opened for current study
        And User intercepts available studies request
        When Study activity add button is clicked
        And Activity from studies is selected
        And User waits for available studies request
        And User selects study 'CDISC DEV-9881'
        And Form continue button is clicked
        Then User selects first activity available for selection

    Scenario: [Fields Validation][From Study] User must be able to select existing study by its acronym when adding study activity
        Given The page 'activities/list' is opened for current study
        And User intercepts available studies request
        When Study activity add button is clicked
        And Activity from studies is selected
        And User waits for available studies request
        And User selects study 'Empty study'
        And Form continue button is clicked
        Then User selects first activity available for selection

    Scenario: [Fields Validation][From Library] User must not be able to create Study Activity from library without SoA group selected
        Given The page 'activities/list' is opened for current study
        When Study activity add button is clicked
        When Activity from library is selected
        And Form continue button is clicked
        And User selects first activity available for selection
        And Form save button is clicked
        Then The validation appears and Create Activity form stays on SoA group selection

    Scenario: [Actions][Approve] User must be able to add newly created approved Activity
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'BIOMARKERS' id
        And [API] Activity is added to the selected study
        Given The page 'activities/list' is opened for current study
        Then The Study Activity is found

    Scenario: [Add][Negative case][Draft Activity] User must mot be able to add newly created draft Activity
        Given The page 'activities/list' is opened for current study
        And [API] Study Activity is created and not approved
        When Study activity add button is clicked
        And Activity from library is selected
        And Form continue button is clicked
        When User searches for activity created via API
        Then The Activity in Draft status is not found

    Scenario: [Add][Negative case][Retired Group]  User must not be able to add activity that has Retired group
        Given The page 'activities/list' is opened for current study
        And [API] Study Activity is created and group is inactivated
        When Study activity add button is clicked
        And Activity from library is selected
        And Form continue button is clicked
        And The table is loaded
        And User searches for activity created via API
        And The table is loaded
        And The first matching activity is selected
        And User selects Activity SoA group as 'INFORMED CONSENT'
        And Form save button is clicked
        Then Warning that 'Retired' 'groups' can not be added to the study is displayed
        And The form is not closed
        
    Scenario: [Add][Negative case][Retired Subgroup] User must not be able to add activity that has Retired subgroup
        Given The page 'activities/list' is opened for current study
        And [API] Study Activity is created and subgroup is inactivated
        When Study activity add button is clicked
        And Activity from library is selected
        And Form continue button is clicked
        And The table is loaded
        And User searches for activity created via API
        And The table is loaded
        And The first matching activity is selected
        And User selects Activity SoA group as 'INFORMED CONSENT'
        And Form save button is clicked
        Then Warning that 'Retired' 'subgroups' can not be added to the study is displayed
        And The form is not closed
