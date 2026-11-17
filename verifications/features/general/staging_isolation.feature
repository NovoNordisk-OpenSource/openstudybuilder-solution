@REQ_ID:1370753
Feature: CDISC staging isolation
    @impact:data_schema
    Scenario: Every CDISC staging node must carry the CDISCStaging marker label
        Given the database is reachable and has content
        Then every node with a known staging label also has the CDISCStaging label

    @impact:data_schema
    Scenario: No node without a known staging label carries the CDISCStaging marker label
        Given the database is reachable and has content
        Then no node without a known staging label has the CDISCStaging label
