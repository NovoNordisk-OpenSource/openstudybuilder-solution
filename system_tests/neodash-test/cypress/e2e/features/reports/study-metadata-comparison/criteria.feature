@REQ_ID:1741028
@neodash_tests
Feature: Study Metadata Comparison - Criteria

    As a user, I want to compare metadata for two studies or two study versions in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Study Metadata Comparison' page is opened

    Scenario: User must be able to view the Criteria report panels
        Given The neoDash 'Criteria' tab is selected
        Then The following set of neoDash reports are displayed
            | report                  |
            | Current Study Selection |
            | Study Criteria          |

    Scenario: User must be able to view values in the Criteria tables for two selected studies
        Given Two studies are selected for comparison
        And The neoDash 'Criteria' tab is selected
        Then The Current Study Selection table shows values for the selected studies
        And The Study Criteria table returns comparison values

    @manual_test
    Scenario: User must be able to compare criteria - display differences only
        Given The neoDash 'Select studies' tab is selected
        When The user selects date: '2024-05-08T02:12:39' in the Select Base panel
        And The user selects date: '2024-05-08T02:14:18' in the Select Compare panel
        And The the Show only differences is set to 'Yes'
        And The user navigates to the 'Criteria' page
        Then The differences are shown in the Study criteria comparison panel with following differences
            | baseCriteria                      | compareCriteria | diff |
            | Test dosing criteria from scratch | Criteria for v1 | yes  |