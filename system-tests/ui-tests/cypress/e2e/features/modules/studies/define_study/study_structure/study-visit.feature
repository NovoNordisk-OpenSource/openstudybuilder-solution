@REQ_ID:1074254
Feature: Studies - Study Visit

    See shared notes for study visits in file study-visit-intro-notes.txt

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study visits.

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: User must be able to navigate to Study Visit page using side menu
        Given A test study is selected
        And The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Visits' tab is selected
        Then The current URL is '/study_structure/visits'

    Scenario: User must be able to see the Study Visit table with options listed in this scenario
        Given The '/studies/Study_000001/study_structure/visits' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add content                                                     |
            | Edit                                                            |
            | Show version history                                            |
            | Filters                                                         |
            | Columns                                                         |
            | Export                                                          |
            | Add select boxes to table to allow selection of rows for export |
        And A table is visible with following headers
            | headers                     |
            | Epoch                       |
            | Visit type                  |
            | SoA Milestone               |
            | Visit Class                 |
            | Visit Subclass              |
            | Repeating frequency         |
            | Visit name                  |
            | Anchor visit in visit group |
            | Visit group                 |
            | Global anchor visit         |
            | Contact mode                |
            | Time reference              |
            | Timing                      |
            | Visit number                |
            | Unique visit number         |
            | Visit short name            |
            | Study duration days         |
            | Study duration weeks        |
            | Visit window                |
            | Collapsible visit group     |
            | Show Visit                  |
            | Visit description           |
            | Epoch Allocation Rule       |
            | Visit start rule            |
            | Visit end rule              |
            | Study day                   |
            | Study week                  |
            | Week in Study               |
            | Modified                    |
            | Modified by                 |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000005/study_structure/visits' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must not be able to add a new Study Visit when no Study Epoch has been defined
        Given The study without Study Epoch has been selected
        Given The '/studies/Study_000005/study_structure/visits' page is opened
        When The 'add-visit' button is clicked
        Then The the user is prompted with a notification message "To add visits, you need to difine the epochs first. Would you like to define epochs?"
        And The 'Add epoch' button is visible
        And The 'Cancel' button is visible

    Scenario: User must not be able to create an visit without epoch selected
        Given A test study is selected
        And The epoch exists in selected study
        And The '/studies/Study_000001/study_structure/visits' page is opened
        When The epoch for visit is not selected in new visit form
        Then The validation appears under study period field

    Scenario: User must not be able to create an visit without type, contact mode, time reference and timing defined
        Given A test study is selected
        And The epoch exists in selected study
        And The '/studies/Study_000001/study_structure/visits' page is opened
        When The type, contact mode, time reference and timing is not selected in new visit form
        Then The validation appears under given study details fields
    
    Scenario: User must not be able to select time referece for an anchor visit
        Given The study without anchor visit has been selected
        And The epoch exists in selected study
        And The '/studies/Study_000003/study_structure/visits' page is opened
        When The new Anchor Visit creation is initiated
        Then It is not possible to edit Time Reference for anchor visit

    Scenario: User must be able to create an anchor visit
        Given The study without anchor visit has been selected
        And The epoch exists in selected study
        And The '/studies/Study_000003/study_structure/visits' page is opened
        When The new Anchor Visit is added
        Then The new Anchor Visit is visible within the Study Visits table

    @manual_test
    Scenario: User must be able to create an information visit with visit 0
        Given A test study is selected
        And The epoch exists in selected study
        When The '/studies/Study_000001/study_structure/visits' page is opened
        And The first scheduled visit is created with the visit type as an Information visit
        And The visit timing is set to the lowest timing of all existing visit when compared to the Global Anchor time reference
        Then The Information visit should be created with 0 as Visit number
        And No reordering of existing visits should happen

    Scenario: User must not be able to create an anchor visit if one already exists
        Given The study with defined anchor visit is selected
        And The '/studies/Study_000003/study_structure/visits' page is opened
        When The form for new study visit is opened
        Then The Anchor visit checkbox is disabled

    Scenario: User must be able to edit the study visit
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And The study with defined visit is selected
        When The study visit is edited
        Then The study visit data is reflected within the Study Visits table

    Scenario: User must be able to update study visit epoch
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        When The user opens edit form for the study epoch for chosen study visit
        Then The study epoch field is enabled for editing

    @pending_implementation
    Scenario: User must not be able to update study epoch without updating the timing to correct chronological order
        Given The '/studies/Study_000002/study_structure/visits' page is opened
        And There are at least 3 visits created for the study
        When The user tries to update last treatment visit epoch to Screening without updating the timing
        Then The system displays the message "The following visit can't be created as the next Epoch Name 'Treatment' starts at the '1' Study Day"


    @manual_test
    Scenario: User must be able to edit the study information visit with visit 0 to other visit type
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A studty inforamtion visit with visit 0 is created
        When This study information visit is edited to be a different visit type
        Then This visit can no longer be Visit 0
        And Reordering will occur of existing visits

    @manual_test
    Scenario: User must be able to edit the study information visit with visit 0 to same visit type
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A studty inforamtion visit with visit 0 is created
        When This study information visit is edited to the same visit type
        Then This visit should be given the visit number of 0
        When This visit is edited to higher visit timing compare to the Global Anchor time reference
        Then Reordering of other visits will occur

    Scenario: User must be able to delete the study visit
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And The study with defined visit is selected
        When The study visit is deleted
        Then The pop up displays 'Visit deleted'

    @manual_test
    Scenario: User must be able to delete the study information visit with visit 0
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A studty inforamtion visit with visit 0 is created
        When This study information visit is deleted
        Then No reordering of other visits will occur

    @manual_test
    Scenario: User must be able to delete the study information visit without visit 0
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A studty inforamtion visit without visit 0 is created
        When This study information visit is deleted
        Then The reordering of other visits will occur