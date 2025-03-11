@REQ_ID:1074253
Feature: Studies - Registry Identifiers

   Background: User is logged in and study has been selected
      Given The user is logged in
      And A test study is selected

   Scenario: User must be able to navigate to the Registry Identifiers page
      Given The '/studies' page is opened
      When The 'Registry Identifiers' submenu is clicked in the 'Define Study' section
      Then The current URL is '/studies/Study_000001/registry_identifiers'

   Scenario: User must be able to see the page table with correct columns
      Given The '/studies/Study_000001/registry_identifiers' page is opened
      Then The table display following predefined data
         | column | row | value                                             |
         | 0      | 0   | ClinicalTrials.gov ID                             |
         | 0      | 1   | EUDRACT ID                                        |
         | 0      | 2   | Universal Trial Number (UTN)                      |
         | 0      | 3   | Japanese Trial Registry ID (JAPIC)                |
         | 0      | 4   | Investigational New Drug Application (IND) Number |
         | 0      | 5   | EU Trial Number                                   |
         | 0      | 6   | CID ID SIN Number                                 |
         | 0      | 7   | National Clinical Trial Number                    |
         | 0      | 8   | Japanese Trial Registry Number                    |
         | 0      | 9  | NMPA Number                                       |
         | 0      | 10  | EUDAMED number                                    |
         | 0      | 11  | Investigational Device Exemption Number           |


   Scenario: User must be able to provide informations for Registry Identifiers
      Given The '/studies/Study_000001/registry_identifiers' page is opened
      When The identifiers are set with following data
         | identifier                                        | value      |
         | ClinicalTrials.gov ID                             | Azerty1234 |
         | EUDRACT ID                                        | Querty5678 |
         | Universal Trial Number (UTN)                      | Wxcv9876   |
         | Japanese Trial Registry ID (JAPIC)                | POIU9631   |
         | Investigational New Drug Application (IND) Number | Zxcv2142   |
         | EU Trial Number                                   | Azerty2345 |
         | CID ID SIN Number                                 | Azerty3456 |
         | National Clinical Trial Number                    | Azerty5678 |
         | Japanese Trial Registry Number                    | Azerty6789 |
         | NMPA Number                                       | Azerty0123 |
         | EUDAMED number                                    | Azerty9999 |
         | Investigational Device Exemption Number           | Azerty1111 |

      Then The identifiers table is showing following data
         | identifier                                        | value      |
         | ClinicalTrials.gov ID                             | Azerty1234 |
         | EUDRACT ID                                        | Querty5678 |
         | Universal Trial Number (UTN)                      | Wxcv9876   |
         | Japanese Trial Registry ID (JAPIC)                | POIU9631   |
         | Investigational New Drug Application (IND) Number | Zxcv2142   |
         | EU Trial Number                                   | Azerty2345 |
         | CID ID SIN Number                                 | Azerty3456 |
         | National Clinical Trial Number                    | Azerty5678 |
         | Japanese Trial Registry Number                    | Azerty6789 |
         | NMPA Number                                       | Azerty0123 |
         | EUDAMED number                                    | Azerty9999 | 
         | Investigational Device Exemption Number           | Azerty1111 |


   Scenario: User must be able to select not applicable for Registry Identifiers
      Given The '/studies/Study_000001/registry_identifiers' page is opened
      When The not applicable is checked for all identifiers
         | identifier                                        |
         | ClinicalTrials.gov ID                             |
         | EUDRACT ID                                        |
         | Universal Trial Number (UTN)                      |
         | Japanese Trial Registry ID (JAPIC)                |
         | Investigational New Drug Application (IND) Number |
         | EU Trial Number                                   |
         | CID ID SIN Number                                 |
         | National Clinical Trial Number                    |
         | Japanese Trial Registry Number                    |
         | NMPA Number                                       |
         | EUDAMED number                                    |
         | Investigational Device Exemption Number           |

      Then The identifiers table is showing following data
         | identifier                                        | value          |
         | ClinicalTrials.gov ID                             | Not Applicable |
         | EUDRACT ID                                        | Not Applicable |
         | Universal Trial Number (UTN)                      | Not Applicable |
         | Japanese Trial Registry ID (JAPIC)                | Not Applicable |
         | Investigational New Drug Application (IND) Number | Not Applicable |
         | EU Trial Number                                   | Not Applicable |
         | CID ID SIN Number                                 | Not Applicable |
         | National Clinical Trial Number                    | Not Applicable |
         | Japanese Trial Registry Number                    | Not Applicable |
         | NMPA Number                                       | Not Applicable |
         | EUDAMED number                                    | Not Applicable |
         | Investigational Device Exemption Number           | Not Applicable |


   @manual_test
   Scenario: User must be able to read change history of output
      Given The '/studies/Study_000001/registry_identifiers' page is opened
      When The user opens version history
      Then The user is presented with version history of the output containing timestamp and username

   @manual_test
   Scenario: User must be able to read change history of selected element
      Given The '/studies/Study_000001/registry_identifiers' page is opened
      When The user clicks on History for particular element
      Then The user is presented with history of changes for that element
      And The history contains timestamps and usernames