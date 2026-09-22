@neodash_tests
Feature: CRF Library Versions - CRF Release Notes

    As a user, I want to be able to explore CRF Release Notes

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'CRF Library Versions' page is opened

    Scenario: User must be able to view CRF Release Notes
        Given The neoDash 'CRF Collection' tab is selected
        And The user selects 'ODM version 1.3.2 with DoB' from the 'Select a from dropdown' dropdown
        And The user navigates to the 'CRF Versions' page
        And The user selects 'Adverse Event' in the 'CRF - Select Base' table
        And The user selects 'Informed Consent and Demography' in the 'CRF - Select Compare' table
        And The user navigates to the 'CRF Release Notes' page
        Then The table 'Release Notes( v 0.1 → v 0.1)' displays the following items
            | column        | value   |
            | CRF OID       | F.DM    |
            | Level         | Item    |
            | Group OID     | G.DM.DM |
            | Item OID      | I.AGE   |
            | Attribute     | comment |
            | Change Type   | Added   |
            | Base Value    | _null_  |
            | Compare Value |         |
