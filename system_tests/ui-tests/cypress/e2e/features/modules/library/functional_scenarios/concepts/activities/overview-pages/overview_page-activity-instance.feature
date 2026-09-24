@REQ_ID:1070683 @skip_on_prv_val

Feature: Library - Concepts - Activities - Activity Instance Overview Page
    As a user, I want to verify that the Activity Instance Overview Page in the Concepts Library, can display correctly.

    Background: 
        Given The user is logged in
        When [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
        And Group, subgroup, activity and instance names created through API are found
        And User intecepts activity groupings request
        And User intecepts activity items request
        And Overview page for activity instance created via API is opened
        And Instance overview page is opened
        And User waits for activity groupings request
        And User waits for activity items request

    Scenario: [Navigation][Group] User must be able to navigate to activity group overview page by clicking its name in the activity instance table
        Given The '/library/activities/activity-instances' page is opened
        When Activity instance created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened

    Scenario: [Navigation][Group] User must be able to navigate to activity group overview page by clicking its name in the instance overview page
        When The group overview page can be opened by clicking the group link in overview page
        Then Group overview page is opened

    Scenario: [Navigation][Subgroup] User must be able to navigate to activity subgroup overview page by clicking its name in the activity instance table
        Given The '/library/activities/activity-instances' page is opened
        When Activity instance created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened

    Scenario: [Navigation][Subgroup] User must be able to navigate to activity group overview page by clicking its name in the instance overview page
        When The subgroup overview page can be opened by clicking the subgroup link in overview page
        Then Subgroup overview page is opened

    Scenario: [Navigation][Activity] User must be able to navigate to activity overview page by clicking its name in the activity instance table
        Given The '/library/activities/activity-instances' page is opened
        When Activity instance created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened

    Scenario: [Navigation][Activity] User must be able to navigate to activity overview page by clicking its name in the instance overview page
        When The activity overview page can be opened by clicking the activity link in overview page
        Then Activity overview page is opened
    
    Scenario: [Navigation][Activity Instance] User must be able to navigate to activity overview page by clicking its name in the activity instance table
        Given The '/library/activities/activity-instances' page is opened
        When Activity instance created via API is searched for and found
        And User goes to instance overview page by clicking its name
        Then Instance overview page is opened

    Scenario: [COSMoS YAML] Verify that the instance overview page displays all sections correctly
        When I click on the COSMoS YAML tab
        And User waits for 1 seconds
        When The download button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # Ad the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When The close overview button is clicked
        Then Instance overview page is opened       
        
    Scenario: [Sections] Verify that the activities instance overview page displays correctly
        And The 'Activity groupings' table is displaying correct columns
        |  header                  |
        |  Activity group          |
        |  Activity subgroup       |
        |  Activity                |
        And The 'Activity Items' table is displaying correct columns
        |  header                  |
        |  Activity Item Class     |
        |  Data type               |
        |  Name                    |
        |  Submission value        |
        And The Instance linked group, subgroup and instance are displayed in the Activity groupings table
        And The free text search field should be displayed in the 'Activity groupings' table
        And The free text search field should be displayed in the 'Activity Items' table

    Scenario: [History] Verify that the activity instance attributes history page displays correctly
        When Activity instance attributes history button is clicked
        Then The history page is opened

    Scenario: [History] Verify that the activity instance groupings history page displays correctly
        When Activity instance groupings history button is clicked
        Then The history page is opened

    Scenario: [Linking] Verify that the activities instance overview page can link to the correct groups, subgroups and activities
        When Version '0.1' is selected from the Version dropdown list in the instance attributes section
        And The status displayed on the summary for Activity Instance Attributes is 'Draft' and version is '0.1'
        And The Start date value is saved
        Then The correct End date should be displayed
        And The Instance linked group, subgroup and instance are displayed in the Activity groupings table
        And The Activity Items table is empty
        When Version '1.0' is selected from the Version dropdown list in the instance attributes section
        And The status displayed on the summary for Activity Instance Attributes is 'Final' and version is '1.0'
        Then The Instance linked group, subgroup and instance are displayed in the Activity groupings table

    Scenario: [Edit] Edit the Instance Attributes
        When [API] The feature flag 'new_activity_instance_wizard_stepper' is enabled
        When [API] The feature flag 'activity_instance_wizard_stepper_edit_mode' is enabled
        And Overview page for activity instance created via API is opened
        And Instance overview page is opened
        When Activity instance attributes new version button is clicked
        And The status displayed on the summary for Activity Instance Attributes is 'Draft' and version is '1.1'
        And The Instance linked group, subgroup and instance are displayed in the Activity groupings table
        And The Instance linked activity has status 'Final' and version '1.0'
        And The pencil button is clicked
        Then The Activity Instance Attributes edition page is displayed

    Scenario: [Approve] Approve the Instance Attributes
        When Activity instance approve attributes button is clicked
        Then The status displayed on the summary for Activity Instance Attributes is 'Final' and version is '2.0'
        And The Instance linked group, subgroup and instance are displayed in the Activity groupings table
        And The Instance linked activity has status 'Final' and version '1.0'

    Scenario: [Approve] Approve the Instance Groupings
        Given Activity instance groupings new version button is clicked
        Then User waits for 3 seconds
        When Activity instance approve groupings button is clicked
        Then The status displayed on the summary for Activity Instance Groupings is 'Final' and version is '2.0'
        And The Instance linked group, subgroup and instance are displayed in the Activity groupings table
        And The Instance linked activity has status 'Final' and version '1.0'

    Scenario: [Table][Search][Negative case] User must be able to search not existing grouping and table will be correctly filtered
        When User searches for non-existing item in 'Activity groupings' table
        Then The Activity groupings table for Instance is empty

    Scenario: [Table][Search][Negative case] User must be able to search not existing activity items and table will be correctly filtered
        When User searches for non-existing item in 'Activity Items' table
        Then The Activity Items table is empty

    @pending_development
    Scenario: [Table][Pagination] Verify that the pagination works in both Activity groupings and Activity items table
        When I select 5 rows per page from dropdown list in the Activity groupings table
        Then The Activity groupings table should be displayed with 5 rows per page
        When I click on the next page button in the Activity groupings table
        Then The Activity grouping table should display the next page within 5 rows per page
        When I select 5 rows per page from dropdown list in the Activity items table
        Then The Activity items table should be displayed with 5 rows per page
        When I click on the next page button in the Activity items table
        Then The Activity items table should display the next page within 5 rows per page

    @manual_test
    Scenario: [Table][Export] Verify that the export functionality work in both Activity groupings and Activity items table
        And The Export functionality works in both Activity groupings and Activity items table