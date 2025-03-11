@manual_test
@REQ_ID:1074260
Feature: Studies - Study SoA Footnotes


    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study footnotes for the schedule of activities.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: User must be able to navigate to study SoA Footnotes page using side menu
        Given The '/studies' page is opened
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        And The 'SoA Footnotes' tab is selected
        Then The current URL is '/studies/Study_000001/activities/footnotes'

    Scenario: User must be able to see the SoA Footnotes table with listed columns
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add SoA footnote                                                |
            | Show version history                                            |
            | Filters                                                         |
            | Columns                                                         |
            | Export                                                          |
            | Add select boxes to table to allow selection of rows for export |
        And A table is visible with following headers
            | headers           |
            | #                 |
            | Footnote          |
            | SoA items covered |
        And The following columns available to be displayed
            | 4  | Activity groups    |
            | 5  | Activity subgroups |
            | 6  | Activities         |
            | 7  | Study epochs       |
            | 8  | Study visits       |
            | 9  | Activity schedules |
            | 10 | Modified           |
            | 11 | Modified by        |

    # Footnote number is derived, see scenario below.
    #? We need to clarify if ordering is needed (e.g. to control order when multiple footnotes are attached to the same SoA item)
    # A suggestion is they are then sorted alphabetically by the footnote text
    # Column 3 list a concatination of items a SoA footnote is related to.
    # Column 4-9 each list the items of various types the SoA footnote is related to.


    ### Basic actions
    # NOTE: SoA footnotes are based on syntax templates.

    Scenario: User must be able to add a new Study SoA Footnote from standards
        # From standards := from parent or preinstantiated syntax templates
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        When The new Footnote is added for the study from standards
        Then The new Footnote is visible in the Study Footnote Table

    Scenario: User must be able to add a new Study SoA Footnote from studies by study id
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        When The new Footnote is added for the study from other studies by study id
        Then The new Footnote is visible in the Study Footnote Table

    @pending_implementation
    Scenario: User must be able to add a new Study SoA Footnote from studies by study acronym
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        When The new Footnote is added for the study from other studies by study acronym
        Then The new Footnote is visible in the Study Footnote Table

    Scenario: User must be able to add a new Study SoA Footnote from scratch
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        When The new Footnote is added for the study from scratch
        Then The new Footnote is visible in the Study Footnote Table

    Scenario: User must be able to edit template parameters for a Study SoA Footnote
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        And a Study SoA Footnote exist
        When The 'Edit' action is clicked for the Study SoA Footnote
        And the Study SoA Footnote template parameters is updated
        Then The updated SoA Footnote is visible in the Study SoA Footnote Table

    Scenario: User must be able to edit the Study SoA Footnote template text
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        And a Study SoA Footnote exist
        When The 'Edit' action is clicked for the Study SoA Footnote
        And the Study SoA Footnote template text is updated
        Then The user is notified this will be changed to be a user defined template
        And The updated SoA Footnote is visible in the Study SoA Footnote Table

    Scenario: User must be able to delete a Study Footnote
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        And a Study Footnote exist
        When The 'Delete' action is clicked for the Study Footnote
        Then The pop-up displays "Footnote deleted"
        And The Study SoA Footnote is no longer available

    ### Footnote selection for SoA items

    Scenario: User must be able to select a Study SoA Footnote and relate it to SoA items
        Given The '/studies/Study_000001/activities/detailed' page is opened
        And a Study SoA Footnote is selected from the Detailed SoA footnote list for editing
        And the 'SoA Footnote selection' view is selected
        And SoA items are selected
        And the user clicks the 'SAVE' button
        Then the Study SoA Footnote is added to the SoA item
        And all related Study SoA Footnotes get automatically numbered

    Scenario: User must be able to remove relationship of a Study SoA Footnote from SoA item
        Given The '/studies/Study_000001/activities/detailed' page is opened
        And a Study SoA Footnote is selected from the Detailed SoA footnote list for editing
        And the 'SoA Footnote selection' view is selected
        And SoA items are de-selected
        And the user clicks the 'SAVE' button
        Then the Study SoA Footnote is removed from the SoA item
        And all Study SoA Footnotes get automatically renumbered


    ### Footnote numbering

    @api_specification
    Scenario: System must support automatic numbering of Study SoA Footnotes for a study when a footnote is added
        Given a Study SoA Footnote is related to any item in the Schedule of Activities of a study
        # Activity Group, Activity Subgroup, Activity, Study Visit, Schedule of Activity (the X's in flowchart).
        Then all related Study SoA Footnotes in the study will be automatically renumbered with letters 'a', 'b', etc. starting from the first occurrence in top left corner ending at the bottom right corner
        # Letters should only be within the 26 in the English alphabet
    
    @api_specification
    Scenario: System must assign the same Study SoA Footnote nmber when  the same footnotes is assigned multiple times to different SoA items
    When the same Study SoA Footnotes is assigned multiple times to different SoA items
    Then it must get the same number based on first occurrence

    @api_specification
    Scenario: When multiple footnotes are asigned to the same SoA item and they are asigned a number then the system must sort footnotes by the assigned number 
        Given multiple Study SoA Footnotes is related to a SoA item in the Schedule of Activities of a study
        And the Study SoA Footnote is asigned a number
        Then the Study SoA Footnotes should be sorted by the assigned number for this SoA item

    @api_specification
    Scenario: When multiple footnotes are asigned to the same SoA item and they are not asigned a number then the system must sort footnotes alphabetically for number asignment
        Given multiple Study SoA Footnotes is related to a SoA item in the Schedule of Activities of a study
        And the Study SoA Footnote is not asigned a number
        Then the Study SoA Footnotes should be sorted alphabetically for this SoA item when being assigned a number

    # Combinations can also occur, two foototes asigned to the same item, one already assign a number, second not assigned yet, then the initially assigned should come first

    @api_specification
    Scenario: System must support automatic numbering of Study SoA Footnotes for a study when a footnote is removed
        Given a Study SoA Footnote is removed from any item in the Schedule of Activities of a study
        # Activity Group, Activity Subgroup, Activity, Study Visit, Schedule of Activity.
        Then all remaining related Study Footnotes in the study will be automatically renumbered with letters 'a', 'b', etc. starting from the first occurrence in the top left corner ending at the bottom right corner

    #? Clarify what we do when we have more than 26 study footnotes?


    ### Footnote constraints

    Scenario: User must not be able to create a Study SoA Footnote without a footnote text
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        When The footnote text field is not populated
        And The 'save-button' button is clicked
        Then The required field validation appears for the empty footnote text field
        And The form is not closed

    Scenario: User must not be able to create two Study SoA Footnote within one study using the same footnote text
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        When The footnote text field is not populated
        And Another Study SoA Footnote is created with the same footnote text
        Then The system displays the message "Value \"footnote text\" is not unique for the study"
        And The form is not closed

    Scenario: User must not be able to use text longer than 400 characters for the Study SoA Footnote text
        Given The '/studies/Study_000001/activities/footnotes' page is opened
        When The Study SoA Footnote text entered exceed 400 characters
        Then The message "Study SoA Footnotes must not exceed 400 characters" is displayed


    ### Display SoA Footnote
    # We should add scenarios for displaying footnote references in Detail SoA as well as Protocol SoA


    ### View History
    #? Note, this view history is likely only for the Study Footnote text and numbering, likely not the linkage to SoA items
    #? - this we should add on the Detailed SoA page in some way, as an outbound relationship from a SoA item.

    Scenario: User must be able to view history of changes for Study Footnotes
        Given the '/studies/Study_000001/activities/footnotes' page is opened
        And the 'List of Study SoA Footnotes'  tab is selected
        When The 'View Page History' is clicked
        Then The 'History for Study SoA Footnote' window is displayed with the following column list with values
            | Column | Header             |
            | 0      | Uid                |
            | 1      | #                  |
            | 2      | Footnote           |
            | 3      | SoA items covered  |
            | 4      | Activity groups    |
            | 5      | Activity subgroups |
            | 6      | Activities         |
            | 7      | Study epochs       |
            | 8      | Study visits       |
            | 9      | Activity schedules |
            | 10     | Modified           |
            | 11     | Modified by        |
            | 12     | Change type        |
            | 13     | User               |
            | 14     | From               |
            | 15     | To                 |
        And latest 10 rows of the history is displayed

    Scenario: User must be able to view history of changes for a selected Study Footnote
        Given The test Study Footnote exists
        When The 'History' option is clicked from the three dot menu list for a SoA Footnow row
        Then The 'History for Study SoA Footnote [uid]' window is displayed with the following column list with values
            | Column | Header             |
            | 1      | #                  |
            | 2      | Footnote           |
            | 3      | SoA items covered  |
            | 4      | Activity groups    |
            | 5      | Activity subgroups |
            | 6      | Activities         |
            | 7      | Study epochs       |
            | 8      | Study visits       |
            | 9      | Activity schedules |
            | 10     | Modified           |
            | 11     | Modified by        |
            | 12     | Change type        |
            | 13     | User               |
            | 14     | From               |
            | 15     | To                 |