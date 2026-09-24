@REQ_ID:1070684

Feature: Library - Syntax Templates - Filtering
    As a user I want to navigate to each page

    Background: User must be logged in
        Given The user is logged in

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/objective_templates' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                   |
        | Indication or disorder |
        | Objective category     |
        | Confirmatory testing   |
    
    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/endpoint_templates' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
            | name                   |
            | Indication or disorder |
            | Endpoint category      |
            | Endpoint sub-category  |    
        
    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/timeframe_templates/parent' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name            |
        | Sequence number |
        | Template        |
        | Status          |
        | Version         |

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/criteria_templates/Dosing/parent' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                   |
        | Indication or disorder |
        | Criterion category     |
        | Criterion sub-category |

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/criteria_templates/Exclusion/parent' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                   |
        | Indication or disorder |
        | Criterion category     |
        | Criterion sub-category |

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/criteria_templates/Inclusion/parent' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                   |
        | Indication or disorder |
        | Criterion category     |
        | Criterion sub-category |

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/criteria_templates/Randomisation/parent' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                   |
        | Indication or disorder |
        | Criterion category     |
        | Criterion sub-category |

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/criteria_templates/Run-in/parent' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                   |
        | Indication or disorder |
        | Criterion category     |
        | Criterion sub-category |

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/criteria_templates/Withdrawal/parent' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name                   |
        | Indication or disorder |
        | Criterion category     |
        | Criterion sub-category |

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
            | name                   |
            | Indication or disorder |
            | Activity group         |
            | Activity subgroup      |