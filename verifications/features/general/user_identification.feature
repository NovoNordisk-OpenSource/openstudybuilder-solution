@REQ_ID:1370753
Feature: User identification

  @impact:data_schema
  Scenario: Relevant nodes and relations must have author_id field set
    Given the database is reachable and has content
    Then all relevant nodes have author_id field set
    And all relevant relations have author_id field set

  @impact:business_rules
  Scenario: User nodes referenced from other relevant nodes and relations must exist
    Given the database is reachable and has content
    Then for each node author_id field value there must exist one User node with the same user_id field value
    And for each relation author_id field value there must exist one User node with the same user_id field value
    And there is no User node with user_id set to null

  @impact:business_rules
  Scenario Outline: API endpoints must return not-null author username
    Given the API is reachable
    Then get <url> returns not null value for <json_path> field

    Examples:
      | url             | json_path          |
      | /configurations | $..author_username |
      | /ct/packages    | $..author_username |
      | /studies        | $..version_author  |
