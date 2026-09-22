@REQ_ID:xxx
Feature: Basic requirements

    Background: User is logged in the system
        Given The user is logged in

    Scenario: User must be able to use UTF-8 charset within the UI
        Given User selects study with id 'CDISC DEV-9876'
        And The page 'study_title' is opened for current study
        When The 'Edit study title' button is clicked
        And The study title form is filled with UTF-8 charset
        And Action is confirmed by clicking save
        Then The UI is showing the UTF-8 charset correctly