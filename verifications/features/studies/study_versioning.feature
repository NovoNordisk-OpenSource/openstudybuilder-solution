@REQ_ID:1370753 @REQ_ID:1741028
Feature: Versioning of studies

Rule: As a database user,
      I want the database model to support persistent representation of released and locked studies,
      So that I can query the database and get the study definition data for any specific release or locked version as well as the latest draft, released or locked study definition data.

    @impact:data_schema
    Scenario: All versions of a study except the latest must have an end date
        Given there are versioned studies
        Then only the last HAS_VERSION relationship of each study should be without an end date

    @impact:data_schema
    Scenario: A study root must not have more than one type of relationship for LATEST, LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED, each pointing at a relevant value node
        Given there are versioned studies
        Then the study root node has no more than one each of LATEST_nnn relationships

    @impact:business_rules
    Scenario: A study root must not have duplicated HAS_VERSION relationships by status and date
        Given there are versioned studies
        Then there are no duplicated HAS_VALUE relationships by status and date

    Scenario: Study versions that have an end date must have their end date after their start date
        Given there are versioned studies
        Then no HAS_VERSION relationship has a negative duration

    @impact:data_schema
    Scenario: All study versions must have a start date
        Given there are versioned studies
        Then no HAS_VERSION relationship lacks a start date

    @impact:business_rules
    Scenario: All HAS_VERSION relationship from a study root node must be in chronologic order
        Given there are versioned studies
        Then all HAS_VERSION relationship from a study root node are in chronologic order

    @impact:data_schema
    Scenario: The relationships LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED must have a matching HAS_VERSION relationship
        Given there are versioned studies
        Then there is a matching HAS_VERSION for every LATEST_nnn relationship

    @impact:data_schema
    Scenario: A study root node must have a LATEST relationship to the latest study value node
        Given there are versioned studies
        Then the LATEST relationship points to the latest study version

    @impact:business_rules
    Scenario: Locking a study must also create a corresponding released version
        Given there are versioned studies
        Then all HAS_VERSION relationships with status LOCKED have a matching HAS_VERSION with status RELEASED

    @impact:business_rules
    Scenario: Each Study version is connected to only one version of each Study Selection, such as study visit or study epoch
        Given there are versioned studies
        Then only one version of each StudySelection node is connected to each StudyValue node

    @impact:business_rules
    Scenario: Only LOCKED or RELEASED study versions can have HAS_PROTOCOL_SOA_CELL or HAS_PROTOCOL_SOA_FOOTNOTE relationships
        Given there are versioned studies
        Then only LOCKED or RELEASED study versions have HAS_PROTOCOL_SOA_CELL or HAS_PROTOCOL_SOA_FOOTNOTE relationships
