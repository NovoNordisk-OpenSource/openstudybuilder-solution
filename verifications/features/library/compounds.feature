@REQ_ID:1370753 @REQ_ID:1070683
Feature: Library of Compounds, Medicinal and Pharmaceutical Products

    @impact:data_schema
    Scenario: Compound Alias must link to a Compound
        Given the library contains compound aliases
        Then each CompoundAliasValue node links to one CompoundRoot node

    @impact:data_schema
    Scenario: Medicinal Products must be represented by MedicinalProductRoot/Value nodes linked to CTTermContext, PharmaceuticalProductRoot, NumericValueWithUnitRoot nodes
        Given the library contains medicinal products
        Then each MedicinalProductValue node links to one MedicinalProductRoot node
        And each MedicinalProductValue node links to one CompoundRoot node
        And each MedicinalProductValue dose frequency CTTermContext node links to one CTTermRoot node
        And each MedicinalProductValue node links to one CTTermContext dispenser node
        And each MedicinalProductValue node links to one CTTermContext delivery device node
        And each MedicinalProductValue node links to one or more PharmaceuticalProductRoot nodes
        And each MedicinalProductValue node links to one or more NumericValueWithUnitRoot dose value nodes

    @impact:data_schema
    Scenario: Pharmaceutical Products must be represented by PharmaceuticalProductRoot/Value nodes linked to IngredientFormulation, CTTerms nodes
        Given the library contains pharmaceutical products
        Then each PharmaceuticalProductValue node links to one PharmaceuticalProductRoot node
        And each PharmaceuticalProductValue node links to one CTTermContext route of administration node
        And each PharmaceuticalProductValue node links to one CTTermContext dosage form node
        And each PharmaceuticalProductValue node links to one or more IngredientFormulation nodes

    @impact:data_schema
    Scenario: Pharmaceutical product ingredients must be linked to ActiveSubstanceRoot, LagTimeRoot, NumericValueWithUnitRoot nodes
        Given the library contains pharmaceutical product ingredients
        Then each Ingredient node links to one ActiveSubstanceRoot node
        Then each Ingredient node links to one LagTimeRoot node
        Then each Ingredient node links to one NumericValueWithUnitRoot strength node
        Then each Ingredient node links to one NumericValueWithUnitRoot half life node

    @impact:data_schema
    Scenario: Active Substances must be represented by ActiveSubstanceRoot/Value nodes potentially linked to one DictionaryTermRoot UNII node
        Given the library contains active substances
        Then each ActiveSubstanceValue node links to one ActiveSubstanceRoot node
        And each ActiveSubstanceValue node links to zero or one DictionaryTermRoot UNII node
