@REQ_ID:1070686

Feature: Library - Endpoint instance

  As a user, I want to manage every endpoint instance under the instance Instantiations Library
  Background: User must be logged in
    Given The user is logged in

  Scenario: User must be able to navigate to the endpoint instance under the Syntax instance Library
    Given The '/library' page is opened
    When The 'Endpoints' submenu is clicked in the 'Template Instantiations' section
    Then The current URL is '/library/endpoints'

  Scenario: User must be able to see the columns list on the main page as below
    Given The '/library/endpoints' page is opened
    Then A table is visible with following headers
      | headers           |
      | Library           |
      | Template          |
      | Endpoint          |
      | Modified          |
      | Status            |
      | Version           |
      | Number of studies |

  Scenario: User must be able to select visibility of columns in the table 
    Given The '/library/endpoints' page is opened
    When The first column is selected from Select Columns option for table with actions
    Then The table contain only selected column and actions column

  @manual_test
  Scenario: User must be able to view the history for the Endpoint instance
    Given The '/library/endpoints' page is opened
    And The test endpoint instance exists in the table
    When The three dots menu list clicked for the test instance
    And The 'History' option is clicked
    Then The History for Endpoint window is displayed
    And The following column list with values will exist
      | header            |
      | Library           |
      | Template          |
      | Endpoint          |
      | Status            |
      | Version           |
      | Number of studies |
      | Change type       |
      | User              |
      | From              |
      | To                |
    And The table is not empty
    When The CLOSE button is clicked
    Then The current URL is '/library/endpoints'

  @manual_test
  Scenario: User must not be able to view 'Delete' option for the Endpoint instance
    Given The '/library/endpoints' page is opened
    And The test endpoint instance exists in the table
    When The three dots menu list clicked for the test instance
    Then The 'Delete' option is not available for the Endpoint instance

  @manual_test
  Scenario: User must be able to view the list of studies with a specific Endpoint
    Given The '/library/endpoints' page is opened
    And The test endpoint instance exists in the table
    When The three dots menu list clicked for the test instance
    And The 'Display studies using this endpoint' option is clicked
    Then The List of studies with a specific Endpoint window is displayed
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
    Then The current URL is '/library/endpoints'


  @manual_test
  Scenario: User must be able to read change history of selected element
    Given the '/library/endpoints' page is opened
    When The user clicks on History for particular element
    Then The user is presented with history of changes for that element
    And The history contains timestamps and usernames