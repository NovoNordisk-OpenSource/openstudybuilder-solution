@REQ_ID:1370753 @REQ_ID:1070674 @REQ_ID:1070680 @REQ_ID:1070676 @REQ_ID:1070679
Feature: Versioning in the library

Rule: As a database user,
      I want the database model to support persistent representation of versioned library items,
      So that I can query the database and get the library item data for any specific version as well as the latest draft, final or retired version.

    @impact:data_schema
    Scenario: The relationships LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED must have no properties
        Given there are versioned library items
        When a root-value pair has a LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED relationship
        Then the LATEST_nnn relationship has no properties

    @impact:data_schema
    Scenario: The relationships LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED must have a matching HAS_VERSION
        Given there are versioned library items
        When a root-value pair has a LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED relationship
        Then there is a matching HAS_VERSION for every LATEST_nnn relationship

    @impact:data_schema
    Scenario: Only the latest HAS_VERSION relationship must lack an end date
        Given there are versioned library items
        Then only the latest HAS_VERSION relationship for a root-value pair lacks an end date

    @impact:data_schema
    Scenario: All HAS_VERSION relationships must have a start date
        Given there are versioned library items
        Then no HAS_VERSION relationship lacks a start date

    @impact:data_schema
    Scenario: All HAS_VERSION relationships must have a positive duration
        Given there are versioned library items
        Then no HAS_VERSION relationship has a negative duration

    @impact:business_rules
    Scenario: All HAS_VERSION relationship from a node must be in chronologic order
        Given there are versioned library items
        Then all HAS_VERSION relationship from a node are in chronologic order

    @impact:data_schema
    Scenario: A root must have no more than one each of LATEST, LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED
        Given there are versioned library items
        Then the root node has no more than one each of LATEST_nnn relationships

    @impact:business_rules
    Scenario: A root must have no duplicated HAS_VERSION relationships by date
        Given there are versioned library items
        Then there are no duplicated HAS_VALUE relationships by date

    @impact:business_rules
    Scenario: A root must have no duplicated HAS_VERSION relationships by version number
        Given there are versioned library items
        Then there are no duplicated HAS_VALUE relationships by version number

    @impact:data_schema
    Scenario Outline: Every LATEST_nnn relationship must point to the latest version of corresponding state
        Given there are versioned library items
        When a root-value pair has a LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED relationship
        Then every <relationship> relationship points to the latest value in state <status>

        Examples:
        | relationship   | status  |
        | LATEST         | Any     |
        | LATEST_FINAL   | Final   |
        | LATEST_DRAFT   | Draft   |
        | LATEST_RETIRED | Retired |

    @impact:data_schema
    Scenario Outline: The latest version of each status must have a corresponding LATEST_nnn relationship
        Given there are versioned library items
        Then the latest HAS_VERSION relationship with status <status> has a corresponding <relationship> relationship

        Examples:
        | relationship   | status  |
        | LATEST_FINAL   | Final   |
        | LATEST_DRAFT   | Draft   |
        | LATEST_RETIRED | Retired |

    @impact:data_schema
    Scenario: Retiring a library item is done by adding a HAS_VERSION relationship with status Retired to the exiting value node
        Given the database is reachable and has content
        Then each Retired HAS_VERSION relationship has a corresponsding Final
