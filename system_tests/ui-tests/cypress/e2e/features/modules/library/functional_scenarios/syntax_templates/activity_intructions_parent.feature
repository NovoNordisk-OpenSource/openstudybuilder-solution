@REQ_ID:1070684
Feature: Library - Syntax Templates - Activity Instructions - Parent

    As a user, I want to manage every Activity template under the Syntax Template Library
    Background: User must be logged in
        Given The user is logged in
        
    Scenario: [Create][Sequence number] System must generate sequence number for Activity Instruction Templates when they are created
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And The '/library/activity_instruction_templates/parent' page is opened
        And The activity instruction is searched and found
        When The latest sequence number is saved
        And [API] Activity Instruction in status Draft exists
        And The activity instruction is searched and found
        Then Sequence number is incremented

    @pending_implementation
    Scenario: Template Instantiations must be update when parent template has been updated
        Given The test Activity Parent Template exists with a status as 'Draft'
        When The'Approve' option is clicked from the three dot menu list
        Then all related activity template instantiations must be cascade updated to new version and approved
        And the displayed pop-up snack must include information on number of updated activity template instantiations

    @smoke_test
    Scenario: [Create][Positive case] User must be able to create Activity Instruction template
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        And The activity instruction template form is filled with base data
        And Form continue button is clicked
        And Form continue button is clicked
        And All activity instruction indexes are filled in
        And User intercepts activity templates request
        And Form save button is clicked
        And User waits for activity templates request
        And The activity instruction is searched and found
        Then The Activity Instruction template is visible in the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Create][N/A indexes] User must be able to create Activity Instruction template with NA indexes
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        And The activity instruction template form is filled with base data
        And Form continue button is clicked
        And Form continue button is clicked
        When All Not Applicable checkboxes are checked
        And The mandatory indexes are filled
        And User intercepts activity templates request
        And Form save button is clicked
        And User waits for activity templates request
        And The activity instruction is searched and found
        Then The Activity Instruction template is visible in the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Actions][Edit][0.1 version] User must be able to edit initial version of the Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And The 'library/activity_instruction_templates/parent' page is opened
        And The activity instruction is searched and found
        When The 'Edit' option is clicked from the three dot menu list
        And The activity instruction template form is filled with base data
        And Form continue button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        And Template change description is provided
        And User intercepts activity templates request
        And Form save button is clicked
        And User waits for activity templates request
        And The activity instruction is searched and found
        Then The Activity Instruction template is visible in the table
        And The item has status 'Draft' and version '0.2'

    Scenario: [Create][Mandatory fields] User must not be able to create Activity Instruction template without: Template Text
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        When Form continue button is clicked
        Then The validation appears for Template name
        And The form is not closed

    Scenario: [Create][Uniqueness check][Name] User must not be able to create Activity Instruction template with not unique Template Text
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        And The activity instruction template form is filled with already existing name
        And Form continue button is clicked
        And Form continue button is clicked
        And All activity instruction indexes are filled in
        And Form save button is clicked
        Then The pop up displays 'already exists'
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to create Activity Instruction template without: Indication or Disorder
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        And The activity instruction template form is filled with base data
        And Form continue button is clicked
        And Form continue button is clicked
        And All activity instruction indexes are filled in
        When Indication or Disorder index is cleared
        And Form save button is clicked
        Then The validation appears for Indication or Disorder field
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to create Activity Instruction template without: Activity Group
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        And The activity instruction template form is filled with base data
        And Form continue button is clicked
        And Form continue button is clicked
        And All activity instruction indexes are filled in
        And The Activity Group index is cleared
        And Form save button is clicked
        Then The validation appears for activity template group field
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to create Activity Instruction template without: Activity SubGroup
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        And The activity instruction template form is filled with base data
        And Form continue button is clicked
        And Form continue button is clicked
        And All activity instruction indexes are filled in
        And The Activity Subgroup index is cleared
        And Form save button is clicked
        Then The validation appears for activity template subgroup field
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to create Activity Instruction template without: Activity
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        And The activity instruction template form is filled with base data
        And Form continue button is clicked
        And Form continue button is clicked
        And All activity instruction indexes are filled in
        And The Activity index is cleared
        And Form save button is clicked
        Then The validation appears for Activity field
        And The form is not closed

    Scenario: [Create][Syntax validation] User must be able to verify syntax when creating Activity Instruction template
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        When The new template name is prepared with a parameters
        And The syntax is verified
        Then The pop up displays "This syntax is valid"

    Scenario: [Create][Hide parameters] User must be able to hide parameter of the Activity Instruction template
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        When The new template name is prepared with a parameters
        And Form continue button is clicked
        And The user hides the parameter in the next step
        Then The parameter is not visible in the text representation

    Scenario: [Create][Select parameters] User must be able to select parameter of the Activity Instruction template
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        When The new template name is prepared with a parameters
        And Form continue button is clicked
        And The user picks the parameter from the dropdown list
        Then The parameter value is visible in the text representation

    Scenario: [Actions][Delete] User must be able to delete the Draft Activity Instruction template in version below 1.0
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        Then User intercepts activity templates request
        And The 'library/activity_instruction_templates/parent' page is opened
        And User waits for activity templates request
        And The activity instruction is searched and found
        When The 'Delete' option is clicked from the three dot menu list
        Then The parent activity is no longer available

    Scenario: [Actions][Approve] User must be able to approve the Draft Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        Then User intercepts activity templates request
        And The 'library/activity_instruction_templates/parent' page is opened
        And User waits for activity templates request
        And The activity instruction is searched and found
        When The 'Approve' option is clicked from the three dot menu list
        Then The pop up displays 'Activity template is now in Final state'
        And The item has status 'Final' and version '1.0'

    Scenario: [Actions][Edit indexing] User must be able to edit indexing of Final Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        And Group name created through API is found
        Then User intercepts activity templates request
        And The 'library/activity_instruction_templates/parent' page is opened
        And User waits for activity templates request
        And The activity instruction is searched and found
        When The 'Edit indexing' option is clicked from the three dot menu list
        And The activity group data is loaded in the edit indexing form
        And The indication indexes edition is initiated
        And Form save button is clicked
        And The pop up displays 'Indexing properties updated'
        And The activity instruction is searched and found
        And The 'Edit indexing' option is clicked from the three dot menu list
        And The activity group data is loaded in the edit indexing form
        Then The indication index is updated

    Scenario: [Actions][Edit][Mandatory fields] User must not be able to save changes to Activity Instruction template without: Change description
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        Then User intercepts activity templates request
        And The 'library/activity_instruction_templates/parent' page is opened
        And User waits for activity templates request
        And The activity instruction is searched and found
        When The 'Edit' option is clicked from the three dot menu list
        And User goes to Change description step
        And The template change description is cleared
        And Form save button is clicked
        Then The validation appears for change description field
        And The form is not closed

    Scenario: [Actions][New version] User must be able to add a new version of the Final Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        Then User intercepts activity templates request
        And The 'library/activity_instruction_templates/parent' page is opened
        And User waits for activity templates request
        And The activity instruction is searched and found
        When The 'New version' option is clicked from the three dot menu list
        Then The pop up displays 'New version created'
        And The item has status 'Draft' and version '1.1'

    Scenario: [Actions][Edit][1.1 version] User must be able to edit new version of the Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        Then User intercepts activity templates request
        And The 'library/activity_instruction_templates/parent' page is opened
        And User waits for activity templates request
        And The activity instruction is searched and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'
        When The 'Edit' option is clicked from the three dot menu list
        And The activity template metadata update is started
        And Form continue button is clicked
        And Form continue button is clicked
        And All activity instruction indexes are cleared and filled in
        And Form continue button is clicked
        And Template change description is provided
        And Form save button is clicked
        And The activity instruction is searched and found
        Then The item has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '2.0'

    Scenario: [Actions][Inactivate] User must be able to inactivate the Final Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        Then User intercepts activity templates request
        And The 'library/activity_instruction_templates/parent' page is opened
        And User waits for activity templates request
        And The activity instruction is searched and found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The pop up displays 'Activity template retired'
        And The item has status 'Retired' and version '1.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate the Retired Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        And [API] Activity Instruction is inactivated
        Then User intercepts activity templates request
        And The 'library/activity_instruction_templates/parent' page is opened
        And User waits for activity templates request
        And The activity instruction is searched and found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The pop up displays 'Activity template is now in Final state'
        And The item has status 'Final' and version '1.0'

    @manual_test
    Scenario: User must be able to view the history for the Parent Activity template with a status as 'Retired'
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        And [API] Activity Instruction is inactivated
        Then User intercepts activity templates request
        And The 'library/activity_instruction_templates/parent' page is opened
        And User waits for activity templates request
        And The activity instruction is searched and found
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
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames

    Scenario: [Cancel][Creation] User must be able to Cancel creation of the Activity Instruction template
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The Add template button is clicked
        And The activity template edition form is filled with data
        And Form continue button is clicked
        And Form continue button is clicked
        And All activity instruction indexes are filled in
        When Fullscreen wizard is closed by clicking cancel button
        And Action is confirmed by clicking continue
        Then The form is no longer available
        And The parent activity is no longer available

    Scenario: [Cancel][Edition] User must be able to Cancel edition of the Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The activity instruction is searched and found
        When The 'Edit' option is clicked from the three dot menu list
        And The activity template edition form is filled with data
        And Form continue button is clicked
        And Form continue button is clicked
        And All activity instruction indexes are filled in
        And Fullscreen wizard is closed by clicking cancel button
        And Action is confirmed by clicking continue
        Then The form is no longer available
        And The parent activity is no longer available

    Scenario: [Cancel][Indexing edtion] User must be able to Cancel indexes edition of the Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The activity instruction is searched and found
        When The 'Edit indexing' option is clicked from the three dot menu list
        When The indication indexes edition is initiated
        And Modal window form is closed by clicking cancel button
        Then The form is no longer available
        When The 'Edit indexing' option is clicked from the three dot menu list
        And The indexes are not updated

    Scenario: [Actions][Availability] User must only have access correct actions depending on item state
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The activity instruction is searched and found
        When The item actions button is clicked
        Then Only actions that should be avaiable for the Draft item are displayed
        And [API] Activity Instruction is approved
        And The activity instruction is searched and found
        When The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed
        And 'Edit indexing' action is available
        And 'Create pre-instantiation' action is available
        And [API] Activity Instruction is inactivated
        And The activity instruction is searched and found
        When The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed
