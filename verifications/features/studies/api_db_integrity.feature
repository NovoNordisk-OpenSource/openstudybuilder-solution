@REQ_ID:1370753 @REQ_ID:1074254
@impact:data_schema
@impact:business_rules
Feature: API-defined database integrity
    Consolidated checks using Cypher from clinical-mdr-api ``db_integrity_checks.QUERIES``.

    Scenario: All non-deleted studies pass API integrity checks
        Given the database is reachable and has content
        Then all API database integrity checks pass for non-deleted studies
