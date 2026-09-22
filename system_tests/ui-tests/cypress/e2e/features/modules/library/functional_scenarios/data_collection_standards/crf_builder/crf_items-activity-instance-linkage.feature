@REQ_ID:3519343

Feature: Library - Data Collection Standards - CRF Builder - CRF Items - Activity Instance Links

    As a user, I want to manage Activity Instance Links in CRF Items and view the results in the CRF Viewer within the library's data collection standards

    Background: User must be logged in
        Given The user is logged in
        And The linked instances list is cleared

    Scenario: [Create][Form View][Single Link][CRF Item Page] User must be able to add one Activity Instance Link to a CRF Item in Form View and verify result in CRF Viewer
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And Created test CRF Item is found
        When The 'Manage Activity Instance Links' option is clicked from the three dot menu list
        Then The RESET button is disabled
        And The Edit Item page is opened
        And The Edit Item page does not show any linked Activity Instances
        And By default the Form view of CRF Item instance linkage is selected
        When I click the Activity Instance Link plus button
        Then Activity Instance Item 1 table is visible
        And Activity Instance for Activity Instance Item 1 is selected
        And Activity Item Class for Activity Instance Item 1 is selected
        And Selected Activity Instance name is saved for Activity Instance Item 1
        Then The RESET button is enabled
        And User goes to 'Item' step of crf item creation
        And The CRF Item datatype is set as 'integer'
        When The 'save-button' button is clicked
        Then The form is no longer available
        And The current URL is '/library/crf-builder/items'
        When The '/library/crf-builder/odm-viewer' page is opened
        When I select created Form from the Form Name dropdown list
        And User clicks the GENERATE button
        Then The iframe containing generated data is displayed
        When I click the Activity Instance option from the right top corner
        Then The added Activity Instance Link is displayed under the test item name

    Scenario: [Create][Form View][Multiple Links][CRF Item Page] User must be able to add multiple Activity Instance Links to a CRF Item in Form View and verify result in CRF Viewer
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And Created test CRF Item is found
        When The 'Manage Activity Instance Links' option is clicked from the three dot menu list
        When I click the Activity Instance Link plus button
        Then Activity Instance Item 1 table is visible
        And Activity Instance for Activity Instance Item 1 is selected
        And Activity Item Class for Activity Instance Item 1 is selected
        And Selected Activity Instance name is saved for Activity Instance Item 1
        When I click the Activity Instance Link plus button
        Then Activity Instance Item 2 table is visible
        When Activity Instance for Activity Instance Item 2 is selected
        And Activity Item Class for Activity Instance Item 2 is selected
        And Selected Activity Instance name is saved for Activity Instance Item 2
        And User goes to 'Item' step of crf item creation
        And The CRF Item datatype is set as 'integer'
        When The 'save-button' button is clicked
        Then The form is no longer available
        And The current URL is '/library/crf-builder/items'
        When The '/library/crf-builder/odm-viewer' page is opened
        When I select created Form from the Form Name dropdown list
        And User clicks the GENERATE button
        Then The iframe containing generated data is displayed
        When I click the Activity Instance option from the right top corner
        Then The added Activity Instance Link is displayed under the test item name

    Scenario: [Create][Table View][Single Link][CRF Item Page] User must be able to add Activity Instance Links in Table View and verify result in CRF Viewer
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And Created test CRF Item is found
        When The 'Manage Activity Instance Links' option is clicked from the three dot menu list
        Then The RESET button is disabled
        And The Edit Item page is opened
        And By default the Form view of CRF Item instance linkage is selected
        When User switch to table view of CRF Item instance linkage
        When User selects first value for linked Activity Instance
        And I select an Activity Item Class from the table
        And Selected Activity Instance name in the table view is saved
        And User goes to 'Item' step of crf item creation
        And The CRF Item datatype is set as 'integer'
        And The 'save-button' button is clicked
        Then The form is no longer available
        And The current URL is '/library/crf-builder/items'
        When The '/library/crf-builder/odm-viewer' page is opened
        When I select created Form from the Form Name dropdown list
        And User clicks the GENERATE button
        Then The iframe containing generated data is displayed
        When I click the Activity Instance option from the right top corner
        Then The added Activity Instance Link is displayed under the test item name
    
    Scenario: [Mandatory Field Validation][Form View][CRF Item Page] User must select both Activity Instance and Activity Item Class to save Activity Instance Link
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And Created test CRF Item is found
        When The 'Manage Activity Instance Links' option is clicked from the three dot menu list
        Then The RESET button is disabled
        And The Edit Item page is opened
        When I click the Activity Instance Link plus button
        Then Activity Instance Item 1 table is visible
        And I am not able to select a value from the Activity Item Class dropdown list before I have selected a value from the Activity Instance dropdown list
        And User goes to 'Item' step of crf item creation
        And The CRF Item datatype is set as 'integer'
        And User goes to 'Activity Instance Links' step of crf item creation
        When The 'save-button' button is clicked
        Then I should see alert messages for both Activity Instance and Activity Item Class fields
        And Activity Instance for Activity Instance Item 1 is selected
        When Activity Item Class dropdown is activivated without selecting any value
        Then I should see a field validation message for the Activity Item Class dropdown list
        When The 'save-button' button is clicked
        Then I should see an alert message for the Activity Item Class field

    Scenario: [Delete][Form View][CRF Item Page] User must be able to delete Activity Instance Link from a CRF Item in Form View and verify result in CRF Viewer
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And Created test CRF Item is found
        When The 'Manage Activity Instance Links' option is clicked from the three dot menu list
        Then The RESET button is disabled
        And The Edit Item page is opened
        When I click the Activity Instance Link plus button
        Then Activity Instance Item 1 table is visible
        And The Delete button is visible
        When I click the Delete button
        Then The Edit Item page does not show any linked Activity Instances
        When I click the Activity Instance Link plus button
        Then Activity Instance Item 1 table is visible
        And Activity Instance for Activity Instance Item 1 is selected
        And Activity Item Class for Activity Instance Item 1 is selected
        And Selected Activity Instance name is saved for Activity Instance Item 1
        And User goes to 'Item' step of crf item creation
        And The CRF Item datatype is set as 'integer'
        And The 'save-button' button is clicked
        Then The form is no longer available
        And The current URL is '/library/crf-builder/items'
        When The 'Manage Activity Instance Links' option is clicked from the three dot menu list
        And The Edit Item page is opened
        And Activity Instance Item 1 table is visible
        Then Saved linked Activity Instance Item table is visible
        When I click the Delete button
        Then The Edit Item page does not show any linked Activity Instances
        And The RESET button is enabled
        And User goes to 'Item' step of crf item creation
        And The CRF Item datatype is set as 'integer'
        When The 'save-button' button is clicked
        Then The form is no longer available
        And The current URL is '/library/crf-builder/items'
        When The 'Manage Activity Instance Links' option is clicked from the three dot menu list
        And The Edit Item page is opened
        Then The Edit Item page does not show any linked Activity Instances
        And The RESET button is disabled

   @manual_test
    Scenario: [Reset][Form View][CRF Item Page] User must be able to reset Activity Instance Link from a CRF Item and verify page state
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And Created test CRF Item is found
        When The 'Manage Activity Instance Links' option is clicked from the three dot menu list
        Then The RESET button is disabled
        And The Edit Item page is opened
        And The Edit Item page does not show any linked Activity Instances
        And By default the Form view of CRF Item instance linkage is selected
        When I click the Activity Instance Link plus button
        Then Activity Instance Item 1 table is visible
        And Activity Instance for Activity Instance Item 1 is selected
        And Activity Item Class for Activity Instance Item 1 is selected
        And Selected Activity Instance name is saved for Activity Instance Item 1
        Then The RESET button is enabled
        When I click the RESET button
        Then The Edit Item page does not show any linked Activity Instances
        And The RESET button is disabled

