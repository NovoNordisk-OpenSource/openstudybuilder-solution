@REQ_ID:XXXX 

Feature: Library - Concept Overview Page Versioning Check
  As a user, I want to verify that every Overview Page in the Concepts Library, including Activities, 
        Activity Groups, Activity Subgroups, and Activity Instances can manage the version correctly.

  Background: User is logged in
    Given The user is logged in
    When The '/administration' page is opened
    And The 'Feature flags' button is clicked
    Then Activity instance wizard feature flag is turned off
    And [API] Activity Instance in status Final with Final group, subgroub and activity linked exists
    And [API] Activity, activity instance, group and subgroup names are fetched
    
  Scenario: Edit the activity
    Given The '/library/activities/activities' page is opened
    And A test activity overview page is opened
    When I click 'New version' button
    Then I verify that the version is '1.1' and status is 'Draft'
    And I verify that there is an instance with status 'Final' and version '1.0'
    And I verify that there is an instance with status 'Draft' and version '0.1'
    When I click 'Edit' button 
    And I make changes to the activity, enter a reason for change and save
    Then I verify that the version is '1.2' and status is 'Draft'
    And I verify that no 'Activity instances' is linked

  Scenario: Approve the Activity
    Given The '/library/activities/activities' page is opened
    And A test activity overview page is opened
    When I click 'Approve' button
    Then I verify that the version is '2.0' and status is 'Final'
    And I verify that there is an instance with status 'Final' and version '2.0'
    And I verify that there is an instance with status 'Draft' and version '1.2'
 
Scenario: Edit the Instance
    Given The '/library/activities/activity-instances' page is opened
    And A test instance overview page is opened
    When I click 'New version' button
    Then I verify that the version is '2.1' and status is 'Draft'
    And I verify that there is an activity with status 'Final' and version '2.0'
    When I click 'Edit' button 
    And I make changes to the instance and save
    Then I verify that the version is '2.2' and status is 'Draft'
    # I verify that no 'Activity' is linked (API and UI not implemented yet)
 
  Scenario: Approve the Instance
    Given The '/library/activities/activity-instances' page is opened
    And A test instance overview page is opened
    When I click 'Approve' button
    Then I verify that the version is '3.0' and status is 'Final'
    And I verify that there is an activity with status 'Final' and version '2.0'

  Scenario: Edit the Group
    Given The '/library/activities/activity-groups' page is opened
    And A test group overview page is opened
    When I click 'New version' button
    Then I verify that the version is '1.1' and status is 'Draft'
    And I verify that there is a subgroup with status 'Final' and version '1.0'
    When I click 'Edit' button 
    And I make changes to the group, enter a reason for change and save
    Then I verify that the version is '1.2' and status is 'Draft'
    # And I verify that no 'Activity subgroups' is linked (API and UI not implemented yet)

  Scenario: Approve the Group
    Given The '/library/activities/activity-groups' page is opened
    And A test group overview page is opened
    When I click 'Approve' button
    Then I verify that the version is '2.0' and status is 'Final'
    #And I verify that there is a subgroup with status 'Draft' and version '1.2'
    #version incrementation not implemented yet
    #And I verify that there is a subgroup with status 'Final' and version '1.0' 
    
  Scenario: Edit the SubGroup
    Given The '/library/activities/activity-subgroups' page is opened
    And A test subgroup overview page is opened
    When I click 'New version' button
    And I verify that there are activities with status 'Final' and version '2.0'
    #waiting for API implementation
    #And I verify that there is a group with status 'Final' and version '2.0'
    Then I verify that the version is '1.1' and status is 'Draft'
    When I click 'Edit' button 
    And I make changes to the subgroup, enter a reason for change and save
    Then I verify that the version is '1.2' and status is 'Draft'
    And I verify that no 'Activities' is linked
    # And I verify that no 'Activity group' is linked  (API and UI not implemented yet)

  Scenario: Approve the SubGroup
    Given The '/library/activities/activity-subgroups' page is opened
    And A test subgroup overview page is opened
    When I click 'Approve' button
    Then I verify that the version is '2.0' and status is 'Final'
    #waiting for API implmentation
    #And I verify that there are activities with status 'Draft' and version '1.2'
    #And I verify that there are activities with status 'Final' and version '2.0'
    #And I verify that there is a group with status 'Final' and version '2.0'

 @manual_test 
  Scenario: Switch between edit version and previous version for instance overview page 
    Given The '/library/activities/activity-instances' page is opened
    And A test instance overview page is opened
    Then I verify that the version is '2.0' and status is 'Final'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then I verify that the version is '2.1' and status is 'Draft'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then I verify that the version is '2.2' and status is 'Draft'
    And I verify the definition is 'new def'
    When I select the earlier version 2.0 from the version dropdown list
    Then I verify that the version is '2.0' and status is 'Final'
    And I verify the definition is 'def'

  @manual_test  
  Scenario: Switch between edit version and previous version for activity overview page
    Given The '/library/activities/activities' page is opened
    And A test activity overview page is opened
    Then I verify that the version is '2.0' and status is 'Final'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then I verify that the version is '2.1' and status is 'Draft'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then I verify that the version is '2.2' and status is 'Draft'
    And I verify the definition is 'new def'
    When I select the earlier version 2.0 from the version dropdown list
    Then I verify that the version is '2.0' and status is 'Final'
    And I verify the definition is 'def'

  @manual_test 
  Scenario: Switch between edit version and previous version for group overview page 
    Given The '/library/activities/activity-groups' page is opened
    And A test group overview page is opened
    Then I verify that the version is '2.0' and status is 'Final'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then I verify that the version is '2.1' and status is 'Draft'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then I verify that the version is '2.2' and status is 'Draft'
    And I verify the definition is 'new def'
    When I select the earlier version 2.0 from the version dropdown list
    Then I verify that the version is '2.0' and status is 'Final'
    And I verify the definition is 'def'

@manual_test
  Scenario: Switch between edit version and previous version for subgroup overview page 
    Given The '/library/activities/activity-subgroups' page is opened
    And A test subgroup overview page is opened
    Then I verify that the version is '2.0' and status is 'Final'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then I verify that the version is '2.1' and status is 'Draft'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then I verify that the version is '2.2' and status is 'Draft'
    And I verify the definition is 'new def'
    When I select the earlier version 2.0 from the version dropdown list
    Then I verify that the version is '2.0' and status is 'Final'
    And I verify the definition is 'def'
