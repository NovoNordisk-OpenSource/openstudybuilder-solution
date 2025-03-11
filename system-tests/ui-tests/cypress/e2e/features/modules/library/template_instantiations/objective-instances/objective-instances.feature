@REQ_ID:1070686
Feature: Library - Objective instance

  As a user, I want to manage every Objective Instance under the Template Instantiations Library
  Background: User must be logged in
    Given The user is logged in

  Scenario: User must be able to navigate to the Objective instances under the Template Instantiations Library
    Given The '/library' page is opened
    When The 'Objectives' submenu is clicked in the 'Template Instantiations' section
    Then The current URL is '/library/objectives'

  Scenario: User must be able to see the columns list on the main page as below
    Given The '/library/objectives' page is opened
    Then A table is visible with following headers
      | headers           |
      | Library           |
      | Template          |
      | Objective         |
      | Modified          |
      | Status            |
      | Version           |
      | Number of studies |

  Scenario: User must be able to select visibility of columns in the table 
    Given The '/library/objectives' page is opened
    When The first column is selected from Select Columns option for table with actions
    Then The table contain only selected column and actions column

  Scenario: User must be able to view the history for the Objective instance
    Given The '/library/objectives' page is opened
    And The test objective instance exists in the table list
    When The three dots menu list clicked for the test instance
    And The 'History' option is clicked
    Then The History for objective window is displayed
    And The following column list with values will exist
      | header            |
      | Library           |
      | Template          |
      | Objective         |
      | Status            |
      | Version           |
      | Number of studies |
      | Change type       |
      | User              |
      | From              |
      | To                |
    And The table is not empty
    When The CLOSE button is clicked
    Then The current URL is '/library/objectives'

  Scenario: User must not be able to view 'Delete' option for the Objective instance
    Given The '/library/objectives' page is opened
    And The test objective instance exists in the table list
    When The three dots menu list clicked for the test instance
    Then The 'Delete' option is not available for the objective instance

  Scenario: User must be able to view the list of studies with a specific objective
    Given The '/library/objectives' page is opened
    And The test objective instance exists in the table list
    When The three dots menu list clicked for the test instance
    And The 'Display studies using this objective' option is clicked
    Then The List of studies with a specific objective window is displayed
    And The following column list with values will exist
      | header        |
      | View          |
      | Project ID    |
      | Project name  |
      | Brand name    |
      | Study number  |
      | Study ID      |
      | Study acronym |
      | Status        |
    And The table is not empty
    When The CLOSE button is clicked
    Then The current URL is '/library/objectives'

  @manual_test
  Scenario: User must be able to read change history of selected element
    Given The '/library/objectives' page is opened
    When The user clicks on History for particular element
    Then The user is presented with history of changes for that element
    And The history contains timestamps and usernames