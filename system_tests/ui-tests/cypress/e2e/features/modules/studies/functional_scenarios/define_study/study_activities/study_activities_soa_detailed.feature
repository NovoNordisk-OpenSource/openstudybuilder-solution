@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Schedule of Activities - Detailed

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study SoA.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to Detailed SoA page using side menu
        Given The '/studies' page is opened
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        And The 'Schedule of Activities' tab is selected
        Given The page 'activities/soa' is opened for current study

    Scenario: [Table][Complexity Score][Detailed SoA]User must be presented with complexity score for given study
        Given The page 'activities/soa' is opened for current study
        Then The complexity score presents current score for study based on existing acitvities

    @manual_test
    Scenario: User must be presented with time unit of visits the same as defined in first defined study visity
        Given The page 'activities/soa' is opened for current study
        And The test study data contains defined visits
        Then The SoA is displaying the data using correct time unit

    @smoke_test
    Scenario: [Actions][Add Activity][From Library] User must be able to add Study Activity from Detailed SoA selecting From Library
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When Action 'Add activity' is selected for first study activity
        And Activity from library is selected
        And Form continue button is clicked
        And User selects first activity available for selection
        And User selects SoA group as 'INFORMED CONSENT' for selected activity
        And Data of selected activity is saved
        And Form save button is clicked
        Then The pop up displays 'Study activity added'
        And Detailed SoA table is loaded
        And User expand table
        When User search added activity in detailed SoA
        Then The Activity is visible in the SoA

    Scenario: [Actions][Add Activity][From Study] User must be able to add Study Activity from Detailed SoA selecting From Study
        And User selects study with id 'CDISC DEV-9881'
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And User intercepts available studies request
        And Action 'Add activity' is selected for first study activity
        And Activity from studies is selected
        And User waits for available studies request
        And User selects study 'CDISC DEV-9876'
        And Form continue button is clicked
        And User selects first activity available for selection
        And Data of selected activity is saved
        And Form save button is clicked
        Then The pop up displays 'Study activity added'
        And Detailed SoA table is loaded
        And User expand table
        When User search added activity in detailed SoA
        Then The Activity is visible in the SoA

    Scenario: [Actions][Add Activity][From Study][By Acronym] User must be able to search study by acronym when adding study activity through detailed SoA
        And User selects study with id 'CDISC DEV-9881'
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And User intercepts available studies request
        And Action 'Add activity' is selected for first study activity
        And Activity from studies is selected
        And User waits for available studies request
        And User selects study 'E2E Main Test Study'
        And Form continue button is clicked
        Then User selects first activity available for selection

    Scenario: [Actions][Remove Activity] User must be able to remove Study Activity from Detailed SoA
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And The Study Activity is searched for
        When Action 'Remove Activity' is selected for first study activity
        And Action is confirmed by clicking continue
        Then The pop up displays 'Study activity removed'
        And The page is reloaded
        And The Study Activity is searched for
        And No activities are found

    @manual_test
    Scenario: User must be able to change activity grouping for given Study Activity in Detailed SoA
        Given At least '1' activites are present in the selected study
        Given The page 'activities/soa' is opened for current study
        When Action 'Remove activity' is selected for study activity 
        And The user updates the Activity Group for that Activity in Detailed SoA
        And The user updates the Activity SubGroup for that Activity in Detailed SoA
        And The user provides the rationale for activity request for that Activity in Detailed SoA
        Then The pop up snack displays 'The Study activity Aspartate Aminotransferase has been updated.'
        And The changes are visible in Detailed SoA

    Scenario: [Placeholder][Submitted] User must be able to see highlighted (yellow) submitted placeholder in the Detailed SoA
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Submitted Requested Activity
        And [API] Requested Activity is added to the study
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And User search added activity in detailed SoA
        Then Row containing submitted placeholder is highlighted with yellow color

    Scenario: [Placeholder][Not-Submitted] User must be able to see highlighted (orange) not-submitted placeholder in the Detailed SoA
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Unsubmitted Requested Activity
        And [API] Requested Activity is added to the study
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And User search added activity in detailed SoA
        Then Row containing unsubmitted placeholder is highlighted with orange color

    @manual_test
    Scenario: User must be able to add activity from different activity group than selected
        Given At least '1' activites are present in the selected study
        Given The page 'activities/soa' is opened for current study
        When The user adds an activity from different group than selected to add activity
        Then The activity is assigned to group user has selected

    Scenario: [Actions][Reordering] User must be able to enable reordering of activities in Detailed SoA
        When Activity name list is cleared
        And [API] Group and subgroup are created and approved
        And [API] All Activities are deleted from selected study
        And [API] Get SoA Group 'TRIAL MATERIAL' id
        And [API] Study Activity with prefix 'ReorderingTest_1_' based on existing group and subgroup is created and approved
        And [API] Activity is added to the selected study
        And Activity name is added to the list
        And [API] Study Activity with prefix 'ReorderingTest_2_' based on existing group and subgroup is created and approved
        And [API] Activity is added to the selected study
        And Activity name is added to the list
        And [API] Study Activity with prefix 'ReorderingTest_3_' based on existing group and subgroup is created and approved
        And [API] Activity is added to the selected study
        And Activity name is added to the list
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And User intercepts reorder activities request
        When The user enables the Reorder Activities function for acitivities in the same flowchart group
        And User waits for 2 seconds
        And The user updates the order of activities
        And User waits for 1 seconds
        And User clicks Finish reordering button
        And User waits for reorder activities request
        And Detailed SoA table is loaded
        Then The new order of activites is visible

    Scenario: [New study] User must be able to see buttons for adding new activity or visit when Study is empty
        Given The '/studies/select_or_add_study/active' page is opened
        And User waits for the table
        And The Add Study button is clicked
        When New study project id, study number and study acronym are filled in
        And Form save button is clicked
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        And The 'Schedule of Activities' tab is selected
        Then Text about no added visits and activities is displayed
        And User can click Add visit button
        Then The current URL is '/study_structure/visits'
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        And The 'Schedule of Activities' tab is selected
        And User can click Add study activity button
        Then The current URL is '/activities/list'

    @manual_test @BUG_ID:2851795
    Scenario:[Edit] User must be presented with all activity groups linked when editing the activity
        Given The page 'activities/soa' is opened for current study
        And The activity with more than one activity group exists in the table
        When The user opens the edit form for that activity
        Then The Activity group dropdown is presenting all linked activity groups

    @manual_test @BUG_ID:2844670
    Scenario:[Edit] User must be able to hide groups when activity groups has been changed
        Given The page 'activities/soa' is opened for current study
        And The activity with linked activity group is present for the study
        When The user hides that activity group
        Then The group is hidden correctly