@REQ_ID:1070684
@REQ_ID:1070686
@neodash_tests
Feature: Syntax Template Dashboard - Select Template Parameter Value

    As a user, I want to be able to view and filter different template parameters and values

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Syntax Template Dashboard' page is opened

    Scenario: User must be able to view different parameter values in Select Template Parameter Values
        Given The neoDash 'Select Template Parameter Value' tab is selected
        Then The following set of neoDash reports are displayed
            | report                    |
            | Template Parameters       |
            | Select Template Parameter |
            | Template Parameter Values |
            | Select Parameter Value    |

    Scenario: User must be able to select and view different parameters
        Given The neoDash 'Select Template Parameter Value' tab is selected
        When The user types 'Disease' in the Select Template Parameter selector
        And The user clicks 'DiseaseDisorder' in the Select Template Parameter selector
        Then The table 'Template Parameters' displays the following items
            | column             | value           |
            | Template Parameter | DiseaseDisorder |
        And The table 'Template Parameter Values' displays the following items
            | column             | value                           |
            | Parameter          | DiseaseDisorder                 |
            | Name               | Adult growth hormone deficiency |
            | Sentence Case Name | adult growth hormone deficiency |
    Scenario: User must be able to select and view different parameter values
        Given The neoDash 'Select Template Parameter Value' tab is selected
        When The user types 'Adult' in the Select Parameter Value selector
        And The user clicks 'Adult growth hormone deficiency' in the Select Parameter Value selector
        Then The table 'Template Parameters' displays the following items
            | column              | value           |
            | Template Parameter | DiseaseDisorder |
        And The table 'Template Parameter Values' displays the following items
            | column             | value                           |
            | Parameter          | DiseaseDisorder                 |
            | Name               | Adult growth hormone deficiency |
            | Sentence Case Name | adult growth hormone deficiency |