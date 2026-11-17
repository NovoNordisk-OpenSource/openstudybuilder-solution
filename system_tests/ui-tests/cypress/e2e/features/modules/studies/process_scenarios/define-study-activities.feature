@REQ_ID:3679901

Feature: Studies - Define Study - Study Structure and Study Activities - E2E verification

         As a user taking part in study specification for protocol authoring,
         I must be able to define:
         - Study epochs
         - Study visits
         - Study activities
         - Request activities as placeholders
         - Study SoA
         - Footnotes for SoA
         So structured study metadata specification can enable a more automated clinical system setup and downstream digital dataflow.

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

    Scenario: [Epochs] User must be able to define epochs Screening, type Pre treatment, Treatment, type Treatment, Follow-up, type Post treatment, Basic, No treatment on selected study
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
        When User click create epoch button
        And User continues to next step of study structure stepper
        And User waits for 1 seconds
        And User sets epoch 'type' as 'No Treatment'
        And User sets epoch 'subtype' as 'Basic'
        And User sets epoch description
        And User intercepts epochs data
        And User continues to next step of study structure stepper
        And User waits for epochs data
        When The form is no longer available
        And Study Epoch is found
        Then The added Epoch name, type 'No Treatment' and subtype 'Basic' is visible in the table


    Scenario: [Visit][Create] User must be able to define scheduled Information visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitType           | Information         |
            | contactMode         | On Site Visit       |
            | timeReference       | Global anchor visit |
            | timing              | -8                  |
            | timeUnit            | days                |
            | visitWindowMin      | 0                   |
            | visitWindowMax      | 0                   |
            | visitWindowUnit     | days                |
            | epoch               | Screening           |
            | showVisitInProtocol | true                |
            | soaMilestone        | true                |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Create] User must be able to define scheduled Screening visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitType           | Screening           |
            | contactMode         | On Site Visit       |
            | timeReference       | Global anchor visit |
            | timing              | -7                  |
            | timeUnit            | days                |
            | visitWindowMin      | -1                  |
            | visitWindowMax      | 1                   |
            | visitWindowUnit     | days                |
            | epoch               | Screening           |
            | showVisitInProtocol | true                |
            | soaMilestone        | true                |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Create] User must be able to define scheduled Randomisation visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitType           | Randomisation       |
            | contactMode         | On Site Visit       |
            | timeReference       | Global anchor visit |
            | timing              | 0                   |
            | timeUnit            | days                |
            | visitWindowMin      | -1                  |
            | visitWindowMax      | 1                   |
            | visitWindowUnit     | days                |
            | epoch               | Treatment           |
            | showVisitInProtocol | true                |
            | soaMilestone        | true                |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Create] User must be able to define scheduled Treatment visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitType           | Treatment           |
            | contactMode         | On Site Visit       |
            | timeReference       | Global anchor visit |
            | timing              | 21                  |
            | timeUnit            | days                |
            | visitWindowMin      | -3                  |
            | visitWindowMax      | 3                   |
            | visitWindowUnit     | days                |
            | epoch               | Treatment           |
            | showVisitInProtocol | true                |
            | soaMilestone        | true                |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Create] User must be able to define Anchor visit in visit group
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitClass          | Anchor visit in visit group |
            | visitType           | Treatment                   |
            | contactMode         | On Site Visit               |
            | timeReference       | Global anchor visit         |
            | timing              | 7                           |
            | timeUnit            | days                        |
            | visitWindowMin      | 0                           |
            | visitWindowMax      | 0                           |
            | visitWindowUnit     | days                        |
            | epoch               | Treatment                   |
            | showVisitInProtocol | true                        |
            | soaMilestone        | true                        |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Create] User must be able to define scheduled Treatment visit referenced in timing to Visit 3
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitGroup          | Visit 3       |
            | visitType           | Treatment     |
            | contactMode         | On Site Visit |
            | timing              | 7             |
            | timeUnit            | days          |
            | visitWindowMin      | 0             |
            | visitWindowMax      | 0             |
            | visitWindowUnit     | days          |
            | epoch               | Treatment     |
            | showVisitInProtocol | true          |
            | soaMilestone        | true          |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Create] User must be able to define scheduled Repeating visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitClass          | Repeating visit     |
            | visitType           | Treatment           |
            | contactMode         | Phone Contact       |
            | timeReference       | Global anchor visit |
            | expectedTiming      | 30                  |
            | timeUnit            | days                |
            | visitWindowMin      | 0                   |
            | visitWindowMax      | 0                   |
            | visitWindowUnit     | days                |
            | epoch               | Treatment           |
            | showVisitInProtocol | true                |
            | soaMilestone        | false               |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Create] User must be able to define Manually Defined Visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitClass          | Manually defined visit |
            | visitType           | Treatment              |
            | contactMode         | Virtual                |
            | timeReference       | Global anchor visit    |
            | visitName           | V4-PITSTOP             |
            | visitShortName      | V4PIT                  |
            | timing              | 26                     |
            | timeUnit            | days                   |
            | uniqueVisitNumber   | 410                    |
            | visitWindowMin      | 0                      |
            | visitWindowMax      | 0                      |
            | visitWindowUnit     | days                   |
            | epoch               | Treatment              |
            | showVisitInProtocol | true                   |
            | soaMilestone        | false                  |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Create] User must be able to define scheduled End of Treatment visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitType           | End of treatment    |
            | contactMode         | On Site Visit       |
            | timeReference       | Global anchor visit |
            | timing              | 40                  |
            | timeUnit            | days                |
            | visitWindowMin      | -3                  |
            | visitWindowMax      | 3                   |
            | visitWindowUnit     | days                |
            | epoch               | Treatment           |
            | showVisitInProtocol | true                |
            | soaMilestone        | true                |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Create] User must be able to define Early discontinuation
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitType           | Early discontinuation |
            | contactMode         | On Site Visit         |
            | timeReference       | Visit 6               |
            | visitSuffix         | A                     |
            | timeUnit            | days                  |
            | visitWindowUnit     | days                  |
            | epoch               | Treatment             |
            | showVisitInProtocol | true                  |
            | soaMilestone        | true                  |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Remove] User must not be able to delete a visit which is time reference for another visit
        And The page 'study_structure/visits' is opened for current study
        When The user selects visit 'V3D1' in the timeline view
        And The 'delete-visit-timeline' button is clicked
        And Action is confirmed by clicking continue
        Then The user is prompted with a notification message "The Visit can't be deleted as other visits (['V3D8']) are referencing this Visit"

    Scenario: [Visit][Create] User must be able to define Non-visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitType           | Non-visit |
            | isTechnicalVisit    | true      |
            | contactMode         | Virtual   |
            | visitWindowUnit     | days      |
            | epoch               | Treatment |
            | showVisitInProtocol | true      |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved


    Scenario: [Visit][Create] User must be able to define Unscheduled visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitType           | Unscheduled |
            | isTechnicalVisit    | true        |
            | contactMode         | Virtual     |
            | visitWindowUnit     | days        |
            | epoch               | Treatment   |
            | showVisitInProtocol | true        |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved

    Scenario: [Visit][Create] User must be able to define Unscheduled visit connected to Basic epoch
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitType           | Unscheduled |
            | contactMode         | Virtual     |
            | expectedTiming      | 35          |
            | timeUnit            | days        |
            | visitWindowUnit     | days        |
            | epoch               | Basic       |
            | showVisitInProtocol | true        |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved
        Then The visit 'V0' is visible in the Study Visits timeline view:
            | visitType   | Information |
            | studyDay    | -8          |
            | studyWeek   | -1          |
            | visitWindow | ±0D         |
        And The visit 'V1' is visible in the Study Visits timeline view:
            | visitType   | Screening |
            | studyDay    | -7        |
            | studyWeek   | -1        |
            | visitWindow | ±1D       |
        And The visit 'V2' is visible in the Study Visits timeline view:
            | visitType   | Randomisation |
            | studyDay    | 0             |
            | studyWeek   | 0             |
            | visitWindow | ±1D           |
        And The visit 'V3D1' is visible in the Study Visits timeline view:
            | visitType   | Treatment |
            | studyDay    | 7         |
            | studyWeek   | 1         |
            | visitWindow | ±0D       |
        And The visit 'V3D8' is visible in the Study Visits timeline view:
            | visitType   | Treatment |
            | studyDay    | 14        |
            | studyWeek   | 2         |
            | visitWindow | ±0D       |
        And The visit 'V4' is visible in the Study Visits timeline view:
            | visitType   | Treatment |
            | studyDay    | 21        |
            | studyWeek   | 3         |
            | visitWindow | ±3D       |
        And The visit 'V4PIT' is visible in the Study Visits timeline view:
            | visitType   | Treatment |
            | studyDay    | 26        |
            | studyWeek   | 3         |
            | visitWindow | ±0D       |
        And The visit 'P5.n' is visible in the Study Visits timeline view:
            | visitType   | Treatment |
            | studyDay    | 30        |
            | studyWeek   | 4         |
            | visitWindow | ±0D       |
        And The visit 'O6' is visible in the Study Visits timeline view:
            | visitType | Unscheduled |
        And The visit 'V7' is visible in the Study Visits timeline view:
            | visitType   | End of treatment |
            | studyDay    | 40               |
            | studyWeek   | 5                |
            | visitWindow | ±3D              |

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
        And User assign activity 'Weight' to visit 'V4'
        And User assign activity 'Alanine Aminotransferase' to visit 'V4'
        And User assign activity 'E2E_placeholder_' to visit 'V1'
        And User assign activity 'E2E_placeholder_' to visit 'V2'
        And User assign activity 'E2E_placeholder_2_' to visit 'V4'
        And User assign activity 'E2E_FirstActivity' to visit 'V1'
        And User assign activity 'E2E_FirstActivity' to visit 'V3'
        And User assign activity 'E2E_FirstActivity' to visit 'VD1'
        And User assign activity 'E2E_SecondActivity' to visit 'V4'
        And User assign activity 'E2E_SecondActivity' to visit 'V4PIT'
        And User assign activity 'E2E_SecondActivity' to visit 'V4'
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        Then User confirms activity 'Albumin' is assigned to visit 'V0'
        And User confirms activity 'Albumin' is assigned to visit 'V1'
        And User confirms activity 'Weight' is assigned to visit 'V2'
        And User confirms activity 'Weight' is assigned to visit 'V4'
        And User confirms activity 'Alanine Aminotransferase' is assigned to visit 'V4'
        And User confirms activity placeholder 'E2E_placeholder_' is assigned to visit 'V1'
        And User confirms activity placeholder 'E2E_placeholder_' is assigned to visit 'V2'
        And User confirms activity placeholder 'E2E_placeholder_2_' is assigned to visit 'V4'
        And User confirms activity 'E2E_FirstActivity' is assigned to visit 'V1'
        And User confirms activity 'E2E_FirstActivity' is assigned to visit 'V3'
        And User confirms activity 'E2E_FirstActivity' is assigned to visit 'V3B'
        And User confirms activity 'E2E_SecondActivity' is assigned to visit 'V4'
        And User confirms activity 'E2E_SecondActivity' is assigned to visit 'V4PIT'
        And User confirms activity 'E2E_SecondActivity' is assigned to visit 'V4'

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
        And User confirms activity 'Cause of Death' is assigned to visit 'V4'

    Scenario: [Exchange][Placeholder] User must be able to exchange an activity placeholder with two activities from Detailed SoA view, keeping the visits assigment
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And Action 'Exchange Activity' is selected for activity 'E2E_placeholder_'
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
        And Action 'Edit Activity' is selected for activity 'E2E_placeholder_2_'
        And User waits for 1 seconds
        When User edits Activity SoA group to 'GENETICS'
        And User waits for 1 seconds
        And The activity group is edited to 'Laboratory Assessments'
        And The activity subgroup is edited to 'Biochemistry'
        And User change placeholder name to 'New_E2E_placeholder_2_'
        And Modal window 'Save' button is clicked
        And Detailed SoA table is loaded
        And User expand table
        Then Activity 'New_E2E_placeholder_2_' is visible under subgroup 'Biochemistry', group 'Laboratory Assessments' and soa group 'GENETICS'

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
        And User searches for 'Alanine Aminotransferase' and confirms no results returned

    Scenario: [Footnotes][From Scratch][Link] User must be able to define new footnote and link it to two existing visits
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And User clicks plus icon to initate adding a footnote
        And User clicks plus icon in the activity 'Adverse Event' row for visit 'V2'
        And User clicks plus icon in the activity 'E2E_SecondActivity' row for visit 'V4PIT'
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
        And Footnote 'My First footnote' linkage to 'V4PIT' is visible in the footnotes table
        And Footnote index 'a' is visible in the detaied SoA next to activity 'Adverse Event' visit 'V2'
        And Footnote index 'a' is visible in the detaied SoA next to activity 'E2E_SecondActivity' visit 'V4PIT'
        And User switches to the 'protocol' view
        And Footnote index 'a' has footnote text 'My First footnote' displayed on the protocol page
        And Footnote index 'a' is assgined to visit 'V2' for activity 'Adverse Event'
        And Footnote index 'a' is assgined to visit 'V4PIT' for activity 'E2E_SecondActivity'

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
