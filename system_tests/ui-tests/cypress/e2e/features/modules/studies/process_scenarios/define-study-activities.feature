@REQ_ID:XXX
Feature: Studies - Define Study - Study Structure and Study Activities - E2E verification

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9844'

    Scenario: [Test data] Study is cleared before start of tests
        Given [API] The feature flag 'streamline_placeholder_activities' is enabled
        Given [API] All visit groups uids are fetched
        And [API] All visit groups are removed
        And [API] Study vists uids are fetched for selected study
        And [API] Study visits in selected study are cleaned-up
        And [API] All Activities fotnotes are deleted from selected study
        And [API] All Activities are deleted from selected study
        And [API] All epochs assigned to the selected study are fetched
        And [API] All epochs assigned to the selected study are deleted
        Given User selects study with id 'CDISC DEV-9879'
        And [API] All Activities fotnotes are deleted from selected study
        Given [API] All Activities are deleted from selected study
        And [API] Get SoA Group 'GENETICS' id
        And [API] Get class uid for activity instance creation
        And [API] Group and subgroup are created and approved to be used for activity creation
        And [API] Activity with data collection set to 1 and 'E2E_FirstActivity' included in the name is created and approved
        And [API] Activity is added to the selected study
        And [API] Activity with data collection set to 1 and 'E2E_SecondActivity' included in the name is created and approved
        And [API] Activity is added to the selected study
        And [API] Footnote with text 'My other footnote' is added to the selected study

    Scenario: [Epochs] User must be able to define epochs Screening, type Pre treatment, Treatment, type Treatment, Follow-up, type Post treatment on selected study
        Given The page 'study_structure/epochs' is opened for current study
        When User click create epoch button
        And User continues to next step of study structure stepper
        And User waits for 1 seconds
        And User sets epoch 'type' as 'Pre Treatment'
        And User sets epoch 'subtype' as 'Screening'
        And User sets epoch description
        And User intercepts epochs data
        And User continues to next step of study structure stepper
        And User waits for epochs data
        When The form is no longer available
        And Study Epoch is found
        Then The added Epoch name, type 'Pre Treatment' and subtype 'Screening' is visible in the table
        When User click create epoch button
        And User continues to next step of study structure stepper
        And User waits for 1 seconds
        And User sets epoch 'type' as 'Treatment'
        And User sets epoch 'subtype' as 'Treatment'
        And User sets epoch description
        And User intercepts epochs data
        And User continues to next step of study structure stepper
        And User waits for epochs data
        When The form is no longer available
        And Study Epoch is found
        Then The added Epoch name, type 'Treatment' and subtype 'Treatment' is visible in the table
        When User click create epoch button
        And User continues to next step of study structure stepper
        And User waits for 1 seconds
        And User sets epoch 'type' as 'Post Treatment'
        And User sets epoch 'subtype' as 'Follow-Up'
        And User sets epoch description
        And User intercepts epochs data
        And User continues to next step of study structure stepper
        And User waits for epochs data
        When The form is no longer available
        And Study Epoch is found
        Then The added Epoch name, type 'Post Treatment' and subtype 'Follow-Up' is visible in the table

    Scenario: [Visit][V0] User must be able to define scheduled visit V0 connected to Screening epoch
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Screening' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Information'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Global anchor visit'
        And Time unit 'weeks' is selected for the visit
        And Visit timing -2 is selected for the visit
        And User intercepts create visit request
        When Form save button is clicked
        Then The study visit is created
        And User searches for 'V0'
        And Study visit class is 'Scheduled visit' and the timing is '-2 weeks'

    Scenario:[Visit][V1][Global Anchor] User must be able to define one scheduled visit V1 that will be a global anchor connected to the Treatment epoch
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Treatment' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Randomisation'
        And Contact mode is selected as 'On Site Visit'
        And Time unit 'weeks' is selected for the visit
        And Anchor visit checkbox is checked
        And User intercepts create visit request
        When Form save button is clicked
        Then The study visit is created
        And User searches for 'V1'
        And Study visit class is 'Scheduled visit' and the timing is '0 weeks'
    
    Scenario: [Visit][V1] User must be able to add additional visit between existing V0 and V1
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Screening' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Screening'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Global anchor visit'
        And Time unit 'weeks' is selected for the visit
        And Visit timing -1 is selected for the visit
        And User intercepts create visit request
        When Form save button is clicked
        Then The study visit is created
        And User searches for 'V1'
        And Study visit class is 'Scheduled visit' and the timing is '-1 weeks'
        And User searches for 'V2'
        And Study visit class is 'Scheduled visit' and the timing is '0 weeks'

    Scenario: [Visit][V3][V4] User must be able to define two scheduled visits V3 and V4 connected to the Treatment epoch
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Treatment' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Treatment'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Global anchor visit'
        And Time unit 'weeks' is selected for the visit
        And Visit timing 1 is selected for the visit
        And User intercepts create visit request
        When Form save button is clicked
        Then The study visit is created
        And User searches for 'V3' 
        And Study visit class is 'Scheduled visit' and the timing is '1 weeks'
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Treatment' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Treatment'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Global anchor visit'
        And Time unit 'weeks' is selected for the visit
        And Visit timing 2 is selected for the visit
        And User intercepts create visit request
        When Form save button is clicked
        Then The study visit is created
        And User searches for 'V4'
        And Study visit class is 'Scheduled visit' and the timing is '2 weeks'

    Scenario: [Visit][V4X] User must be able to define special visit V4X in reference to Vist V4
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Visit scheduling type is selected as 'SPECIAL_VISIT'
        And Form continue button is clicked
        And Epoch 'Treatment' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Early discontinuation'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Visit 4'
        And Form save button is clicked
        And The pop up displays 'Visit added'
        And User searches for 'V4X'
        And Study visit class is 'Special visit' and the timing is ''

    Scenario: [Visit][V5] User must be able to define scheduled visit V5 connected to Follow-up epoch
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Follow-Up' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'End of trial'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Global anchor visit'
        And Time unit 'weeks' is selected for the visit
        And Visit timing 3 is selected for the visit
        And User intercepts create visit request
        When Form save button is clicked
        Then The study visit is created
        And User searches for 'V5'
        And Study visit class is 'Scheduled visit' and the timing is '3 weeks'

    Scenario: [Visit][V3B] User must be able to add manually defined visit between V3 and V4
        Given User intercepts epochs data
        Given User intercepts epochs codelists request
        When The page 'study_structure/visits' is opened for current study
        And User waits for epochs codelists request
        And User waits for epochs data
        When Add visit button is clicked
        And Visit scheduling type is selected as 'MANUALLY_DEFINED_VISIT'
        And Form continue button is clicked
        And Epoch 'Treatment' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Treatment'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Global anchor visit'
        And Time unit 'weeks' is selected for the visit
        And Visit timing 1 is selected for the visit
        And Visit name is set to 'Visit 3B'
        And Visit short name is set to 'V3B'
        And Visit number is set to '3.01'
        And Visit unique number is set to 301
        And Form save button is clicked
        And The pop up displays 'Visit added'
        And User searches for 'V3B'
        And Study visit class is 'Manually defined visit' and the timing is '1 weeks'
        And User searches for 'V4'
        And Study visit class is 'Scheduled visit' and the timing is '2 weeks'
        And User searches for 'V4X'
        And Study visit class is 'Special visit' and the timing is ''
        And User searches for 'V5'
        And Study visit class is 'Scheduled visit' and the timing is '3 weeks'

    Scenario: [Add][Activity][From Library] User must be able to add from list view two Activities to the study from Library
        Given The page 'activities/list' is opened for current study
        When Study activity add button is clicked
        And Activity from library is selected
        And Form continue button is clicked
        And The Study Activity with name 'Albumin' is searched for
        And Activity row containing 'Biochemistry' is selected
        And SoA group 'EFFICACY' is selected for activity row containing 'Biochemistry'
        And The Study Activity creation search field is cleared
        And The Study Activity with name 'Weight' is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'BIOMARKERS' for first matching activity
        And Form save button is clicked
        And The form is no longer available
        And User searches for 'Albumin'
        Then Only one row is present
        And User searches for 'Weight'
        Then Only one row is present

    Scenario: [Add][Activity][From Library] User must be able to add from detailed soa view one Activities to the study from Library
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And Action 'Add activity' is selected for activity 'Albumin'
        And Activity from library is selected
        And Form continue button is clicked
        And The Study Activity with name 'Alanine Aminotransferase' is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'EFFICACY' for first matching activity
        And Form save button is clicked
        Given The page 'activities/list' is opened for current study
        And User searches for 'Alanine Aminotransferase'
        Then Only one row is present

    Scenario: [Add][Activity][From Studies] User must be able to add from list view two Activities to the study fron another Study
        Given The page 'activities/list' is opened for current study
        When Study activity add button is clicked
        And Activity from studies is selected
        And User selects study 'CDISC DEV-9879'
        And Form continue button is clicked
        And The Study Activity with name 'E2E_FirstActivity' is searched for
        And The first matching activity is selected
        And The Study Activity creation search field is cleared
        And The Study Activity with name 'E2E_SecondActivity' is searched for
        And The first matching activity is selected
        And Form save button is clicked
        And The form is no longer available
        And User searches for 'E2E_FirstActivity'
        Then Only one row is present
        And User searches for 'E2E_SecondActivity'
        Then Only one row is present

    Scenario: [Add][Placeholder] User must be able to add two Activity placeholders
        Given The page 'activities/list' is opened for current study
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        And User sets Activity Placeholder name with 'E2E_placeholder_'
        And User selects Activity SoA group as 'EFFICACY'
        And User selects first group for placeholder
        And User selects first subgroup for placeholder
        And User sets Activity rationale
        And Form save button is clicked
        And The form is no longer available
        And User searches for 'E2E_placeholder_'
        Then Only one row is present
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        And User sets Activity Placeholder name with 'E2E_placeholder_2_'
        And User selects Activity SoA group as 'EFFICACY'
        And User selects first group for placeholder
        And User selects first subgroup for placeholder
        And User sets Activity rationale
        And Form save button is clicked
        And The form is no longer available
        And User searches for 'E2E_placeholder_2_'
        Then Only one row is present

    Scenario: [Visibility][Activity] User must be able to see that by default the added Activities are hidden and it can be changed in the detailed soa
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And The activity 'Albumin' visibility is set to hidden
        And The activity 'Weight' visibility is set to hidden
        And The activity 'Alanine Aminotransferase' visibility is set to hidden
        And The activity 'E2E_FirstActivity' visibility is set to hidden
        And The activity 'E2E_SecondActivity' visibility is set to hidden
        And The activity 'E2E_placeholder_' visibility is set to hidden
        And User switches to the 'protocol' view
        And Activity 'Albumin' is not visible in the protocol SoA
        And Activity 'Weight' is not visible in the protocol SoA
        And Activity 'Alanine Aminotransferase' is not visible in the protocol SoA
        And Activity 'E2E_FirstActivity' is not visible in the protocol SoA
        And Activity 'E2E_SecondActivity' is not visible in the protocol SoA
        And Activity 'E2E_placeholder_' is not visible in the protocol SoA
        And User switches to the 'detailed' view
        And User clicks eye icon on activity 'Albumin' level
        And User clicks eye icon on activity 'Weight' level
        And User clicks eye icon on activity 'Alanine Aminotransferase' level
        And User clicks eye icon on activity 'E2E_FirstActivity' level
        And User clicks eye icon on activity 'E2E_SecondActivity' level
        And User clicks eye icon on activity 'E2E_placeholder_' level
        And User clicks eye icon on activity 'E2E_placeholder_2_' level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        And Activity 'Albumin' is visible in the protocol SoA
        And Activity 'Weight' is visible in the protocol SoA
        And Activity 'Alanine Aminotransferase' is visible in the protocol SoA
        And Activity 'E2E_FirstActivity' is visible in the protocol SoA
        And Activity 'E2E_SecondActivity' is visible in the protocol SoA
        And Placeholder 'E2E_placeholder_' is visible in the protocol SoA
        And Placeholder 'E2E_placeholder_2_' is visible in the protocol SoA

    Scenario: [Visit assignment][Activity] User must be able to assign each activity to at least one visit
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User assign activity 'Albumin' to visit 'V0'
        And User assign activity 'Albumin' to visit 'V1'
        And User assign activity 'Weight' to visit 'V2'
        And User assign activity 'Weight' to visit 'V5'
        And User assign activity 'Alanine Aminotransferase' to visit 'V5'
        And User assign activity 'E2E_placeholder_' to visit 'V1'
        And User assign activity 'E2E_placeholder_' to visit 'V2'
        And User assign activity 'E2E_placeholder_2_' to visit 'V4'
        And User assign activity 'E2E_FirstActivity' to visit 'V1'
        And User assign activity 'E2E_FirstActivity' to visit 'V3'
        And User assign activity 'E2E_FirstActivity' to visit 'V3B'
        And User assign activity 'E2E_SecondActivity' to visit 'V4'
        And User assign activity 'E2E_SecondActivity' to visit 'V4X'
        And User assign activity 'E2E_SecondActivity' to visit 'V5'
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        Then User confirms activity 'Albumin' is assigned to visit 'V0'
        And User confirms activity 'Albumin' is assigned to visit 'V1'
        And User confirms activity 'Weight' is assigned to visit 'V2'
        And User confirms activity 'Weight' is assigned to visit 'V5'
        And User confirms activity 'Alanine Aminotransferase' is assigned to visit 'V5'
        And User confirms activity placeholder 'E2E_placeholder_' is assigned to visit 'V1'
        And User confirms activity placeholder 'E2E_placeholder_' is assigned to visit 'V2'
        And User confirms activity placeholder 'E2E_placeholder_2_' is assigned to visit 'V4'
        And User confirms activity 'E2E_FirstActivity' is assigned to visit 'V1'
        And User confirms activity 'E2E_FirstActivity' is assigned to visit 'V3'
        And User confirms activity 'E2E_FirstActivity' is assigned to visit 'V3B'
        And User confirms activity 'E2E_SecondActivity' is assigned to visit 'V4'
        And User confirms activity 'E2E_SecondActivity' is assigned to visit 'V4X'
        And User confirms activity 'E2E_SecondActivity' is assigned to visit 'V5'

    Scenario: [Exchange][Activity] User must be able to exchange an activity from Detailed SoA view, keeping the visits assignment
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And Action 'Exchange Activity' is selected for activity 'Weight'
        And Form continue button is clicked
        When The Study Activity with name 'Cause of Death' is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'BIOMARKERS' for first matching activity
        And Form save button is clicked
        And The form is no longer available
        And User waits for 1 seconds
        And User clicks eye icon on activity 'Cause of Death' level
        And User switches to the 'protocol' view
        Then User confirms activity 'Cause of Death' is assigned to visit 'V2'
        And User confirms activity 'Cause of Death' is assigned to visit 'V5'

    Scenario: [Exchange][Placeholder] User must be able to exchange an activity placeholder with two activities from Detailed SoA view, keeping the visits assigment
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And Action 'Exchange Activity' is selected for activity 'E2E_placeholder_2_'
        And Form continue button is clicked
        When The Study Activity with name 'Adverse Event' is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'REMINDERS' for first matching activity
        And The Study Activity creation search field is cleared
        When The Study Activity with name 'End of Study' is searched for
        And The first matching activity is selected
        And User sets SoA Group as 'REMINDERS' for first matching activity
        And Form save button is clicked
        And The form is no longer available
        And User waits for 1 seconds
        And User clicks eye icon on activity 'Adverse Event' level
        And User clicks eye icon on activity 'End of Study' level
        And User switches to the 'protocol' view
        Then User confirms activity 'Adverse Event' is assigned to visit 'V1'
        And User confirms activity 'Adverse Event' is assigned to visit 'V2'
        And User confirms activity 'End of Study' is assigned to visit 'V1'
        And User confirms activity 'End of Study' is assigned to visit 'V2'

    Scenario: [Edit][Activity] User must be able to edit the activity from activities list (including soa group and group and subgroup if multiple groupings are available)
        Given The page 'activities/list' is opened for current study
        And User searches for 'Albumin'
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        When User edits Activity SoA group to 'ELIGIBILITY AND OTHER CRITERIA'
        And User waits for 1 seconds
        And The activity group is edited to 'AE Requiring Additional Data'
        And The activity subgroup is edited to 'Laboratory Assessment'
        And User is not allowed to edit activity Library field
        And User is not allowed to edit activity 'Albumin' field
        And Modal window 'Save' button is clicked
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        Then Activity 'Albumin' is visible under subgroup 'Laboratory Assessment', group 'AE Requiring Additional Data' and soa group 'ELIGIBILITY AND OTHER CRITERIA'

    Scenario: [Edit][Activity] User must be able to edit the activity from detailed SoA (including soa group and group and subgroup if multiple groupings are available)
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And Action 'Edit Activity' is selected for activity 'Albumin'
        And User waits for 1 seconds
        When User edits Activity SoA group to 'GENETICS'
        And User waits for 1 seconds
        And The activity group is edited to 'Laboratory Assessments'
        And The activity subgroup is edited to 'Biochemistry'
        And User is not allowed to edit activity Library field
        And User is not allowed to edit activity 'Albumin' field
        And Modal window 'Save' button is clicked
        And Detailed SoA table is loaded
        And User expand table
        Then Activity 'Albumin' is visible under subgroup 'Biochemistry', group 'Laboratory Assessments' and soa group 'GENETICS'

    Scenario: [Edit][Placeholder] User must be able to edit the placeholder from detailed SoA (including group, subgroup, name, soa group)
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And Action 'Edit Activity' is selected for activity 'E2E_placeholder_'
        And User waits for 1 seconds
        When User edits Activity SoA group to 'GENETICS'
        And User waits for 1 seconds
        And The activity group is edited to 'Laboratory Assessments'
        And The activity subgroup is edited to 'Biochemistry'
        And User change placeholder name to 'New_E2E_placeholder_'
        And Modal window 'Save' button is clicked
        And Detailed SoA table is loaded
        And User expand table
        Then Activity 'New_E2E_placeholder_' is visible under subgroup 'Biochemistry', group 'Laboratory Assessments' and soa group 'GENETICS'

    Scenario: [Edit][Activity][Red bell handling] User must be able to see the red bell notification next to edited activities
        Given The page 'activities/list' is opened for current study 
        And User searches for 'E2E_FirstActivity'
        When User gets full activity name starting with 'E2E_FirstActivity'
        Given The '/library/activities/activities' page is opened
        And The Study Activity is searched for
        When The 'New version' option is clicked from the three dot menu list
        Then The pop up displays 'New version created'
        And User sets status filter to 'draft'
        When The 'Edit' option is clicked from the three dot menu list
        And The activity name is updated
        And User edits activity group to 'General'
        And User edits activity subgroup to 'Lipids'
        And User fills in the reason for change
        And Form save button is clicked
        When The 'Approve' option is clicked from the three dot menu list
        Given The page 'activities/list' is opened for current study 
        And User searches for 'E2E_SecondActivity'
        When User gets full activity name starting with 'E2E_SecondActivity'
        Given The '/library/activities/activities' page is opened
        And The Study Activity is searched for
        When The 'Inactivate' option is clicked from the three dot menu list
        Given The page 'activities/list' is opened for current study
        When The user filters the table by red alert status
        And Table contains value 'E2E_FirstActivity'
        And Table contains value 'E2E_SecondActivity'
        When User searches for 'E2E_FirstActivity'
        Then The red alert badge is present
        When User searches for 'E2E_SecondActivity'
        Then The red alert badge is present

    Scenario: [Edit][Activity][Red bell handling] User must be able to accept changes for first activity and decline them for the second activity
        Given The page 'activities/list' is opened for current study 
        And The user opens bulk review changes window
        Then The activity 'E2E_FirstActivity' is displayed as changed with new 'name' value from 'E2E_FirstActivity' to 'Update E2E_FirstActivity'
        And The activity 'E2E_FirstActivity' is displayed as changed with new 'group' value from 'API_Group' to 'General'
        And The activity 'E2E_FirstActivity' is displayed as changed with new 'subgroup' value from 'API_SubGroup' to 'Lipids'
        Then The activity 'E2E_SecondActivity' is displayed as changed with new 'status' value from 'Final' to 'Retired'
        And The action 'Accept' is clicked for activity 'E2E_FirstActivity'
        And The action 'Decline' is clicked for activity 'E2E_SecondActivity'
        And Action is confirmed by clicking save
        And Action is confirmed by clicking continue
        And User searches for 'Update E2E_FirstActivity'
        Then The red alert badge is not present
        And The yellow alert badge is not present
        And Table contains value 'Update E2E_FirstActivity'
        And The Study Activity Group is displayed as 'General' in the table
        And The Study Activity Subgroup is displayed as 'Lipids' in the table
        And User searches for 'E2E_SecondActivity'
        And The yellow alert badge is present

    Scenario: [Remove][Activity] User must be able to remove the activity from the detailed soa level
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And Action 'Remove Activity' is selected for activity 'Alanine Aminotransferase'
        And Action is confirmed by clicking continue
        Then The pop up displays 'Study activity removed'
        And The page is reloaded
        And The Study Activity is searched for
        And No activities are found

    Scenario: [Footnotes][From Scratch][Link] User must be able to define new footnote and link it to two existing visits
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And User clicks plus icon to initate adding a footnote
        And User clicks plus icon in the activity 'Adverse Event' row for visit 'V2'
        And User clicks plus icon in the activity 'E2E_SecondActivity' row for visit 'V4X'
        When The button with text 'Continue' is clicked
        And User selects to create a footnote from scratch
        And Form continue button is clicked
        And User sets the footnote value 'My First footnote'
        And Form continue button is clicked
        And Footnote value 'My First footnote' is displayed in last step of footnote definition
        And Form save button is clicked
        Then Added footnote 'My First footnote' is visible in the table, including index 'a'
        And Footnote 'My First footnote' linkage to 'Adverse Event V2' is visible in the footnotes table
        And Footnote 'My First footnote' linkage to 'E2E_SecondActivity' is visible in the footnotes table
        And Footnote 'My First footnote' linkage to 'V4X' is visible in the footnotes table
        And Footnote index 'a' is visible in the detaied SoA next to activity 'Adverse Event' visit 'V2'
        And Footnote index 'a' is visible in the detaied SoA next to activity 'E2E_SecondActivity' visit 'V4X'
        And User switches to the 'protocol' view
        And Footnote index 'a' has footnote text 'My First footnote' displayed on the protocol page
        And Footnote index 'a' is assgined to visit 'V2' for activity 'Adverse Event'
        And Footnote index 'a' is assgined to visit 'V4X' for activity 'E2E_SecondActivity'

    Scenario: [Footnotes][From Studies][Link] User must be able to add footnote from another studies and link it to one existing visit
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And User clicks plus icon to initate adding a footnote
        And User clicks plus icon in the activity 'Adverse Event' row for visit 'V2'
        When The button with text 'Continue' is clicked
        And User selects to add a footnote from existing study
        And User selects study 'CDISC DEV-9879'
        And Form continue button is clicked
        And Footnote 'My other footnote' is copied
        And Form save button is clicked
        Then Added footnote 'My other footnote' is visible in the table, including index 'b'
        And Footnote 'My other footnote' linkage to 'Adverse Event V2' is visible in the footnotes table
        And Footnote index 'a, b' is visible in the detaied SoA next to activity 'Adverse Event' visit 'V2'
        And User switches to the 'protocol' view
        And Footnote index 'b' has footnote text 'My other footnote' displayed on the protocol page
        And Footnote index 'a' is assgined to visit 'V2' for activity 'Adverse Event'
        And Footnote index 'b' is assgined to visit 'V2' for activity 'Adverse Event'

    Scenario: [Footnotes][Existing][Link] User must be able to link existing footnote to the one of the activity
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And Action 'Link/Unlink Footnote' is selected for footnote 'My other footnote'
        And User clicks plus icon in the activity 'Update E2E_FirstActivity'
        When The button with text 'Save linking' is clicked
        And User waits for 1 seconds
        And Footnote 'My other footnote' linkage to 'Adverse Event V2' is visible in the footnotes table
        And Footnote 'My other footnote' linkage to 'Update E2E_FirstActivity' is visible in the footnotes table
        And Footnote index 'b' is visible in the detaied SoA next to activity 'Update E2E_FirstActivity'
        And User switches to the 'protocol' view
        And Footnote index 'b' has footnote text 'My other footnote' displayed on the protocol page
        And Footnote index 'b' is assgined to activity 'Update E2E_FirstActivity'
        And Footnote index 'b' is assgined to visit 'V2' for activity 'Adverse Event'

    Scenario: [Footnotes][Existing][Unlink] User must be able to unlink footnote from the visit
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And Action 'Link/Unlink Footnote' is selected for footnote 'My other footnote'
        And User clicks minus icon in the activity 'Update E2E_FirstActivity'
        When The button with text 'Save linking' is clicked
        And User waits for 1 seconds
        And Footnote 'My other footnote' linkage to 'Adverse Event V2' is visible in the footnotes table
        And Footnote 'My other footnote' linkage to 'Update E2E_FirstActivity' is not visible in the footnotes table
        And Footnote is not linked in the detaied SoA to activity 'Update E2E_FirstActivity'
        And User switches to the 'protocol' view
        And Footnote index 'b' has footnote text 'My other footnote' displayed on the protocol page
        And Footnote index 'b' is not assgined to activity 'Update E2E_FirstActivity'
        And Footnote index 'b' is assgined to visit 'V2' for activity 'Adverse Event'

    Scenario: [Footnotes][Remove] User must be able to remove the footnote that is already linked
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And Action 'Remove Footnote' is selected for footnote 'My other footnote'
        And Action is confirmed by clicking continue
        Then Footnote 'My other footnote' is no longer available in the footnote table
        And User switches to the 'protocol' view
        And Footnote 'My other footnote' is no longer available on the protocol page

    #Scenario: User must be able to see that the detailed SoA is reflected in the Protocol view
