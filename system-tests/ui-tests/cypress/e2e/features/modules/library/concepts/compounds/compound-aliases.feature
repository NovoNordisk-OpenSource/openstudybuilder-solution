@REQ_ID:1070683  @manual_test
Feature: Library - Compound Aliases
  As a user, I want to manage every Compound Aliases Item in the Compound Concepts
  Background: User must be logged in
    Given The user is logged in

  Scenario: User must be able to navigate to the Library Compound Aliases page
    Given The '/library/compounds/aliases' page is opened
    When The 'Compounds' submenu is clicked in the 'Concepts' section
    And The 'Compound Aliases' tab is selected
    Then The current URL is '/library/compounds/aliases'

  Scenario: User must be able to see the Compound Aliases table with with options as defined in this scenario
    Given The '/library/compounds/aliases' page is opened
    Then A table is visible with following options
      | options                |
      | Add new compound alias |
      | Filters                |
      | Columns                |
      | Export                 |
    And  A table is visible with following headers
      | headers              |
      | Compound Name        |
      | Name                 |
      | Sentence case name   |
      | Is Preferred Synonym |
      | Definition           |
      | Modified             |
      | Version              |
      | Status               |

  @manual_test
  Scenario: User must be able to add a new Compound Aliases
    Given The '/library/compounds/aliases' page is opened
    When The 'Add new compound alias' button is clicked
    And The form for new compound alias is filled and saved
    Then The pop-up snack displayed as 'compound alias added'
    And The added compound is visible in the last row of the table by default

  @manual_test
  Scenario: User must not be able to continue Step 2 of new compound alias without filled in mandatory field 'Compound name'
    Given The '/library/compounds/aliases' page is opened
    When The 'Add new compound alias' button is clicked
    And The 'Compound name' field under 'Select compound' is not filled with data
    Then The user is not able to continue the 'Define compound alias' step
    And The pop up displays 'This field is required'

  @manual_test
  Scenario: User must not be able to save a new compound without selecting mandatory fields 'Compound alias name', 'Sentence case name' and 'Is preferred synonym'
    Given The '/library/compounds/aliases' page is opened
    When The 'Add new compound alias' button is clicked
    And The 'Compound alias name', 'Sentence case name' and 'Is preferred synonym' fields under 'Define compound alias' is not filled
    Then The user is not able to save the new compound alias
    And The pop up displays 'This field is required'

  @manual_test
  Scenario: System must validate that unique values are provided for compound name, compound number (long and short) and analyte number
    Given The '/library/compounds/aliases' page is opened
    When The Add or Edit compound button is clicked
    And one of the following <fields> hold a value that are non-unique
      | fields                  |
      | Compound Name           |
      | Compound Number (long)  |
      | Compound Number (short) |
      | Analyte Number          |
    And The save button in the Add or Edit compound form is clicked
    Then The system displays the message "Value <value> in field <field> is not a unique value in the library"
    And The Add or Edit compound form is not closed

  @manual_test
  Scenario: User must be able to delete a compound that have never been approved
    Given The '/library/compounds/compounds' page is opened
    And The test compound is available with a status as 'Draft'
    When The 'Delete' button is clicked for the test compound
    And The 'Continue' button is clicked for the test compound
    Then The pop-up snack displayed as 'Compound deleted'
    And The test compound is no longer displayed in the compound table

  @manual_test
  Scenario: User must be able to approve a compound with a status as 'Draft'
    Given The '/library/compounds/compounds' page is opened
    And The test compound is available with as status as 'Draft'
    When The 'Approve' button is clicked for the test compound with an incremented value as an example'0.1'
    Then The pop-up snack displayed as 'Compound is now in Final state'
    And The Compound is added in the last row of the table with an incremented value as an example '1.0'

  @manual_test
  Scenario: User must be able to view a history for a compound with a status as 'Draft'
    Given The '/library/compounds/compounds' page is opened
    And The test compound is available with a status as 'Draft'
    When The 'History' button is clicked for the test compound with status as 'Draft'
    Then A 'History for Compound <Compound name>' is displayed with the following headers and its values
      | Column | Header             |
      | 1      | Library            |
      | 2      | Name               |
      | 3      | Change description |
      | 4      | Status             |
      | 5      | Version            |
      | 6      | User               |
      | 7      | From               |
      | 8      | To                 |

  @manual_test
  Scenario: User must be able to view a history for a compound with a status as 'Final'
    Given The '/library/compounds/compounds' page is opened
    And The test compound is available with a status as 'Final'
    When The 'History' button is clicked for the test compound with status as 'Final'
    Then A 'History for Compound <Compound name>' is displayed with the following headers and its values
      | Column | Header             |
      | 1      | Library            |
      | 2      | Name               |
      | 3      | Change description |
      | 4      | Status             |
      | 5      | Version            |
      | 6      | User               |
      | 7      | From               |
      | 8      | To                 |

  @manual_test
  Scenario: User must be able to inactivate the approved version of the Compound
    Given The test Compound exists with a status as 'Final'
    When The 'Inactivate' button is clicked for the approved Compound
    Then The pop-up snack displayed as 'Compound in-activated'
    And The relevant Compound is displayed with a status as 'Retired' with a same version

  @manual_test
  Scenario: User must be able to reactivate the inactivated version of the Compound
    Given The test compound exists with a status as 'Retired'
    When The 'Reactivate' button is clicked for the inactivated Compound
    Then The pop-up snack displayed as 'Compound reactivated'
    And The relevant Compound is displayed with a status as 'Final' with a same version

  @manual_test
  Scenario: User must be able to add a new version for the approved Compound
    Given The test Compound exists with a status as 'Final'
    When The 'New version' button is clicked for the approved compound with an incremented value as an example '1.0'
    Then The pop-up snack displayed as 'New version created'
    And The relevant Compound is displayed with a status as 'Draft' with an incremented value as an example '1.1'