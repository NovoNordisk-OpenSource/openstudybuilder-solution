@REQ_ID:1070684
Feature: Library - Syntax Templates - Criteria - Withdrawal - Parent

  As a user, I want to manage every Withdrawal Criteria template under the Syntax template Library
  Background: User must be logged in
    Given The user is logged in

  Scenario: [Create][Sequence number] System must generate sequence number for Withdrawal Criteria Templates when they are created
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The latest sequence number is saved
    And [API] 'Withdrawal' Criteria in status Draft exists
    And The criteria is found
    Then Sequence number is incremented

  @smoke_test
  Scenario: [Create][Positive case] User must be able to create Withdrawal Criteria template
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The Add template button is clicked
    When The criteria template form is filled with base data
    And Form continue button is clicked
    And Form continue button is clicked
    And Template indexes are set for 'criterion'
    And User intercept getCriteria request
    And Form save button is clicked
    And User awaits for the getCriteria request to finish
    And The criteria is found
    Then The Criteria is visible in the Criteria Templates Table
    And The item has status 'Draft' and version '0.1'

  Scenario: [Create][N/A indexes] User must be able to create Withdrawal Criteria template with NA indexes
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The Add template button is clicked
    When The criteria template form is filled with base data
    And Form continue button is clicked
    And Form continue button is clicked
    And All Not Applicable checkboxes are checked
    And User intercept getCriteria request
    And Form save button is clicked
    And User awaits for the getCriteria request to finish
    And The criteria is found
    Then The Criteria is visible in the Criteria Templates Table
    And The item has status 'Draft' and version '0.1'

  Scenario: [Create][Mandatory fields] User must not be able to create Withdrawal Criteria template without: Template Text
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The Add template button is clicked
    When Form continue button is clicked
    Then The validation appears for Template name
    And The form is not closed

  Scenario: [Create][Mandatory fields] User must not be able to create Withdrawal Criteria template without: Indication or Disorder
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The Add template button is clicked
    And The criteria template form is filled with base data
    And Form continue button is clicked
    And Form continue button is clicked
    When Template indexes are set for 'criterion'
    And Indication or Disorder index is cleared
    Then Form save button is clicked
    And The validation appears for Indication or Disorder field
    And The form is not closed

  Scenario: [Create][Mandatory fields] User must not be able to create Withdrawal Criteria template without: Criterion Category
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The Add template button is clicked
    And The criteria template form is filled with base data
    And Form continue button is clicked
    And Form continue button is clicked
    When Template indexes are set for 'criterion'
    And Category index is cleared for 'criterion' template
    Then Form save button is clicked
    And The validation appears for 'criterion' template category field
    And The form is not closed

  Scenario: [Create][Mandatory fields] User must not be able to create Withdrawal Criteria template without: Criterion Sub-Category
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The Add template button is clicked
    And The criteria template form is filled with base data
    And Form continue button is clicked
    And Form continue button is clicked
    When Template indexes are set for 'criterion'
    And Subcategory index is cleared for 'criterion' template
    Then Form save button is clicked
    And The validation appears for 'criterion' template subcategory field
    And The form is not closed

  Scenario: [Create][Syntax validation] User must be able to verify syntax when creating Withdrawal Criteria template
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The Add template button is clicked
    When The new template name is prepared with a parameters
    And The syntax is verified
    Then The pop up displays "This syntax is valid"

  Scenario: [Create][Hide parameters] User must be able to hide parameter of the Withdrawal Criteria template
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The Add template button is clicked
    When The new template name is prepared with a parameters
    And Form continue button is clicked
    And The user hides the parameter in the next step
    Then The parameter is not visible in the text representation

  Scenario: [Create][Select parameter] User must be able to select parameter of the Withdrawal Criteria template
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The Add template button is clicked
    When The new template name is prepared with a parameters
    And Form continue button is clicked
    And The user picks the parameter from the dropdown list
    Then The parameter value is visible in the text representation

  @manual_test
  Scenario: User must be able to view the history for the Withdrawal Criteria template with a status as 'Retired'
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And [API] Criteria is approved
    And [API] Criteria is inactivated
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'Reactivate' option is clicked from the three dot menu list
    Then The 'History for template' window is displayed with the following column list with values
      | Column | Header                 |
      | 1      | Indication or disorder |
      | 2      | Criterion category     |
      | 3      | Criterion sub-category |
      | 4      | Template               |
      | 5      | Guidance text          |
      | 6      | Status                 |
      | 7      | Version                |
      | 8      | Change type            |
      | 9      | User                   |
      | 10     | From                   |
      | 11     | To                     |

  @manual_test
  Scenario: User must be able to read change history of output
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    When The user opens version history
    Then The user is presented with version history of the output containing timestamp and username

  @manual_test
  Scenario: User must be able to read change history of selected element
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The 'Show history' option is clicked from the three dot menu list
    When The user clicks on History for particular element
    Then The user is presented with history of changes for that element
    And The history contains timestamps and usernames

  Scenario: [Cancel][Creation] User must be able to Cancel creation of the Withdrawal Criteria template
    Given The 'library/criteria_templates/Withdrawal/parent' page is opened
    And The Add template button is clicked
    And The criteria template edition form is filled with data
    And Form continue button is clicked
    And Form continue button is clicked
    And All Not Applicable checkboxes are checked
    When Fullscreen wizard is closed by clicking cancel button
    And Action is confirmed by clicking continue
    Then The form is no longer available
    And The criteria is not found

  Scenario: [Cancel][Edition] User must be able to Cancel edition of the Withdrawal Criteria template
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'Edit' option is clicked from the three dot menu list
    And The criteria template edition form is filled with data
    And Form continue button is clicked
    And Form continue button is clicked
    And All Not Applicable checkboxes are checked
    And Fullscreen wizard is closed by clicking cancel button
    And Action is confirmed by clicking continue
    Then The form is no longer available
    And The criteria is not found

  Scenario: [Cancel][Indexing edtion] User must be able to Cancel indexes edition of the Withdrawal Criteria template
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And [API] Criteria is approved
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'Edit indexing' option is clicked from the three dot menu list
    When The indication indexes edition is initiated
    And Modal window form is closed by clicking cancel button
    Then The form is no longer available
    When The 'Edit indexing' option is clicked from the three dot menu list
    And The indexes are not updated

  Scenario: [Actions][Edit][0.1 version] User must be able to edit initial version of the Withdrawal Criteria template
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'Edit' option is clicked from the three dot menu list
    And The criteria metadata update is initiated
    And Form continue button is clicked
    And Form continue button is clicked
    And Template indexes are cleared and updated for 'criterion'
    And Form continue button is clicked
    And Template change description is provided
    And User intercept getCriteria request
    And Form save button is clicked
    And User awaits for the getCriteria request to finish
    And The criteria is found
    Then The Criteria is visible in the Criteria Templates Table
    And The item has status 'Draft' and version '0.2'

  Scenario: [Actions][Delete] User must be able to delete the Draft Withdrawal Criteria template in version below 1.0
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'Delete' option is clicked from the three dot menu list
    Then The pop up displays "Template deleted"
    And The criteria is not found

  Scenario: [Actions][Approve] User must be able to approve the Draft Withdrawal Criteria template
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'Approve' option is clicked from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The item has status 'Final' and version '1.0'

  Scenario: [Actions][Edit indexing] User must be able to edit indexing of Final Withdrawal Criteria template
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And [API] Criteria is approved
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'Edit indexing' option is clicked from the three dot menu list
    And Template indexes are cleared and updated for 'criterion'
    And Form save button is clicked
    And The criteria is found
    And The 'Edit indexing' option is clicked from the three dot menu list
    Then Template indexes are verified

  Scenario: [Actions][Edit][Mandatory fields] User must not be able to save changes to Withdrawal Criteria template without: Change description
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'Edit' option is clicked from the three dot menu list
    And User goes to Change description step
    And The template change description is cleared
    And Form save button is clicked
    Then The validation appears for change description field
    And The form is not closed

  Scenario: [Actions][New version] User must be able to add a new version of the Final Withdrawal Criteria template
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And [API] Criteria is approved
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'New version' option is clicked from the three dot menu list
    Then The pop up displays 'New version created'
    And The item has status 'Draft' and version '1.1'

  Scenario: [Actions][Edit][1.1 version] User must be able to edit new version of the Withdrawal Criteria template
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And [API] Criteria is approved
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'New version' option is clicked from the three dot menu list
    Then The item has status 'Draft' and version '1.1'
    When The 'Edit' option is clicked from the three dot menu list
    And The criteria metadata update is initiated
    And Form continue button is clicked
    And Form continue button is clicked
    And Template indexes are cleared and updated for 'criterion'
    And Form continue button is clicked
    And Template change description is provided
    And User intercept getCriteria request
    And Form save button is clicked
    And The criteria is found
    Then The item has status 'Draft' and version '1.2'
    When The 'Approve' option is clicked from the three dot menu list
    Then The item has status 'Final' and version '2.0'

  Scenario: [Actions][Inactivate] User must be able to inactivate the Final Withdrawal Criteria template
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And [API] Criteria is approved
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'Inactivate' option is clicked from the three dot menu list
    Then The pop up displays 'Template inactivated'
    And The item has status 'Retired' and version '1.0'

  Scenario: [Actions][Reactivate] User must be able to reactivate the Retired Withdrawal Criteria template
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And [API] Criteria is approved
    And [API] Criteria is inactivated
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The 'Reactivate' option is clicked from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The item has status 'Final' and version '1.0'

  Scenario: [Actions][Availability] User must only have access correct actions depending on item state
    Given [API] 'Withdrawal' Criteria in status Draft exists
    And The 'library/criteria_templates/Withdrawal/parent' page is opened
    And User intercept getCriteria request
    And User awaits for the getCriteria request to finish
    And The criteria is found
    When The item actions button is clicked
    Then Only actions that should be avaiable for the Draft item are displayed
    And [API] Criteria is approved
    And The criteria is found
    When The item actions button is clicked
    Then Only actions that should be avaiable for the Final item are displayed
    Then 'Edit indexing' action is available
    And 'Create pre-instantiation' action is available
    And [API] Criteria is inactivated
    And The criteria is found
    And The item actions button is clicked
    Then Only actions that should be avaiable for the Retired item are displayed