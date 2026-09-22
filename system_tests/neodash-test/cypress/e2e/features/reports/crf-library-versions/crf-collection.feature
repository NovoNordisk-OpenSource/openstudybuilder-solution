@neodash_tests
Feature: CRF Library Versions - CRF Collection

    As a user, I want to be able to explore CRF Collection

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'CRF Library Versions' page is opened

    Scenario: User must be able to compare CRF Collections
        Given The neoDash 'CRF Collection' tab is selected
        And The user selects 'ODM version 1.3.2 with DoB' from the 'Select a from dropdown' dropdown
        And The user selects 'ODM version 1.3.2 with DoB' in the 'Select Base Collection' table
        And The user selects 'ODM version 1.3.2 with DoB' in the 'Select Compare Collection' table
        And The user selects 'Informed Consent and Demography' from the 'select CRF' field
        And The user selects 'Informed Consent' from the 'select Group' field
        Then The table 'CRF Attributes differences - ODM version 1.3.2 with DoB' displays the following items
            | column        | value          |
            | CRF OID       | F.AE           |
            | Area          | Identification |
            | CRF attribute | name           |
            | Base          | Adverse Event  |
            | Compare       | Adverse Event  |
            | Change Type   | No Changes     |
        And The table 'Group Attributes differences - F.DM' displays the following items
            | column          | value            |
            | Group OID       | G.DM.DM          |
            | Area            | Identification   |
            | Group attribute | name             |
            | Base            | General Demography |
            | Compare         | General Demography |
            | Change Type     | No Changes       |
        And The table 'Item Attributes differences - G.DM.IC' displays the following items
            | column         | value          |
            | Item OID       | I.STUDYID      |
            | Area           | Identification |
            | Item attribute | name           |
            | Base           | Study ID       |
            | Compare        | Study ID       |
            | Change Type    | No Changes     |