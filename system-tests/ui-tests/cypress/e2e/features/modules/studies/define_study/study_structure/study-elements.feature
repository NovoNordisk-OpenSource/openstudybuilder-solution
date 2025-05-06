@REQ_ID:1074254 @manual_test
Feature: Studies - Study Elements

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study elements.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: Navigation to Study Elements page
        Given The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Elements' tab is selected
        Then The current URL is 'studies/Study_000002/study_structure/elements'

    Scenario: User must be able to see the table, search bar, actions, reorder content and row selection options
        Given The '/studies/study_structure/elements' page is opened
        Then The table with search bar, actions, reorder content and select rows options is visible

    Scenario: User must be able to see the Study Elements table with proper options
        Given The '/studies/study_structure/elements' page is opened
        When The table actions button is clicked
        Then The filters, columns, export data, version history and Add Study Element buttons are visible
        And A table is visible with following headers
            | headers            |
            | Element type       |
            | Element sub type   |
            | Element name       |
            | Element short name |
            | Element start rule |
            | Element end rule   |
            | Colour             |
            | Description        |
            | Modified           |
            | Modified By        |

    Scenario: User must be able to use column selection option
        Given The '/studies/study_structure/elements' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    Scenario: User must be able to add a new Study Element
        Given The '/studies/study_structure/elements' page is opened
        When The new Study Element is added
        Then The new Study Element is visible in the table

    Scenario: User must be able to edit the Study Element
        Given The '/studies/study_structure/elements' page is opened
        And The test Study Element is available
        When The Study Element is edited
        Then The Study Element with updated values is visible within the table

    Scenario: User must not be able to create Study Element without Element Type provided
        Given The '/studies/study_structure/elements' page is opened
        When The user opens new Study Element form
        And The user populates the form without Element Type provided and saves
        Then The validation appears for that field
        And The form is not closed

    Scenario: User must not be able to create Study Element without Element Sub Type provided
        Given The '/studies/study_structure/elements' page is opened
        When The user opens new Study Element form
        And The user populates the form without Element Sub Type provided and saves
        Then The validation appears for that field
        And The form is not closed

    Scenario: User must not be able to create Study Element without Element Name provided
        Given The '/studies/study_structure/elements' page is opened
        When The user opens new Study Element form
        And The user populates the form without Element Name provided and saves
        Then The validation appears for that field
        And The form is not closed

    Scenario: User must not be able to create Study Element without Element Short Name provided
        Given The '/studies/study_structure/elements' page is opened
        When The user opens new Study Element form
        And The user populates the form without Element Short Name provided and saves
        Then The validation appears for that field
        And The form is not closed

    Scenario: User must not be able to create the Study Element with not unique name
        Given The '/studies/study_structure/elements' page is opened
        When The Study Element exists with particular name
        And The user populates New Study Element form using the same name and saves
        Then The message about non unqique value for Study Element Name appears

    Scenario: User must not be able to create the Study Element with not unique short name
        Given The '/studies/study_structure/elements' page is opened
        When The Study Element exists with particular name
        And The user populates New Study Element form using the same short name and saves
        Then The message about non unqique value for Study Element Short Name appears

    Scenario Outline: User must not be able to use text longer than specified
        Given The '/studies/study_structure/elements' page is opened
        When The Add or Edit Study Element button is clicked
        And For the '<field>' a text longer than '<length>' is provided
        And The save button is clicked
        And The message "Maximum text length of <fields> is reached" is displayed

        Examples:
            | field              | length |
            | Element name       | 200    |
            | Element short name | 20     |
            | Element code       | 20     |

    Scenario: User must be able to export the data in CSV format
        Given The '/studies/study_structure/elements' page is opened
        And The user exports the data in 'CSV' format
        Then The study specific 'StudyElements' file is downloaded in 'csv' format

    Scenario: User must be able to export the data in JSON format
        Given The '/studies/study_structure/elements' page is opened
        And The user exports the data in 'JSON' format
        Then The study specific 'StudyElements' file is downloaded in 'json' format

    Scenario: User must be able to export the data in XML format
        Given The '/studies/study_structure/elements' page is opened
        And The user exports the data in 'XML' format
        Then The study specific 'StudyElements' file is downloaded in 'xml' format

    Scenario: User must be able to export the data in EXCEL format
        Given The '/studies/study_structure/elements' page is opened
        And The user exports the data in 'EXCEL' format
        Then The study specific 'StudyElements' file is downloaded in 'xlsx' format

    Scenario: User must see the warning message when deleting Study Element
        Given The '/studies/study_structure/elements' page is opened
        And The test study element is available
        And The test study element is related to study design cell
        When The delete action is clicked for the 'To be removed' study element
        Then The warning message appears 'Removing this Study Element will remove all related Study Cells'

    Scenario: User must be able to remove the existing Study Element
        Given The '/studies/study_structure/elements' page is opened
        And The test Study Element is available
        When The delete action is clicked for the test Study Element
        Then The test Study Element is no longer available
        And Related study design cells are cascade deleted
