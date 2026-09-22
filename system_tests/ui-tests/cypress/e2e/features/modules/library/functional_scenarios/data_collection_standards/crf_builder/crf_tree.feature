@REQ_ID:1070683

Feature: Library - Data Collection Standards - CRF Builder - CRF Tree

    As a user, I want to build and manage CRF Tree in the library for data collection standards

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to CRF Tree page
        Given The '/library' page is opened
        When The 'CRF Builder' submenu is clicked in the 'Data Collection Standards' section
        And The 'CRF Tree' tab is selected
        Then The current URL is '/library/crf-builder/crf-tree'

  @manual_test
  Scenario: User must be able to add the links in CRF Tree for newly created child elements
        Given The CRF Collection exists
        When The '/library/crf-builder/crf-tree' page is opened
        Then I can see the CRF Collection without any linked child elements
        When I click '+ FORM' button under the Link column for the CRF Collection
        And I select 'Create and link new element' option
        Then The 'Add CRF Form' page is opened
        When I fill in the mandatory field with valid data and complete the process to create a new CRF Form
        Then I can see the CRF Form is linked to the CRF Collection
        When I click '+ ITEM GROUP' button under the Link column for the newly created CRF Form
        And I select 'Create and link new element' option
        Then The 'Add CRF Item Group' page is opened
        When I fill in the mandatory field with valid data and complete the process to create a new CRF Item Group
        Then I can see the CRF Item Group is linked to the CRF Form
        When I click '+ ITEM' button under the Link column for the newly created CRF Item Group
        And I select 'Create and link new element' option
        Then The 'Add CRF Item' page is opened
        When I fill in the mandatory field with valid data and complete the process to create a new CRF Item
        Then I can see the CRF Item is linked to the CRF Item Group

  @manual_test
  Scenario: User must be able to remove the links in CRF Tree for existing child elements
        Given The CRF Collection exists with linked CRF Form, Item Group, and Item
        When The '/library/crf-builder/crf-tree' page is opened
        Then I can see the linked CRF Form, Item Group, and Items under the parent element
        When I click '+ FORM' button under the Link column for the CRF Collection
        And I select '+ Link or remove existing element' option
        Then The 'Link Forms' page is opened
        When I select the linked CRF Form and click the 'SAVE' button
        Then I can see the CRF Form is not linked to the CRF Collection anymore
        When I click '+ ITEM GROUPS' button under the Link column for the CRF Form
        And I select '+ Link or remove existing element' option
        Then The 'Link Item Groups' page is opened
        When I select the linked CRF Item Group and click the 'SAVE' button
        Then I can see the CRF Item Group is not linked to the CRF Form anymore
        When I click '+ ITEM' button under the Link column for the CRF Collection
        And I select '+ Link or remove existing element' option
        Then The 'Link Items' page is opened
        When I select the linked CRF Item and click the 'SAVE' button
        Then I can see the CRF Item is not linked to the CRF Item Group anymore

  @manual_test
  Scenario: Verify that the user can check the Mandatory checkbox for the CRF Form
        Given The CRF Collection exists with linked CRF Form, Item Group, and Item
        And The '/library/crf-builder/crf-tree' page is opened
        When I click on the 'Edit reference attributes' option from the three-dot menu for the linked CRF Form
        Then The Reference Attributes page is opened
        When I check the 'Mandatory' checkbox and click the 'SAVE' button
        Then The CRF Form is now shown as Mandatory in the 'Reference attributes' column

  @manual_test
  Scenario: Verify that the user can check the Mandatory checkbox for the CRF Item Group
        Given The CRF Collection exists with linked CRF Form, Item Group, and Item
        And The '/library/crf-builder/crf-tree' page is opened
        When I click on the 'Edit reference attributes' option from the three-dot menu for the linked CRF Item Group
        Then The Reference Attributes page is opened
        When I check the 'Mandatory' checkbox and click the 'SAVE' button
        Then The CRF Item Group is now shown as Mandatory in the 'Reference attributes' column

  @manual_test
  Scenario: Verify that the user can check the Mandatory checkbox for the CRF Item
        Given The CRF Collection exists with linked CRF Form, Item Group, and Item
        And The '/library/crf-builder/crf-tree' page is opened
        When I click on the 'Edit reference attributes' option from the three-dot menu for the linked Item
        Then The Reference Attributes page is opened
        When I check the 'Mandatory' checkbox and click the 'SAVE' button
        Then The CRF Item is now shown as Mandatory in the 'Reference attributes' column

  @manual_test
  Scenario: User must be able to see the CRF Form as Repeating in the CRF Tree
        Given The CRF Collection exists with linked CRF Form, Item Group, and Item
        And The given CRF Form is set as Repeating
        And The '/library/crf-builder/crf-tree' page is opened
        Then The given CRF Form has a tick mark in the Repeating column

  @manual_test
  Scenario: User must be able to see the CRF Item Group as Repeating in the CRF Tree
        Given The CRF Collection exists with linked CRF Form, Item Group, and Item
        And The given CRF Item Group is set as Repeating
        And The '/library/crf-builder/crf-tree' page is opened
        Then The given CRF Item Group has a tick mark in the Repeating column