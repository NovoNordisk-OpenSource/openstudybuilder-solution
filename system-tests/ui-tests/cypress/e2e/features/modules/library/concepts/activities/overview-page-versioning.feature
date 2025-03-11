@REQ_ID:XXXX 

Feature: Library - Concept Overview Page Versioning Check
  As a user, I want to verify that every Overview Page in the Concepts Library, including Activities, 
        Activity Groups, Activity Subgroups, and Activity Instances can manage the version correctly.

  Background: User is logged in
    Given The user is logged in

  Scenario: Verify Activity and Instances 
    Given The '/library/activities/activities' page is opened
    And The activity exists with status as Final
    When The '/library/activities/activity-instances' page is opened
    And The test Activity Instance with status Final and version 1.0 is linked to the test activity 
    When The '/library/activities/activities' page is opened
    And The 'Activities' tab is selected
    And I search and select activity
    Then I verify that at least one Activity Instance is linked to the test Activity 
    And I verify that the linked instances are version 1.0 and status Final

  Scenario: Edit an activity
    Given The '/library/activities/activities' page is opened
    And I search and select activity
    When I click 'New version' button
    Then I verify that the Activity version is '1.1' and status is 'Draft'
    When I click 'Edit' button 
    And I make changes to the activity, enter a reason for change and save
    Then I verify that the Activity version is '1.2' and status is 'Draft'
    And I verify that the Activity does not have any linked Activity Instances

  Scenario: Approve the Activity
    Given The '/library/activities/activities' page is opened
    And I search and select activity
    When I click 'Approve' button
    Then I verify that the Activity version is '2.0' and status is 'Final'
    And I verify that the linked Activity Instances list contains all the instances that were linked to the Activity version 1.0
    And I verify that each instance is listed as version 1.2 in status Draft and version 2.0 in status Final

  @manual_test
  Scenario: Verify Group and Subgroup 
    Given The '/library/activities/activity-groups' page is opened
    And The group exists with status as Final
    When The '/library/activities/activity-subgroups' page is opened
    And The test subgroup with status Final and version 1.0 is linked to the test group 
    When The '/library/activities/activity-groups' page is opened
    And The 'Activity Groups' tab is selected
    And I search and open the group overview page
    Then I verify that at least one subgroup is linked to the test group
    And I verify that the linked subgroups are version 1.0 and status Final

  @manual_test
  Scenario: Edit a Group
    Given The '/library/activities/activity-groups' page is opened
    And I search and open the group overview page
    When I click 'New version' button
    Then I verify that the group version is '1.1' and status is 'Draft'
    When I click 'Edit' button 
    And I make changes to the group, enter a reason for change and save
    Then I verify that the group version is '1.2' and status is 'Draft'
    And I verify that the group does not have any linked subgroups

  @manual_test
  Scenario: Approve the Group
    Given The '/library/activities/activity-groups' page is opened
    And I search and open the group overview page
    When I click 'Approve' button
    Then I verify that the group version is '2.0' and status is 'Final'
    And I verify that the linked subgroup list contains all the subgroups that were linked to the group version 1.0
    And I verify that each subgroup is listed as version 1.2 in status Draft and version 2.0 in status Final

  @manual_test
  Scenario: Switch between edit version and previous version for activity overview page
    Given The '/library/activities/activities' page is opened
    And I search and select activity
    And The current version is 1.0 with final status, and the definition is "original def"
    When Click new version button
    Then The page should show the new version 1.1 and Draft status 
    When Click edit version button
    And Update definition to "new def" and reason for change
    And Click on save button
    Then The page should show the new version 1.2, Draft status, and with updated information
    When Select the earlier version 1.0 from the version dropdown list
    Then The page should display the correct information for version 1.0 like "original def"
    
  @manual_test
  Scenario: Switch between edit version and previous version for group overview page 
    Given The '/library/activities/activity-groups' page is opened
    And I search and open the group overview page
    And The current version is 1.0 with final status, and the definition is "original def"
    When Click new version button
    Then The page should show the new version 1.1 and Draft status 
    When Click edit version button
    And Update definition to "new def" and reason for change
    And Click on save button
    Then The page should show the new version 1.2, Draft status, and with updated information
    When Select the earlier version 1.0 from the version dropdown list
    Then The page should display the correct information for version 1.0 like "original def"

@manual_test
  Scenario: Switch between edit version and previous version for subgroup overview page 
    Given The '/library/activities/activity-subgroups' page is opened
    And I search and open the subgroup overview page
    And The current version is 1.0 with final status, and the definition is "original def"
    When Click new version button
    Then The page should show the new version 1.1 and Draft status 
    When Click edit version button
    And Update definition to "new def" and reason for change
    And Click on save button
    Then The page should show the new version 1.2, Draft status, and with updated information
    When Select the earlier version 1.0 from the version dropdown list
    Then The page should display the correct information for version 1.0 like "original def"

@manual_test
  Scenario: Switch between edit version and previous version for instance overview page 
    Given The '/library/activities/activity-instances' page is opened
    And I search and open the instance overview page
    And The current version is 1.0 with final status, and the definition is "original def"
    When Click new version button
    Then The page should show the new version 1.1 and Draft status 
    When Click edit version button
    And Update definition to "new def" and reason for change
    And Click on save button
    Then The page should show the new version 1.2, Draft status, and with updated information
    When Select the earlier version 1.0 from the version dropdown list
    Then The page should display the correct information for version 1.0 like "original def"