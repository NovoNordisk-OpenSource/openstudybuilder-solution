@neodash_tests
Feature: CRF Library Versions - Collection Release Notes

    As a user, I want to be able to explore Collection Release Notes

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'CRF Library Versions' page is opened

    Scenario: User must be able to view Collection Release Notes
        Given The neoDash 'CRF Collection' tab is selected
        And The user selects 'ODM version 1.3.2 with DoB' from the 'Select a from dropdown' dropdown
        And The user selects 'ODM version 1.3.2 with DoB' in the 'Select Base Collection' table
        And The user selects 'ODM version 1.3.2 with DoB' in the 'Select Compare Collection' table
        And The user navigates to the 'Collection Release Notes' page
        And The user selects 'Informed Consent and Demography' from the 'CRF in Collection' field
        And The user selects 'No Changes' from the 'Type of Change' field
        Then The table 'ODM version 1.3.2 with DoB - Release Notes( v 0.1 → v 0.1)' displays the following items
            | column        | value      |
            | CRF OID       | F.DM       |
            | Level         | CRF        |
            | Group OID     |            |
            | Item OID      |            |
            | Attribute     | status     |
            | Change Type   | No Changes |
            | Base Value    | No changes |
            | Compare Value | No changes |
