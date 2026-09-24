@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Visits

    See shared notes for study visits in file study-visit-intro-notes.txt

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study visits.

    Background: User is logged in and study has been selected
        Given The user is logged in

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to Study Visit page using side menu
        Given User selects study with id 'CDISC DEV-9876'
        And The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Visits' tab is selected
        Then The current URL is '/study_structure/visits'

    Scenario: [Table][Options] User must be able to see the Study Visit table with following options
        Given User selects study with id 'CDISC DEV-9876'
        When The page 'study_structure/visits' is opened for current study
        Then A table is visible with following options
            | options                                            |
            | add-visit                                          |
            | edit-study-visits                                  |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the Study Visit table with following columns
        Given User selects study with id 'CDISC DEV-9876'
        When The page 'study_structure/visits' is opened for current study
        And A table is visible with following headers
            | headers                     |
            | Epoch                       |
            | Visit type                  |
            | SoA Milestone               |
            | Visit Class                 |
            | Visit Subclass              |
            | Repeating frequency         |
            | Visit name                  |
            | Anchor visit in visit group |
            | Visit group                 |
            | Global anchor visit         |
            | Contact mode                |
            | Time reference              |
            | Timing                      |
            | Visit number                |
            | Unique visit number         |
            | Visit short name            |
            | Study duration days         |
            | Study duration weeks        |
            | Visit window                |
            | Collapsible visit group     |
            | Show visit                  |
            | Visit description           |
            | Epoch Allocation Rule       |
            | Visit start rule            |
            | Visit end rule              |
            | Study day                   |
            | Study week                  |
            | Week in Study               |
            | Modified                    |
            | Modified by                 |

    Scenario: [Online help] User must be able to read online help for the page
        Given User selects study with id 'CDISC DEV-9876'
        When The page 'study_structure/visits' is opened for current study
        And The online help button is clicked
        Then The online help panel shows 'Study Visits' panel with content "A clinical encounter where the the subject interacts with the investigator. There can be one more visits in an Epoch. To edit visit(s) in the table view click on the pencil in the top-right menu."

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given User selects study with id 'CDISC DEV-9876'
        When The page 'study_structure/visits' is opened for current study
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        When User selects study with id 'CDISC DEV-9876'
        Given The page 'study_structure/visits' is opened for current study
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyVisits' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        When User selects study with id 'CDISC DEV-9876'
        Given The page 'study_structure/visits' is opened for current study
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyVisits' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        When User selects study with id 'CDISC DEV-9876'
        Given The page 'study_structure/visits' is opened for current study
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyVisits' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        When User selects study with id 'CDISC DEV-9876'
        Given The page 'study_structure/visits' is opened for current study
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'StudyVisits' file is downloaded in 'xlsx' format
