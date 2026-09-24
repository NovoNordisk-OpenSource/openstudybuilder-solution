@REQ_ID:1370753 @REQ_ID:1070674 @REQ_ID:1070680 @REQ_ID:1070676 @REQ_ID:1070679
Feature: CT Codelist rules

Rule: As a database user,
      I want the library to follow a set of rules that guarantee that the data is clear and consistent.

    @impact:business_rules
    Scenario: There are no codelists containing duplicated term names
        Given there are codelists containing multiple terms in the database
        Then the list of term names within each codelist contains no duplicates

    @impact:business_rules
    Scenario: There are no codelists containing duplicated term concept ids
        Given there are codelists containing multiple terms in the database
        Then the list of term concept ids within each codelist contains no duplicates

    @impact:business_rules
    Scenario: There are no codelists containing duplicated term submission values
        Given there are codelists containing multiple terms in the database
        Then the list of term submission values within each codelist contains no duplicates

    @impact:business_rules
    Scenario: Paried codelists for code and decode values have matching names.
        Given there are paired codelists in the database
        Then the two codelists have matching names

    @impact:business_rules
    Scenario: Paired codelists for code and decode values contain the same terms.
        Given there are paired codelists in the database
        Then the two codelists contain the same terms

    @impact:library_quality
    Scenario: Ordinal codelists have at least one term with a defined ordinal value
        Given there are ordinal codelists containing terms in the database
        Then each ordinal codelist has at least one term with a defined ordinal value
