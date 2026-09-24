@REQ_ID:1741028
@neodash_tests
Feature: Study Metadata Comparison - Study Fields

    As a user, I want to compare metadata for two studies or two study versions in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Study Metadata Comparison' page is opened

    Scenario: User must be able to view the Study Fields report panels
        Given The neoDash 'Study Fields' tab is selected
        Then The following set of neoDash reports are displayed
            | report                  |
            | Current Study Selection |
            | Study Field Comparison  |

    Scenario: User must be able to view values in the Study Fields tables for two selected studies
        Given Two studies are selected for comparison
        And The neoDash 'Study Fields' tab is selected
        Then The Current Study Selection table shows values for the selected studies
        And The Study Field Comparison table returns comparison values

    @manual_test
    Scenario: User must be able to compare study field values - display differences only
        Given The neoDash 'Select studies' tab is selected
        When The user selects version 1 in the Select Base panel
        And The user selects version 1.1 in the Select Compare panel
        And The the Show only differences is set to 'Yes'
        And The user navigates to the 'Study Fields' page
        Then The differences are shown in the Study field comparison panel with following differences
            | StudyField             | Base                         | Compare                  | Diff |
            | Ct gov id              | XX-v1                        | XX-v1.1                  | yes  |
            | Study acronym          |                              | versioning               | yes  |
            | Study id prefix        |                              | CDISC DEV                | yes  |
            | Study number           |                              | 1111                     | yes  |
            | Study title            | Title version 1              | Title version 1.1        | yes  |
            | Study type code        | Expanded Access              | Interventional           | yes  |
            | Therapeutic area codes | Nonalcoholic steatohepatitis | Type 1 Diabetes mellitus | yes  |
