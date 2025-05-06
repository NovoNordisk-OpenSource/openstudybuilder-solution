@REQ_ID:1074260
Feature: Studies - Detailed SoA

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study SoA.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: User must be able to navigate to Detailed SoA page using side menu
        Given The '/studies' page is opened
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        And The 'Schedule of Activities' tab is selected
        Then The current URL is '/studies/Study_000001/activities/soa'

    @manual_test
    Scenario: User must be able to see the Detailed SoA matrix table with options listed in this scenario
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        Then A table is visible with following options
            | options                         |
            | Edit SoA items                  |
            | Hide activity in protocol SoA   |
            | Show activity in protocol SoA   |
            | Edit current activity selection |
            | Expand table                    |
            | Collapse table                  |
            | Hide SoA groups                 |
        And A matrix table is visible with Activites, Epoch Visit Day Window, Study Epochs and Study Visits headers

    @manual_test
    Scenario: User must be able to view the study activities in the detailed SoA table matrix including SoA groups
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        And the option to 'Hide SoA groups' is disabled
        Then The Detailed SoA table matrix display rows for each test study activities grouped by activity group, activity subgroup and SoA group

    @manual_test
    Scenario: User must be able to view the study activities in the detailed SoA table matrix without SoA groups
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        And the option to 'Hide SoA groups' is enabled
        Then The Detailed SoA table matrix display rows for each test study activities grouped by activity group and activity subgroup

    @manual_test
    Scenario: User must be presented with time unit of visits the same as defined in first defined study visity
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        And The test study data contains defined visits
        Then The SoA is displaying the data using correct time unit

    @manual_test
    Scenario: User must be able to set the schedule of a study activity at a visit
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The test study activity is schedule at a test visit by selecting the checkbox to be checked
        Then The Detailed SoA table matrix display a checkmark in the table cell of the test activity row and the test visit column


    #### Activity Actions

    @manual_test
    Scenario: User must be able to remove the schedule of a study activity at a visit
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The test study activity schedule is removed at a test visit by selecting the checkbox to be unchecked
        Then The Detailed SoA table matrix will not display a checkmark in the table cell of the test activity row and the test visit column

    @manual_test
    Scenario: User must be able to mark a [SoA row] to be displayed in the Detailed SoA
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The test <SoA row> is marked to be displayed in the Detailed SoA
        And The Detailed SoA tab is opened
        Then The test <SoA row> is displayed in the Detailed SoA

        Examples:
            | SoA row           |
            | SoA Group         |
            | Activity Group    |
            | Activity Subgroup |
            | Activity          |

    @manual_test
    Scenario: User must be able to mark a [SoA row] to be hidden in the Detailed SoA
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The test <SoA row> is marked to be hidden in the Detailed SoA
        And The Detailed SoA tab is opened
        Then The test <SoA row> is not displayed in the Detailed SoA

        Examples:
            | SoA row           |
            | SoA Group         |
            | Activity Group    |
            | Activity Subgroup |
            | Activity          |

    Scenario: User must be able to remove Study Activity from Detailed SoA
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user click on 'Remove Activity' action for an Activity
        And The user confirms the deletion pop-up
        Then The pop up displays 'Study activity removed'
        And The Activity is no longer visible in the SoA

    @manual_test
    Scenario: User must be able to change activity grouping for given Study Activity in Detailed SoA
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user click on 'Remove activity' action for an Activity
        And The user updates the Activity Group for that Activity in Detailed SoA
        And The user updates the Activity SubGroup for that Activity in Detailed SoA
        And The user provides the rationale for activity request for that Activity in Detailed SoA
        Then The pop up snack displays 'The Study activity Aspartate Aminotransferase has been updated.'
        And The changes are visible in Detailed SoA

    @manual_test
    Scenario: User must be able to exchange activity in given Study in Detailed SoA through selection from studies
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user click on 'Exchange Activity' action for an Activity
        And The user goes through selection from studies form
        Then The newly selected avtivity replaces previous activity in study
        And The scheduling is not affected

    Scenario: User must be able to exchange activity in given Study in Detailed SoA through selection from library
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user click on 'Exchange Activity' action for an Activity
        And The user goes through selection from library form
        Then The newly selected activity replaces previous activity in study

    @manual_test
    Scenario: User must be able to exchange activity in given Study in Detailed SoA by creating an placeholder for new Activity Request
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user click on 'Exchange Activity' action for an Activity
        And The user goes through creating a placeholder for new Activity Request form
        Then The newly selected avtivity replaces previous activity in study
        And The scheduling is not affected

    @manual_test
    Scenario: User must be able to exchange activity in given Study in Detailed SoA by requesting an activity
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user click on 'Exchange Activity' action for an Activity
        And The user goes through creating a placeholder for new Activity Request form
        Then The newly selected avtivity replaces previous activity in study

    @manual_test
    Scenario: User must be able to add activity from different activity group than selected
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user adds an activity from different group than selected to add activity
        Then The activity is assigned to group user has selected

    Scenario: User must be able to add activity from library
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user click on 'Add activity' action for an Activity
        And The user goes through selection from library form
        Then The newly created activity is present in SoA

    @manual_test
    Scenario: User must be able to add activity from study by Study ID
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user click on 'Add activity' action for an Activity
        And The user goes through selection from library form
        Then The newly created avtivity is present in SoA

    @manual_test
    Scenario: User must be able to add activity from study by Study Acronym
        Given At least '1' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user click on 'Add activity' action for an Activity
        And The user goes through selection from library form
        Then The newly created avtivity is present in SoA

    Scenario: User must be able to open bulk edit activities form on Detailed SoA
        Given At least '2' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user selects rows in SoA table
        And The user clicks on Bulk Edit action on SoA table options
        Then The bulk edit view is presented to user allowing to update Activity Group and Visits for selected activities

    @manual_test @pending_implementation 
    Scenario: User must be able to bulk edit activities on Detailed SoA
        Given At least '2' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user edits activities in bulk
        Then The data for bulk edited activities is updated

    @manual_test @pending_implementation 
    Scenario: User must be able to remove selection of activity on the form for bulk edit in Detailed SoA
        Given At least '2' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user selects rows in SoA table
        And The user clicks on Bulk Edit action on SoA table options
        And The user removes selection of one of Activities on the form
        Then The selection disappears from the form

    Scenario: User must not be able to bulk edit without selecting Activity Group and Visit
        Given At least '2' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user edits activities in bulk without selecting Activity Group and Visit
        Then The validation appears for Activity Group field in bulk edit form

    Scenario: User must be able to bulk delete activities on Detailed SoA
        Given At least '2' activites are present in 'Study_000001' study
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user delete activities in bulk
        Then The activities are removed from the study
        
    Scenario: User must be able to enable reordering of activities in Detailed SoA
        Given At least '3' activities are present in 'Study_000001' in the same 'Acute Kidney Injury' flowchart subgroup and 'BIOMARKERS' group
        And The '/studies/Study_000001/activities/soa' page is opened
        When The user enables the Reorder Activities function for acitivities in the same 'Acute Kidney Injury' flowchart subgroup and 'BIOMARKERS' group
        And The user updates the order of activities
        Then The new order of activites is visible
