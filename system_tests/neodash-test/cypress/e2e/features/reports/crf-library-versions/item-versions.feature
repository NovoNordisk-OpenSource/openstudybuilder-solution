@neodash_tests
Feature: CRF Library Versions - Item Versions

    As a user, I want to be able to explore Item Versions

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'CRF Library Versions' page is opened

    Scenario: User must be able to view Item Versions
        Given The neoDash 'CRF Collection' tab is selected
        And The user selects 'ODM version 1.3.2 with DoB' from the 'Select a from dropdown' dropdown
        And The user navigates to the 'Item Versions' page
        And The user selects 'Age' in the 'Item - Select Base' table
        And The user selects 'Diastolic blood pressure' in the 'Item - Select Compare' table
        Then The table 'Item Attributes differences - (v 0.1 → v 0.1)' displays the following items
            | column         | value          |
            | Item OID       | I.AGE          |
            | Area           | Identification |
            | Item attribute | comment        |
            | Base           |                |
            | Compare        |                |
            | Change Type    | Removed        |