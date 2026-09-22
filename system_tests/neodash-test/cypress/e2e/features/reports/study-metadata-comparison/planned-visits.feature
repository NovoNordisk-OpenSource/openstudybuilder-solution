@REQ_ID:1741028
@neodash_tests
Feature: Study Metadata Comparison - Planned Visits

    As a user, I want to compare metadata for two studies or two study versions in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Study Metadata Comparison' page is opened

    Scenario: User must be able to view the Planned Visits report panels
        Given The neoDash 'Planned Visits' tab is selected
        Then The following set of neoDash reports are displayed
            | report                     |
            | Change Type                |
            | Current Study Selection    |
            | Visit Attribute Changes    |

    Scenario: User must be able to view values in the Planned Visits tables for two selected studies
        Given Two studies are selected for comparison
        And The neoDash 'Planned Visits' tab is selected
        Then The Current Study Selection table shows values for the selected studies
        And The Change Type table returns values
        And The Visit Attribute Changes table returns values

    @manual_test
    Scenario: User must be able to compare planned visits - display differences only
        Given The neoDash 'Select studies' tab is selected
        When The user selects date: '2024-05-08T02:12:39' in the Select Base panel
        And The user selects date: '2024-05-08T02:13:53' in the Select Compare panel
        And The the Show only differences is set to 'Yes'
        And The user navigates to the 'Planned Visits' page
        And The user filter the Visit Name column to 'Visit 2'
        Then The differences are shown in the Visit attribute changes panel with following differences
            | visitName | visitNumber | visitPropType          | base                               | comp                             | diff |
            | Visit 2   | 2           | Is global anchor visit | False                              | True                             | yes  |
            | Visit 2   | 2           | StudyDay               | 213.0 (Day 213)                    | 1.0 (Day 1)                      | yes  |
            | Visit 2   | 2           | StudyDurationDays      | 212.0 (212 days)                   | 0.0 (0 days)                     | yes  |
            | Visit 2   | 2           | StudyDurationWeeks     | 30.0 (30 weeks)                    | 0.0 (0 weeks)                    | yes  |
            | Visit 2   | 2           | StudyWeek              | 31.0 (Week 31)                     | 1.0 (Week 1)                     | yes  |
            | Visit 2   | 2           | TimePoint              | 212 days after Global anchor visit | 0 days after Global anchor visit | yes  |
            | Visit 2   | 2           | Visit window max       | 35                                 | 0                                | yes  |
            | Visit 2   | 2           | WeekInStudy            | 30.0 (Week 30)                     | 0.0 (Week 0)                     | yes  |