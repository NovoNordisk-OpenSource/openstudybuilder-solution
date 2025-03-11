@REQ_ID:1070683
Feature: Library - Concept Overview Pages Display
    As a user, I want to verify that every Overview Page in the Concepts Library, including Activities, 
        Activity Groups, Activity Subgroups, and Activity Instances can display correctly.

    Background: 
        Given The user is logged in
        And A test group has been created
        And A test subgroup has been created and linked to the test group
        And A test activity has been created and linked to the test group
        And A test activity instance has been created and linked to the test activity

    Scenario: Verify that the activities overview page displays correctly
        Given The '/library/activities/activities' page is opened
        When I search for the test activity through the filter field
        And I click on the link for the test group in the activity page
        Then The test group overview page should be opened
        When I click on the link for the test subgroup in the activity page
        Then The test subgroup overview page should be opened
        When I click on the test activity name in the activity page
        Then The test activity overview page should be opened
        And The test group, test subgroup and test instance should be displayed on the test activity overview page
        And The group overview page can be opened by clicking the group link in the activity overview page
        And The subgroup overview page can be opened by clicking the subgroup link in the activity overview page

    Scenario: Verify that the instance overview page displays correctly
        Given The '/library/activities/activity-instances' page is opened
        When I search for the test instance through the filter field
        Then The test group, test subgroup and test activity should be displayed in the row of the test instance
        When I click on the link for the test group in the instance page
        Then The test group overview page should be opened
        When I click on the link for the test subgroup in the instance page
        Then The test subgroup overview page should be opened
        When I click on the link for the test instance name in the instance page
        Then The test instance overview page should be opened
        And The test group, test subgroup and test activity should be displayed on the test instance overview page
        And The group overview page can be opened by clicking the group link in the instance overview page
        And The subgroup overview page can be opened by clicking the subgroup link in the instance overview page
        And The activity overview page can be opened by clicking the activity link in the instance overview page

    Scenario: Verify that the group overview page displays correctly
        Given The '/library/activities/activity-groups' page is opened
        When I search for the test group through the filter field
        And I click on the link for the test group in the group page
        Then The test group overview page should be opened
        And The test subgroup should be displayed on the group overview page
        And The subgroup overview page can be opened by clicking the subgroup link in the group overview page

    Scenario: Verify that the subgroup overview page displays correctly
        Given The '/library/activities/activity-subgroups' page is opened
        When I search for the test subgroup through the filter field
        And I click on the link for the test group in the subgroup page
        Then The test group overview page should be opened
        When I click on the link for the test subgroup in the subgroup page
        Then The test subgroup overview page should be opened
        And The test group and test activity should be displayed on the subgroup overview page