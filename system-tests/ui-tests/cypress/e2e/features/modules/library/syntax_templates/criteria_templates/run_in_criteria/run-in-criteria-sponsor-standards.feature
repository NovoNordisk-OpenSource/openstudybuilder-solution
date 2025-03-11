@REQ_ID:1070684
Feature: Library - Run-in Criteria - parent template

  As a user, I want to manage every Run-in Criteria template under the Syntax template Library
  Background: User must be logged in
    Given The user is logged in

  Scenario: User must be able to navigate to the Run-in Criteria template under the Syntax template Library
    Given The '/library' page is opened
    When The 'Criteria' submenu is clicked in the 'Syntax Templates' section
    And The 'Run-in' tab is selected
    Then The current URL is 'library/criteria_templates/Run-in/parent'


  Scenario: User must be able to see the columns list on the main page as below
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    Then A table is visible with following headers
      | headers         |
      | Sequence number |
      | Parent template |
      | Guidance text   |
      | Modified        |
      | Status          |
      | Version         |

  Scenario: User must be able to select visibility of columns in the table
    Given The '/library/criteria_templates/Run-in/parent' page is opened
    When The first column is selected from Select Columns option for table with actions
    Then The table contain only selected column and actions column

  Scenario: User must be able to add a new Run-in Criteria template in parent standards tab
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    When The new criteria is added in the library
    Then The new Criteria is visible in the Criteria Templates Table


  Scenario: User must be able to add a new Run-in Criteria template with NA indexes in parent standards tab
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    When The new Criteria is added in the library with not applicable for indexes
    Then The new Criteria is visible with Not Applicable indexes in the Criteria Templates Table

  Scenario: User must be able to edit draft version of the Run-in Criteria template
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    And The new criteria is added in the library
    When The 'Edit' option is clicked from the three dot menu list
    And The criteria metadata is updated
    Then The updated Criteria is visible within the table


  Scenario: User must not be able to create a new Run-in Criteria template without Template Text populated
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    When The new Criteria template is added without template text
    Then The validation appears for Template Text field
    And The form is not closed

  Scenario: User must not be able to create a new Run-in Criteria template without Indication or Disorder populated
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    When The new Criteria template is added without mandatory data
    Then The validation appears for Indication or Disorder, Criterion Category, Criterion Sub-Category
    And The form is not closed

  Scenario: User must be able to verify valid syntax when adding a new Run-in Criteria template
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    When The new template name is prepared with a parameters
    And The syntax is verified
    Then The pop up displays "This syntax is valid"

  Scenario: User must be able to hide parameter from the Run-in Criteria template
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    When The new template name is prepared with a parameters
    And The user hides the parameter in the next step
    Then The parameter is not visible in the text representation

  Scenario: User must be able to select parameter for the Run-in Criteria template
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    When The new template name is prepared with a parameters
    And The user picks the parameter from the dropdown list
    Then The parameter value is visible in the text representation

  Scenario: User must be able to delete the drafted version of Run-in Criteria template in version below 1.0
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    And The new criteria is added in the library
    When The 'Delete' option is clicked from the three dot menu list
    Then The pop up displays "Template deleted"
    And The criteria is no longer available

  Scenario: User must be able to approve the drafted version of Run-in Criteria template
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    And The new criteria is added in the library
    When The 'Approve' option is clicked from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The status of the criteria template displayed as Final with a version rounded up to full number

  Scenario: User must be able to edit indexing for final version of the templates
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    And The criteria template exists with a status as 'Final'
    When The 'Edit indexing' option is clicked from the three dot menu list
    And The indexing is updated for the Criteria Template
    And The 'Edit indexing' option is clicked from the three dot menu list
    Then The indexes in criteria template are updated

  Scenario: User must not be able to save the edited version of the draft Run-in Criteria template without filled in mandatory field 'Change description'
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    And The new criteria is added in the library
    When The 'Edit' option is clicked from the three dot menu list
    And The created criteria template is edited without change description provided
    Then The validation appears for criteria change description field
    And The form is not closed

  Scenario: User must be able to add a new version for the Run-in Criteria template with a status as 'Final'
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    And The criteria template exists with a status as 'Final'
    When The 'New version' option is clicked from the three dot menu list
    Then The pop up displays 'New version created'
    And The criteria template is updated to draft with version incremented by 0.1

  Scenario: User must be able to inactivate the Run-in Criteria template with a status as 'Final'
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    And The Final criteria template exist
    And The criteria template exists with a status as 'Final'
    When The 'Inactivate' option is clicked from the three dot menu list
    Then The pop up displays 'Template inactivated'
    And The template is displayed with a status as Retired with the same version as before

  Scenario: User must be able to reactivate the Run-in Criteria template with a status as 'Retired'
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    And The Retired criteria template exist
    And The criteria template exists with a status as 'Retired'
    When The 'Reactivate' option is clicked from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The criteria template is displayed with a status as Final with the same version as before


  @manual_test
  Scenario: User must be able to view the history for the Run-in Criteria template with a status as 'Retired'
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    Given The criteria template exists with a status as 'Retired'
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
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    When The user opens version history
    Then The user is presented with version history of the output containing timestamp and username

  @manual_test
  Scenario: User must be able to read change history of selected element
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    When The user clicks on History for particular element
    Then The user is presented with history of changes for that element
    And The history contains timestamps and usernames

  Scenario Outline: User must be able to filter the table by text fields
    Given The 'library/criteria_templates/Run-in/parent' page is opened
    When The user filters field '<name>'
    Then The table is filtered correctly

    Examples:
      | name                   |
      | Indication or disorder |
      | Criterion category     |
      #| Criterion sub-category |