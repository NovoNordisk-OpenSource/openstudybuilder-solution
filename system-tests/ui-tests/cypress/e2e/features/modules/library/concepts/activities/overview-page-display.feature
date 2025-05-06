@REQ_ID:1070683
Feature: Library - Concept Overview Pages Display
    As a user, I want to verify that every Overview Page in the Concepts Library, including Activities, 
        Activity Groups, Activity Subgroups, and Activity Instances can display correctly.

    Background: 
        Given The user is logged in
        When [API] Activity Instance in status Final with Final group, subgroub and activity linked exists
        And Group name created through API is found
        And Subgroup name created through API is found
        And Activity name created through API is found
        And Instance name created through API is found

    Scenario: Verify that the activities overview page displays correctly
        Given The '/library/activities/activities' page is opened
        When I search for the test activity through the filter field
        And I click on the link for the test group in table
        Then The test group overview page should be opened
        When I click on the link for the test subgroup in the activity page
        Then The test subgroup overview page should be opened
        When I click on the test activity name in the activity page
        Then The test activity overview page should be opened
        When I click on the history button
        Then The history page should be opened
        And The test group, test subgroup and test instance should be displayed on the test activity overview page
        And The group overview page can be opened by clicking the group link in overview page
        And The subgroup overview page can be opened by clicking the subgroup link in overview page
        When I click on the COSMoS YAML tab
        Then The COSMoS YAML page should be opened with Download button and Close button displayed
        When The Download YAML content button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # And the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When I click on the Close button in the COSMoS YAML page
        Then The test activity overview page should be opened

    Scenario: Verify that the instance overview page displays correctly
        Given The '/library/activities/activity-instances' page is opened
        When I search for the test instance through the filter field
        Then The test group, test subgroup and test activity should be displayed in the row of the test instance
        When I click on the link for the test group in table
        Then The test group overview page should be opened
        When I click on the link for the test subgroup in the instance page
        Then The test subgroup overview page should be opened
        When I click on the link for the test instance name in the instance page
        Then The test instance overview page should be opened
        When I click on the history button
        Then The history page should be opened
        And The test group, test subgroup and test activity should be displayed on the test instance overview page
        And The group overview page can be opened by clicking the group link in overview page
        And The subgroup overview page can be opened by clicking the subgroup link in overview page
        And The activity overview page can be opened by clicking the activity link in overview page
        #And The activity instance overview page can be opened by clicking the activity instance link in the instance overview page
        When I click on the COSMoS YAML tab
        Then The COSMoS YAML page should be opened with Download button and Close button displayed
        When The Download YAML content button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # Ad the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When I click on the Close button in the COSMoS YAML page
        Then The test instance overview page should be opened

    Scenario: Verify that the group overview page displays correctly
        Given The '/library/activities/activity-groups' page is opened
        When I search for the test group through the filter field
        And I click on the link for the test group in table
        Then The test group overview page should be opened
        When I click on the history button
        Then The history page should be opened
        And The test subgroup should be displayed on the group overview page
        And The subgroup overview page can be opened by clicking the subgroup link in overview page
        When I click on the COSMoS YAML tab
        Then The COSMoS YAML page should be opened with Download button and Close button displayed
        When The Download YAML content button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # And the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When I click on the Close button in the COSMoS YAML page
        Then The test group overview page should be opened

    Scenario: Verify that the subgroup overview page displays correctly
        Given The '/library/activities/activity-subgroups' page is opened
        When I search for the test subgroup through the filter field
        And I click on the link for the test group in table
        Then The test group overview page should be opened
        When I click on the link for the test subgroup in the subgroup page
        Then The test subgroup overview page should be opened
        When I click on the history button
        Then The history page should be opened
        And The test group and test activity should be displayed on the subgroup overview page
        When I click on the COSMoS YAML tab
        Then The COSMoS YAML page should be opened with Download button and Close button displayed
        When The Download YAML content button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # And the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When I click on the Close button in the COSMoS YAML page
        Then The test subgroup overview page should be opened
