@REQ_ID:1370753 @REQ_ID:1070674 @REQ_ID:1070680 @REQ_ID:1070676 @REQ_ID:1070679
Feature: CT Term dates

Rule: As a database user,
      I want the database model to support persistent representation of versioned controlled terminology terms,
      So that I can query the database and get the term data for any specific version as well as the latest draft, final or retired version.

    @impact:business_rules
    Scenario: Codelists linking to several versions of a term must do it in chronologic order without overlaps or gaps
        Given there are codelists with obsolete terms
        And there are codelists with current terms
        Then the codelists link to the terms in chronologic order

    @impact:business_rules
    Scenario: Codelists must only link to terms that are active 
        Given there are codelists with obsolete terms
        And there are codelists with current terms
        Then codelists only link to terms that are active

    @impact:business_rules
    Scenario: All obsolete terms must have an end date after their start date
        Given there are codelists with obsolete terms
        And there are codelists with current terms
        Then no obsolete term has a negative duration
