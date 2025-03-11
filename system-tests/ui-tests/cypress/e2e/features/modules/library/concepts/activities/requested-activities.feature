@REQ_ID:1070683

Feature: Library - Requested Activities

    As a user, I want to manage Requested Activities in the Concepts Library
    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to the Requested Activities page
        Given The '/library' page is opened
        When The 'Activities' submenu is clicked in the 'Concepts' section
        And The 'Requested Activities' tab is selected
        Then The current URL is '/library/activities/requested-activities'

    Scenario: User must be able to see the columns list on the main page as below
        Given The '/library/activities/requested-activities' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add activity                                                    |
            | Filters                                                         |
            | Columns                                                         |
            | Export                                                          |
            | Show version history                                            |
            | Add select boxes to table to allow selection of rows for export |
            | search-field                                                    |

        And A table is visible with following headers
            | headers                        |
            | Activity group                 |
            | Activity subgroup              |
            | Activity                       |
            | Sentence case name             |
            | Abbreviation                   |
            | Definition                     |
            | Rationale for activity request |
            | Modified                       |
            | Modified by                    |
            | Status                         |
            | Version                        |

    Scenario: User must be able to select visibility of columns in the table 
        Given The '/library/activities/requested-activities' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to add a new activity request
        Given The '/library/activities/requested-activities' page is opened
        When The activity request container is filled with data and saved
        Then The pop up displays 'Activity created'
        And The newly added activity request is visible in the the table

    Scenario: User must not be able to save new activity request without mandatory fields of 'Activity group', 'Activity subgroup', 'Activity name' and 'Rationale for activity request'
        Given The '/library/activities/requested-activities' page is opened
        When The Add activity request button is clicked
        And The Activity group, Activity name, Sentence case name and Rationale for activity request fields are not filled with data
        Then The user is not able to save the acitivity request
        And The message is displayed as 'This field is required' in mandatory fields
        And The message is not displayed as 'This field is required' in optional fields
        When Input a value for Activity group field, but not for Activity subgroup field
        Then The message is displayed as 'This field is required' in the subgroup field

    Scenario: System must ensure value of 'Sentence case name' is mandatory
        Given The '/library/activities/requested-activities' page is opened
        And The Add activity request button is clicked
        When The user input a value for Activity name 'TEST'
        And The user clear default value from Sentance case name
        Then The message is displayed as 'This field is required' in empty Sentance case name field

    Scenario: System must default value for 'Sentence case name' to lower case value of 'Activity name'
        Given The '/library/activities/requested-activities' page is opened
        And The Add activity request button is clicked
        When The user input a value for Activity name 'TEST'
        Then The field for Sentence case name will be defaulted to the lower case value of the Activity name

    Scenario: System must ensure value of 'Sentence case name' independent of case is identical to the value of 'Activity name'
        Given The '/library/activities/requested-activities' page is opened
        And The Add activity request button is clicked
        When The value for Sentence case name independent of case is not identical to the value of Activity name
        Then The user is not able to save the acitivity request
        And The message is displayed as 'Sentence case name value must be identical to name value' in the Sentence case name field

    Scenario: User must be able to add a new version for the approved activity request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Final
        When The 'New version' option is clicked from the three dot menu list
        Then The requested activity has status 'Draft' and version '1.1'

    Scenario: User must be able to inactivate the approved version of the activity request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Final
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The requested activity has status 'Retired' and version '1.0'

    Scenario: User must be able to reactivate the inactivated version of the activity request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Retired
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The requested activity has status 'Final' and version '1.0'

    Scenario: User must be able to edit the drafted version of the activity request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Draft
        When The 'Edit' option is clicked from the three dot menu list
        Then The activity request is edited
        And The requested activity has status 'Draft' and version '0.2'

    Scenario: User must be able to edit and approve new version of requested activity
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Final
        When The 'New version' option is clicked from the three dot menu list
        Then The requested activity has status 'Draft' and version '1.1'
        When The 'Edit' option is clicked from the three dot menu list
        And The activity request is edited
        Then The requested activity has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The requested activity has status 'Final' and version '2.0'

    Scenario: User must be able to Approve the drafted version of the activity request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Draft
        When The 'Approve' option is clicked from the three dot menu list
        Then The requested activity has status 'Final' and version '1.0'

    Scenario: User must be able to Delete the intial created version of the activity request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Draft
        When The 'Delete' option is clicked from the three dot menu list
        Then The requested activity is no longer available

    Scenario: User must be able to Cancel creation of the activity request
        Given The '/library/activities/requested-activities' page is opened
        And The activity request form is filled with data
        When Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And The requested activity is not created

    Scenario: User must be able to Cancel edition of the activity request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Draft
        When The 'Edit' option is clicked from the three dot menu list
        When The requested activity edition form is filled with data
        And Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And The requested activity is not edited

    @manual_test
    Scenario: User must be able to handle and approve an activity placeholder request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Final
        When The 'Handle placeholder request' option is clicked from the three dot menu list
        And The activity request is approved
        Then The new activity request is saved with a status as 'Retired'
        And The activity request appears as available activity in the study
        And The activity appears in sponsor library

    @manual_test
    Scenario: User must be able to handle and reject an activity placeholder request
        Given The '/library/activities/requested-activities' page is opened
        And The test activity request exists with a status as Final
        When The 'Handle placeholder request' option is clicked from the three dot menu list
        And The activity request is rejected
        Then The new activity request is saved with a status as 'Retired'
        And The activity request appears as rejected for study

    Scenario: User must only have access to aprove, edit, delete, history actions for Drafted version of the requested activity
        Given The '/library/activities/requested-activities' page is opened
        When The test activity request exists with a status as Draft
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Draft item are displayed

    Scenario: User must only have access to new version, inactivate, history actions for Final version of the requested activity
        Given The '/library/activities/requested-activities' page is opened
        When The test activity request exists with a status as Final
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed

    Scenario: User must only have access to reactivate, history actions for Retired version of the requested activity
        Given The '/library/activities/requested-activities' page is opened
        When The test activity request exists with a status as Retired
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed

    Scenario: User must have access to Handle placeholder request action for Final version of the requested activity
        Given The '/library/activities/requested-activities' page is opened
        When The test activity request exists with a status as Final
        And The item actions button is clicked
        Then 'Handle placeholder request' action is available

    Scenario: User must be able to search created activity request
        Given The '/library/activities/requested-activities' page is opened
        When First activity request for search test is created
        And Second activity request for search test is created
        Then One activity request is found after performing full name search
        And More than one item is found after performing partial name search 

    Scenario: User must be able to search not existing activity request and table will correctly filtered
        Given The '/library/activities/requested-activities' page is opened
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: User must be able to combine search and filters to narrow table results
        Given The '/library/activities/requested-activities' page is opened
        When The user filters table by status 'Final'
        And The existing item in status Draft is searched for
        And The item is not found and table is correctly filtered
        And The user changes status filter value to 'Draft'
        Then More than one item is found after performing partial name search

    Scenario Outline: User must be able to filter the table by text fields
        Given The '/library/activities/requested-activities' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                  |
        | Activity group                 |
        | Activity subgroup              |
        | Activity                       |
        | Sentence case name             |
        | Abbreviation                   |
        | Definition                     |
        | Rationale for activity request |
        | Modified by                    |
        | Status                         |
        | Version                        |