@REQ_ID:1070684
Feature: Library - Objective templates

  As a user, I want to manage every Objective template under the Syntax Template Library
  Background: User must be logged in
    Given The user is logged in

  Scenario: User must be able to navigate to the Objective template under the Syntax Template Library
    Given The '/library' page is opened
    When The 'Objectives' submenu is clicked in the 'Syntax Templates' section
    Then The current URL is '/library/objective_templates'

  Scenario: User must be able to see the Parent Objective template table with listed columns
    Given The '/library/objective_templates' page is opened
    Then A table is visible with following headers
      | headers         |
      | Sequence number |
      | Parent template |
      | Modified        |
      | Status          |
      | Version         |

  Scenario: User must be able to select visibility of columns in the table
    Given The '/library/objective_templates' page is opened
    When The first column is selected from Select Columns option for table with actions
    Then The table contain only selected column and actions column

  Scenario: System must generate sequence number for Objective Parent Templates when they are created
    Given The '/library/objective_templates' page is opened
    And [API] Create objective template
    And The objective template is found
    When The latest objective sequence number is saved
    And [API] Create objective template
    And The objective template is found
    Then Objective sequence number is incremented

  # If approval is for version +1.0 and any instantiations exist then a cascade update and approval is needed
  @pending_implementation
  Scenario: Template Instantiations must be update when parent template has been updated
    Given The test Objective Parent Template exists with a status as 'Draft'
    When The'Approve' option is clicked from the three dot menu list
    Then all related objective template instantiations must be cascade updated to new version and approved
    And the displayed pop-up snack must include information on number of updated objective template instantiations

  Scenario: User must be able to add a new Parent Objective template in Parent Templates tab
    Given The 'library/objective_templates' page is opened
    When The new objective is added in the library
    Then The item has status 'Draft' and version '0.1'
    And The objective template name is displayed in the table

  Scenario: User must be able to add a new Parent Objective template with NA indexes in Sponsor standards tab
    Given The 'library/objective_templates' page is opened
    When The new Objective is added in the library with not applicable for indexes
    And The item has status 'Draft' and version '0.1'
    And The 'Edit' option is clicked from the three dot menu list
    Then The template has not applicable selected for all indexes

  Scenario: User must be able to edit draft version of the Parent Objective template
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And The objective template is found
    When The 'Edit' option is clicked from the three dot menu list
    And The objective metadata is updated
    Then The item has status 'Draft' and version '0.2'
    And The 'Edit' option is clicked from the three dot menu list
    And The objective template name is checked and user goes to indexes
    And The updated indexes in objective template are visible in the form

  Scenario: User must not be able to create a new Parent Objective template without Template Text populated
    Given The 'library/objective_templates' page is opened
    When The new Objective template is added without template text
    Then The validation appears for Template name
    And The form is not closed

  Scenario: User must not be able to create a new Parent Objective template with not unique Template Text
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And The second objective is added with the same template text
    Then The pop up displays 'already exists'
    And The form is not closed

  Scenario: User must not be able to create a new Parent Objective template without Indication or Disorder populated
    Given The 'library/objective_templates' page is opened
    When The new Objective template is added without Indication or Disorder
    Then The validation appears for Indication or Disorder field
    And The form is not closed

  Scenario: User must not be able to create a new Parent Objective template without Objective Category populated
    Given The 'library/objective_templates' page is opened
    When The new Objective template is added without Objective Category
    Then The validation appears for Objective Category field
    And The form is not closed

  Scenario: User must be able to verify valid syntax when adding a new Parent Objective template
    Given The 'library/objective_templates' page is opened
    When The new template name is prepared with a parameters
    And The syntax is verified
    Then The pop up displays "This syntax is valid"

  Scenario: User must be able to hide parameter from the Parent Objective template
    Given The 'library/objective_templates' page is opened
    When The new template name is prepared with a parameters
    And The user hides the parameter in the next step
    Then The parameter is not visible in the text representation

  Scenario: User must be able to test template for the Parent Objective template
    Given The 'library/objective_templates' page is opened
    When The new template name is prepared with a parameters
    And The user picks the parameter from the dropdown list
    Then The parameter value is visible in the text representation

  Scenario: User must be able to delete the drafted version of Parent Objective template in version below 1.0
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And The objective template is found
    When The 'Delete' option is clicked from the three dot menu list
    Then The pop up displays "Template deleted"
    And The objective is no longer available

  Scenario: User must be able to approve the drafted version of Parent Objective template
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And The objective template is found
    When The 'Approve' option is clicked from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The item has status 'Final' and version '1.0'

  Scenario: User must be able to edit indexing for final version of the templates
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The 'Edit indexing' option is clicked from the three dot menu list
    And The indexing is updated for the Objective Template
    And The 'Edit indexing' option is clicked from the three dot menu list
    Then The updated indexes in objective template are visible in the form

  Scenario: User must not be able to save the edited version of the draft Parent Objective template without filled in mandatory field 'Change description'
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And The objective template is found
    When The 'Edit' option is clicked from the three dot menu list
    And The template is edited witout providing mandatory change description
    Then The validation appears for template change description field
    And The form is not closed

  Scenario: User must be able to add a new version for the Parent Objective template with a status as 'Final'
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The 'New version' option is clicked from the three dot menu list
    Then The pop up displays 'New version created'
    And The item has status 'Draft' and version '1.1'

  Scenario: User must be able to edit and approve new version of objective
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The 'New version' option is clicked from the three dot menu list
    Then The item has status 'Draft' and version '1.1'
    When The 'Edit' option is clicked from the three dot menu list
    And The objective metadata is updated
    Then The item has status 'Draft' and version '1.2'
    When The 'Approve' option is clicked from the three dot menu list
    Then The item has status 'Final' and version '2.0'

  Scenario: User must be able to inactivate the Parent Objective template with a status as 'Final'
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The 'Inactivate' option is clicked from the three dot menu list
    Then The pop up displays 'Template inactivated'
    And The item has status 'Retired' and version '1.0'

  Scenario: User must be able to reactivate the Parent Objective template with a status as 'Retired'
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And [API] Approve objective template
    And [API] Objective template is inactivated
    And The objective template is found
    When The 'Reactivate' option is clicked from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The item has status 'Final' and version '1.0'

  @pending_implementation @manual_test
  Scenario: User must be able to view the history for the Parent Objective template
    Given The 'library/objective_templates' page is opened
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
    Given The 'library/objective_templates' page is opened
    When The user opens version history
    Then The user is presented with version history of the output containing timestamp and username

  @manual_test
  Scenario: User must be able to read change history of selected element
    Given The 'library/objective_templates' page is opened
    When The user clicks on History for particular element
    Then The user is presented with history of changes for that element
    And The history contains timestamps and usernames

  Scenario: User must be able to Cancel creation of the objective
    Given The 'library/objective_templates' page is opened
    And The objective template form is filled with data
    When Fullscreen wizard is closed by clicking cancel button
    And Action is confirmed by clicking continue
    Then The form is no longer available
    And The objective template is not created

  Scenario: User must be able to Cancel edition of the objective
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And The objective template is found
    When The 'Edit' option is clicked from the three dot menu list
    When The objective template edition form is filled with data
    And Fullscreen wizard is closed by clicking cancel button
    And Action is confirmed by clicking continue
    Then The form is no longer available
    And The objective template is found
    When The 'Edit' option is clicked from the three dot menu list
    And The objective template is not updated

  Scenario: User must be able to Cancel indexes edition of the objective
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The 'Edit indexing' option is clicked from the three dot menu list
    When The objective indexes edition is initiated
    And Modal window form is closed by clicking cancel button
    Then The form is no longer available
    When The 'Edit indexing' option is clicked from the three dot menu list
    And The objective indexes are not updated

  Scenario: User must only have access to aprove, edit, delete, history actions for Drafted version of the objective
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And The objective template is found
    When The item actions button is clicked
    Then Only actions that should be avaiable for the Draft item are displayed

  Scenario: User must only have access to new version, inactivate, history actions for Final version of the objective
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The item actions button is clicked
    Then Only actions that should be avaiable for the Final item are displayed

  Scenario: User must have access to edit indexing, create pre-instantiation actions for Final version of the objective
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And [API] Approve objective template
    And The objective template is found
    When The item actions button is clicked
    Then 'Edit indexing' action is available
    And 'Create pre-instantiation' action is available

  Scenario: User must only have access to reactivate, history actions for Retired version of the objective
    Given The 'library/objective_templates' page is opened
    And [API] Create objective template
    And [API] Approve objective template
    And [API] Objective template is inactivated
    And The objective template is found
    And The item actions button is clicked
    Then Only actions that should be avaiable for the Retired item are displayed

  Scenario: User must be able to search created objective
    Given The 'library/objective_templates' page is opened
    When [API] Search Test - Create first objective template
    And [API] Search Test - Create second objective template
    Then The objective template is found
    And More than one item is found after performing partial name search 

  Scenario: User must be able to search not existing objective and table will correctly filtered
    Given The 'library/objective_templates' page is opened
    When The not existing item is searched for
    Then The item is not found and table is correctly filtered

  Scenario: User must be able to search item ignoring case sensitivity
    Given The 'library/objective_templates' page is opened
    When The existing item in search by lowercased name
    And More than one result is found

  Scenario: User must be able to combine search and filters to narrow table results
    Given The 'library/objective_templates' page is opened
    When The user adds status to filters
    And The user changes status filter value to 'Final'
    And The existing item in status Draft is searched for
    And The item is not found and table is correctly filtered
    And The user changes status filter value to 'Draft'
    Then More than one item is found after performing partial name search

  Scenario Outline: User must be able to filter the table by text fields
    Given The 'library/objective_templates' page is opened
    When The user filters field '<name>'
    Then The table is filtered correctly

    Examples:
      | name                   |
      | Indication or disorder |
      | Objective category     |
      | Confirmatory testing   |

  Scenario: User must be able to use table pagination
      Given The '/library/objective_templates' page is opened
      When The user switches pages of the table
      Then The table page presents correct data