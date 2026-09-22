@REQ_ID:1070684
@REQ_ID:1070686
@neodash_tests
Feature: Syntax Template Dashboard - Template Instantiations

    As a user, I want to be able to view and filter template instantiations

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Syntax Template Dashboard' page is opened

    Scenario: User must be able to view template instantiations
        Given The neoDash 'Template Instantiations' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                                                 |
            | Template Instantiations Using Selected Template Parameter and/or Value |
            | Selected Template Parameter and/or Value                               |

    Scenario: User must be able to view different template instantiations
        Given The neoDash 'Template Instantiations' tab is selected
        Then The table 'Template Instantiations Using Selected Template Parameter and/or Value' displays the following items
            | column  | value             |
            | Library | Sponsor           |
            | Seq Num | CE1               |
            | Type    | Criteria Template |

    Scenario: User must be able to filter template instantiations based on selected parameters and/or values
        Given The neoDash 'Select Template Parameter Value' tab is selected
        And The user types 'Activity' in the Select Template Parameter selector
        And The user clicks 'ActivityInstance' in the Select Template Parameter selector
        And The user switches to the 'Template Instantiations' page
        Then The table 'Selected Template Parameter and/or Value' displays the following items
            | column              | value            |
            | Selected Parameters | ActivityInstance |
        And The table 'Template Instantiations Using Selected Template Parameter and/or Value' displays the following items
            | column  | value             |
            | Library | Sponsor           |
            | Seq Num | E1                |
            | Type    | Endpoint Template |