@REQ_ID:1898007
Feature: Studies - Study Operational SoA

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of the Study Operational SoA.

    # Note, data collection specification is not impemented yet, so currently only the study activity instance and operational SoA is supported.
    # See also file: study-activity-instance.feature

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: User must be able to navigate to Operational SoA page using side menu
        Given The '/studies' page is opened
        When The 'Data Specifications' submenu is clicked in the 'Define Study' section
        When The 'Operational SoA' tab is selected
        Then The current URL is '/studies/Study_000001/data_specifications/operational'

    Scenario: User must be able to see the Operational SoA matrix table with options listed in this scenario
        Given The '/studies/Study_000004/data_specifications/operational' page is opened
        Then expand table and Show SoA groups is available on the page
        And A table is visible with following headers
            | headers             |
            | Activities          |
            | Epoch               |
            | Visit               |
            | Study week          |
            | Window              |
            | Topic Code          |
            | ADaM Param Code     |


    @pending_implementation
    Scenario: User must be able to view the study activity instances in the Operational SoA table matrix including SoA groups
        Given The '/studies/Study_000001/data_specifications/operational' page is opened
        When The test study activity instances is selected for the study
        And the option to 'Show SoA groups' is enabled
        Then The Operational SoA table matrix display rows for each test study activity instance grouped by activity, activity group, activity subgroup and SoA group

    @pending_implementation
    Scenario: User must be able to view the study activity instance in the Operational SoA table matrix without SoA groups
        Given The '/studies/Study_000001/data-specification/detailed-detailed-operational-soa' page is opened
        When The test study activity instances is selected for the study
        And the option to 'Show SoA groups' is disabled
        Then The Operational SoA table matrix display rows for each test study activity instance grouped by activity, activity group and activity subgroup

    @pending_implementation
    Scenario: User must be able to view the study activity instance attributes in the Operational SoA table matrix
        Given The '/studies/Study_000001/data-specification/detailed-detailed-operational-soa' page is opened
        When The test study activity instances is selected for the study
        And the option to 'Show Activity instance attributes' is enabled
        Then The Operational SoA table matrix display rows for each test study activity instance including the attributes: topic code, ADaM Param Code

    @pending_implementation
    Scenario: User must be able to view details of a specific study activity instance in the Operational SoA table matrix
        Given The '/studies/Study_000001/data-specification/detailed-detailed-operational-soa' page is opened
        When The test study activity instances is selected for the study
        And the hyperlink for a study activity instances is selected
        Then a new tab opens with the library details overview of the selected activity instance