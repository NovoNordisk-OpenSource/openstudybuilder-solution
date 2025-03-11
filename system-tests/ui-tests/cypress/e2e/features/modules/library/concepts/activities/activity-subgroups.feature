@REQ_ID:1070683

Feature: Library - Activity Subgroups

    As a user, I want to manage every Activity Subgroups in the Concepts Library
    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to the Activity Subgroups page
        Given The '/library' page is opened
        When The 'Activities' submenu is clicked in the 'Concepts' section
        And The 'Activity Subgroups' tab is selected
        Then The current URL is '/library/activities/activity-subgroups'

    Scenario: User must be able to see the columns list on the main page as below
        Given The '/library/activities/activity-subgroups' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add activity subgroup                                           |
            | Filters                                                         |
            | Columns                                                         |
            | Export                                                          |
            | Show version history                                            |
            | Add select boxes to table to allow selection of rows for export |
            | search-field                                                    |

        Then A table is visible with following headers
            | headers            |
            | Activity group     |
            | Activity subgroup  |
            | Sentence case name |
            | Abbreviation       |
            | Definition         |
            | Modified           |
            | Status             |
            | Version            |

    Scenario: User must be able to select visibility of columns in the table 
        Given The '/library/activities/activity-subgroups' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to add a new activity subgroups
        Given The '/library/activities/activity-subgroups' page is opened
        When The Add activity subgroup button is clicked
        And The test activity subgroup container is filled with data and saved
        Then The newly added activity subgroup is visible in the the table

    Scenario: User must not be able to save new activity subgroup without filling mandatory fields of 'Group name', 'Subgroup name', 'Sentence case name' and 'Definition'
        Given The '/library/activities/activity-subgroups' page is opened
        When The Add activity subgroup button is clicked
        And The Activity groups, Subgroup name, Sentence case name and Definition fields are not filled with data
        Then The user is not able to save the acitivity subgroup
        And The message is displayed as 'This field is required' in each of the mandatory field

    Scenario: System must default value for 'Sentence case name' to lower case value of 'Activity subgroup name'
        Given The '/library/activities/activity-subgroups' page is opened
        When The Add activity subgroup button is clicked
        And The user enters a value for Activity subgroup name
        Then The field for Sentence case name will be defaulted to the lower case value of the Activity subgroup name

    Scenario: System must ensure value of 'Sentence case name' independent of case is identical to the value of 'Activity subgroup name'
        Given The '/library/activities/activity-subgroups' page is opened
        When The Add activity subgroup button is clicked
        And The user define a value for Sentence case name and it is not identical to the value of Activity subgroup name
        Then The user is not able to save the acitivity subgroup
        And The message is displayed as 'Sentence case name value must be identical to name value' in the Sentence case name field

    Scenario: User must be able to add a new version for the approved activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        And The activity subgroup exists with status as Final
        When The 'New version' option is clicked from the three dot menu list
        Then The activity subgroup has status 'Draft' and version '1.1'

    Scenario: User must be able to edit and approve new version of activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        And The activity subgroup exists with status as Final
        When The 'New version' option is clicked from the three dot menu list
        Then The activity subgroup has status 'Draft' and version '1.1'
        When The 'Edit' option is clicked from the three dot menu list
        And The activity subgroup is edited
        Then The activity subgroup has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The activity subgroup has status 'Final' and version '2.0'

    Scenario: User must be able to inactivate the approved version of the activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        And The activity subgroup exists with status as Final
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The activity subgroup has status 'Retired' and version '1.0'

    Scenario: User must be able to reactivate the inactivated version of the activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        And The activity subgroup exists with status as Retired
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The activity subgroup has status 'Final' and version '1.0'

    Scenario: User must be able to edit the drafted version of the activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        And The activity subgroup exists with status as Draft
        When The 'Edit' option is clicked from the three dot menu list
        Then The activity subgroup is edited
        And The activity subgroup has status 'Draft' and version '0.2'

    Scenario: User must be able to approve the drafted version of the activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        And The activity subgroup exists with status as Draft
        When The 'Approve' option is clicked from the three dot menu list
        Then The activity subgroup has status 'Final' and version '1.0'

    Scenario: User must be able to Delete the intial created version of the activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        And The activity subgroup exists with status as Draft
        When The 'Delete' option is clicked from the three dot menu list
        Then The activity subgroup is no longer available

    Scenario: User must be able to Cancel creation of the activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        And The test activity subgroup container is filled with data
        When Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And The activity subgroup is not created

    Scenario: User must be able to Cancel edition of the activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        And The activity subgroup exists with status as Draft
        When The 'Edit' option is clicked from the three dot menu list
        When The activity subgroup edition form is filled with data
        And Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And The activity subgroup is not edited
    
    Scenario: User must only have access to aprove, edit, delete, history actions for Drafted version of the activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        When The activity subgroup exists with status as Draft
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Draft item are displayed

    Scenario: User must only have access to new version, inactivate, history actions for Final version of the activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        When The activity subgroup exists with status as Final
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed

    Scenario: User must only have access to reactivate, history actions for Retired version of the activity subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        When The activity subgroup exists with status as Retired
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed

    Scenario: User must be able to search created subgroup
        Given The '/library/activities/activity-subgroups' page is opened
        When First activity subgroup for search test is created
        And Second activity subgroup for search test is created
        Then One activity subgroup is found after performing full name search
        And More than one item is found after performing partial name search 

    Scenario: User must be able to search not existing subgroup and table will correctly filtered
        Given The '/library/activities/activity-subgroups' page is opened
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: User must be able to combine search and filters to narrow table results
        Given The '/library/activities/activity-subgroups' page is opened
        When The user filters table by status 'Final'
        And The existing item in status Draft is searched for
        And The item is not found and table is correctly filtered
        And The user changes status filter value to 'Draft'
        Then More than one item is found after performing partial name search

    Scenario Outline: User must be able to filter the table by text fields
        Given The '/library/activities/activity-subgroups' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                  |
        | Activity group        |
        | Activity subgroup     |
        | Sentence case name    |
        | Abbreviation          |
        | Definition            |
        | Status                |
        | Version               |

