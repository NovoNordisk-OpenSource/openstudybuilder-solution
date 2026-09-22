@REQ_ID:1074253
Feature: Manage Registry Identifiers in OpenStudyBuilder API

    Background: Test user must be able to call the OpenStudyBuilder API and test data exist
        Given The test user can call the OpenStudyBuilder API
        Given a test study identified by 'uid' is in status 'Locked' for the 'study_value_version'

    Rule: As an API user,
        I want the system to ensure registry identifiers can be defined for  a study,
        So these can be used as part of the study specification in down-stream systems.


        Scenario Outline: The API must support creation of registry identifiers for a study
            When the <registry identifier> registry identifier is created for a study using the POST API endpoint '/studies'
            Then the <registry identifier> is defined for the study
            Examples:
                | registry identifier                                    |
                | ClinicalTrials.gov ID                                  |
                | EUDRACT ID                                             |
                | Universal Trial Number (UTN)                           |
                | Japanese Trial Registry ID (JAPIC)                     |
                | Investigational New Drug Application (IND) Number      |
                | WHO ID                                                 |
                | EU Trial Number                                        |
                | CIV-ID/SIN Number                                      |
                | National Clinical Trial Number                         |
                | Japanese Trial Registry Number (jRCT)                  |
                | National Medical Products Administration (NMPA) Number |
                | EUDAMED SRN Number                                     |
                | Investigational Device Exemption (IDE) Number          |

        @TestID:test_get_protocol_title_for_specific_version
        Scenario Outline: The API must support update of registry identifiers for a study
            When the <registry identifier> registry identifier is updated for a study using the PATCH API endpoint '/studies'
            Then the <registry identifier> is updated for the study
            Examples:
                | registry identifier                                    |
                | ClinicalTrials.gov ID                                  |
                | EUDRACT ID                                             |
                | Universal Trial Number (UTN)                           |
                | Japanese Trial Registry ID (JAPIC)                     |
                | Investigational New Drug Application (IND) Number      |
                | WHO ID                                                 |
                | EU Trial Number                                        |
                | CIV-ID/SIN Number                                      |
                | National Clinical Trial Number                         |
                | Japanese Trial Registry Number (jRCT)                  |
                | National Medical Products Administration (NMPA) Number |
                | EUDAMED SRN Number                                     |
                | Investigational Device Exemption (IDE) Number          |


        Scenario Outline: The API must support remove of registry identifiers for a study
            When the <registry identifier> registry identifier is removed for a study using the DELETE/PATCH/??? API endpoint '/studies'
            Then the <registry identifier> is removed for the study
            Examples:
                | registry identifier                                    |
                | ClinicalTrials.gov ID                                  |
                | EUDRACT ID                                             |
                | Universal Trial Number (UTN)                           |
                | Japanese Trial Registry ID (JAPIC)                     |
                | Investigational New Drug Application (IND) Number      |
                | WHO ID                                                 |
                | EU Trial Number                                        |
                | CIV-ID/SIN Number                                      |
                | National Clinical Trial Number                         |
                | Japanese Trial Registry Number (jRCT)                  |
                | National Medical Products Administration (NMPA) Number |
                | EUDAMED SRN Number                                     |
                | Investigational Device Exemption (IDE) Number          |


        Scenario: The API must support defining registry identifiers as not applicable for a study
            When the a registry identifier is defined as 'Not applicable' for a study using the POST API endpoint '/studies'
            And no registry identifier is defined for the study with a value
            Then the registry identifier is defined as 'No applicable' for the study


    ### History of registry identifier

    # To be made