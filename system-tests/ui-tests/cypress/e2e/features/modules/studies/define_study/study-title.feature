@REQ_ID:1074250
Feature: Studies - Study Title Management

    As a User I want to have ability to define title of my study.

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And A test study is selected

    Scenario:  User must be able to navigate to the Study Title page
        Given The '/studies' page is opened
        When The 'Study Title' submenu is clicked in the 'Define Study' section
        Then The current URL is '/studies/Study_000001/study_title'

    Scenario: User must be able to add a new Study Title
        Given The '/studies/Study_000001/study_title' page is opened
        And A test study is selected
        When The 'Edit study title' button is clicked
        And The study title form is filled with new title and saved
        Then The study selected has new title appended

    Scenario: User must be able to copy the Study Title from currently existing study
        Given The '/studies/Study_000001/study_title' page is opened
        And A test study is selected
        When The 'Edit study title' button is clicked
        And The study title is copied from another study
        Then The study selected has new title copied