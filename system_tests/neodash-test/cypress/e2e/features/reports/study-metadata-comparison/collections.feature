@REQ_ID:1741028
@neodash_tests
Feature: Study Metadata Comparison - Collections

    As a user, I want to compare metadata for two studies or two study versions in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Study Metadata Comparison' page is opened

    Scenario: User must be able to view the Collections report panels
        Given The neoDash 'Collections' tab is selected
        Then The following set of neoDash reports are displayed
            | report                        |
            | Change Type                   |
            | Current Study Selection       |
            | Planned Collections at Visits |

    Scenario: User must be able to view values in the Collections tables for two selected studies
        Given Two studies are selected for comparison
        And The neoDash 'Collections' tab is selected
        Then The Current Study Selection table shows values for the selected studies
        And The Change Type table returns values
        And The Planned Collections at Visits table returns values

    @manual_test
    Scenario: User must be able to compare collections - Added
        Given The neoDash 'Select studies' tab is selected
        And The user selects the following project in Select Projects panel
            | project   |
            | CDISC DEV |
        When The user selects date: '2024-05-08T02:12:39' in the Select Base panel
        And The user selects date: '2024-05-08T05:20:37' in the Select Compare panel
        And The user navigates to the 'Collections' page
        And The user filter the Change Type column to 'Added'
        Then The Planned collections at visits panel displays the following rows
            | VisitID | VisitShortLabel | Activity                            | Base | Compare | ChangeType |
            | 1       | V1              | Adverse Event                       | x    |         | Added      |
            | 1       | V1              | Albumin                             | x    |         | Added      |
            | 1       | V1              | Cholesterol                         | x    |         | Added      |
            | 1       | V1              | Creatine Kinase MM                  | x    |         | Added      |
            | 1       | V1              | Diastolic Blood Pressure            | x    |         | Added      |
            | 1       | V1              | HDL Cholesterol                     | x    |         | Added      |
            | 1       | V1              | HbA1c                               | x    |         | Added      |
            | 1       | V1              | LDL Cholesterol                     | x    |         | Added      |
            | 1       | V1              | Medical History/Concomitant Illness | x    |         | Added      |
            | 1       | V1              | Pulse Rate                          | x    |         | Added      |
            | 2       | V2              | Adverse Event                       | x    |         | Added      |
            | 2       | V2              | Albumin                             | x    |         | Added      |

    @manual_test
    Scenario: User must be able to compare collections - Deleted
        Given The neoDash 'Select studies' tab is selected
        And The user selects the following project in Select Projects panel
            | project   |
            | CDISC DEV |
        When The user selects date: '2024-05-08T02:12:39' in the Select Base panel
        And The user selects date: '2024-05-08T05:20:37' in the Select Compare panel
        And The user navigates to the 'Collections' page
        And The user filter the Change Type column to 'Deleted'
        Then The Planned collections at visits panel displays the following rows
            | VisitID | VisitShortLabel | Activity                | Base | Compare | ChangeType |
            | 3       | V3              | Systolic Blood Pressure |      | x       | Deleted    |
            | 4       | V4              | Systolic Blood Pressure |      | x       | Deleted    |
            | 5       | V5              | Systolic Blood Pressure |      | x       | Deleted    |
            | 5       | V5              | Weight                  |      | x       | Deleted    |
            | 6       | V6              | Systolic Blood Pressure |      | x       | Deleted    |
            | 7       | V7              | Systolic Blood Pressure |      | x       | Deleted    |
            | 8       | V8              | Systolic Blood Pressure |      | x       | Deleted    |
            | 8       | V8              | Weight                  |      | x       | Deleted    |
            | 9       | V9              | Systolic Blood Pressure |      | x       | Deleted    |
            | 10      | V10             | Systolic Blood Pressure |      | x       | Deleted    |
            | 11      | V11             | Systolic Blood Pressure |      | x       | Deleted    |
            | 11      | V11             | Weight                  |      | x       | Deleted    |

    @manual_test
    Scenario: User must be able to compare collections - No Change
        Given The neoDash 'Select studies' tab is selected
        And The user selects the following project in Select Projects panel
            | project   |
            | CDISC DEV |
        When The user selects date: '2024-05-08T02:12:39' in the Select Base panel
        And The user selects date: '2024-05-08T05:20:37' in the Select Compare panel
        And The user navigates to the 'Collections' page
        And The user filter the Change Type column to 'No Change'
        Then The Planned collections at visits panel displays the following rows
            | VisitID | VisitShortLabel | Activity                 | Base | Compare | ChangeType |
            | 1       | V1              | Eligibility Criteria Met | x    | x       | No change  |
            | 1       | V1              | Height                   | x    | x       | No change  |
            | 1       | V1              | Systolic Blood Pressure  | x    | x       | No change  |
            | 1       | V1              | Weight                   | x    | x       | No change  |
            | 2       | V2              | Systolic Blood Pressure  | x    | x       | No change  |
            | 2       | V2              | Weight                   | x    | x       | No change  |