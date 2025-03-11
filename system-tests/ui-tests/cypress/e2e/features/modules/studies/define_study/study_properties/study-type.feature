Feature: Studies - Study Type

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: User must be able to navigate to Study Type page using side menu
        Given A test study is selected
        And The '/studies' page is opened
        When The 'Study Properties' submenu is clicked in the 'Define Study' section
        Then The current URL is '/studies/Study_000001/study_properties/type'

    @REQ_ID:987736
    Scenario: User must be able to see the Study Type table with options listed in this scenario
        Given The '/studies/Study_000001/study_properties/type' page is opened
        Then A table is visible with following headers
            | headers                |
            | Study type information |
            | Selected values        |
            | Reason for missing     |
        And The following rows are available in first column
            | values                              |   
            | Study type                          |
            | Trial type                          |
            | Study phase classification          |
            | Extension study                     |
            | Adaptive design                     |
            | Study stop rules                    |
            | Confirmed response minimum duration |
            | Post authorization safety study ind |
        And A table is visible with following options
            | options              |
            | Copy from study      |
            | Edit content         |
            | Show version history |

    Scenario: Editing the study type
        Given The '/studies/Study_000001/study_properties/type' page is opened
        When The study type is fully defined
        Then The study type data is reflected in the table

    Scenario: User must be able to use NONE value for study stop rule
        Given The '/studies/Study_000001/study_properties/type' page is opened
        When The Study Stop Rule NONE option is selected
        Then The Study Stop Rule field is disabled

    Scenario: User must be able to use NA value for the Confirmed response minimum duration
        Given The '/studies/Study_000001/study_properties/type' page is opened
        When The Confirmed response minimum duration NA option is selected
        Then The Confirmed response minimum duration field is disabled
    @unstable_disabled
    Scenario: User must be able to copy the study type data from other existing study without overwriting the data
        Given The '/studies/Study_000001/study_properties/type' page is opened
        And Another study with study type defined exists
        When The study type is partially defined
        And The study type is copied from another study without overwriting
        Then Only the missing information is filled from another study in the study type form
    @unstable_disabled
    Scenario: User must be able to copy the study type data from other existing study with overwriting the data
        Given The '/studies/Study_000001/study_properties/type' page is opened
        And Another study with study type defined exists
        When The study type is fully defined
        And The study type is copied from another study with overwriting
        Then All the informations are overwritten in the study type

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/study_properties/type' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/study_properties/type' page is opened
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames