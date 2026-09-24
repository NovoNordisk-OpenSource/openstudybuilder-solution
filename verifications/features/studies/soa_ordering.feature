@REQ_ID:1370753 @REQ_ID:2755132
Feature: SoA ordering
    @impact:business_rules
    Scenario: Each latest active version of StudyActivity must have order number assigned
        Given there are studies with StudyActivity content
        Then each latest active version of StudyActivity has order assigned

    @impact:business_rules
    Scenario: Each StudyActivitySubGroup linked to latest active version of StudyActivity must have order number assigned
        Given there are studies with StudyActivity content
        Then each StudyActivitySubGroup linked to latest active version of StudyActivity has order assigned

    @impact:business_rules
    Scenario: Each StudyActivityGroup linked to latest active version of StudyActivity must have order number assigned
        Given there are studies with StudyActivity content
        Then each StudyActivityGroup linked to latest active version of StudyActivity has order assigned

    @impact:business_rules
    Scenario: Each StudySoAGroup linked to latest active version of StudyActivity must have order number assigned
        Given there are studies with StudyActivity content
        Then each StudySoAGroup linked to latest active version of StudyActivity has order assigned

    # These checks are disabled for now since the way ordering is implemented is likely to change soon.
    # @impact:business_rules
    # Scenario: Each StudyActivity under the same StudyActivitySubGroup must have unique order assigned
    #     Given there are studies with StudyActivity content
    #     Then each StudyActivity under the same StudyActivitySubGroup has unique order assigned

    # @impact:business_rules
    # Scenario: Each StudyActivitySubGroup under the same StudyActivityGroup must have unique order assigned
    #     Given there are studies with StudyActivity content
    #     Then each StudyActivitySubgroup under the same StudyActivityGroup has unique order assigned

    # @impact:business_rules
    # Scenario: Each StudyActivityGroup under the same StudySoAGroup must have unique order assigned
    #     Given there are studies with StudyActivity content
    #     Then each StudyActivityGroup under the same StudySoAGroup has unique order assigned

    # @impact:business_rules
    # Scenario: StudyActivities under the same StudyActivitySubGroup must have sequential order assigned
    #     Given there are studies with StudyActivity content
    #     Then StudyActivities under the same StudyActivitySubGroup have sequential order assigned

    # @impact:business_rules
    # Scenario: StudyActivitySubGroups under the same StudyActivityGroup must have sequential order assigned
    #     Given there are studies with StudyActivity content
    #     Then StudyActivitySubGroups under the same StudyActivityGroup have sequential order assigned

    # @impact:business_rules
    # Scenario: StudyActivityGroups under the same StudySoAGroup must have sequential order assigned
    #     Given there are studies with StudyActivity content
    #     Then StudyActivityGroups under the same StudySoAGroup have sequential order assigned