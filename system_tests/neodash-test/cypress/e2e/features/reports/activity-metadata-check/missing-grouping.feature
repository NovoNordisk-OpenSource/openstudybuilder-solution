@REQ_ID:1070686
@neodash_tests
Feature: Activity Metadata Check - Missing Grouping

    As a user, I want to be able to ensure activity metadata within StudyBuilder is mapped correctly

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Activity Metadata Check' page is opened    
        
    Scenario: User must be able to view different metrics in Missing Grouping
        Given The neoDash 'Missing Grouping' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                                          |
            | Activity Instances with [:LATEST] Relationship                  |
            | [:LATEST] Activity Instances with a Grouping                    |
            | [:LATEST] Activity Instances with All Conditions Met            |