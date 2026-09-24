@REQ_ID:1070684
@REQ_ID:1070686
@neodash_tests
Feature: Syntax Template Dashboard - Study Usage

    As a user, I want to be able to view and filter study usage

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Syntax Template Dashboard' page is opened

    Scenario: User must be able to view study usage
        Given The neoDash 'Study Usage' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                   |
            | Template Instantiations by Study Usage   |
            | Selected Template Parameter and/or Value |

    Scenario: User must be able to view different study usage
        Given The neoDash 'Study Usage' tab is selected
        Then The Selected Template Parameter and/or Value table should display the following
            | Selected_Parameters | Selected_Values |
            |                     |                 |
        And The table 'Template Instantiations by Study Usage' displays the following items
            | column                 | value                                                                                                                                                                                    |
            | Library                | Sponsor                                                                                                                                                                         |
            | Seq Num                | CE1                                                                                                                                                                                      |
            | Type                   | Criteria                                                                                                                                                                                 |

    Scenario: User must be able to filter study usage based on selected parameters and/or values
        Given The neoDash 'Select Template Parameter Value' tab is selected
        And The user types 'Activity' in the Select Template Parameter selector
        And The user clicks 'ActivityInstance' in the Select Template Parameter selector
        And The user switches to the 'Study Usage' page
        Then The table 'Selected Template Parameter and/or Value' displays the following items
            | column              | value            |
            | Selected Parameters | ActivityInstance |
        And The table 'Template Instantiations by Study Usage' displays the following items
            | column                 | value                                   |
            | Library                | Sponsor                                 |
            | Seq Num                | E6                                      |
            | Type                   | Endpoint                                |
