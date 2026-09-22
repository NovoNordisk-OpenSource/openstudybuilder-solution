@REQ_ID:1070683 @skip_on_prv_val

Feature: Library - Concepts - Activities - Activity Overview Page
    As a user, I want to verify that the Activity Overview Page in the Concepts Library, can display correctly.

    Background: 
        Given The user is logged in
        When [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
        And Group, subgroup, activity and instance names created through API are found
        And Overview page for activity created via API is opened
        And User intercepts linked instances to activities request
        And Activity overview page is opened
        And User waits for linked instances to activity request

    Scenario: [Navigation][Group] User must be able to navigate to activity group overview page by clicking its name in the activity instance table
        Given The '/library/activities/activities' page is opened
        When Activity created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened

    Scenario: [Navigation][Group] User must be able to navigate to activity group overview page by clicking its name in the instance overview page
        And User sets visibility of Activity groupings table columns to true
        When The group overview page can be opened by clicking the group link in overview page
        Then Group overview page is opened

    Scenario: [Navigation][Subgroup] User must be able to navigate to activity subgroup overview page by clicking its name in the activity instance table
        Given The '/library/activities/activities' page is opened
        When Activity created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened

    Scenario: [Navigation][Subgroup] User must be able to navigate to activity group overview page by clicking its name in the instance overview page
        And User sets visibility of Activity groupings table columns to true
        When The subgroup overview page can be opened by clicking the subgroup link in overview page
        Then Subgroup overview page is opened

    Scenario: [Navigation][Activity] User must be able to navigate to activity overview page by clicking its name in the activity instance table
        Given The '/library/activities/activities' page is opened
        When Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
    
    Scenario: [Navigation][Activity Instance] User must be able to navigate to activity instance overview page by clicking its name in the instance overview page
        When The activity instance overview page can be opened by clicking the activity link in overview page
        Then Instance overview page is opened

    Scenario: [COSMoS YAML] Verify that the instance overview page displays all sections correctly
        When I click on the COSMoS YAML tab
        When The download button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # And the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When The close overview button is clicked
        Then Activity overview page is opened       

    Scenario: [Sections] Verify that the activities overview page displays correctly
        And User sets visibility of Activity groupings table columns to true
        And User waits for the table
        And The 'Activity groupings' table is displaying correct columns
        |  header                  |
        |  Activity group          |
        |  Activity subgroup       |
        |  Activity instances      |
        And The 'Activity instances' table is displaying correct columns
        |  header                   |
        |  Name                     |
        |  Version                  |
        |  Status                   |
        |  Activity Instance class  |
        |  Topic code               |
        |  Adam parameter code      |
        And The Activity linked group, subgroup and instance are displayed in the Activity groupings table
        And The free text search field should be displayed in the 'Activity groupings' table
        Then The linked activity instance is found in the Acivity Instances table with status 'Final' and version '1.0'
        And The free text search field should be displayed in the 'Activity instances' table
        And User waits for 1 seconds
        And Activity instance is expanded by clicking chevron button
        And The previous version of linked activity instance is found in the Acivity Instances table in row 2 with status 'Draft' and version '0.1'

    Scenario: [History] Verify that the activity group overview page displays correctly
        When The history button is clicked
        Then The history page is opened
        
    Scenario: [Linking] Verify that the activities overview page can link to the correct groups, subgroups and instances
        And User sets visibility of Activity groupings table columns to true
        When Version '0.1' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Draft' and version is '0.1'
        And The Start date value is saved
        Then The correct End date should be displayed
        And The Activity linked group, subgroup and instance are displayed in the Activity groupings table
        And The linked activity instance is found in the Acivity Instances table with status 'Final' and version '1.0'
        And User intercepts linked instances to activities request
        When Version '1.0' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Final' and version is '1.0'
        And User waits for linked instances to activity request
        Then The Activity linked group, subgroup and instance are displayed in the Activity groupings table
        Then The linked activity instance is found in the Acivity Instances table with status 'Final' and version '1.0'
        And User waits for 1 seconds
        And Activity instance is expanded by clicking chevron button
        And The previous version of linked activity instance is found in the Acivity Instances table in row 2 with status 'Draft' and version '0.1'

    Scenario: [Edit][1.1] Edit the activity
        When The new version plus button is clicked
        And The status displayed on the summary has value 'Draft' and version is '1.1'
        And The linked activity instance is found in the Acivity Instances table with status 'Final' and version '1.0'
        And User waits for 1 seconds
        And Activity instance is expanded by clicking chevron button
        And User waits for 1 seconds
        And The previous version of linked activity instance is found in the Acivity Instances table in row 2 with status 'Draft' and version '0.1'
        When The pencil button is clicked
        And Activity name is changed
        And Form save button is clicked
        And The status displayed on the summary has value 'Draft' and version is '1.2'
        And The Activity Instances table is empty
        
    Scenario: [Approve] Approve the Activity
        When The approve button is clicked
        Given User waits for linked instances to load
        And Form save button is clicked
        And The pop up displays 'Instance linking updated successfully'
        And The page is reloaded
        And The status displayed on the summary has value 'Final' and version is '2.0'
        And The linked activity instance is found in the Acivity Instances table with status 'Final' and version '1.0'

    Scenario: [Edit][2.1] Edit the activity with draft instance
        When The new version plus button is clicked
        And The status displayed on the summary has value 'Draft' and version is '2.1'
        When The pencil button is clicked
        And Activity name is changed
        And Form save button is clicked
        And The status displayed on the summary has value 'Draft' and version is '2.2'
        When The approve button is clicked
        Given User waits for linked instances to load
        And Form save button is clicked
        And The pop up displays 'Instance linking updated successfully'
        And The page is reloaded
        And The status displayed on the summary has value 'Final' and version is '3.0'
        And The linked activity instance is found in the Acivity Instances table with status 'Final' and version '1.0'

    Scenario: [Table][Search][Negative case] User must be able to search not existing grouping and table will be correctly filtered
        And User sets visibility of Activity groupings table columns to true
        When User searches for non-existing item in 'Activity groupings' table
        Then The Activity groupings table is empty

    Scenario: [Table][Search][Negative case] User must be able to search not existing instance and table will be correctly filtered
        When User searches for non-existing item in 'Activity instances' table
        Then The Activity Instances table is empty

    @smoke_test
    Scenario: [Table][Search][Postive case] User must be able to search subgroups connected to group
        When [API] An activity connected to two instances is created
        And [API] Fetch names of activity with two connected instances
        And User intercepts linked instances to activities request
        And Overview page for activity created via API is opened
        And Activity overview page is opened
        And User waits for linked instances to activity request
        And User searches for instance in linked Instances table
        Then 1 result is present in the 'Activity instances' table
        And Activity Instance name is present in first row of the linked Instances table
        And User searches for instance by using partial name in linked Instances table
        Then 2 result is present in the 'Activity instances' table

    @manual_test
    Scenario: [Table][Pagination] Verify that the pagination works in both Activity groupings and Activity instances table
        When I select 5 rows per page from dropdown list in the Activity groupings table
        Then The Activity groupings table should be displayed with 5 rows per page
        When I click on the next page button in the Activity groupings table
        Then The Activity groupings table should display the next page within 5 rows per page
        When I select 10 rows per page from the dropdown list in the Activity instances table
        Then The Activity instances table should be displayed with 10 rows per page
        When I click on the next page button in the Activity instances table
        Then The Activity instances table should display the next page with 10 rows per page

    @manual_test
    Scenario: [Table][Export] Verify that the export functionality work in both Activity groupings and Activity instances table
        And The Export functionality works in both Activity groupings and Activity instances table