@REQ_ID:1370753
Feature: Database indexing
    @impact:performance
    Scenario: All nodes must be included in at least one index
        Given the database is reachable and has content
        Then all nodes are included in at least one index

    @impact:performance
    Scenario: All node labels with a 'uid' property must have an index on the 'uid' property
        Given the database is reachable and has content
        Then node labels with 'uid' property have an index on 'uid' property

    @impact:business_rules
    Scenario: All Root nodes except CTCodelistAttributesRoot, CTCodelistNameRoot, CTTermAttributesRoot must have a UNIQUE index on the 'uid' property
        Given the database is reachable and has content
        Then all root nodes have NODE_KEY constraint on 'uid' property