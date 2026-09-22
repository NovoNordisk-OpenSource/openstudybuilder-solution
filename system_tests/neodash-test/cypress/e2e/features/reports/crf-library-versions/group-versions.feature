@neodash_tests
Feature: CRF Library Versions - Group Versions

    As a user, I want to be able to explore Group Versions

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'CRF Library Versions' page is opened

    Scenario: User must be able to view Group Versions
        Given The neoDash 'CRF Collection' tab is selected
        And The user selects 'ODM version 1.3.2 with DoB' from the 'Select a from dropdown' dropdown
        And The user navigates to the 'Group Versions' page
        And The user selects 'General Demography' in the 'Group - Select Base' table
        And The user selects 'Informed Consent' in the 'Group - Select Compare' table
        Then The table 'Group Attributes differences' displays the following items
            | column          | value          |
            | Group OID       | G.DM.DM        |
            | Area            | Identification |
            | Group attribute | comment        |
            | Base            |                |
            | Compare         |                |
            | Change Type     | Removed        |
