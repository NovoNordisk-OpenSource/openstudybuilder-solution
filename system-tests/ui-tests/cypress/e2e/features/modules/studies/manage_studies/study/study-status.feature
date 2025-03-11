@REQ_ID:1741028
Feature: Studies - Study Status

    Background: User must be logged in
        Given The user is logged in

    Scenario:  User must be able to navigate to the Study Status page
        Given A test study is selected
        Given The '/studies' page is opened
        When The 'Study' submenu is clicked in the 'Manage Study' section
        And The 'Study Status' tab is selected
        Then The current URL is '/studies/Study_000001/study_status/study_status'

    Scenario: User must be able to see the Study Status page table with correct columns
        Given A test study is selected
        Given The '/studies/Study_000001/study_status/study_status' page is opened
        Then A table is visible with following headers
            | headers             |
            | Study status        |
            | Version             |
            | Release description |
            | Modified            |
            | Modified by         |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/study_status/study_status' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @pending_implementation
    Scenario: User must not be able to Lock a Study when study number is not defined
        Given A study in draft status without study number is selected
        And The '/studies/Study_000001/study_status/study_status' page is opened
        When The study is locked with description provided
        Then The pop up displays 'Cannot lock study without study_number nor study_title'
        And The form is not closed

    @pending_implementation
    Scenario: User must not be able to Lock a Study when study title is not defined
        Given A study in draft status without title is selected
        And The '/studies/Study_000001/study_status/study_status' page is opened
        When The study is locked with description provided
        Then The pop up displays 'Cannot lock study without study_number nor study_title'
        And The form is not closed

    @pending_implementation
    Scenario: User must not be able to Lock a Study when the study is a subpart study
        Given A study in draft status defined as a study subpart
        When The '/studies/Study_000001/study_status/study_status' page is opened
        Then The action button to lock the study is disabled

    @pending_implementation
    Scenario: User must be able to Release a Study
        Given A study in draft status with defined study number and study title is selected
        Given The '/studies/Study_000001/study_status/study_status' page is opened
        When The study is released with description provided
        Then The pop up displays 'Study snapshot has been released'
        And A row for the Released Study Status is displayed with a current time stamp and Release description and version incremented by 0.1
        And A the first row is showing Draft without Version and description, with the current timestamp

    @pending_implementation
    Scenario: User must be able to Lock a normal Study
        Given A study in draft status with defined study number and study title is selected
        And study is not defined as a main or subpart study
        And The '/studies/Study_000001/study_status/study_status' page is opened
        When The study is locked with description provided
        Then The pop up displays 'Study has been locked and new  version created'
        And A row for the Locked Study Status is displayed with a current time stamp and Lock description and version rounded up to full number
        And A row for the Released Study Status is displayed with a current time stamp and Lock description and version rounded up to full number

    @pending_implementation
    Scenario: User must be able to Lock a main Study with subparts
        Given A study in draft status with defined study number and study title is selected
        And study is defined as a main study with subparts
        And The '/studies/Study_000001/study_status/study_status' page is opened
        When The study is locked with description provided
        Then TThe pop up displays 'Study has been locked and new  version created'
        And A row for the Locked Study Status is displayed with a current time stamp and Lock description and version rounded up to full number including all subpart studies
        And A row for the Released Study Status is displayed with a current time stamp and Lock description and version rounded up to full number including all subpart studies

    @pending_implementation
    Scenario: User must be able to Unlock a normal Study
        Given A study in locked status with defined study number and study title is selected
        And study is not defined subpart study
        And The '/studies/Study_000001/study_status/study_status' page is opened
        When The study is unlocked
        Then The pop up displays 'Study has been unlocked and new draft version created'
        And A the first row is showing Draft without Version and description, with the current timestamp

    @pending_implementation
    Scenario: User must be able to Unlock a main Study with subparts
        Given A study in locked status with defined study number and study title is selected
        And study is defined as a main study with subparts
        And The '/studies/Study_000001/study_status/study_status' page is opened
        When The study is unlocked
        Then The pop up displays 'Study has been unlocked and new draft version created'
        And A the first row is showing Draft without Version and description, with the current timestamp including all subpart studies

    @pending_implementation
    Scenario: User must not be able to Unlock a subpart Study
        Given A study in locked status with defined study number and study title is selected
        And study is defined subpart study
        When The '/studies/Study_000001/study_status/study_status' page is opened
        Then The action button to unlock the study is disabled