@REQ_ID:1070684
Feature: Library - Syntax Templates - Time Frames - Parent
  As a user, I want to manage every Timeframe template under the Syntax template Library
  
  Background: User must be logged in
    Given The user is logged in

  Scenario: [Create][Sequence number] System must generate sequence number for Timeframe Templates when they are created
    Given [API] Timeframe template in status Draft exists
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The latest sequence number is saved
    And [API] Timeframe template in status Draft exists
    And The timeframe template is found
    Then Sequence number is incremented

  @smoke_test
  Scenario: [Create][Positive case] User must be able to create Timeframe template
    Given The '/library/timeframe_templates/parent' page is opened
    When The Add template button is clicked
    And The timeframe template form is filled with base data
    And Form save button is clicked
    Then The pop up displays 'Time frame template added'
    And The timeframe template is found
    Then The Timeframe is visible in the Table

  Scenario: [Create][Mandatory fields] User must not be able to create Timeframe template without: Template Text
    Given The '/library/timeframe_templates/parent' page is opened
    And The Add template button is clicked
    When Form save button is clicked
    Then The validation appears for timeframe name field

  Scenario: [Create][Mandatory fields] User must not be able to create Timeframe template with not unique Template Text
    Given [API] Timeframe template in status Draft exists
    And The '/library/timeframe_templates/parent' page is opened
    And The Add template button is clicked
    And The second timeframe is added with the same template text
    And Form save button is clicked
    Then The pop up displays 'already exists'
    And The user is not able to save

  Scenario: [Create][Syntax validation] User must be able to verify syntax when creating Timeframe template
    Given The '/library/timeframe_templates/parent' page is opened
    When The Add template button is clicked
    And The timeframe template form is filled with base data
    And The 'verify-syntax-button' button is clicked
    Then The pop up displays 'This syntax is valid'

  Scenario: [Create][Select parameters] User must be able to select parameter of the Activity Instruction template
    Given The '/library/timeframe_templates/parent' page is opened
    When The Add template button is clicked
    And The timeframe template form is filled with base data
    And Timeframe template text type is selected
    And Form save button is clicked
    Then The timeframe template is found
    And The Timeframe with paramter is visible in the Table

  @manual_test
  Scenario: User must be able to read change history of output
    Given The '/library/timeframe_templates/parent' page is opened
    When The user opens version history
    Then The user is presented with version history of the output containing timestamp and username

  @manual_test
  Scenario: User must be able to read change history of selected element
    Given The '/library/timeframe_templates/parent' page is opened
    And The 'Show history' option is clicked from the three dot menu list
    When The user clicks on History for particular element
    Then The user is presented with history of changes for that element
    And The history contains timestamps and usernames

    Scenario: [Cancel][Creation] User must be able to Cancel creation of the Timeframe template
    Given The '/library/timeframe_templates/parent' page is opened
    And The Add template button is clicked
    And The timeframe template form is filled with base data
    When Overlay cancel button is clicked
    Then The form is no longer available
    And The timeframe template is not found

  Scenario: [Cancel][Edition] User must be able to Cancel edition of the Timeframe template
    Given [API] Timeframe template in status Draft exists
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'Edit' option is clicked from the three dot menu list
    And The timeframe template edition form is filled with data
    And Overlay cancel button is clicked
    And Action is confirmed by clicking continue
    Then The form is no longer available
    And The timeframe template is not found

  Scenario: [Actions][Edit][0.1 version] User must be able to edit initial version of the Timeframe template
    Given [API] Timeframe template in status Draft exists
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'Edit' option is clicked from the three dot menu list
    And The timeframe template metadata update is started
    And Form save button is clicked
    Then The pop up displays 'Time frame template updated'
    And The timeframe template is found
    And The Timeframe is visible in the Table
    And The item has status 'Draft' and version '0.2'

  Scenario: [Actions][Edit][Mandatory fields] User must not be able to save changes to Timeframe template without: Change description
    Given [API] Timeframe template in status Draft exists
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'Edit' option is clicked from the three dot menu list
    And Change description for timeframe template is cleared
    And Form save button is clicked
    Then The validation appears for timeframe change description field

  Scenario: [Actions][Approve] User must be able to approve the Draft Timeframe template
    Given [API] Timeframe template in status Draft exists
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'Approve' option is clicked from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The item has status 'Final' and version '1.0'

  Scenario: [Actions][Delete] User must be able to delete the Draft Timeframe template in version below 1.0
    Given [API] Timeframe template in status Draft exists
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'Delete' option is clicked from the three dot menu list
    Then The pop up displays 'Timeframe template has been deleted'
    And The timeframe template is not found

  Scenario: [Actions][View history][Draft item] User must be able to view the history for the Draft Timeframe template
    Given [API] Timeframe template in status Draft exists
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'History' option is clicked from the three dot menu list
    Then The History for template window is displayed
    And The following column list with values will exist
      | header          |
      | Sequence number |
      | Template        |
      | Status          |
      | Version         |
      | Change type     |
      | User            |
      | From            |
      | To              |

  Scenario: [Actions][New version] User must be able to add a new version of the Final Timeframe template
    Given [API] Timeframe template in status Draft exists
    And [API] Timeframe template is approved
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'New version' option is clicked from the three dot menu list
    Then The pop up displays 'New version created'
    And The item has status 'Draft' and version '1.1'

  Scenario: [Actions][Edit][1.1 version] User must be able to edit new version of the Timeframe template
    Given [API] Timeframe template in status Draft exists
    And [API] Timeframe template is approved
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'New version' option is clicked from the three dot menu list
    Then The item has status 'Draft' and version '1.1'
    When The 'Edit' option is clicked from the three dot menu list
    And The timeframe template metadata update is started
    And Change description for timeframe template is provided
    And Form save button is clicked
    And The timeframe template is found
    Then The item has status 'Draft' and version '1.2'
    When The 'Approve' option is clicked from the three dot menu list
    Then The item has status 'Final' and version '2.0'

  Scenario: [Actions][Inactivate] User must be able to inactivate the Final Timeframe template
    Given [API] Timeframe template in status Draft exists
    And [API] Timeframe template is approved
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'Inactivate' option is clicked from the three dot menu list
    Then The pop up displays 'Template inactivated'
    And The item has status 'Retired' and version '1.0'

  Scenario: [Actions][View history][Final item] User must be able to view the history for the Draft Timeframe template
    Given [API] Timeframe template in status Draft exists
    And [API] Timeframe template is approved
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'History' option is clicked from the three dot menu list
    Then The History for template window is displayed
    And The following column list with values will exist
      | header          |
      | Sequence number |
      | Template        |
      | Status          |
      | Version         |
      | Change type     |
      | User            |
      | From            |
      | To              |

  Scenario: [Actions][Reactivate] User must be able to reactivate the Retired Timeframe template
    Given [API] Timeframe template in status Draft exists
    And [API] Timeframe template is approved
    And [API] Timeframe template is inactivated
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'Reactivate' option is clicked from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The item has status 'Final' and version '1.0'

  Scenario: [Actions][View history][Retired item] User must be able to view the history for the Retired Timeframe template
    Given [API] Timeframe template in status Draft exists
    And [API] Timeframe template is approved
    And [API] Timeframe template is inactivated
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The 'History' option is clicked from the three dot menu list
    Then The History for template window is displayed
    And The following column list with values will exist
      | header          |
      | Sequence number |
      | Template        |
      | Status          |
      | Version         |
      | Change type     |
      | User            |
      | From            |
      | To              |

  Scenario: [Actions][Availability] User must only have access correct actions depending on item state
    Given [API] Timeframe template in status Draft exists
    And The '/library/timeframe_templates/parent' page is opened
    And Timeframe template created via API is searched for
    When The item actions button is clicked
    Then Only actions that should be avaiable for the Draft item are displayed
    And [API] Timeframe template is approved
    And Timeframe template created via API is searched for
    When The item actions button is clicked
    Then Only actions that should be avaiable for the Final item are displayed
    Then 'Delete' action is not available
    And [API] Timeframe template is inactivated
    And Timeframe template created via API is searched for
    And The item actions button is clicked
    Then Only actions that should be avaiable for the Retired item are displayed
