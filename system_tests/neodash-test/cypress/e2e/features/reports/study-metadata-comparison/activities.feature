@REQ_ID:1741028
@neodash_tests
Feature: Study Metadata Comparison - Activities

    As a user, I want to compare metadata for two studies or two study versions in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Study Metadata Comparison' page is opened

    Scenario: User must be able to view the Activities report panels
        Given The neoDash 'Activities' tab is selected
        Then The following set of neoDash reports are displayed
            | report                                                     |
            | Change Type                                                |
            | Current Study Selection                                    |
            | Detailed Flowchart Compare Between Base and Compare Study  |
            | SoA L1 - Protocol SoA view - grey is showing not displayed |


    Scenario: User must be able to view values in the Activities tables for two selected studies
        Given Two studies are selected for comparison
        And The neoDash 'Activities' tab is selected
        Then The Current Study Selection table shows values for the selected studies
        And The Change Type table returns values
        And The Detailed Flowchart Compare table returns values

    @manual_test
    Scenario: User must be able to compare flowchart activities - Added
        Given The neoDash 'Select studies' tab is selected
        And The user selects the following project in Select Projects panel
            | project   |
            | CDISC DEV |
        When The user selects date: '2024-05-08T02:12:39' in the Select Base panel
        And The user selects date: '2024-05-08T05:20:37' in the Select Compare panel
        And The user navigates to the 'Activities' page
        And The user filter the Change Type column to 'Activity added'
        Then The Detailed Flowchart compare between base and compare study panel displays the following rows
            | ChangeType     | FlowchartGroupBase          | ActivityGroupBase                   | ActivitySubgroupBase                | FlowchartGroupCompare | ActivityGroupCompare | ActivitySubgroupCompare | ActivityDetail                                             |
            | Activity added | SAFETY                      | Medical History/Concomitant Illness | Medical History/Concomitant Illness |                       |                      |                         | Medical History/Concomitant Illness(Data collection: true) |
            | Activity added | SAFETY                      | Vital Signs                         | Vital Signs                         |                       |                      |                         | Pulse Rate(Data collection: true)                          |
            | Activity added | SUBJECT RELATED INFORMATION | Randomisation                       | Randomisation                       |                       |                      |                         | Randomized(Data collection: true)                          |
            | Activity added | SAFETY                      | Laboratory Assessments              | Lipids                              |                       |                      |                         | LDL Cholesterol(Data collection: true)                     |
            | Activity added | SAFETY                      | Laboratory Assessments              | Lipids                              |                       |                      |                         | Cholesterol(Data collection: true)                         |
            | Activity added | SAFETY                      | AE Requiring Additional Data        | Laboratory Assessment               |                       |                      |                         | Albumin(Data collection: true)                             |
            | Activity added | EFFICACY                    | Laboratory Assessments              | Glucose Metabolism                  |                       |                      |                         | HbA1c(Data collection: true)                               |
            | Activity added | SAFETY                      | Vital Signs                         | Vital Signs                         |                       |                      |                         | Diastolic Blood Pressure(Data collection: true)            |
            | Activity added | SAFETY                      | Laboratory Assessments              | Lipids                              |                       |                      |                         | HDL Cholesterol(Data collection: true)                     |
            | Activity added | SAFETY                      | Laboratory Assessments              | Biochemistry                        |                       |                      |                         | Creatine Kinase MM(Data collection: true)                  |
            | Activity added | SAFETY                      | Adverse Event                       | Adverse Event                       |                       |                      |                         | Adverse Event(Data collection: true)                       |
    # Don't have data for this test
    # Scenario: User must be able to compare flowchart activities - Deleted
    #     Given The neoDash 'Select studies' tab is selected
    #     And The user selects the following project in Select Projects panel
    #     |project|
    #     |CDISC DEV|
    #     When The user selects date: '2024-05-08T02:12:39' in the Select Base panel
    #     And The user selects date: '2024-05-08T05:20:37' in the Select Compare panel
    #     And The user navigates to the 'Activities' page
    #     And The user filter the Change Type column to 'Activity deleted'
    #     Then The Detailed Flowchart compare between base and compare study panel displays the following rows
    #     |ChangeType|FlowchartGroupBase|ActivityGroupBase|ActivitySubgroupBase|FlowchartGroupCompare|ActivityGroupCompare|ActivitySubgroupCompare|ActivityDetail|


    @manual_test
    Scenario: User must be able to compare flowchart activities - Activity moved
        Given The neoDash 'Select studies' tab is selected
        And The user selects the following project in Select Projects panel
            | project   |
            | CDISC DEV |
        When The user selects date: '2024-05-08T02:12:39' in the Select Base panel
        And The user selects date: '2024-05-08T05:20:37' in the Select Compare panel
        And The user navigates to the 'Activities' page
        And The user filter the Change Type column to 'Activity moved'
        Then The Detailed Flowchart compare between base and compare study panel displays the following rows
            | ChangeType     | FlowchartGroupBase | ActivityGroupBase | ActivitySubgroupBase | FlowchartGroupCompare       | ActivityGroupCompare | ActivitySubgroupCompare | ActivityDetail                                 |
            | Activity moved | SAFETY             | Vital Signs       | Vital Signs          | SUBJECT RELATED INFORMATION | Vital Signs          | Vital Signs             | Systolic Blood Pressure(Data collection: true) |

    @manual_test
    Scenario: User must be able to compare flowchart activities - No change
        Given The neoDash 'Select studies' tab is selected
        And The user selects the following project in Select Projects panel
            | project   |
            | CDISC DEV |
        When The user selects date: '2024-05-08T02:12:39' in the Select Base panel
        And The user selects date: '2024-05-08T05:20:37' in the Select Compare panel
        And The user navigates to the 'Activities' page
        And The user filter the Change Type column to 'No change'
        Then The Detailed Flowchart compare between base and compare study panel displays the following rows
            | ChangeType | FlowchartGroupBase          | ActivityGroupBase    | ActivitySubgroupBase | FlowchartGroupCompare       | ActivityGroupCompare | ActivitySubgroupCompare | ActivityDetail                                  |
            | No change  | SUBJECT RELATED INFORMATION | Body Measurements    | Body Measurements    | SUBJECT RELATED INFORMATION | Body Measurements    | Body Measurements       | Height(Data collection: true)                   |
            | No change  | SUBJECT RELATED INFORMATION | Body Measurements    | Body Measurements    | SUBJECT RELATED INFORMATION | Body Measurements    | Body Measurements       | Weight(Data collection: true)                   |
            | No change  | SUBJECT RELATED INFORMATION | Eligibility Criteria | Eligibility Criteria | SUBJECT RELATED INFORMATION | Eligibility Criteria | Eligibility Criteria    | Eligibility Criteria Met(Data collection: true) |