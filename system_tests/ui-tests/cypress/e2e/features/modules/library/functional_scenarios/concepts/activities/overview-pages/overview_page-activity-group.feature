@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Group Overview Page
    As a user, I want to verify that the Activity Group Overview Page in the Concepts Library, can display correctly.

    Background: 
        Given The user is logged in
        When [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
        And Group, subgroup, activity and instance names created through API are found
        And Overview page for group created via API is opened
        And Group overview page is opened

    Scenario: [Navigation][Group] User must be able to navigate to activity group overview page by clicking its name in the group table
        Given The '/library/activities/activity-groups' page is opened
        When Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened

    Scenario: [Navigation][Subgroup] User must be able to navigate to activity group overview page by clicking its name in the group overview page
        When The subgroup overview page can be opened by clicking the subgroup link in overview page
        Then Subgroup overview page is opened

    Scenario: [COSMoS YAML] Verify that the group overview page displays all sections correctly
        When I click on the COSMoS YAML tab
        When The download button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # And the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When The close overview button is clicked
        Then Group overview page is opened   

    Scenario: [Sections] Verify that the activity group overview page displays correctly
        And The 'Activity subgroups' table is displaying correct columns
        |  header     |
        |  Name       |
        |  Definition |
        |  Version    |
        |  Status     |
        And The linked subgroup is found in the Groups table with status 'Final' and version '1.0'
        And The free text search field should be displayed in the 'Activity subgroups' table

    Scenario: [History] Verify that the activity group overview page displays correctly
        When The history button is clicked
        Then The history page is opened
    
    Scenario: [Linking] Verify that the activities group overview page can link to the correct subgroup
        When Version '0.1' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Draft' and version is '0.1'
        And The Start date value is saved
        Then The correct End date should be displayed
        And The Activity subgroups table is empty
        When Version '1.0' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Final' and version is '1.0'
        Then The linked subgroup is found in the Groups table with status 'Final' and version '1.0'

    Scenario: [Edit][1.1] Edit the Group
        When The new version plus button is clicked
        Then The status displayed on the summary has value 'Draft' and version is '1.1'
        And The linked subgroup is found in the Groups table with status 'Final' and version '1.0'
        When The pencil button is clicked
        And Group name is changed
        And Form save button is clicked
        Then The status displayed on the summary has value 'Draft' and version is '1.2'
        And The Activity subgroups table is empty

    Scenario: [Approve] Approve the Group
        When The approve button is clicked
        Then The status displayed on the summary has value 'Final' and version is '2.0'
        And The linked subgroup is found in the Groups table with status 'Final' and version '1.0'

    Scenario: [Edit][2.1] Edit the Group
        When The new version plus button is clicked
        And The status displayed on the summary has value 'Draft' and version is '2.1'
        When The pencil button is clicked
        And Group name is changed
        And Form save button is clicked
        And The status displayed on the summary has value 'Draft' and version is '2.2'
        When The approve button is clicked
        And The status displayed on the summary has value 'Final' and version is '3.0'
        And The linked subgroup is found in the Groups table with status 'Final' and version '1.0'
  
    Scenario: [Linking][New subgroup] Verify that the activities group overview page can link to the correct subgroup with different versions
        And [API] Activity subgroup is created
        And [API] Activity subgroup is approved
        And [API] Activity is created
        And Subgroup name created through API is found
        When The '/library/activities/activities' page is opened
        And Overview page for group created via API is opened
        And Group overview page is opened
        When Version '2.0' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Final' and version is '2.0'
        Then The linked subgroup is found in the Groups table with status 'Final' and version '1.0'
        When Version '3.0' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Final' and version is '3.0'
        Then Both subgroups are visible in the Activity subgroup table with status 'Final' and version '1.0'

    Scenario: [Table][Search][Negative case] User must be able to search not existing subgroup and table will be correctly filtered
        When User searches for non-existing item in 'Activity subgroups' table
        Then The Activity subgroups table is empty

    @smoke_test
    Scenario: [Table][Search][Postive case] User must be able to search subgroups connected to group
        And Overview page for group created via API is opened
        And Group overview page is opened
        And User searches for subgroup in linked Subgroups table
        Then 1 result is present in the 'Activity subgroup' table
        And Subgroup name is present in first row of the Activity Subgroup table
        And User searches for subgroup by using partial name in linked Subgroups table
        Then 2 result is present in the 'Activity subgroup' table

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity in subroup table
        And User searches for subgroup by using lowecased name in linked Subgroups table
        Then 1 result is present in the 'Activity subgroup' table
        And Subgroup name is present in first row of the Activity Subgroup table

    @manual_test
    Scenario: Verify that the pagination works in the Activity subgroups table
        When I select 5 rows per page from dropdown list in the Activity subgroups table
        Then The Activity subgroups table should be displayed with 5 rows per page
        When I click on the next page button in the Activity subgroups table
        Then The Activity subgroups table should display the next page within 5 rows per page
         When I select 10 rows per page from dropdown list in the Activity subgroups table
        Then The Activity subgroups table should be displayed with 10 rows per page
        When I click on the next page button in the Activity subgroups table
        Then The Activity subgroups table should display the next page within 10 rows per page

    @manual_test
    Scenario: Verify that the export functionality work in the Activity subgroups table
        And The Export functionality works in the Activity subgroups table