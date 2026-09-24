@REQ_ID:1741028
@neodash_tests
Feature: Study Metadata Comparison - Objectives and Endpoints

    As a user, I want to compare metadata for two studies or two study versions in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Study Metadata Comparison' page is opened

    Scenario: User must be able to view the Objectives and Endpoints report panels
        Given The neoDash 'Objectives/Endpoints' tab is selected
        Then The following set of neoDash reports are displayed
            | report                   |
            | Current Study Selection  |
            | Objectives               |
            | Endpoints (by Objective) |

    Scenario: User must be able to view values in the Objectives and Endpoints tables for two selected studies
        Given Two studies are selected for comparison
        And The neoDash 'Objectives/Endpoints' tab is selected
        Then The Current Study Selection table shows values for the selected studies
        And The Objectives table returns comparison values
        And The Endpoints (by Objective) table returns comparison values

    @manual_test
    Scenario: User must be able to compare objectives and endpoints - display differences only
        Given The neoDash 'Select studies' tab is selected
        When The user selects date: '2024-05-08T02:12:39' in the Select Base panel
        And The user selects date: '2024-05-08T02:14:18' in the Select Compare panel
        And The the Show only differences is set to 'Yes'
        And The user navigates to the 'Objectives\/Endpoints' page
        Then The differences are shown in the Objectives comparison panel with following differences
            | number | baseObjective                                                                                                                                        | compareObjective | diff |
            | Obj 1  | Time to first occurrence of MACE+, a composite endpoint consisting of: CV death, nonfatal MI,nonfatal stroke, or hospitalization for unstable angina |                  | yes  |

        And The differences are shown in the Endpoints (by Objective) comparison panel with following differences
            | number         | objective                                                                                                                                            | baseEndpoint                                                 | compareEndpoint | diff |
            | Obj 1 - Endp 1 | Time to first occurrence of MACE+, a composite endpoint consisting of: CV death, nonfatal MI,nonfatal stroke, or hospitalization for unstable angina | Mean change from baseline in hba1c                           |                 | yes  |
            | Obj 1 - Endp 2 | Time to first occurrence of MACE+, a composite endpoint consisting of: CV death, nonfatal MI,nonfatal stroke, or hospitalization for unstable angina | Disease control rate of cagrilintide + insulin icodec cohort |                 | yes  |
            | Obj 1 - Endp 3 | Time to first occurrence of MACE+, a composite endpoint consisting of: CV death, nonfatal MI,nonfatal stroke, or hospitalization for unstable angina | Mean change from baseline in 1,5 ag (anhydroglucitol)        |                 | yes  |