Feature: Basic requirements

    Background: User is logged in the system
        Given The user is logged in

    Scenario: User must be able to use UTF-8 charset within the UI
        Given A test study is selected
        And The '/studies/Study_000001/study_title' page is opened
        When The 'Edit study title' button is clicked
        And The study title form is filled with UTF-8 charset
        Then The UI is showing the UTF-8 charset correctly