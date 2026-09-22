@REQ_ID:3015483

Feature: Studies - View Listings - Analysis Study Metadata (New)

    # This feature covers automated test implementation of functionality hat has previously 
    # been manually tested. The functionality is currently on an experiment status 
    # in StudyBuilder. It is preliminary work to get ready for supporting Statisticians and 
    # Clinical Data Scientists. 

    Background: User must be logged in
        Given The user is logged in

@manual_test
    Scenario:  User must be able to navigate to the Study MDVISIT page
        And User selects study with id 'CDISC DEV-9876'
        Given The '/studies' page is opened
        When The 'Analysis Study Metadata (New)' submenu is clicked in the 'View Listings' section
        Then The current URL is '/analysis_study_metadata_new/mdvisit'

@manual_test
    Scenario: User must be able to select Column labels
        Given The page 'analysis_study_metadata_new/mdvisit' is opened for current study
        And The user selects 'Column labels' option
        Then A table is visible with following headers
            | headers                                    |
            | Study Identifier                           | 
            | Analysis Visit (N)                         |
            | Analysis Visit                             |  
            | Visit Label                                |
            | Visit Type code                            |  
            | Analysis Visit 1 (N) Planned Day           | 
            | Analysis Visit 1 Planned Day               | 
            | Analysis Visit 2 (N) Planned Week          |
            | Analysis Visit 2 Planned Week              |  


@manual_test
    Scenario: User must be able to select Column name
        Given The page 'analysis_study_metadata_new/mdvisit' is opened for current study
        And The user selects 'Column names' option
        Then A table is visible with following headers
            | headers   |
            | STUDYID   |
            | AVISITN   |
            | AVISIT    |
            | VISLABEL  |
            | VISTPCD   |
            | AVISIT1N  |      
            | AVISIT1   |
            | AVISIT2N  |
            | AVISIT2   |


@manual_test
    Scenario: Scenario: Verify that the number of studies displayed on the MDVISIT page matches the study visits listed on the Study Structure page.
        Given The page 'analysis_study_metadata_new/mdvisit' is opened for current study
        When Check the number of studies displayed on the MDVISIT page
        And Check the number of study visits listed on the Study Structure page
        Then The number of studies displayed on the MDVISIT page matches the study visits listed on the Study Structure page

@manual_test
    Scenario: It must be possible to use the free text search field to narrow down the rows shown on the screen
        Given The page 'analysis_study_metadata_new/mdvisit' is opened for current study
        When The user inputs the test text in the free text search field
        Then The corresponding results should be displayed in the table

@manual_test
    Scenario: It must be possible to add filters for each column and sort the table based on the columns
        Given The page 'analysis_study_metadata_new/mdvisit' is opened for current study
        When The user applies a filter to the specified column
        And The user sorts the table by the specified column in ascending order
        Then the table should display only the rows that match the filter criteria
        And the rows in the table should be sorted according to the specified column in ascending order
        When the user sorts the table by the same column in descending order
        Then the rows in the table should be sorted according to the specified column in descending order

@manual_test
    Scenario: It must be possible to export the table to CSV, JSON, XML and Excel
        Given The page 'analysis_study_metadata_new/mdvisit' is opened for current study
        When The user clicks on the Export button
        Then CSV, JSON, XML, and Excel options must be available
        Then The corresponding file in the selected format should be downloaded to the local machine


