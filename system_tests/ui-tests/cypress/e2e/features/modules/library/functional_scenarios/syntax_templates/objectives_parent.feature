@REQ_ID:1070684
Feature: Library - Syntax Templates - Objectives - Parent

  As a user, I want to manage every Objective template under the Syntax Template Library
  Background: User must be logged in
    Given The user is logged in
    And The 'library/objective_templates' page is opened

  Scenario: [Create][Sequence number] System must generate sequence number for Objective Templates when they are created
    And [API] Create objective template
    And The objective template is found
    When The latest sequence number is saved
    And [API] Create objective template
    And The objective template is found
    Then Sequence number is incremented

  # If approval is for version +1.0 and any instantiations exist then a cascade update and approval is needed
  @pending_implementation
  Scenario: Template Instantiations must be update when parent template has been updated
    Given The test Objective Parent Template exists with a status as 'Draft'
    When The'Approve' option is clicked from the three dot menu list
    Then all related objective template instantiations must be cascade updated to new version and approved
    And the displayed pop-up snack must include information on number of updated objective template instantiations

  @smoke_test
  Scenario: [Create][Positive case] User must be able to create Objective template
    And The Add template button is clicked
    When The objective template form is filled with base data
    And Form continue button is clicked
    And Form continue button is clicked
    And Objective criteria specific indexes are set
    And Form save button is clicked
    And The objective template is found
    Then The item has status 'Draft' and version '0.1'
    And The objective template name is displayed in the table

  Scenario: [Create][N/A indexes] User must be able to create Objective template with NA indexes
    And The Add template button is clicked
    When The objective template form is filled with base data
    And Form continue button is clicked
    And Form continue button is clicked
    And All Not Applicable checkboxes are checked
    And Form save button is clicked
    And The objective template is found
    And The item has status 'Draft' and version '0.1'
    And The 'Edit' option is clicked from the three dot menu list
    And User goes to Index template step
    Then The template has not applicable selected for all indexes

  Scenario: [Create][Mandatory fields] User must not be able to create Objective template without: Template Text
    And The Add template button is clicked
    When Form continue button is clicked
    Then The validation appears for Template name
    And The form is not closed

  Scenario: [Create][Mandatory fields] User must not be able to create Objective template with not unique Template Text
    And [API] Create objective template
    And The Add template button is clicked
    And The second objective is added with the same template text
    And Form continue button is clicked
    And Form continue button is clicked
    And All Not Applicable checkboxes are checked
    And Form save button is clicked
    Then The pop up displays 'already exists'
    And The form is not closed

  Scenario: [Create][Mandatory fields] User must not be able to create Objective template without: Indication or Disorder
    And The Add template button is clicked
    And The objective template form is filled with base data
    And Form continue button is clicked
    And Form continue button is clicked
    And Form save button is clicked
    Then The validation appears for Indication or Disorder field
    And The form is not closed

  Scenario: [Create][Mandatory fields] User must not be able to create Objective template without: Objective Category
    And The Add template button is clicked
    And The objective template form is filled with base data
    And Form continue button is clicked
    And Form continue button is clicked
    And Form save button is clicked
    Then The validation appears for 'objective' template category field
    And The form is not closed

  Scenario: [Create][Syntax validation] User must be able to verify syntax when creating Objective template
    And The Add template button is clicked
    When The new template name is prepared with a parameters
    And The syntax is verified
    Then The pop up displays "This syntax is valid"

  Scenario: [Create][Hide parameters] User must be able to hide parameter of the Objective template
    And The Add template button is clicked
    When The new template name is prepared with a parameters
    And Form continue button is clicked
    And The user hides the parameter in the next step
    Then The parameter is not visible in the text representation

  Scenario: [Create][Select parameter] User must be able to select parameter of the Objective template
    And The Add template button is clicked
    When The new template name is prepared with a parameters
    And Form continue button is clicked
    And The user picks the parameter from the dropdown list
    Then The parameter value is visible in the text representation

  @pending_implementation @manual_test
  Scenario: User must be able to view the history for the Parent Objective template
    And The objective template exists
    When The 'History' option is clicked from the three dot menu list
    Then The 'History for template' window is displayed with the following column list with values
      | Column | Header                 |
      | 1      | Sequence number        |
      | 2      | Indication or disorder |
      | 3      | Objective category     |
      | 4      | Confirmatory testing   |
      | 5      | Parent template        |
      | 6      | Status                 |
      | 7      | Version                |
      | 8      | Change type            |
      | 9      | User                   |
      | 10     | From                   |
      | 11     | To                     |
    And The history table contains the history of values in the template

  @manual_test
  Scenario: User must be able to read change history of output
    When The user opens version history
    Then The user is presented with version history of the output containing timestamp and username

  @manual_test
  Scenario: User must be able to read change history of selected element
    And The 'Show history' option is clicked from the three dot menu list
    When The user clicks on History for particular element
    Then The user is presented with history of changes for that element
    And The history contains timestamps and usernames

  Scenario: [Cancel][Creation] User must be able to Cancel creation of the Objective template
    And The Add template button is clicked
    And The objective template edition form is filled with data
    And Form continue button is clicked
    And Form continue button is clicked
    And All Not Applicable checkboxes are checked
    When Fullscreen wizard is closed by clicking cancel button
    And Action is confirmed by clicking continue
    Then The form is no longer available
    And The objective template is not found

  Scenario: [Cancel][Edition] User must be able to Cancel edition of the Objective template
    And [API] Create objective template
    And The objective template is found
    When The 'Edit' option is clicked from the three dot menu list
    And The objective template edition form is filled with data
    And Form continue button is clicked
    And Form continue button is clicked
    And All Not Applicable checkboxes are checked
    And Fullscreen wizard is closed by clicking cancel button
    And Action is confirmed by clicking continue
    Then The form is no longer available
    And The objective template is not updated

  Scenario: [Cancel][Indexing edtion] User must be able to Cancel indexes edition of the Objective template
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The 'Edit indexing' option is clicked from the three dot menu list
    When The indication indexes edition is initiated
    And Modal window form is closed by clicking cancel button
    Then The form is no longer available
    When The 'Edit indexing' option is clicked from the three dot menu list
    And The indexes are not updated

  Scenario: [Actions][Edit][0.1 version] User must be able to edit initial version of the Objective template
    And [API] Create objective template
    And The objective template is found
    When The 'Edit' option is clicked from the three dot menu list
    And The objective metadata update is started
    And Form continue button is clicked
    And Form continue button is clicked
    And Objective criteria specific indexes are updated
    And Form continue button is clicked
    And Template change description is provided
    And Form save button is clicked
    And The objective template is found
    Then The item has status 'Draft' and version '0.2'
    And The 'Edit' option is clicked from the three dot menu list
    And The objective template name is checked
    And User goes to Index template step
    And Objective indexes are verified

  Scenario: [Actions][Delete] User must be able to delete the Draft Objective template in version below 1.0
    And [API] Create objective template
    And The objective template is found
    When The 'Delete' option is clicked from the three dot menu list
    Then The pop up displays "Template deleted"
    And The objective template is not found

  Scenario: [Actions][Approve] User must be able to approve the Draft Objective template
    And [API] Create objective template
    And The objective template is found
    When The 'Approve' option is clicked from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The item has status 'Final' and version '1.0'

  Scenario: [Actions][Edit indexting] User must be able to edit indexing of Final Objective template
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The 'Edit indexing' option is clicked from the three dot menu list
    And Objective criteria specific indexes are cleared and updated
    And Form save button is clicked
    And The objective template is found
    And The 'Edit indexing' option is clicked from the three dot menu list
    And Objective indexes are verified

  Scenario: [Actions][Edit][Mandatory fields] User must not be able to save changes to Objective template without: Change description
    And [API] Create objective template
    And The objective template is found
    When The 'Edit' option is clicked from the three dot menu list
    And User goes to Change description step
    And The template change description is cleared
    And Form save button is clicked
    Then The validation appears for change description field
    And The form is not closed

  Scenario: [Actions][New version] User must be able to add a new version of the Final Objective template
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The 'New version' option is clicked from the three dot menu list
    Then The pop up displays 'New version created'
    And The item has status 'Draft' and version '1.1'

  Scenario: [Actions][Edit][1.1 version] User must be able to edit new version of the Objective template
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The 'New version' option is clicked from the three dot menu list
    Then The item has status 'Draft' and version '1.1'
    When The 'Edit' option is clicked from the three dot menu list
    And The objective metadata update is started
    And Form continue button is clicked
    And Form continue button is clicked
    And Objective criteria specific indexes are updated
    And Form continue button is clicked
    And Template change description is provided
    And Form save button is clicked
    And The objective template is found
    Then The item has status 'Draft' and version '1.2'
    When The 'Approve' option is clicked from the three dot menu list
    Then The item has status 'Final' and version '2.0'

  Scenario: [Actions][Inactivate] User must be able to inactivate the Final Objective template
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The 'Inactivate' option is clicked from the three dot menu list
    Then The pop up displays 'Template inactivated'
    And The item has status 'Retired' and version '1.0'

  Scenario: [Actions][Reactivate] User must be able to reactivate the Retired Objective template
    And [API] Create objective template
    And [API] Approve objective template
    And [API] Objective template is inactivated
    And The objective template is found
    When The 'Reactivate' option is clicked from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The item has status 'Final' and version '1.0'

  Scenario: [Actions][Availability] User must only have access correct actions depending on item state
    And [API] Create objective template
    And The objective template is found
    When The item actions button is clicked
    Then Only actions that should be avaiable for the Draft item are displayed
    And [API] Approve objective template
    And The objective template is found
    When The item actions button is clicked
    Then Only actions that should be avaiable for the Final item are displayed
    Then 'Edit indexing' action is available
    And 'Create pre-instantiation' action is available
    And [API] Objective template is inactivated
    And The objective template is found
    And The item actions button is clicked
    Then Only actions that should be avaiable for the Retired item are displayed
