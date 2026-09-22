@REQ_ID:1070684 @smoke_test

Feature: Library - Syntax Templates - Navigation
    As a user I want to navigate to each page

    Background: User must be logged in
        Given The user is logged in
        Then The '/library' page is opened

    Scenario: [Navigation] User must be able to navigate to the Activty Instruction under the Syntax template Library
        When The 'Activity Instructions' submenu is clicked in the 'Syntax Templates' section
        And The 'Parent' tab is selected
        Then The current URL is '/library/activity_instruction_templates/parent'
        And The 'Pre-instance' tab is selected
        Then The current URL is '/library/activity_instruction_templates/pre-instances'
        And The 'User Defined' tab is selected
        Then The current URL is '/library/activity_instruction_templates/user'

    Scenario: [Navigation] User must be able to navigate to the Criteria under the Syntax template Library
        Given The 'Criteria' submenu is clicked in the 'Syntax Templates' section
        When The 'Dosing' tab is selected
        Then The current URL is 'library/criteria_templates/Dosing/parent'
        When The 'Exclusion' tab is selected
        Then The current URL is 'library/criteria_templates/Exclusion/parent'
        And The 'Inclusion' tab is selected
        Then The current URL is 'library/criteria_templates/Inclusion/parent'
        And The 'Randomisation' tab is selected
        Then The current URL is 'library/criteria_templates/Randomisation/parent'
        And The 'Run-in' tab is selected
        Then The current URL is 'library/criteria_templates/Run-in/parent'
        And The 'Withdrawal' tab is selected
        Then The current URL is 'library/criteria_templates/Withdrawal/parent'

    Scenario: [Navigation] User must be able to navigate to the Endpoint under the Syntax template Library
        When The 'Endpoints' submenu is clicked in the 'Syntax Templates' section
        And The 'Parent' tab is selected
        Then The current URL is '/library/endpoint_templates/parent'
        And The 'Pre-instance' tab is selected
        Then The current URL is '/library/endpoint_templates/pre-instances'
        And The 'User Defined' tab is selected
        Then The current URL is '/library/endpoint_templates/user'

    Scenario: [Navigation] User must be able to navigate to the Objective under the Syntax template Library
        When The 'Objectives' submenu is clicked in the 'Syntax Templates' section
        And The 'Parent' tab is selected
        Then The current URL is '/library/objective_templates/parent'
        And The 'Pre-instance' tab is selected
        Then The current URL is '/library/objective_templates/pre-instances'
        And The 'User Defined' tab is selected
        Then The current URL is '/library/objective_templates/user'

    Scenario: [Navigation] User must be able to navigate to the Timeframe under the Syntax template Library
        Given The 'Time Frames' submenu is clicked in the 'Syntax Templates' section
        And The 'Parent' tab is selected
        Then The current URL is '/library/timeframe_templates/parent'
        And The 'User Defined' tab is selected
        Then The current URL is '/library/timeframe_templates/user'