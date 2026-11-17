@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Visits - Table View

   See shared notes for study visits in file study-visit-intro-notes.txt

   As a system user,
   I want the system to ensure [Scenario],
   So that I can make complete and consistent specification of study visits.

   Background: User is logged in and study has been selected
      Given The user is logged in
      And User selects study with id 'CDISC DEV-9876'
      Given [API] All visit groups uids are fetched
      And [API] All visit groups are removed
      And [API] Study vists uids are fetched for selected study
      When [API] Study visits in selected study are cleaned-up
      Given [API] The epoch with type 'Pre Treatment' and subtype 'Screening' exists in selected study
      Given [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study


   Scenario: [Table][Columns][Names] User must be able to see the page structure for Study Visits table view
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      Then A table is visible with following headers
         | headers               |
         | Epoch                 |
         | Visit type            |
         | Visit Class           |
         | Visit name            |
         | Contact mode          |
         | Timing                |
         | Unique visit number   |
         | Visit short name      |
         | Show visit            |
         | Visit description     |
         | Epoch Allocation Rule |
         | Visit start rule      |
         | Visit end rule        |
         | Study day             |
         | Study week            |

   Scenario: [Table][Options] User must be able to see the Study Vists table with following options
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      Then A table is visible with following options
         | edit-study-visits     |
         | columns-layout-button |
         | filters-button        |
         | table-export-button   |
         | search-field          |
         | select-rows           |
         | History               |

   Scenario: [Table][Columns][Visibility] User must be able to use column selection option
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      When The first column is selected from Select Columns option for table with actions
      Then The table contain only selected column and actions column

   Scenario: User must be able to enter edit mode for visits in table view
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      And The 'edit-study-visits' button is clicked
      Then The 'add-visit' element is visible
      And The 'close-edit-mode' element is visible

   Scenario: User must be able to exit edit mode for visits in table view
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      And The 'edit-study-visits' button is clicked
      When The 'close-edit-mode' button is clicked
      Then The 'edit-study-visits' element is visible
      And The 'close-edit-mode' button is not visible
      And The 'add-visit' button is not visible

   Scenario: User must not be able to create a visit without visit class selected
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      When The user defines a visit in the table view with following data:
         | visitType           | Screening             |
         | contactMode         | Phone Contact         |
         | startRule           | R1                    |
         | endRule             | R2                    |
         | epochAllocationRule | Current Visit         |
         | description         | Description for Visit |
      And The 'save-visit-changes' button is clicked
      Then The user is prompted with a notification message "Visit Class must be one of: 'SINGLE_VISIT', 'NON_VISIT', 'UNSCHEDULED_VISIT' or 'MANUALLY_DEFINED_VISIT'"

   Scenario: User must not be able to create a visit without contact mode selected
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      When The user defines a visit in the table view with following data:
         | visitType           | Screening             |
         | startRule           | R1                    |
         | endRule             | R2                    |
         | epochAllocationRule | Current Visit         |
         | description         | Description for Visit |
      And The 'save-visit-changes' button is clicked
      Then The user is prompted with a notification message "Visit Contact Mode must be a dictionary"

   Scenario: User must not be able to create a visit without visit type selected
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      When The user defines a visit in the table view with following data:
         | visitClass          | Manually defined visit |
         | visitName           | No type visit          |
         | visitShortName      | V1                     |
         | contactMode         | Phone Contact          |
         | timeReference       | Global anchor visit    |
         | startRule           | R1                     |
         | endRule             | R2                     |
         | epochAllocationRule | Current Visit          |
         | epoch               | Screening              |
         | description         | Description for Visit  |
      And The 'save-visit-changes' button is clicked
      Then The user is prompted with a notification message "Visit Type must be a dictionary"

   Scenario: User must not be able to create visit without visit name defined
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      When The user defines a visit in the table view with following data:
         | visitClass          | Manually defined visit |
         | visitShortName      | V1                     |
         | visitType           | Screening              |
         | contactMode         | Phone Contact          |
         | timeReference       | Global anchor visit    |
         | timeUnit            | days                   |
         | timing              | 1                      |
         | uniqueVisitNumber   | 1                      |
         | startRule           | R1                     |
         | endRule             | R2                     |
         | epochAllocationRule | Current Visit          |
         | epoch               | Screening              |
         | description         | Description for Visit  |
      And The 'save-visit-changes' button is clicked
      Then The user is prompted with a notification message "The following fields are required for a manually defined visit: 'visit_name'."


   Scenario: User must be able to define a new visit in the Study Visits table view
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      When The user defines a visit in the table view with following data:
         | visitClass          | Manually defined visit |
         | visitName           | Fully Defined Visit    |
         | visitShortName      | V1                     |
         | visitType           | Screening              |
         | contactMode         | Phone Contact          |
         | timeReference       | Global anchor visit    |
         | timeUnit            | days                   |
         | timing              | 1                      |
         | uniqueVisitNumber   | 1                      |
         | startRule           | R1                     |
         | endRule             | R2                     |
         | epochAllocationRule | Current Visit          |
         | epoch               | Screening              |
         | description         | Description for Visit  |
      When The user intercepts study visit 'create' request
      And The 'created' visit is saved
      When The 'close-edit-mode' button is clicked
      Then The visit 'Fully Defined Visit' is visible in the Study Visits table view:
         | Epoch                       | Screening              |
         | Visit type                  | Screening              |
         | SoA Milestone               | No                     |
         | Visit Class                 | Manually defined visit |
         | Time reference              | Global anchor visit    |
         | Anchor visit in visit group | No                     |
         | Contact mode                | Phone Contact          |
         | Timing                      | 1 days                 |

   Scenario: User must be able to edit an existing visit in the Study Visits table view
      And The page 'study_structure/visits' is opened for current study
      And The 'visit-view-type-table' button is clicked
      When The user defines a visit in the table view with following data:
         | visitClass          | Manually defined visit |
         | visitName           | Visit To Edit          |
         | visitShortName      | SN                     |
         | visitType           | Screening              |
         | contactMode         | Phone Contact          |
         | timeReference       | Global anchor visit    |
         | timeUnit            | day                    |
         | timing              | 1                      |
         | uniqueVisitNumber   | 1                      |
         | startRule           | R1                     |
         | endRule             | R2                     |
         | epochAllocationRule | Current Visit          |
         | epoch               | Screening              |
         | description         | Description for Visit  |
      And The user intercepts study visit 'create' request
      And The 'created' visit is saved
      And The user edits the visit 'Visit To Edit' in table view with following data:
         | visitName         | Edited Visit        |
         | epoch             | Intervention        |
         | visitShortName    | V1                  |
         | uniqueVisitNumber | 2                   |
         | description       | Updated description |
      When The user intercepts study visit 'edit' request
      And The 'edited' visit is saved
      And The 'close-edit-mode' button is clicked
      Then The visit 'Edited Visit' is visible in the Study Visits table view:
         | Epoch                       | Intervention        |
         | Visit type                  | Screening           |
         | SoA Milestone               | No                  |
         | Visit description           | Updated description |
         | Time reference              | Global anchor visit |
         | Anchor visit in visit group | No                  |
         | Contact mode                | Phone Contact       |
         | Timing                      | 1 day               |