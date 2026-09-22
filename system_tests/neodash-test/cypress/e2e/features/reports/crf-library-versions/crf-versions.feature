@neodash_tests
Feature: CRF Library Versions - CRF Versions

    As a user, I want to be able to explore CRF Versions

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'CRF Library Versions' page is opened

    Scenario: User must be able to view CRF Versions
        Given The neoDash 'CRF Collection' tab is selected
        And The user selects 'ODM version 1.3.2 with DoB' from the 'Select a from dropdown' dropdown
        And The user navigates to the 'CRF Versions' page
        And The user selects 'Adverse Event' in the 'CRF - Select Base' table
        And The user selects 'Informed Consent and Demography' in the 'CRF - Select Compare' table
        And The user selects 'G.DM.DM' from the 'Select Group' field
        Then The table 'CRF Attributes differences' displays the following items
            | column        | value          |
            | CRF OID       | F.AE           |
            | Area          | Identification |
            | CRF attribute | name           |
            | Base          | Adverse Event  |
            | Compare       |                |
            | Change Type   | Removed        |
        And The table 'Group Attributes differences' displays the following items
            | column          | value          |
            | Group OID       | G.DM.DM        |
            | Area            | Identification |
            | Group attribute | comment        |
            | Base            |                |
            | Compare         |                |
            | Change Type     | Added          |
        And The table 'Item Attributes differences - G.DM.DM' displays the following items
            | column         | value          |
            | Item OID       | I.AGE          |
            | Area           | Identification |
            | Item attribute | comment        |
            | Base           |                |
            | Compare        |                |
            | Change Type    | Added          |