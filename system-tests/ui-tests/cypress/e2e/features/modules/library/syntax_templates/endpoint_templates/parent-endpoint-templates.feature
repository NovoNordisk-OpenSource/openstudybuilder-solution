@REQ_ID:1070684
Feature: Library - Endpoint templates

    As a user, I want to manage every Endpoint template under the Syntax Template Library
    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to the Endpoint template under the Syntax Template Library
        Given The '/library' page is opened
        When The 'Endpoints' submenu is clicked in the 'Syntax Templates' section
        Then The current URL is '/library/endpoint_templates'

    Scenario: User must be able to see the Parent Endpoint template table with listed columns
        Given The '/library/endpoint_templates' page is opened
        And A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: User must be able to select visibility of columns in the table
        Given The '/library/endpoint_templates' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @api_specification
    Scenario: System must generated sequence number for Endpoint Parent Templates when they are created
        Given an Endpoint Parent Template is created
        # This could be with a reference to the API POST Endpoint and a following API GET Endpoint - or just formulated as a functional requrement
        Then the attribute for 'Sequence number' will hold an automatic generated number as 'OT'+[Order of Endpoint Parent Template]

    @api_specification
    Scenario: System must generated sequence number for Endpoint Pre-instance Templates when they are created
        Given an Endpoint Pre-instance Template is created
        Then the attribute for 'Sequence number' will hold an automatic generated number as 'OT'+[Order of Endpoint Parent Template]+'-OP'+[Order of Pre-instantiation]

    # If approval is for version +1.0 and any instantiations exist then a cascade update and approval is needed
    @pending_implementation
    Scenario: Template Instantiations must be update when parent template has been updated
        Given The test Endpoint Parent Template exists with a status as 'Draft'
        When The'Approve' option is clicked from the three dot menu list
        Then all related endpoint template instantiations must be cascade updated to new version and approved
        And the displayed pop-up snack must include information on number of updated endpoint template instantiations

    Scenario: User must be able to add a new Parent Endpoint template in Sponsor standards tab
        Given The 'library/endpoint_templates' page is opened
        When The new endpoint is added in the library
        Then The new Endpoint is visible in the Endpoint Templates Table

    Scenario: User must be able to add a new Parent Endpoint template with NA indexes in Sponsor standards tab
        Given The 'library/endpoint_templates' page is opened
        When The new Endpoint is added in the library with not applicable for indexes
        Then The new Endpoint is visible with Not Applicable indexes in the Endpoint Templates Table

    Scenario: User must be able to edit draft version of the Parent Endpoint template
        Given The 'library/endpoint_templates' page is opened
        Given The new endpoint is added in the library
        Then The pop up displays "Endpoint template added"
        When The 'Edit' action is clicked for the created endpoint
        And The endpoint metadata is updated
        Then The updated Endpoint is visible within the table

    Scenario: User must not be able to create a new Parent Endpoint template without Template Text populated
        Given The 'library/endpoint_templates' page is opened
        When The new Endpoint template is added without template text
        Then The validation appears for Template Text field
        And The form is not closed

    Scenario: User must not be able to create a new Parent Endpoint template with not unique Template Text
        Given The 'library/endpoint_templates' page is opened
        When The new endpoint is added in the library
        And The second endpoint is added with the same template text
        Then The pop up displays 'already exists'
        And The form is not closed

    Scenario: User must not be able to create a new Parent Endpoint template without Indication or Disorder populated
        Given The 'library/endpoint_templates' page is opened
        When The new Endpoint template is added without Indication or Disorder
        Then The validation appears for Indication or Disorder field
        And The form is not closed

    Scenario: User must not be able to create a new Parent Endpoint template without Endpoint Category populated
        Given The 'library/endpoint_templates' page is opened
        When The new Endpoint template is added without Endpoint Category
        Then The validation appears for Endpoint Category field
        And The form is not closed

    Scenario: User must not be able to create a new Parent Endpoint template without Endpoint Subcategory Relation
        Given The 'library/endpoint_templates' page is opened
        When The new Endpoint template is added without Endpoint Subcategory
        Then The validation appears for Endpoint Subcategory field
        And The form is not closed

    Scenario: User must be able to verify valid syntax when adding a new Parent Endpoint template
        Given The 'library/endpoint_templates' page is opened
        When The new template name is prepared with a parameters
        And The syntax is verified
        Then The pop up displays "This syntax is valid"

    Scenario: User must be able to hide parameter from the Parent Endpoint template
        Given The 'library/endpoint_templates' page is opened
        When The new template name is prepared with a parameters
        And The user hides the parameter in the next step
        Then The parameter is not visible in the text representation

    Scenario: User must be able to test template for the Parent Endpoint template
        Given The 'library/endpoint_templates' page is opened
        When The new template name is prepared with a parameters
        And The user picks the parameter from the dropdown list
        Then The parameter value is visible in the text representation

    Scenario: User must be able to delete the drafted version of Parent Endpoint template in version below 1.0
        Given The 'library/endpoint_templates' page is opened
        Given The new endpoint is added in the library
        Then The pop up displays "Endpoint template added"
        When The 'Delete' action is clicked for the created endpoint
        Then The pop up displays "Endpoint template has been deleted"
        And The endpoint is no longer available

    Scenario: User must be able to approve the drafted version of Parent Endpoint template
        Given The 'library/endpoint_templates' page is opened
        Given The new endpoint is added in the library
        Then The pop up displays "Endpoint template added"
        When The 'Approve' action is clicked for the created endpoint
        Then The pop up displays 'Template is now in Final state'
        And The status of the template displayed as Final with a version rounded up to 1.0

    Scenario: User must be able to edit indexing for final version of the templates
        Given The 'library/endpoint_templates' page is opened
        Given The endpoint template exists with a status as 'Final'
        When The 'Edit indexing' action is clicked for the endpoint
        And The indexing is updated for the Endpoint Template
        And The 'Edit indexing' action is clicked for the endpoint
        Then The indexes in endpoint template are updated

    Scenario: User must not be able to save the edited version of the draft Parent Endpoint template without filled in mandatory field 'Change description'
        Given The 'library/endpoint_templates' page is opened
        Given The new endpoint is added in the library
        Then The pop up displays "Endpoint template added"
        When The 'Edit' action is clicked for the created endpoint
        When The created endpoint template is edited without change description provided
        Then The validation appears for endpoint change description field
        And The form is not closed

    Scenario: User must be able to add a new version for the Parent Endpoint template with a status as 'Final'
        Given The 'library/endpoint_templates' page is opened
        Given The endpoint template exists with a status as 'Final'
        When The 'New version' action is clicked for the endpoint
        Then The pop up displays 'New version created'
        And The endpoint template is updated to draft with version incremented by 0.1

    Scenario: User must be able to inactivate the Parent Endpoint template with a status as 'Final'
        Given The 'library/endpoint_templates' page is opened
        Given The endpoint template exists with a status as 'Final'
        When The 'Inactivate' action is clicked for the endpoint
        Then The pop up displays 'Template inactivated'
        And The endpoint template is displayed with a status as Retired with the same version as before

    Scenario: User must be able to reactivate the Parent Endpoint template with a status as 'Retired'
        Given The 'library/endpoint_templates' page is opened
        Given The endpoint template exists with a status as 'Retired'
        When The 'Reactivate' action is clicked for the endpoint
        Then The pop up displays 'Template is now in Final state'
        And The endpoint template is displayed with a status as Final with the same version as before


    @manual_test
    Scenario: User must be able to view the history for the Parent Endpoint template with a status as 'Retired'
        Given The 'library/endpoint_templates' page is opened
        Given The endpoint template exists with a status as 'Retired'
        When The 'Reactivate' action is clicked for the endpoint
        Then The 'History for template' window is displayed with the following column list with values
            | Column | Header                 |
            | 1      | Indication or disorder |
            | 2      | Criterion category     |
            | 3      | Criterion sub-category |
            | 4      | Template               |
            | 5      | Guidance text          |
            | 6      | Status                 |
            | 7      | Version                |
            | 8      | Change type            |
            | 9      | User                   |
            | 10     | From                   |
            | 11     | To                     |

    @manual_test
    Scenario: User must be able to read change history of output
        Given The 'library/endpoint_templates' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The 'library/endpoint_templates' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames

    Scenario Outline: User must be able to filter the table by text fields
        Given The 'library/endpoint_templates' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
            | name                  |
            | Indication or disorder |
            # | Endpoint category     |
            # | Endpoint sub-category |
