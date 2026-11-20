@REQ_ID:2332141 
@pending_implementation

Feature: StudyBuilder: Study Set-up User access privilege
  As a study set-up user user,
  I want to able to log in with read and write access previlege for 'Study' Module and read access previlege for 'Library' Module,
  So that I can create, update, delete, retire and re-activate study definitions using library elements.

  Background: User must be logged in
    Given The user is logged in
    And granted the system access group Study.Read, Study.Write and Library.Read

  Scenario: User must be able to navigate to the 'Studies' Module
    Given The '/studies' page is opened
    When The 'Studies' menu is clicked in the Home page
    Then The left panel window displayed with mulitple Selection Menu options

  Scenario: User must be able to view the data fields in the 'Studies' Module
    Given The '/studies' page is opened
    When The 'Studies' menu is clicked in the Home page
    And 'Study Criteria' is clicked under 'Define Study' menu item
    Then The sample data records for criteria are visible on the main page.

  Scenario: User must be able to add new data in the 'Studies' Module
    Given The 'Studies' module is clicked in the Home page
    And 'Study Purpose' sub-menu is clicked under 'Define Study' menu item 
    And The 'Study Objectives' tab window is displayed with '+' (Cursor help text displayed as 'Add study objective') option on the right side menu list.
    When The sample test data entered and click on 'Save'
    Then The pop-up snack displayed with a value as 'Study objective added'
    And The relevant newly created Study Objective added as a new row in the table

  Scenario: User must be able to edit existing data in the 'Studies' Module
    Given The 'Studies' module is clicked in the Home page
    And 'Study Population' sub-menu is clicked under 'Define Study' menu item 
    And The 'Edit Content' is clicked on the right side menu list.
    When The sample test data entered and click on 'Save'
    Then The pop-up snack displayed with a value as 'Study population updated'
    And The relevant newly created Study Population fields are updated in the page

  Scenario: User must be able to view the data fields in the 'Library' Module
    Given The '/library' page is opened
    When The 'Library' menu is clicked in the Home page
    And 'Objective Templates' is clicked under 'Syntax Templates' menu item
    Then The sample data records for templates are visible on the main page.

   Scenario: User must not be able to have write access previlege in the data fields of the 'Library' Module
    Given The '/library' page is opened
    When The 'Library' module is clicked in the Home page
    And 'CT Catalogues' sub-menu is clicked under 'Code Lists' menu item 
    Then The 'All' tab window is not displayed with '+' (Cursor help text displayed as 'Add sponsor code list') option on the right side menu list.
    And The 'Edit' option is not available in the three dot menu list for the available sample test Code list item.
