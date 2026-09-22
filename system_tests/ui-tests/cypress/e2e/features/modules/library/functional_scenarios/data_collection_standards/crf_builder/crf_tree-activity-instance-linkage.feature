@REQ_ID:3519343

Feature: Library - Data Collection Standards - CRF Builder - CRF Tree - Activity Instance Links

    As a user, I want to manage Activity Instance Links in CRF Tree and view the results in the CRF Viewer within the library's data collection standards

    Background: User must be logged in
        Given The user is logged in
        And The linked instances list is cleared

    Scenario: [Create][Table View][Single Link][CRF Tree Page] User must be able to add one Activity Instance Link to a CRF Item in Table View and verify result in CRF Viewer
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        And The CRF Tree is expanded for form
        And The CRF Tree is expanded for item group
        Then I can see the CRF Item in the CRF Tree
        When The Manage Activity Instance Links action is selected for CRF Item in the CRF Tree
        Then The Edit Item page is opened
        And By default the Table view of CRF Item instance linkage is selected
        When User selects first value for linked Activity Instance
        And I select an Activity Item Class from the table
        And Selected Activity Instance name in the table view is saved
        And User goes to 'Item' step of crf item creation
        And The CRF Item datatype is set as 'integer'
        And Form save button is clicked
        Then The form is no longer available
        When The '/library/crf-builder/odm-viewer' page is opened
        When I select created Form from the Form Name dropdown list
        And User clicks the GENERATE button
        Then The iframe containing generated data is displayed
        When I click the Activity Instance option from the right top corner
        Then The added Activity Instance Link is displayed under the test item name
   
    Scenario: [Create][Table View][Multiple Links][CRF Tree Page] User must be able to add multiple Activity Instance Links to a CRF Item in Table View and verify result in CRF Viewer
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        And The CRF Tree is expanded for form
        And The CRF Tree is expanded for item group
        Then I can see the CRF Item in the CRF Tree
        When The Manage Activity Instance Links action is selected for CRF Item in the CRF Tree
        Then The Edit Item page is opened
        And By default the Table view of CRF Item instance linkage is selected
        When User selects first value for linked Activity Instance
        And I select an Activity Item Class from the table
        And Selected Activity Instance name in the table view is saved
        And User selects last value for linked Activity Instance
        And I select an Activity Item Class from the table
        And Selected Activity Instance name in the table view is saved
        And User goes to 'Item' step of crf item creation
        And The CRF Item datatype is set as 'integer'
        And Form save button is clicked
        Then The form is no longer available
        And The current URL is '/library/crf-builder/crf-tree'
        When The '/library/crf-builder/odm-viewer' page is opened
        When I select created Form from the Form Name dropdown list
        And User clicks the GENERATE button
        Then The iframe containing generated data is displayed
        When I click the Activity Instance option from the right top corner
        Then The added Activity Instance Link is displayed under the test item name

    Scenario: [Create][Form View][CRF Tree Page] User must be able to add Activity Instance Links in Form View and verify result in CRF Viewer
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        And The CRF Tree is expanded for form
        And The CRF Tree is expanded for item group
        Then I can see the CRF Item in the CRF Tree
        When The Manage Activity Instance Links action is selected for CRF Item in the CRF Tree
        Then The Edit Item page is opened
        And By default the Table view of CRF Item instance linkage is selected
        When User switch to Form view of CRF Item instance linkage
        When I click the Activity Instance Link plus button
        Then Activity Instance Item 1 table is visible
        And Activity Instance for Activity Instance Item 1 is selected
        And Activity Item Class for Activity Instance Item 1 is selected
        And Selected Activity Instance name is saved for Activity Instance Item 1
        And User goes to 'Item' step of crf item creation
        And The CRF Item datatype is set as 'integer'
        And Form save button is clicked
        Then The form is no longer available
        And The current URL is '/library/crf-builder/crf-tree'
        When The '/library/crf-builder/odm-viewer' page is opened
        When I select created Form from the Form Name dropdown list
        And User clicks the GENERATE button
        Then The iframe containing generated data is displayed
        When I click the Activity Instance option from the right top corner
        Then The added Activity Instance Link is displayed under the test item name

 @manual_test
    Scenario: [Mandatory Field Validation][CRF Tree Page] User must select both Activity Instance and Activity Item Class to save Activity Instance Link
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        And The CRF Tree is expanded for form
        And The CRF Tree is expanded for item group
        Then I can see the CRF Item in the CRF Tree
        When The Manage Activity Instance Links action is selected for CRF Item in the CRF Tree
        Then The Edit Item page is opened
        And By default the Table view of CRF Item instance linkage is selected
        And Activity Instance for Activity Instance Item 1 is selected
        And Activity Item Class for Activity Instance Item 1 is selected
        And Selected Activity Instance name is saved for Activity Instance Item 1
        And User goes to 'Item' step of crf item creation
        And The CRF Item datatype is set as 'integer'
        And Form save button is clicked
        Then I should see a validation message for the Activity Item Class dropdown list indicating that selection is required
        And The Edit Item page is opened
        When User switch to Form view of CRF Item instance linkage
        Then I can see no linked Activity Item Class in the Form View
