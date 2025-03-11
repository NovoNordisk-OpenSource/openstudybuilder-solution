@REQ_ID:1741028
Feature: Studies - Browse released or locked study definitions

        # Initially the E2E test will cover one study field for each relevant sub section in the menu.
        # Later the test can be extended to cover a study field on every relevant page tab.

        Background: User must be logged in
                Given The user is logged in

        Rule: User must be able to browse the locked or released study definition data independent of the latest draft version.

                Scenario Outline: User must be able to browse the latest study definition content when the study status is Draft
                        Given The CDISC DEV-1111 study is selected
                        When The '<page>' for '<study field>' is selected
                        Then The '<value>' is displayed

                        Examples:
                                | page                                    | study field           | value                              |
                                | study_title                             | Study Title           | Title for new draft                |
                                | registry_identifiers                    | ClinicalTrials.gov ID | XX-new-draft                       |
                                | study_properties/type                   | Study Type            | Observational                      |
                                | study_structure/arms                    | Arm name              | Arm for new draft                  |
                                | population                              | Therapeutic area      | Diabetes mellitus                  |
                                | selection_criteria/Inclusion%20Criteria | Inclusion Criteria    | Criteria for new draft             |
                                | study_purpose/objectives                | Objective             | Objective for new draft            |
                                # | activities/list                         | Activity              | Activity Placeholder for new draft |


                Scenario Outline: User must be able to browse the locked study definition content when the study previously has been locked
                        Given The CDISC DEV-1111 study is selected
                        And The Study Status page in Manage Study is accessed
                        And The test study definition in status Locked and version 1 is selected
                        When The '<page>' for '<study field>' is selected
                        Then The '<value>' is displayed

                        Examples:
                                | page                                    | study field           | value                        |
                                | study_title                             | Study Title           | Title version 1              |
                                | registry_identifiers                    | ClinicalTrials.gov ID | XX-v1                        |
                                | study_properties/type                   | Study Type            | Expanded Access              |
                                | study_structure/arms                    | Arm name              | Arm v1                       |
                                | population                              | Therapeutic area      | Nonalcoholic steatohepatitis |
                                | selection_criteria/Inclusion%20Criteria | Inclusion Criteria    | Criteria for v1              |
                                | study_purpose/objectives                | Objective             | Objective for v1             |
                                # | activities/list                         | Activity              | Activity Placeholder for v1  |


                Scenario Outline: User must be able to browse the released study definition content when the study previously has been released
                        Given The CDISC DEV-1111 study is selected
                        And The Study Status page in Manage Study is accessed
                        And The test study definition in status Released and version 1.1 is selected
                        When The '<page>' for '<study field>' is selected
                        Then The '<value>' is displayed

                        Examples:
                                | page                                    | study field           | value                         |
                                | study_title                             | Study Title           | Title version 1.1             |
                                | registry_identifiers                    | ClinicalTrials.gov ID | XX-v1.1                       |
                                | study_properties/type                   | Study Type            | Interventional                |
                                | study_structure/arms                    | Arm name              | Arm v1.1                      |
                                | population                              | Therapeutic area      | Type 1 Diabetes mellitus      |
                                | selection_criteria/Inclusion%20Criteria | Inclusion Criteria    | Criteria for v1.1             |
                                | study_purpose/objectives                | Objective             | Objective for v1.1            |
                                # | activities/list                         | Activity              | Activity Placeholder for v1.1 |