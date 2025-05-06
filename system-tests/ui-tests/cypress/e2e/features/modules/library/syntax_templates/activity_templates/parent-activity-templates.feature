@REQ_ID:1070684
Feature: Library - Activity Templates

    As a user, I want to manage every Activity template under the Syntax Template Library
    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to navigate to the Activity template under the Syntax Template Library
        Given The '/library' page is opened
        When The 'Activity Instructions' submenu is clicked in the 'Syntax Templates' section
        Then The current URL is '/library/activity_instruction_templates/parent'

    Scenario: User must be able to see the Parent Activity template table with listed columns
        Given The '/library/activity_instruction_templates/parent' page is opened
        And A table is visible with following headers
            | headers         |
            | Sequence number |
            | Activity        |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: User must be able to select visibility of columns in the table
        Given The '/library/activity_instruction_templates/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @api_specification
    Scenario: System must generated sequence number for Activity Parent Templates when they are created
        Given an Activity Parent Template is created
        Then the attribute for 'Sequence number' will hold an automatic generated number as 'OT'+[Order of Activity Parent Template]

    @api_specification
    Scenario: System must generated sequence number for Activity Pre-instance Templates when they are created
        Given an Activity Pre-instance Template is created
        Then the attribute for 'Sequence number' will hold an automatic generated number as 'OT'+[Order of Activity Parent Template]+'-OP'+[Order of Pre-instantiation]

    @pending_implementation
    Scenario: Template Instantiations must be update when parent template has been updated
        Given The test Activity Parent Template exists with a status as 'Draft'
        When The'Approve' option is clicked from the three dot menu list
        Then all related activity template instantiations must be cascade updated to new version and approved
        And the displayed pop-up snack must include information on number of updated activity template instantiations

    Scenario: User must be able to add a new Parent Activity template in Sponsor standards tab
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new activity is added in the library
        Then The new Activity is visible in the Activity Templates Table

    Scenario: User must be able to add a new Parent Activity template with NA indexes in Sponsor standards tab
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity is added in the library with not applicable for indexes
        Then The new Activity is visible with Not Applicable indexes in the Activity Templates Table

    Scenario: User must be able to edit draft version of the Parent Activity template
        Given The 'library/activity_instruction_templates/parent' page is opened
        Given The new activity is added in the library
        When The 'Edit' option is clicked from the three dot menu list
        And The activity metadata is updated
        Then The updated Activity is visible within the table

    Scenario: User must not be able to create a new Parent Activity template without Template Text populated
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity template is added without template text
        Then The validation appears for Template name
        And The form is not closed

    Scenario: User must not be able to create a new Parent Activity template with not unique Template Text
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new activity is added in the library
        And The second activity is added with the same template text
        Then The pop up displays 'already exists'
        And The form is not closed

    Scenario: User must not be able to create a new Parent Activity template without Indication or Disorder field populated
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity template is added without Indication or Disorder
        Then The validation appears for Indication or Disorder field
        And The form is not closed

    Scenario: User must not be able to create a new Parent Activity template without Activity Group field populated
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity template is added without Activity Group
        Then The validation appears for Activity Group field
        And The form is not closed

    Scenario: User must not be able to create a new Parent Activity template without Activity Subgroup field populated
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity template is added without Activity Subgroup
        Then The validation appears for Activity Subgroup field
        And The form is not closed

    Scenario: User must not be able to create a new Parent Activity template without Activity field populated
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity template is added without Activity field
        Then The validation appears for Activity field
        And The form is not closed

    Scenario: User must be able to verify valid syntax when adding a new Parent Activity template
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new template name is prepared with a parameters
        And The syntax is verified
        Then The pop up displays "This syntax is valid"

    Scenario: User must be able to hide parameter from the Parent Activity template
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new template name is prepared with a parameters
        And The user hides the parameter in the next step
        Then The parameter is not visible in the text representation

    Scenario: User must be able to test template for the Parent Activity template
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new template name is prepared with a parameters
        And The user picks the parameter from the dropdown list
        Then The parameter value is visible in the text representation

    Scenario: User must be able to delete the drafted version of Parent Activity template in version below 1.0
        Given The 'library/activity_instruction_templates/parent' page is opened
        Given The new activity is added in the library
        When The 'Delete' option is clicked from the three dot menu list
        Then The parent activity is no longer available

    Scenario: User must be able to approve the drafted version of Parent Activity template
        Given The 'library/activity_instruction_templates/parent' page is opened
        Given The new activity is added in the library
        When The 'Approve' option is clicked from the three dot menu list
        Then The pop up displays 'Activity template is now in Final state'
        And The activity template has status Final and version 1.0

    Scenario: User must be able to edit indexing for final version of the templates
        Given The 'library/activity_instruction_templates/parent' page is opened
        Given The activity template exists with a status as 'Final'
        When The 'Edit indexing' option is clicked from the three dot menu list
        And The indexing is updated for the Activity Template
        And The 'Edit indexing' option is clicked from the three dot menu list
        Then The indexes in activity template are updated

    Scenario: User must not be able to save the edited version of the draft Parent Activity template without filled in mandatory field 'Change description'
        Given The 'library/activity_instruction_templates/parent' page is opened
        Given The new activity is added in the library
        When The 'Edit' option is clicked from the three dot menu list
        When The created activity template is edited without change description provided
        Then The validation appears for activity change description field
        And The form is not closed

    Scenario: User must be able to add a new version for the Parent Activity template with a status as 'Final'
        Given The 'library/activity_instruction_templates/parent' page is opened
        Given The new activity is added in the library
        When The 'Approve' option is clicked from the three dot menu list
        Given The activity template exists with a status as 'Final'
        When The 'New version' option is clicked from the three dot menu list
        Then The pop up displays 'New version created'
        And The activity template has status Draft and version incremented by 0.1

    Scenario: User must be able to inactivate the Parent Activity template with a status as 'Final'
        Given The 'library/activity_instruction_templates/parent' page is opened
        Given The new activity is added in the library
        When The 'Approve' option is clicked from the three dot menu list
        Given The activity template exists with a status as 'Final'
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The pop up displays 'Activity template retired'
        And The activity template has status Retired and the same version as before

    Scenario: User must be able to reactivate the Parent Activity template with a status as 'Retired'
        Given The 'library/activity_instruction_templates/parent' page is opened
        Given The activity template exists with a status as 'Retired'
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The pop up displays 'Activity template is now in Final state'
        And The activity template has status Final and the same version as before

    @manual_test
    Scenario: User must be able to view the history for the Parent Activity template with a status as 'Retired'
        Given The 'library/activity_instruction_templates/parent' page is opened
        Given The activity template exists with a status as 'Retired'
        When The 'Reactivate' option is clicked from the three dot menu list
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
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames

    Scenario: User must be able to use table pagination
        Given The '/library/activity_instruction_templates/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario Outline: User must be able to filter the table by text fields
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
            | name                   |
            | Indication or disorder |
            | Activity group         |
            | Activity subgroup     |