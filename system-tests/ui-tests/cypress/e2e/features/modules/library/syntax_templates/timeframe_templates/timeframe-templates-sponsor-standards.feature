@REQ_ID:1070684
Feature: Library - Time frame templates - Sponsor standards

  As a user, I want to manage every Timeframe template under the Syntax template Library
  Background: User must be logged in
    Given The user is logged in

  Scenario: User must be able to navigate to the Time frame template under the Syntax template Library
    Given The '/library' page is opened
    When The 'Time Frames' submenu is clicked in the 'Syntax Templates' section
    Then The current URL is '/library/timeframe_templates/parent'
    And The 'Parent' tab is displayed by default

  Scenario: User must be able to see the columns list on the main page as below
    Given The '/library/timeframe_templates/parent' page is opened
    Then A table is visible with following headers
      | headers         |
      | Sequence number |
      | Template        |
      | Modified        |
      | Status          |
      | Version         |

  Scenario: User must be able to select visibility of columns in the table
    Given The '/library/timeframe_templates/parent' page is opened
    When The first column is selected from Select Columns option for table with actions
    Then The table contain only selected column and actions column

  Scenario: User must be able to add a new Time frame template in Sponsor standards tab
    Given The '/library/timeframe_templates/parent' page is opened
    When The Add time frame template section selected with test data
    And The 'save-button' button is clicked
    Then The pop up displays 'Time frame template added'
    And  The new Timeframe is visible in the Timeframe Template Table

  Scenario: User must not be able to create a new Time frame template without filled in mandatory field 'Add time frame template'
    Given The '/library/timeframe_templates/parent' page is opened
    When The Add time frame template section selected without test data
    Then The message is displayed as 'This field is required'

  Scenario: User must be able to verify valid syntax when adding a new Time frame template
    Given The '/library/timeframe_templates/parent' page is opened
    When The Add time frame template section selected with test data
    And The 'verify-syntax-button' button is clicked
    Then The pop up displays 'This syntax is valid'

  Scenario: User must be able to edit draft version of the Time frame template
    Given The '/library/timeframe_templates/parent' page is opened
    And The test time frame template exists with a status as 'Draft'
    When The 'Edit' option is selected from the three dot menu list
    And The template is updated with test data and saved
    Then The pop up displays 'Time frame template updated'
    And The updated Timeframe is visible in the Timeframe Template Table

  Scenario: User must not be able to save the edited version of the draft Time frame template without filled in mandatory field 'Change description'
    Given The '/library/timeframe_templates/parent' page is opened
    And The test time frame template exists with a status as 'Draft'
    When The 'Edit' option is selected from the three dot menu list
    And Change description field is not filled with test data
    Then The message is displayed as 'This field is required'

  Scenario: User must be able to approve the drafted version of Time frame template
    Given The '/library/timeframe_templates/parent' page is opened
    And The test timeframe template exists in draft status and version 0.1
    When The 'Approve' option is selected from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The status of the template displayed as 'Final' with an incremented value as an example as 1.0

  Scenario: User must be able to delete the Time frame template with a status as 'Draft' and with an intial created version
    Given The '/library/timeframe_templates/parent' page is opened
    And The test timeframe template exists in draft status and version 0.1
    When The 'Delete' option is selected from the three dot menu list
    Then The pop up displays 'Timeframe template has been deleted'
    And The drafted template is disappered from the table

  Scenario: User must not be able to view 'Delete' option for the Time frame template with a status as 'Draft' that is not in initial version
    Given The '/library/timeframe_templates/parent' page is opened
    Given The test timeframe template exists in Draft status and version 1.1
    When The three dots menu list clicked for the test template
    Then The Delete option is not available for the Drafted template not in initial version

  Scenario: User must be able to view the history for the Time frame template with a status as 'Draft'
    Given The '/library/timeframe_templates/parent' page is opened
    And The test time frame template exists with a status as 'Draft'
    When The 'History' option is selected from the three dot menu list
    Then The 'History for template' window is displayed
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

  Scenario: User must be able to add a new version for the Time frame template with a status as 'Final'
    Given The '/library/timeframe_templates/parent' page is opened
    And The test timeframe template exists in Final status and version 1.0
    When The 'New version' option is selected from the three dot menu list
    Then The pop up displays 'New version created'
    And The template is created as a draft version with an incremented value as an example 1.1

  Scenario: User must be able to inactivate the Time frame template with a status as 'Final'
    Given The '/library/timeframe_templates/parent' page is opened
    And The test timeframe template exists in Final status and version 1.0
    When The 'Inactivate' option is selected from the three dot menu list
    Then The pop up displays 'Template inactivated'
    And The timeframe template is displayed with a status as 'Retired' with the same version as before

  Scenario: User must be able to view the history for the Time frame template with a status as 'Final'
    Given The '/library/timeframe_templates/parent' page is opened
    And The test timeframe template exists in Final status and version 1.0
    When The 'History' option is selected from the three dot menu list
    Then The 'History for template' window is displayed
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

  Scenario: User must be able to reactivate the Time frame template with a status as 'Retired'
    Given The '/library/timeframe_templates/parent' page is opened
    And The test timeframe template exists in Retired status
    When The 'Reactivate' option is selected from the three dot menu list
    Then The pop up displays 'Template is now in Final state'
    And The timeframe template is displayed with a status as 'Final' with the same version as before

  Scenario: User must be able to view the history for the timeframe template with a status as 'Retired'
    Given The '/library/timeframe_templates/parent' page is opened
    And The test timeframe template exists in Retired status
    When The 'History' option is selected from the three dot menu list
    Then The 'History for template' window is displayed
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

  @manual_test
  Scenario: User must be able to read change history of output
    Given The '/library/timeframe_templates/parent' page is opened
    When The user opens version history
    Then The user is presented with version history of the output containing timestamp and username

  @manual_test
  Scenario: User must be able to read change history of selected element
    Given The '/library/timeframe_templates/parent' page is opened
    When The user clicks on History for particular element
    Then The user is presented with history of changes for that element
    And The history contains timestamps and usernames

  Scenario Outline: User must be able to filter the table by text fields
    Given The 'library/timeframe_templates/parent' page is opened
    When The user filters field '<name>'
    Then The table is filtered correctly

    Examples:
      | name            |
      | Sequence number |
      | Template        |
      # | Modified        |
      | Status          |
      | Version         |
