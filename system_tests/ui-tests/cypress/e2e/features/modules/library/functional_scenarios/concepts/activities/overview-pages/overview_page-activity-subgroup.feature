@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Subgroup Overview Page
    As a user, I want to verify that the Activity Subgroup Overview Page in the Concepts Library, can display correctly.

    Background: 
        Given The user is logged in
        When [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
        And Group, subgroup, activity and instance names created through API are found
        And Overview page for subgroup created via API is opened
        And User intercepts linked activities to subgroup request
        And User intercepts linked groups to subgroup request
        And Subgroup overview page is opened
        And User waits for linked activities to subgroup request
        And User waits for linked groups to subgroup request

    Scenario: [Navigation][Group] User must be able to navigate to activity group overview page by clicking its name in the activity subgroup overview page
        When The group overview page can be opened by clicking the group link in overview page
        Then Group overview page is opened

    Scenario: [Navigation][Subgroup] User must be able to navigate to activity subgroup overview page by clicking its name in the activity subgroup table
        Given The '/library/activities/activity-subgroups' page is opened
        When Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened

    Scenario: [Navigation][Activity] User must be able to navigate to activity overview page by clicking its name in the activity subgroup overview page
        When The activity overview page can be opened by clicking the activity link in overview page
        Then Activity overview page is opened

    Scenario: [COSMoS YAML] Verify that the instance overview page displays all sections correctly
        When I click on the COSMoS YAML tab
        When The download button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # And the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When The close overview button is clicked
        Then Subgroup overview page is opened      

    Scenario: [Sections] Verify that the activity subgroup overview page version 2 displays correctly
        And The 'Activity group' table is displaying correct columns
        |  header     |
        |  Name       |
        |  Version    |
        |  Status     |
        And The 'Activities' table is displaying correct columns
        |  header     |
        |  Name       |
        |  Requested  |
        |  Version    |
        |  Status     |
        And The linked group is found in the Groups table with status 'Final' and version '1.0'
        #And The free text search field should be displayed in the 'Activity group' table
        And The linked activity is found in the Acivities table with status 'Final' and version '1.0'
        And The free text search field should be displayed in the 'Activities' table

    Scenario: [History] Verify that the activity group overview page displays correctly
        When The history button is clicked
        Then The history page is opened

    Scenario: [Linking] Verify that the activities subgroup overview page version 2 can link to the correct subgroup
        When Version '0.1' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Draft' and version is '0.1'
        And The Start date value is saved
        Then The correct End date should be displayed
        And The linked group is found in the Groups table with status 'Final' and version '1.0'
        And The Activities table is empty
        When Version '1.0' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Final' and version is '1.0'
        Then The linked group is found in the Groups table with status 'Final' and version '1.0'
        And The linked activity is found in the Acivities table with status 'Final' and version '1.0'

    Scenario: [Edit][1.1] Edit the SubGroup
        When The new version plus button is clicked
        And The linked activity is found in the Acivities table with status 'Final' and version '1.0'
        #waiting for API implementation
        #And The linked group is found in the Groups table with status 'Final' and version '1.0'
        Then The status displayed on the summary has value 'Draft' and version is '1.1'
        When The pencil button is clicked
        And Subgroup name is changed
        And Form save button is clicked
        Then The status displayed on the summary has value 'Draft' and version is '1.2'
        And The Activities table is empty
        #And The Group table is empty

    Scenario: [Approve] Approve the SubGroup
        When The approve button is clicked
        Then The status displayed on the summary has value 'Final' and version is '2.0'
        And The linked activity is found in the Acivities table with status 'Final' and version '2.0'
        And The linked group is found in the Groups table with status 'Final' and version '1.0'

    @pending_implementation
    Scenario: [Table][Search][Negative case] User must be able to search not existing group and table will be correctly filtered
        When User searches for non-existing item in 'Activity group' table
        Then The Activities groups table is empty

    Scenario: [Table][Search][Negative case] User must be able to search not existing activity and table will be correctly filtered
        When User searches for non-existing item in 'Activities' table
        Then The Activities table is empty

    @pending_implementation
    Scenario: [Table][Search][Postive case] User must be able to search groups connected to subgroup
        And Overview page for subgroup created via API is opened
        Then Subgroup overview page is opened
        And User searches for group in linked Activity Group table
        Then 1 result is present in the 'Activity group' table
        And Group name is present in first row of the Activity Group table
        And User searches for group by using partial name in linked Activity Group table
        Then 2 result is present in the 'Activity group' table

    Scenario: [Table][Search][Postive case] User must be able to search created activities connected to subgroup
        And [API] Activity is created
        And [API] Activity is approved
        And Overview page for subgroup created via API is opened
        Then Subgroup overview page is opened
        And User searches for activity in linked Activities table
        Then 1 result is present in the 'Activities' table
        And Activity name is present in first row of the linked Activity table
        And User searches for activity by using partial name in linked Activities table
        Then 2 result is present in the 'Activities' table

    @pending_implementation
    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity in group table
        And User searches for group by using lowecased name in linked Activity Group table
        Then 1 result is present in the 'Activity group' table
        And Group name is present in first row of the Activity Group table

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity in activities table
        And User searches for activity by using lowecased name in linked Activities table
        Then 1 result is present in the 'Activities' table
        And Activity name is present in first row of the linked Activity table

    @manual_test
    Scenario: [Table][Pagination] Verify that the pagination works in both Activity group and Activities table
        When I select 5 rows per page from dropdown list in the Activity group table
        Then The Activity group table should be displayed with 5 rows per page
        When I click on the next page button in the Activity group table
        Then The Activities table should display the next page within 5 rows per page
        When I select 5 rows per page from dropdown list in the Activities table
        Then The Activities table should be displayed with 5 rows per page
        When I click on the next page button in the Activities table
        Then The Activities table should display the next page within 5 rows per page

    @manual_test
    Scenario: [Table][Export] Verify export functionality work in both Activity group and Activities table
        And The free text search field works in both Activity group and Activities table
        And The Export functionality works in both Activity group and Activities table
        And The Filter functionality works in both Activity group and Activities table