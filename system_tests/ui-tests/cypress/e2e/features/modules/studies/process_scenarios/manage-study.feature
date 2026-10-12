@REQ_ID:987736, @REQ_ID:1074253, @REQ_ID:1741028
Feature: Studies - Manage Study - E2E verification

    As a system user,
    I want the system to ensure [Scenario],
    So that I must be able to make complete and consistent specification of study structure, including arms, branches, cohorts, elements and design matrix.

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: [Draft][Create] User must be able to add new Study
        Given The '/studies/select_or_add_study/active' page is opened
        And User waits for the table
        And The Add Study button is clicked
        When New study project id, study number and study acronym are filled in
        And User intercepts all available studies request
        And Form save button is clicked
        Then The pop up displays 'Study added'
        And User waits for available studies request
        And Study is found
        Then The study is visible within the table

    Scenario: [Draft][Study Core Attributes] User must be able to edit Study Core Attributes
        And User selects newly created CDISC study
        Given The page 'study_status/core_attributes' is opened for current study
        When User clicks edit content button
        And Edit Study Attributes window is opened
        And The Project name input field is disabled for edition
        And The Brand name input field is disabled for edition
        And The Study ID input field is disabled for edition
        And The Study Acronym value is updated with 'updated v1'
        And Form save button is clicked
        Then The Study Acronym value is visible in the table

    Scenario: [Draft][Study Title] User must be able to add study title
        And User selects newly created CDISC study
        Given The page 'study_title' is opened for current study
        And User intercepts request with available studies
        When The 'Edit study title' button is clicked
        And User waits for request with available studies
        And User sets study title as 'Study title v1'
        And User sets study short title as 'Study short title v1'
        And Action is confirmed by clicking save
        Then The study title is displayed as 'Study title v1'
        And The study short title is displayed as 'Study short title v1'
        
    Scenario: [Draft][Registry Identifiers] User must be able to add Registry Identifiers
        And User selects newly created CDISC study
        Given The page 'registry_identifiers' is opened for current study
        And User waits for the table
        When The edit content button is clicked
        When The identifiers are set with following data
            | identifier                                        | value         |
            | ClinicalTrials.gov ID                             | RI_1 v1       |
            | EUDRACT ID                                        | RI_2 v1       |
            | Universal Trial Number (UTN)                      | RI_3 v1       |
            | Japanese Trial Registry ID (JAPIC)                | RI_4 v1       |
            | Investigational New Drug Application (IND) Number | RI_5 v1       |
            | EU Trial Number                                   | RI_6 v1       |
            | CIV-ID/SIN Number                                 | RI_7 v1       |
            | National Clinical Trial Number                    | RI_8 v1       |
            | Japanese Trial Registry Number                    | RI_9 v1       |
            | NMPA Number                                       | RI_10 v1      |
            | EUDAMED number                                    | RI_11 v1      |
            | Investigational Device Exemption Number           | RI_12 v1      |
            And Form save button is clicked
            And The form is no longer available
        And User waits for the table
        Then The identifiers table is showing following data
            | identifier                                        | value         |
            | ClinicalTrials.gov ID                             | RI_1 v1       |
            | EUDRACT ID                                        | RI_2 v1       |
            | Universal Trial Number (UTN)                      | RI_3 v1       |
            | Japanese Trial Registry ID (JAPIC)                | RI_4 v1       |
            | Investigational New Drug Application (IND) Number | RI_5 v1       |
            | EU Trial Number                                   | RI_6 v1       |
            | CIV-ID/SIN Number                                 | RI_7 v1       |
            | National Clinical Trial Number                    | RI_8 v1       |
            | Japanese Trial Registry Number                    | RI_9 v1       |
            | NMPA Number                                       | RI_10 v1      |
            | EUDAMED number                                    | RI_11 v1      |
            | Investigational Device Exemption Number           | RI_12 v1      |

    Scenario: [Draft][Edition] User must be able to set study data - properties, attributes, criteria
        And User selects newly created CDISC study
        Given The page 'study_properties/type' is opened for current study
        When The edit content button is clicked
        And The study type is set as 'Observational'
        And Form save button is clicked
        Given The study type is visible as 'Observational'
        Given The page 'study_properties/attributes' is opened for current study
        When The edit content button is clicked
        When The study intervention type is set as 'Medical Device'
        And Form save button is clicked
        Then The study intervention type visible as 'Medical Device'
        #Given The page 'population' is opened for current study
        #When The edit content button is clicked
        #When User sets study therapeutic area as 'Growth hormone deficiency'
        #And Form save button is clicked
        #And The form is no longer available
        #Then The study Therapeutic area is visible as 'Growth hormone deficiency'
        Given The page 'selection_criteria/Dosing%20Criteria' is opened for current study
        When User clicks add study criteria button
        And User selects to create criteria from scratch
        And Form continue button is clicked
        When Study criteria value is set to 'E2E dosing criteria v1'
        And Form continue button is clicked
        And Form save button is clicked
        Then User searches for 'E2E dosing criteria v1'

    Scenario: [Draft][Subpart] User must be able to add study subpart
        And User selects newly created CDISC study
        Given The page 'study_status/subparts' is opened for current study
        When The plus button is clicked
        And Form continue button is clicked
        And User sets study subpart acronym to 'A'
        And Form save button is clicked
        Then Study subpart with acronym 'A' is searched for and found
        When The plus button is clicked
        And Form continue button is clicked
        And User sets study subpart acronym to 'B'
        And Form save button is clicked
        Then Study subpart with acronym 'B' is searched for and found
        When The '/studies/select_or_add_study/active' page is opened
        Then Study subpart with acronym 'A' is searched for and found
        And Study subpart with acronym 'B' is searched for and found

    Scenario: [Test data] User must be able to add data to later verify study versions
        And User selects newly created CDISC study
        Given [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] Uid of study type 'Investigational Arm' is fetched
        And [API] The Study Arm with name 'Arm1' exists within selected study
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Get class uid for activity instance creation
        And [API] Group and subgroup are created and approved to be used for activity creation
        And [API] Activity with data collection set to 1 and 'FirstActivity' included in the name is created and approved
        And [API] The activity instance with name 'FirstInstance_API_' and isRequriedForActivity set to true is created and approved
        And [API] Activity is added to the selected study
        And [API] Activity is assigned to the visit 0 in selected study

    Scenario: [Lock] User must be able to lock existing study
        And User selects newly created CDISC study
        And The page 'study_status/study_status' is opened for current study
        When The lock study request is intercepted
        And User clicks lock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Other'
        And The user provides protocol major version '0'
        And The user provides protocol minor version '1'
        And The user provides explanation for other reason
        And Action is confirmed by clicking save
        And User waits for lock study request
        Then The study is displayed as locked with 'Other' as a reason
        And The procotol version is displayed in table as '0.1'

    Scenario: [Locked] User must not be able to edit locked study
        Given User selects newly created CDISC study
        Given The page 'study_status/core_attributes' is opened for current study
        Then The edit button is disabled
        Given The page 'study_title' is opened for current study
        Then The edit button is disabled
        Given The page 'registry_identifiers' is opened for current study
        Then The edit button is disabled
        Given The page 'study_properties/type' is opened for current study
        Then The edit button is disabled
        Given The page 'study_properties/attributes' is opened for current study
        Then The edit button is disabled
        Given The page 'selection_criteria/Dosing%20Criteria' is opened for current study
        Then The plus button is disabled
        Given The page 'study_status/subparts' is opened for current study
        Then The plus button is disabled
        Given The page 'study_structure/arms' is opened for current study
        Then The edit button is disabled
        Given The page 'study_structure/branches' is opened for current study
        Then The edit button is disabled
        Given The page 'study_structure/cohorts' is opened for current study
        Then The edit button is disabled
        Given The page 'study_structure/epochs' is opened for current study
        Then The plus button is disabled
        Given The page 'study_structure/visits' is opened for current study
        Then The plus button is disabled
        Then The edit button is disabled
        Given The page 'activities/list' is opened for current study
        Then The plus button is disabled
        Given The page 'data_specifications/instances' is opened for current study
        Then The edit button is disabled

    Scenario: [Unlock] User must be able to unlock existing study
        And User selects newly created CDISC study
        And The page 'study_status/study_status' is opened for current study
        When The unlock study request is intercepted
        And User clicks unlock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Study Specification Updates'
        And Action is confirmed by clicking save
        And User waits for unlock study request
        Then The study is displayed as unlocked with 'Study Specification Updates' as a reason

    Scenario: [Test data] User must be able to add more data to later verify study versions (study structure, study activities, study activity instances)
        And User selects newly created CDISC study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] Uid of study type 'Comparator Arm' is fetched
        And [API] The Study Arm with name 'Arm2' exists within selected study
        And [API] The Study Arm with name 'Arm3' exists within selected study
        And [API] The Study Branch is created within selected study
        And [API] The Study Cohort is created within selected study
        And [API] Uids are fetched for element subtype 'Run-in'
        And [API] Element is created for the current study
        And [API] Link Study Element to Epoch and Study Arm within selected study
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Intervention'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Get class uid for activity instance creation
        And [API] Group and subgroup are created and approved to be used for activity creation
        And [API] Activity with data collection set to 1 and 'SecondActivity' included in the name is created and approved
        And [API] The activity instance with name 'SecondInstance_API_' and isRequriedForActivity set to true is created and approved
        And [API] Activity is added to the selected study
        And [API] Activity is assigned to the visit 1 in selected study

    Scenario: [Unlock] User must be able to edit unlocked version of study - attributes, title, registry identifiers, properties, criteria
        And User selects newly created CDISC study
        Given The page 'registry_identifiers' is opened for current study
        And User waits for the table
        When The edit content button is clicked
        When The identifiers are set with following data
            | identifier                                        | value         |
            | ClinicalTrials.gov ID                             | RI_1 v2       |
            | EUDRACT ID                                        | RI_2 v2       |
            | Universal Trial Number (UTN)                      | RI_3 v2       |
            | Japanese Trial Registry ID (JAPIC)                | RI_4 v2       |
            | Investigational New Drug Application (IND) Number | RI_5 v2       |
            | EU Trial Number                                   | RI_6 v2       |
            | CIV-ID/SIN Number                                 | RI_7 v2       |
            | National Clinical Trial Number                    | RI_8 v2       |
            | Japanese Trial Registry Number                    | RI_9 v2       |
            | NMPA Number                                       | RI_10 v2      |
            | EUDAMED number                                    | RI_11 v2      |
            | Investigational Device Exemption Number           | RI_12 v2      |
            And Form save button is clicked
            And The form is no longer available
        And User waits for the table
        Then The identifiers table is showing following data
            | identifier                                        | value         |
            | ClinicalTrials.gov ID                             | RI_1 v2       |
            | EUDRACT ID                                        | RI_2 v2       |
            | Universal Trial Number (UTN)                      | RI_3 v2       |
            | Japanese Trial Registry ID (JAPIC)                | RI_4 v2       |
            | Investigational New Drug Application (IND) Number | RI_5 v2       |
            | EU Trial Number                                   | RI_6 v2       |
            | CIV-ID/SIN Number                                 | RI_7 v2       |
            | National Clinical Trial Number                    | RI_8 v2       |
            | Japanese Trial Registry Number                    | RI_9 v2       |
            | NMPA Number                                       | RI_10 v2      |
            | EUDAMED number                                    | RI_11 v2      |
            | Investigational Device Exemption Number           | RI_12 v2      |
        Given The page 'study_title' is opened for current study
        And User intercepts request with available studies
        When The 'Edit study title' button is clicked
        And User waits for request with available studies
        And User sets study title as 'Study title v2'
        And User sets study short title as 'Study short title v2'
        And Action is confirmed by clicking save
        Then The study title is displayed as 'Study title v2'
        And The study short title is displayed as 'Study short title v2'
        Given The page 'study_properties/type' is opened for current study
        When The edit content button is clicked
        And The study type is set as 'Interventional'
        And Form save button is clicked
        Given The study type is visible as 'Interventional'
        Given The page 'study_properties/attributes' is opened for current study
        When The edit content button is clicked
        When The study intervention type is set as 'Gene Therapy'
        And Form save button is clicked
        Then The study intervention type visible as 'Gene Therapy'
        #Given The page 'population' is opened for current study
        #When The edit content button is clicked
        #When User sets study therapeutic area as "Alzheimer's disease"
        #And User deselects study therapeutic area 'Growth hormone deficiency'
        #And Form save button is clicked
        #And The form is no longer available
        #Then The study Therapeutic area is visible as "Alzheimer's disease"
        Given The page 'selection_criteria/Dosing%20Criteria' is opened for current study
        When User clicks add study criteria button
        And User selects to create criteria from scratch
        And Form continue button is clicked
        When Study criteria value is set to 'E2E dosing criteria v2'
        And Form continue button is clicked
        And Form save button is clicked
        Then User searches for 'E2E dosing criteria v2'

    Scenario: [Check versions] User must be able to switch between study versions
        And User selects newly created CDISC study
        And The page 'study_status/study_status' is opened for current study
        Given User selects locked study version
        And User waits for the table
        Then Locked version of study is visible as selected in the header
        Given The page 'study_status/core_attributes' is opened for current study
        Then The edit button is disabled
        Given The page 'study_title' is opened for current study
        Then The edit button is disabled
        Then The study title is displayed as 'Study title v1'
        And The study short title is displayed as 'Study short title v1'
        Given The page 'registry_identifiers' is opened for current study
        Then The edit button is disabled
        And User waits for the table
        Then The identifiers table is showing following data
            | identifier                                        | value         |
            | ClinicalTrials.gov ID                             | RI_1 v1       |
            | EUDRACT ID                                        | RI_2 v1       |
            | Universal Trial Number (UTN)                      | RI_3 v1       |
            | Japanese Trial Registry ID (JAPIC)                | RI_4 v1       |
            | Investigational New Drug Application (IND) Number | RI_5 v1       |
            | EU Trial Number                                   | RI_6 v1       |
            | CIV-ID/SIN Number                                 | RI_7 v1       |
            | National Clinical Trial Number                    | RI_8 v1       |
            | Japanese Trial Registry Number                    | RI_9 v1       |
            | NMPA Number                                       | RI_10 v1      |
            | EUDAMED number                                    | RI_11 v1      |
            | Investigational Device Exemption Number           | RI_12 v1      |
        Given The page 'study_properties/type' is opened for current study
        Then The edit button is disabled
        Given The study type is visible as 'Observational'
        Given The page 'study_properties/attributes' is opened for current study
        Then The edit button is disabled
        Then The study intervention type visible as 'Medical Device'
        Given The page 'study_status/subparts' is opened for current study
        Then The plus button is disabled
        Given The page 'study_structure/arms' is opened for current study
        Then The edit button is disabled
        And User searches for 'Arm1'
        And User searches for 'Arm2' and confirms no results returned
        And User searches for 'Arm3' and confirms no results returned
        Given The page 'study_structure/branches' is opened for current study
        Then The edit button is disabled
        And No results are present the table
        Given The page 'study_structure/cohorts' is opened for current study
        Then The edit button is disabled
        And No results are present the table
        Given The page 'study_structure/epochs' is opened for current study
        Then The plus button is disabled
        And User searches for 'Run-in'
        And User searches for 'Intervention' and confirms no results returned
        Given The page 'study_structure/visits' is opened for current study
        Then The plus button is disabled
        Then The edit button is disabled
        And User searches for 'Visit 1'
        And Only one row is present
        And User searches for 'Visit 2'
        And Only one row is present
        And User searches for 'Visit 3' and confirms no results returned
        Given The page 'selection_criteria/Dosing%20Criteria' is opened for current study
        Then The plus button is disabled
        And User searches for 'E2E dosing criteria v1'
        And User searches for 'E2E dosing criteria v2' and confirms no results returned
        Given The page 'activities/list' is opened for current study
        Then The plus button is disabled
        And User searches for 'FirstActivity'
        And Only one row is present
        And User searches for 'SecondActivity' and confirms no results returned
        Given The page 'data_specifications/instances' is opened for current study
        Then The edit button is disabled
        And User searches for 'FirstInstance_API_'
        And Only one row is present
        And User searches for 'SecondInstance_API_' and confirms no results returned