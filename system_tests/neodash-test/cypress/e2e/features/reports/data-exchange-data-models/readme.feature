@REQ_ID:NEW
@neodash_tests
Feature: Data Exchange Data Models - ReadMe

    As a user, I want to be able to explore Data Exchange Data Models

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Data Exchange Data Models' page is opened

    Scenario: User must be able to read a small guide of the Data Exchange Data Models
        Given The neoDash 'ReadMe' tab is selected
        Then The following set of neoDash reports are displayed
            | no | report |
            | 0  | Guide  |

