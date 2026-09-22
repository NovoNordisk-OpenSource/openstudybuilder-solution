@background_jobs
Feature: Administration - Background Jobs

    Background: User is logged in
        Given The user is logged in
        And The '/administration' page is opened

    Scenario: User can view background jobs and their statuses
        Given Background jobs API returns a completed, running and failed job
        When User opens the background jobs dialog
        Then The background jobs dialog is visible
        And The background jobs table has the expected columns
        And The background jobs table shows the job statuses

    Scenario: User can view background job details and log
        Given Background jobs API returns a completed job with details
        When User opens the background jobs dialog
        And User opens the background job details
        Then The background job details dialog is visible
        And The background job details show the response and log

    Scenario: User can refresh the background jobs list
        Given Background jobs API returns a completed job
        When User opens the background jobs dialog
        And User refreshes the background jobs list
        Then The background jobs list was requested more than once