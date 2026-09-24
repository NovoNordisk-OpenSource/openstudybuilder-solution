@REQ_ID:1070684
@REQ_ID:1070686
@neodash_tests
Feature: Syntax Template Dashboard - Parent Templates

    As a user, I want to be able to view and filter parent templates

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Syntax Template Dashboard' page is opened

    Scenario: User must be able to view parent templates
        Given The neoDash 'Parent Templates' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                                                 |
            | Parent Syntax Templates Using Selected Template Parameter and/or Value |
            | Selected Template Parameter and/or Value                               |

    Scenario: User must be able to view different parent templates
        Given The neoDash 'Parent Templates' tab is selected
        Then The Selected Template Parameter and/or Value table should display the following
            | Selected_Parameters | Selected_Values |
            |                     |                 |
        And The Parent Syntax Templates using selected Template Parameter and/or Value table should display the following
            | Library | Seq_Num | Type                          | SubType | Template            | TemplateParameter                          | struid                             |
            | Sponsor | AI1     | Activity Instruction Template |         | 1715136795533Second | CompoundDosing, Compound, ActivityInstance | ActivityInstructionTemplate_000001 |

    Scenario: User must be able to filter parent templates based on selected parameters and/or values
        Given The neoDash 'Select Template Parameter Value' tab is selected
        And The user selects 'ActivityInstance' from the 'TemplateParameter name' dropdown
        And The user switches to the 'Parent Templates' page
        Then The Selected Template Parameter and/or Value table should display the following
            | Selected_Parameters | Selected_Values |
            | ActivityInstance    |                 |
        And The Parent Syntax Templates using selected Template Parameter and/or Value table should display the following
            | Library | Seq_Num | Type                          | SubType | Template                                                      | TemplateParameter | struid                             |
            | Sponsor | AI1     | Activity Instruction Template |         | Test 0 [ActivityInstance] [CompoundDosing] [Compound] updated | ActivityInstance  | ActivityInstructionTemplate_000001 |