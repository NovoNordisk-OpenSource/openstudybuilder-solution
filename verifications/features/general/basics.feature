@REQ_ID:1370753
Feature: Basic data model rules
    @impact:library_quality
    Scenario: Naming properties on nodes should not have leading or trailing spaces
        Given the database is reachable and has content
        Then naming properties on nodes should not have leading or trailing spaces

    @impact:library_quality
    Scenario: Definition properties on nodes should be properly formatted
        Given the database is reachable and has content
        Then definitions do not have leading or trailing spaces or line breaks

    @impact:library_quality
    Scenario: Definition properties on nodes should be clean
        Given the database is reachable and has content
        Then definitions do not contain any formatting control codes

    @impact:business_rules
    Scenario: All string properties on CTConfigValue nodes must be in snake_case
        Given the database is reachable and has CTConfigValue nodes
        Then all string properties on CTConfigValue nodes are in snake_case

    @impact:data_schema
    Scenario: There must be no orphan nodes apart from: Counter, UnitDefinitionCounter, Brand, Library, ClinicalProgramme, TemplateParameterValue, TemplateParameterTermValue
        Given the database is reachable and has content
        Then there are no orphan nodes

    @impact:data_schema
    Scenario: There must be no Root nodes without Value nodes connected to them, apart from: CTCodelistRoot, CTTermRoot
        Given the database is reachable and has content
        Then there are no root nodes lacking a relationship to a value node
