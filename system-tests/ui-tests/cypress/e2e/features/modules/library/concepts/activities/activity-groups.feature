@REQ_ID:1070683

Feature: Library - Activity Groups

    As a user, I want to manage every Activity Groups in the Concepts Library
    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to the Activity Groups page
        Given The '/library' page is opened
        When The 'Activities' submenu is clicked in the 'Concepts' section
        And The 'Activity Groups' tab is selected
        Then The current URL is '/library/activities/activity-groups'

    Scenario: User must be able to see the columns list on the main page as below
        Given The '/library/activities/activity-groups' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add activity group                                              |
            | Filters                                                         |
            | Columns                                                         |
            | Export                                                          |
            | Show version history                                            |
            | Add select boxes to table to allow selection of rows for export |
            | search-field                                                    |

        Then A table is visible with following headers
            | headers            |
            | Activity group     |
            | Sentence case name |
            | Abbreviation       |
            | Definition         |
            | Modified           |
            | Status             |
            | Version            |

    Scenario: User must be able to select visibility of columns in the table 
        Given The '/library/activities/activity-groups' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to add a new activity group
        Given The '/library/activities/activity-groups' page is opened
        When The add activity group button is clicked
        And The activity group container is filled with data and saved
        And The newly added activity group is visible in the the table

    Scenario: User must not be able to save new activity group without filling mandatory fields of 'Group name', 'Sentence case name' and 'Definition'
        Given The '/library/activities/activity-groups' page is opened
        When The add activity group button is clicked
        And The Group name and Sentence case name and Definition fields are not filled with data
        Then The user is not able to save the acitivity group
        And The message is displayed as 'This field is required' in the mandatory fields

    Scenario: System must default value for 'Sentence case name' to lower case value of 'Activity group name'
        Given The '/library/activities/activity-groups' page is opened
        When The add activity group button is clicked
        And The user enters a value for Activity group name
        Then The field for Sentence case name will be defaulted to the lower case value of the Activity group name

    Scenario: System must ensure value of 'Sentence case name' independent of case is identical to the value of 'Activity group name'
        Given The '/library/activities/activity-groups' page is opened
        When The add activity group button is clicked
        And The user define a value for Sentence case name and it is not identical to the value of Activity group name
        Then The user is not able to save the acitivity group
        And The validation message appears for sentance case name that it is not identical to name

    Scenario: User must be able to add a new version for the approved activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'

    Scenario: User must be able to edit and approve new version of activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'
        When The 'Edit' option is clicked from the three dot menu list
        And The activity group is edited
        Then The item has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '2.0'

    Scenario: User must be able to inactivate the approved version of the activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '1.0'

    Scenario: User must be able to reactivate the inactivated version of the activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity group is inactivated
        And Activity group is found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: User must be able to edit the drafted version of the activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And Activity group is found
        When The 'Edit' option is clicked from the three dot menu list
        And The activity group is edited
        Then The item has status 'Draft' and version '0.2'
        
    Scenario: User must be able to approve the drafted version of the activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And Activity group is found
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: User must be able to Delete the intial created version of the activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And Activity group is found
        When The 'Delete' option is clicked from the three dot menu list
        Then The activity group is no longer available

    Scenario: User must be able to Cancel creation of the activity group
        Given The '/library/activities/activity-groups' page is opened
        And The test activity group container is filled with data
        When Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And The activity group is not created

    Scenario: User must be able to Cancel edition of the activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And Activity group is found
        When The 'Edit' option is clicked from the three dot menu list
        When The activity group edition form is filled with data
        And Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And The activity group is not edited

    Scenario: User must only have access to aprove, edit, delete, history actions for Drafted version of the activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And Activity group is found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Draft item are displayed

    Scenario: User must only have access to new version, inactivate, history actions for Final version of the activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed

    Scenario: User must only have access to reactivate, history actions for Retired version of the activity group
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity group is inactivated
        And Activity group is found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed

    Scenario: User must be able to search created group
        Given The '/library/activities/activity-groups' page is opened
        When [API] First activity group for search test is created
        And [API] Second activity group for search test is created
        Then One activity group is found after performing full name search
        And More than one item is found after performing partial name search 

    Scenario: User must be able to search not existing group and table will correctly filtered
        Given The '/library/activities/activity-groups' page is opened
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: User must be able to combine search and filters to narrow table results
        Given The '/library/activities/activity-groups' page is opened
        When The user filters table by status 'Final'
        And The existing item in status Draft is searched for
        And The item is not found and table is correctly filtered
        And The user changes status filter value to 'Draft'
        Then More than one item is found after performing partial name search

    Scenario: User must be able to find new version of approved group by setting status filter
        Given The '/library/activities/activity-groups' page is opened
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        When The user filters table by status 'Final'
        And The group can be find in table
        And [API] Activity group gets new version
        And The user changes status filter value to 'Draft'
        And The group can be find in table

    Scenario: User must be able to search item ignoring case sensitivity
        Given The '/library/activities/activity-groups' page is opened
        When The existing item in search by lowercased name
        And More than one result is found

    Scenario Outline: User must be able to filter the table by text fields
        Given The '/library/activities/activity-groups' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name               |
        | Activity group     |
        | Sentence case name |
        | Abbreviation       |
        | Definition         |
        | Status             |
        | Version            |