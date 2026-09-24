@REQ_ID:1370753
Feature: Rules for Concepts in Library

  @impact:business_rules
  Scenario Outline: There are no concepts with duplicated names
    Given the library contains objects of type <object_type>
    Then there are no objects of type <object_type> with duplicated value of <name_property>

    Examples:
      | object_type           | name_property      |
      | ActivityGroup         | name               |
      | ActivityGroup         | name_sentence_case |
      | ActivitySubGroup      | name               |
      | ActivitySubGroup      | name_sentence_case |
      | Activity              | name               |
      | Activity              | name_sentence_case |
      | ActivityInstance      | name               |
      | ActivityInstance      | name_sentence_case |
      | ActivityItemClass     | name               |
      | ActivityInstanceClass | name               |
      | UnitDefinition        | name               |

