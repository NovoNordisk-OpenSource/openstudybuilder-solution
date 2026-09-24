@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Search and Filtering

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study activities.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [Test data] User must be able to create test data
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And Activity, Group And Subgroup names are fetch to be used in SoA
        And Activity, Group And Subgroup created via API names are fetch to be used in Study Activities tests

    @smoke_test
    Scenario: [SoA][Table][Search][Positive case] User must be able to search study activity
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User search study activity
        Then Activity is found in table

    Scenario: [SoA][Table][Search][Case sensitivity] User must be able to search study activity ingnoring case sensitivity
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User search study activity in lowercase
        Then Activity is found in table

    Scenario: [SoA][Table][Search][Partial text] User must be able to search activity by only inputing 3 characters
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        When User search study activity by partial name
        Then Activity is found in table

    Scenario: [SoA][Table][Search][Negative] User must be able to search non-existing study activity
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        When User search for non-existing activity
        Then No activities are found

    Scenario: [SoA][Table][Search][By subgroup] User must be able to search activity by activity subgroup
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        When User search study activity by subgroup
        Then Activity is found in table

    Scenario: [SoA][Table][Search][By group] User must be able to search activity by activity group
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        When User search study activity by group
        Then Activity is found in table

    @smoke_test
    Scenario: [Activity List][Table][Search][Positive case] User must be able to search study activity
        Given The page 'activities/list' is opened for current study
        And User waits for the table
        Then The Study Activity is searched by name and is found

    Scenario: [Activity List][Table][Search][Case sensitivity] User must be able to search study activity ingnoring case sensitivity
        Given The page 'activities/list' is opened for current study
        And User waits for the table
        Then The Study Activity is searched by lowercased name
        And The Study Activity is available in the first row of the table

    Scenario: [Activity List][Table][Search][Partial text] User must be able to search activity by only inputing 3 characters
        Given The page 'activities/list' is opened for current study
        And User waits for the table
        Then The Study Activity is searched by partial name and is found

    Scenario: [Activity List][Table][Search][Negative] User must be able to search non-existing study activity
        Given The page 'activities/list' is opened for current study
        And User waits for the table
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: [Activity List][Table][Search][By subgroup] User must be able to search activity by activity subgroup
        Given The page 'activities/list' is opened for current study
        And User waits for the table
        Then The Study Activity is searched by subgroup and is found

    Scenario: [Activity List][Table][Search][By group] User must be able to search activity by activity group
        Given The page 'activities/list' is opened for current study
        And User waits for the table
        Then The Study Activity is searched by group and is found