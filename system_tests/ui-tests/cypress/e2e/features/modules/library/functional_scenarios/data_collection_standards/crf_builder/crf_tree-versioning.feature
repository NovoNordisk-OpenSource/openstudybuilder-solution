@REQ_ID:1070683

Feature: Library - Data Collection Standards - CRF Versioning
    As a user, I want to manage versioning of CRFs, where a CRF is a hierarchy consisting of its Collections, Item Groups and Items in the CRF Library

    ########################################################################## CRF Versioning functionality Overview ############################################################################
    ##                                                                                                                                                                                         ##
    ## 1 Hierarchical Structure: CRF Collection → Forms → Item Groups → Items                                                                                                                  ##
    ## 2 Basic Business Rules:                                                                                                                                                                 ##           
    ##      2.1 Parent in Draft Status (Not locked) -> Parents always connect to the latest version of the child, updates in the child version automatically reflect on the parent connection. ##
    ##      2.2 Parent in Final Status (Locked) -> Parent connects to the old version of the child, updates in the child version do not affect the parent's connection.                        ##
    ## 3. Example Scenarios:                                                                                                                                                                   ##
    ##      3.1 Scenario:                                                                                                                                                                      ##
    ##          Given Parent in Draft status                                                                                                                                                   ##
    ##          When child is edited or a new version is created                                                                                                                               ##
    ##          Then Parent automatically connects to the latest version of the Child                                                                                                          ##
    ##      3.2 Scenario:                                                                                                                                                                      ##
    ##          Given Parent in Final status.                                                                                                                                                  ##
    ##          When child is edited or a new version is created                                                                                                                               ##
    ##          Then Parent still connected to the old version of the Child                                                                                                                    ##   
    ##      3.3 Scenario:                                                                                                                                                                      ##
    ##          Given Parent in Final status, still connected to the old version of the Child                                                                                                  ##
    ##          When Parent receives a new version, changing to Draft                                                                                                                          ##
    ##          Then Parent should automatically connect to the new version of the Child                                                                                                       ##
    ##                                                                                                                                                                                         ##
    ########################################################################## CRF Versioning functionality Overview ############################################################################

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Draft Parent][Edit Child] User must be able to edit the child elements linked to Draft CRF Collection and the linkage should be updated to the latest version in the CRF Tree
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/forms' page is opened
        When The CRF Form created via API is searched and found
        And The 'Edit' option is clicked from the three dot menu list
        And The CRF Form name created via API is updated
        And Form save button is clicked
        Then The item has status 'Draft' and version '0.2'
        When The '/library/crf-builder/item-groups' page is opened
        And The CRF Item Group created via API is searched and found
        When The 'Edit' option is clicked from the three dot menu list
        And The CRF Item Group name created via API is updated
        And Form save button is clicked
        Then The item has status 'Draft' and version '0.2'
        When The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And User waits for the table
        And The CRF Item created via API is searched and found
        When The 'Edit' option is clicked from the three dot menu list
        And The CRF Item name created via API is updated
        And The CRF Item datatype is set as 'integer'
        And Form save button is clicked
        Then The item has status 'Draft' and version '0.2'
        When The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        And The CRF Tree is expanded for form
        And The CRF Tree is expanded for item group
        Then All elements linked to the CRF Collection have version '0.2', status 'Draft'
        # Notification for editing action is under discussion
        # Then the 'Note, the following CRF Collections have references to this Form, Item Group, or Items, and if updates are saved this will apply to these CRF collections:' notification is presented to the user
        # And the list of affected CRF Collections are listed

    Scenario: [Draft Parent][New version Child] User must be able to create new version of the child elements linked to Draft CRF Collection and the linkage should be updated to the latest version in the CRF Tree
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And [API] CRF Form is approved
        And The '/library/crf-builder/forms' page is opened
        When The CRF Form created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        Then The New version popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Draft' and version '1.1'
        And The '/library/crf-builder/item-groups' page is opened
        When The CRF Item Group created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        Then The New version popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Draft' and version '1.1'
        And The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And User waits for the table
        When The CRF Item created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        Then The New version popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Draft' and version '1.1'
        When The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        And The CRF Tree is expanded for form
        And The CRF Tree is expanded for item group
        Then All elements linked to the CRF Collection have version '1.1', status 'Draft'

    Scenario: [Approve Parent] User must be able to approve CRF Collection and all linked child elements should be put in the Final state
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And The '/library/crf-builder/collections' page is opened
        When The CRF Collection created via API is searched and found
        And The 'Approve' option is clicked from the three dot menu list
        Then The approval popup window is displayed
        And All the child elements should be displayed in the notification page
        When Action is confirmed by clicking continue
        And The item has status 'Final' and version '1.0'
        When The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        And The CRF Tree is expanded for form
        And The CRF Tree is expanded for item group
        Then All elements linked to the CRF Collection have version '1.0', status 'Final'

    Scenario: [Final Parent][New version Child] User must be able to create new version of the child elements linked to Final CRF Collection and the linkage should be stay on the previous version in the CRF Tree
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And [API] CRF Collection is approved
        And The '/library/crf-builder/forms' page is opened
        When The CRF Form created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        Then The New version popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Draft' and version '1.1'
        And The '/library/crf-builder/item-groups' page is opened
        When The CRF Item Group created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        Then The New version popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Draft' and version '1.1'
        And The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And User waits for the table
        When The CRF Item created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        Then The New version popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Draft' and version '1.1'
        When The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        And The CRF Tree is expanded for form
        And The CRF Tree is expanded for item group
        Then All elements linked to the CRF Collection have version '1.0', status 'Final'

     Scenario: [Final Parent][Edit Child] User must be able to edit the child elements linked to Final CRF Collection and the linkage should stay on to the previous version in the CRF Tree
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Item Group is created
        And [API] CRF Item is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Item Group is linked to the form
        And [API] CRF Item is linked to the group
        And [API] CRF Collection is approved
        And The '/library/crf-builder/forms' page is opened
        When The CRF Form created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        And The confirmation dilog is no longer available
        And The pop up displays 'New version created'
        And User waits for the table
        When The 'Edit' option is clicked from the three dot menu list
        And The CRF Form name created via API is updated
        And Form save button is clicked
        Then The item has status 'Draft' and version '1.2'
        When The '/library/crf-builder/item-groups' page is opened
        And The CRF Item Group created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        And The confirmation dilog is no longer available
        And The pop up displays 'New version created'
        And User waits for the table
        When The 'Edit' option is clicked from the three dot menu list
        And The CRF Item Group name created via API is updated
        And Form save button is clicked
        Then The item has status 'Draft' and version '1.2'
        When The '/library/crf-builder/items' page is opened
        And User waits for CRF Items data to load
        And User waits for the table
        And The CRF Item created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        And The confirmation dilog is no longer available
        And The pop up displays 'New version created'
        And User waits for the table
        When The 'Edit' option is clicked from the three dot menu list
        And The CRF Item name created via API is updated
        And The CRF Item datatype is set as 'integer'
        And Form save button is clicked
        Then The item has status 'Draft' and version '1.2'
        When The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        And The CRF Tree is expanded for form
        And The CRF Tree is expanded for item group
        Then All elements linked to the CRF Collection have version '1.0', status 'Final'
        # Notification for editing action is under discussion
        # Then the 'Note, the following CRF Collections have references to this Form, Item Group, or Items, and if updates are saved this will apply to these CRF collections:' notification is presented to the user
        # And the list of affected CRF Collections are listed

    Scenario: [Final Parent][Approve Child] User must be able to approve the child element linked to Final CRF Collection and the linkage should stay on to the previous version in the CRF Tree
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Collection is approved
        And The '/library/crf-builder/forms' page is opened
        When The CRF Form created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        Then The New version popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Draft' and version '1.1'
        When The 'Approve' option is clicked from the three dot menu list
        Then The approval popup window is displayed
        And No child elements should be displayed in the notification page
        When Action is confirmed by clicking continue
        Then The item has status 'Final' and version '2.0'
        When The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        Then CRF Collection links to the form version '1.0', status 'Final'

    Scenario: [Final Parent][New version Parent] User must be able to create new version CRF Collection and the linkage should be updated to the latest version in the CRF Tree
        Given [API] A CRF Collection is created
        And [API] A CRF Form is created
        And [API] CRF Form is linked to the collection
        And [API] CRF Collection is approved
        And The '/library/crf-builder/forms' page is opened
        When The CRF Form created via API is searched and found
        And The 'New version' option is clicked from the three dot menu list
        Then The New version popup window is displayed
        When Action is confirmed by clicking continue
        Then The item has status 'Draft' and version '1.1'
        When The '/library/crf-builder/collections' page is opened
        And The CRF Collection created via API is searched and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'
        When The '/library/crf-builder/crf-tree' page is opened
        And The CRF Collection is found and click in the CRF Tree filters
        And The CRF Tree is expanded for collection
        Then CRF Collection links to the form version '1.1', status 'Draft'

@manual_test
    Scenario: [Draft Parent][Inactive Child] User must after inactive CRF child element for a CRF parent element in Draft see the parent CRF element refer to the new CRF child version on the CRF Tree page.
        Given A CRF Collection in status Draft exists linking a Form, an Item Group, and an Item in Status Final
        When I click on 'Inactive' option from the three dot menu for the Form
        Then The Form is in Retired status
        When The '/library/crf-builder/crf-tree' page is opened 
        Then CRF Collection should automatically refer to the new latest version of the linked Form
        # All scenarios related to CRF forms, Item Groups, and Items can be repeated for the Inactivate action

@manual_test
    Scenario: [Final Parent][Inactive Child] User must after inactive CRF child element for a CRF parent element in Final see the parent CRF element refer to the old CRF child version on the CRF Tree page.
        Given A CRF Collection in status Final exists linking a Form in Status Final
        When I click on 'Inactive' option from the three dot menu for the Form
        Then The Form is in Retired status
        When The '/library/crf-builder/crf-tree' page is opened 
        Then CRF Collection should still link to the old version of the linked Form
        # All scenarios related to CRF forms, Item Groups, and Items can be repeated for the Inactivate action

@manual_test
    Scenario: [Draft Parent][Reactive Child] User must after reactive CRF child element for a CRF parent element in Draft see the parent CRF element refer to the new CRF child version on the CRF Tree page.
        Given A CRF Collection in status Draft exists linking a Form in Status Retired
        When I click on 'Reactivate' option from the three dot menu for the Form
        Then The Form is in Final status
        When The '/library/crf-builder/crf-tree' page is opened 
        Then CRF Collection should automatically refer to the new latest version of the linked Form
        # All scenarios related to CRF forms, Item Groups, and Items can be repeated for the Reactivate action

@manual_test
    Scenario: [Final Parent][Reactive Child] User must after reactive CRF child element for a CRF parent element in Final see the parent CRF element refer to the old CRF child version on the CRF Tree page.
        Given A CRF Collection in status Final exists linking a Form in Status Retired
        When I click on 'Reactivate' option from the three dot menu for the Form
        Then The Form is in Final status
        When The '/library/crf-builder/crf-tree' page is opened 
        Then CRF Collection should still link to the old version of the linked Form
        # All scenarios related to CRF forms, Item Groups, and Items can be repeated for the Reactivate action

# Define how we manage versions of other sub items, like Descriptions, Alias, Conditions, Method,... (this part is under discussion)