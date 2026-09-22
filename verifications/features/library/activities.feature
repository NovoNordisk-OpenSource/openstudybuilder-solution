@REQ_ID:1370753 @REQ_ID:1070683
Feature: Activity model
    @impact:data_schema
    Scenario: All valid combinations of group and subgroup must be represented by ActivityValidGroup nodes
        Given the library contains activities
        Then ActivityValidGroup nodes link to both a group and a subgroup

    @impact:data_schema
    Scenario: All valid choices of group/subgroup combinations for an activity must be represented by ActivityGrouping nodes
        Given the library contains activities
        Then ActivityGrouping nodes link to both an activity and a group/subgroup pair

    @impact:business_rules
    Scenario: An activity instance must only belong to a single activity
        Given the library contains activities
        Then each activity instances link to a single activity

    @impact:business_rules
    Scenario: An activity without data collection must have no activity instances
        Given the library contains activities
        Then activities without data collection have no instances
        And no instances are linked to activities without data collection

    @impact:business_rules
    Scenario: A requested activity must have no activity instances
        Given the library contains activities
        Then requested activities have no instances
        And no instances are linked to requested activities

    @impact:data_schema
    Scenario: HAS_VALID_CODELIST_FOR_ITEMS relationship has consistent graph structure
        Given the library contains activities
        Then HAS_VALID_CODELIST_FOR_ITEMS relationships are only from ActivityItemClassRoot to CTCodelistRoot and are irreflexive with at most one relationship per pair