@REQ_ID:1070684
@REQ_ID:1070686
@neodash_tests
Feature: Syntax Template Dashboard - All Templates

    As a user, I want to be able to view and filter all templates

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Syntax Template Dashboard' page is opened

    Scenario: User must be able to view all templates
        Given The neoDash 'All Templates' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                                       |
            | All Templates Using Selected Template Parameter and/or Value |
            | Selected Template Parameter and/or Value                     |

    Scenario: User must be able to view different all templates
        Given The neoDash 'All Templates' tab is selected
        Then The Selected Template Parameter and/or Value table should display the following
            | Selected_Parameters | Selected_Values |
            |                     |                 |
        And The All Templates using selected Template Parameter and/or Value table should display the following
            | Library | SeqNum | Type                          | Template                                                      | TemplateParameter                          | ParameterValues | TemplateType    |
            | Sponsor | AI1    | Activity Instruction Template | Test 0 [ActivityInstance] [CompoundDosing] [Compound] updated | ActivityInstance, Compound, CompoundDosing |                 | Syntax Template |

    Scenario: User must be able to filter all templates based on selected parameters and/or values
        Given The neoDash 'Select Template Parameter Value' tab is selected
        And The user selects 'Activity' from the 'TemplateParameter name' dropdown
        And The user selects 'Renin Activity' from the 'templateparametertermvalue_name' dropdown
        And The user switches to the 'All Templates' page
        Then The Selected Template Parameter and/or Value table should display the following
            | Selected_Parameters | Selected_Values |
            | Activity            | Renin Activity  |
        And The All Templates using selected Template Parameter and/or Value table should display the following
            | Library | SeqNum | Type              | SubType | Template           | TemplateParameter | ParameterValues | TemplateType    |
            | Sponsor | CI3    | Criteria Template |         | must be [Activity] | Activity          |                 | Syntax Template |