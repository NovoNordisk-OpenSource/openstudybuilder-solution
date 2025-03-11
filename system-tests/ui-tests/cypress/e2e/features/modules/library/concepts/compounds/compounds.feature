@REQ_ID:1070683  @manual_test
Feature: Library - User management of Compounds
  As a user, I want to manage every Compound Item in the Concepts Library
  Background: User must be logged in
    Given The user is logged in

  Scenario: User must be able to navigate to the Library Compound page
    Given The '/library/compounds/compounds' page is opened
    When The 'Compounds' submenu is clicked in the 'Concepts' section
    And The 'Compounds' tab is selected
    Then The current URL is '/library/compounds'
  #Note: The above URL is achievable by shifting the cursor to next tab and revert to the targeted tab.

  Scenario: User must be able to see the Compounds table with with options as defined in this scenario
    Given The '/library/compounds' page is opened
    Then A table is visible with following options
      | options          |
      | Add new compound |
      | Filters          |
      | Columns          |
      | Export           |
    And A table is visible with following headers
      | headers                        |
      | Sponsor Compound               |
      | Compound Name                  |
      | Is INN                         |
      | Compound Number (long)         |
      | Compound Number (short)        |
      | Analyte Number                 |
      | Definition                     |
      | Brand Name                     |
      | Substance Name (UNII)          |
      | Pharmacological Class (MED-RT) |
      | Doses                          |
      | Strength                       |
      | Pharmaceutical Dosage Form     |
      | Route of Administration        |
      | Dose Frequency                 |
      | Delivery Device                |
      | Half-life                      |
      | Lag-time                       |
      | Modified                       |
      | Version                        |
      | Status                         |
  @manual_test
  Scenario: User must be able to add a new compound concept in the library
    Given The single compound is enabled
    And The '/library/compounds/compounds' page is opened
    When The 'Add new compound' button is clicked
    And The form for new compound is filled and saved
    Then The pop-up snack displayed as 'Compound added'
    And The added compound is visible in the last row of the table by default

  @manual_test
  Scenario: User must not be able to continue Step 2 of new compound without filled in mandatory field 'Compound name (INN if defined)'
    Given The '/library/compounds/compounds' page is opened
    When The 'Add new compound' button is clicked
    And The 'Compound name (INN if defined)' field under 'Compound identifiers' is not filled with data
    Then The user is not able to continue the 'Dosing details' step
    And The pop up displays 'This field is required'

  @manual_test
  Scenario: User must not be able to save a new compound without selecting mandatory field 'Is preferred synonym' either 'Yes' or 'No' option
    Given The '/library/compounds/compounds' page is opened
    When The 'Add new compound' button is clicked
    And The 'Is preferred synonym' field under 'Aliases' is not selected either 'Yes' or 'No' option
    Then The user is not able to save the new compound
    And The pop up displays 'This field is required'

  @manual_test
  Scenario: System must validate that unique values are provided for compound name, compound number (long and short) and analyte number
    Given The '/library/compounds/compounds' page is opened
    When The 'Add new compound' button is clicked
    And one of the following <fields> hold a value that are non-unique
      | fields                         |
      | Compound Name (INN if defined) |
      | Compound Number (long)         |
      | Compound Number (short)        |
      | Analyte Number                 |
    And The 'save' button in the 'Add new compound' form is clicked after 'Continue' three steps ahead
    Then The system displayed with the message as "Value <value> in field <field> is not a unique value in the library"
    And The Add new compound form is not closed

  @manual_test
  Scenario: User must be able to delete a compound that have never been approved
    Given The compound is available with a status as 'Draft'
    And The test compound is displayed with an incremented value as an example '0.1'
    When The 'Delete' button is clicked for the test compound
    And The 'Continue' button in the pop-up is clicked for the test compound
    Then The pop-up snack displayed as 'Compound deleted'
    And The test compound is no longer displayed in the compound table

  @manual_test
  Scenario: User must be able to approve a compound with a status as 'Draft'
    Given The '/library/compounds/compounds' page is opened
    And The test compound is available with a status as 'Draft'
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
    Given The test compound exists with a status as 'Final'
    When The 'Inactivate' button is clicked for the approved Compound
    Then The pop-up snack displayed as 'Compound in-activated'
    And The relevant Compound is displayed with a status as 'Retired' with a same version

  @manual_test
  Scenario: User must be able to reactivate the inactivated version of the Compound
    Given The test compound exists with as status as 'Retired'
    When The 'Reactivate' button is clicked for the inactivated Compound
    Then The pop-up snack displayed as 'Compound reactivated'
    And The relevant Compound is displayed with a status as 'Final' with a same version

  @manual_test
  Scenario: User must be able to add a new version for the approved Compound
    Given The test compound exists with a status as 'Final'
    When The 'New version' button is clicked for the approved compound with an incremented value as an example '1.0'
    Then The pop-up snack displayed as 'New version created'
    And The relevant Compound is displayed with a status as 'Draft' with an incremented value as an example '1.1'
