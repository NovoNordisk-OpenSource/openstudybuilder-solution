@REQ_ID:1074260
Feature: Maintaining Study Activity Instances in OpenStudyBuilder API

    Background: Test user must be able to call the OpenStudyBuilder API and test data exist
        Given The test user can call the OpenStudyBuilder API

    Rule: As an API user,
        I want the system to ensure only valid activity instances can be added to a study,
        So that I get consistency between the Detailed SoA and the Operational SoA.

        Scenario Outline: Only activity instances linked to a study activity within a valid grouping can be added to the study
            When a study activity instance is added to a study using the POST or PATCH API endpoint '/studies/<uid>/study-activity-instances'
            Then the API must ensure only an activity instance can be added if it is related to a valid activity grouping for an existing study activity
       
        Examples:
            |TestFile                                                                 | TestID                                            |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_create_study_activity_instance       |

    Rule: As an API user,
        I want the system to classify the current state and needed actions for study activity instances,
        So that I get consistent and complete definition of the Operational SoA versus the Detailed SoA and activity definitions in the library.

        Scenario Outline: State/Actions for Study Activity Instances must be classified by the API as combination of activity selections, Boolean attributes, version and status of Activity Instances in the library
            When The API GET endpoint '/studies/<uid>/study-activity-instances' is called
            Then the response of Study Activity Instances must include classification of <State/Actions> information, <Colour highlight>, <Indicator icon> based on <Rule>
            Examples:
                | Indicator icon       | State/Action                                         | Colour highlight | Rule                                                                                                                         |
                |                      | Required                                             | Green            | Activity Instance is required_for_activity and currently selected for the Activity                                           |
                |                      | Defaulted                                            | Green            | Activity Instance is default_for_activity and currently selected for the Activity                                            |
                |                      | Suggestion                                           | Yellow           | Activity Instance is the only available instance within the grouping combination for related Activity and currently selected |
                | Red exclamation mark | Add missing selection                                | Red              | No Activity Instance has been selected for Activity related to data collection                                               |
                | Red exclamation mark | Add missing selection or add reason for deviation... | Red              | Required Activity Instance for Activity has not been selected                                                                |
                |                      | Add optional selection if relevant                   | Green            | Additional optional Activity Instances can be made as this Activity support multiple selections                              |
                | Red exclamation mark | Multiple selections, Remove selection                | Red              | Multiple Activity Instances has been selected for Activity requiring a single selection                                      |
                |                      | No data collection                                   | Green            | Activity is marked with 'No' for data collection and no Activity Instance can be related                                     |
                |                      | Requested Activity                                   | Yellow           | Activity is Requested so not yet any available Activity Instances                                                            |
                | Orange bell          | Use new available version                            | Yellow           | Activity Instance is available in a newer version than currently selected, and user has not selected to use old version      |
                | Grey bell            | Keep old version or use new available version        | Yellow           | Activity Instance is available in a newer version than currently selected, and user has selected to use old version          |
                | Orange bell          | Retired, change selection                            | Yellow           | Activity Instance is retired                                                                                                 |
                | Grey bell            | Retired, keep retired version                        | Yellow           | Activity Instance is retired but user has selected to keep reference to retired version                                      |
       
        Examples:
            |TestFile                                                                 | TestID                                                                                       |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_create_remove_study_activity_instance_when_study_activity_is_created_removed    |                                                         |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_study_activity_instances_states                                                 |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_delete_study_activity_instance                                                  |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_create_study_activity_instance                                                  |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_edit_study_activity_instance                                                    |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_study_activity_instance_header_endpoint                                         |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_study_activity_instance_audit_trails                                            |
       
        # Note, the process for Requested Activities nor Requested Activity Instances is not yet included in these rules
        # Note, later we should add rules for selection of legacy activity instances


    Rule: As an API user,
        I want the system to support download of study activity instances in .csv and Excel file formats,
        So that I can use the files for reviews and downstream integrations.

        Scenario Outline: Download of study activity instances in .csv and Excel file formats
            When the GET API endpoint '/studies/<uid>/study-activity-instances' is called to download study activity instances in <file-format>
            Then the API must return the following columns with one row for each study activity instances
                # Note in .csv file column header is without underscores in lower case, in Excel as specified.
                | column | header              |
                | 1      | Study number        |
                | 2      | Order               |
                | 3      | Library             |
                | 4      | SoA group           |
                | 5      | Activity group      |
                | 6      | Activity subgroup   |
                | 7      | Activity            |
                | 8      | Data Collection     |
                | 9      | Instance            |
                | 10     | Topic Code          |
                | 11     | SDTM domain         |
                | 12     | State/Actions       |
                | 13     | Details             |
                | 14     | Param code          |
                | 15     | Activity concept ID |
                | 16     | Instance concept ID |
                | 17     | Required            |
                | 17     | Default             |
                | 18     | Multiple selection  |
                | 20     | Legacy              |
                | 21     | Instance class      |
                | 22     | Test code           |
                | 23     | Test name           |
                | 24     | Unit dimension      |
                | 25     | Standard Unit       |
                | 26     | Specimen            |
                | 27     | Modified            |
                | 28     | Modified by         |
                Examples:
                | file-format |
                | .csv |
                | Exc el |
        
        Examples:
            |TestFile                                                                 | TestID                                                     |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_get_study_activity_instances_csv_xml_excel    |


    Rule: As an API user,
          I want the system to add required and defaulted study activity instances when a study activity is added,
          So that I get a simplified workflow when defining the Detailed and Operational SoA.

       Scenario Outline: Add required and defaulted study activity instances when a study activity is added
            When an activity is added to a study within a specific activity grouping
            Then the related activity instances marked as required or defaulted in the library within the specific grouping must be added to the study activity instances
       
        Examples:
            |TestFile                                                                 | TestID                                                                                       |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_create_remove_study_activity_instance_when_study_activity_is_created_removed    |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_create_study_activity_instance                                                  |

      Scenario Outline:
            When only one activity instance is related to a study activity within the grouping then this activity instance must be added to the study as a default
            And an activity is added to a study within a specific activity grouping
            And this study activity only is related to one activity instance within this activity grouping
            Then the related activity instances within the specific grouping must be added to the study activity instances
       
        Examples:
            |TestFile                                                                 | TestID                                            |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_study_activity_instances_states      |

    Rule: As an API user,
          I want the system to remove study activity instances when the related study activity is removed,
          So that I get consistency in the Detailed and Operational SoA.

        Scenario Outline: Remove study activity instances when a study activity is removed
            When an study activity is removed from a study within a specific activity grouping
            Then the related study activity instances must also be removed within the same specific grouping

        Examples:
            |TestFile                                                                 | TestID                                                                                       |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_create_remove_study_activity_instance_when_study_activity_is_created_removed    |
            |/tests/integration/api/study_selections/test_study_activity_instances.py | @TestID:test_delete_study_activity_instance                                                  |
