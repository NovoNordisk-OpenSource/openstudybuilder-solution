@REQ_ID:1975905

Feature: Manage Library Concept Activity Instances in OpenStudyBuilder API 

    As a API user, I want to manage the activity instance in the Concepts Library API endpoints

    Background: Test user must be able to call the OpenStudyBuilder API and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get activity instance details
        When the user requests to get the details of an activity instance with a specific UID
        Then the response should include the following attributes for the activity instance:
            | Library                       |
            | Activity instance class       |
            | Activity                      |
            | Activity Instance             |
            | Definition                    |
            | NCI Concept ID                |
            | NCI Concept Name              |
            | Research Lab                  |
            | Molecular Weight              |
            | Topic code                    |
            | ADaM parameter code           |
            | Required for activity         |
            | Default selected for activity |
            | Data sharing                  |
            | Legacy usage                  |
            | Modified                      |
            | Modified by                   |
            | Status                        |
            | Version                       |

    Test Coverage:
        |TestFile                                                              | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activity_instances.py | @TestID: test_get_activity_instance                   |

    Scenario: Create activity instance when all relevant data is provided
        Given The activity was already created
        And The library name is provided
        And The Activity Group uid is provided 
        And The Activity Subgroup uid is provided
        And The Activity Instance Class uid is provided
        Then The Activity Instance is created successfully

    Test Coverage:
        |TestFile                                                              | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activity_instances.py | @TestID: test_post_activity_instance                  |    

    
    Scenario: The activity instance must not be created when activity is not provided
        Given The activity was not already created
        And The library name is provided
        And The Activity Group uid is provided 
        And The Activity Subgroup uid is provided
        And The Activity Instance Class uid is provided
        Then The Activity Instance is not created successfully

    Test Coverage:
        |TestFile                                                              | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activity_instances.py | @TestID: to be implemented                            | 

    Scenario: The activity instance must not be created when activity group is not provided
        Given The activity was already created
        And The library name is provided
        And The Activity Group uid is not provided 
        And The Activity Subgroup uid is provided
        And The Activity Instance Class uid is provided
        Then The Activity Instance is not created successfully

    Test Coverage:
        |TestFile                                                              | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activity_instances.py | @TestID: to be implemented                            | 

    Scenario: The activity instance must not be created when activity subgroup is not provided
        Given The activity was already created
        And The library name is provided
        And The Activity Group uid is provided 
        And The Activity Subgroup uid is not provided
        And The Activity Instance Class uid is provided
        Then The Activity Instance is not created successfully     

    Test Coverage:
        |TestFile                                                              | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activity_instances.py | @TestID: to be implemented                            | 

    Scenario: The activity instance must not be created when Activity Instance Class is not provided
        Given The activity was already created
        And The library name is provided
        And The Activity Group uid is provided 
        And The Activity Subgroup uid is not provided
        And The Activity Instance Class uid is not provided
        Then The Activity Instance is not created successfully  

    Test Coverage:
        |TestFile                                                              | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activity_instances.py | @TestID: to be implemented                            |     
     
    Scenario: An activity instance with the same name must not be created more than once
        Given The activity was already created
        And Complete activity instance definition is provided
        And Same name for activity instance was provided as an existing one
        Then API refuses the request

    Test Coverage:
        |TestFile                                                              | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activity_instances.py | @TestID: to be implemented                            | 

    Scenario: An activity instance must not be created when there is uid mismatch
        Given The activity was already created
        And The Activity group uid is provided for Activity subgroup uid
        And The activity subgroup uid is provided for activity group uid
        Then API refuses the request

    Test Coverage:
        |TestFile                                                              | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activity_instances.py | @TestID: to be implemented                            | 

    Scenario: An activity instance must not be created when activity group and activity subgroup combination does not existing
        Given The activity was already created
        And The activity group uid is provided
        And The activity subgroup uid is provided
        And The activity group uid and activity subgroup uid are not in valid combination
        Then API refuses the request

    Test Coverage:
        |TestFile                                                              | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activity_instances.py | @TestID: to be implemented                            | 

    Scenario: An activity instance must not be created when both standard unit and categorical response list are provided
        Given The activity was already created
        And Complete activity instance definition is provided
        And Unit dimension and Standard Unit are provided
        And Categorical response list is provided
        Then API refuses the request

    Test Coverage:
        |TestFile                                                              | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activity_instances.py | @TestID: to be implemented                            | 

    Scenario: An activity instance created as numeric finding activity instance class must have unit dimension and standard unit
        Given The activity was already created
        And A valid activity group and activity subgroup combination was provided
        And Unit dimension and standard unit are provided
        Then The activity instance is created successfully

    Scenario: An activity instance created as numeric finding activity instance class must not have unit dimension and standard unit empty
        Given The activity was already created
        And A valid activity group and activity subgroup combination was provided
        And Unit dimension and standard unit are not provided
        Then API refuses the request

    Scenario: An activity instance created as categoric finding activity instance class must have categorical response list
        Given The activity was already created
        And A valid activity group and activity subgroup combination was provided
        And Categorical response list is provided
        Then The activity instance is created successfully                

    Scenario: An activity instance created as categoric finding activity instance class must not have categorical response list empty
        Given The activity was already created
        And A valid activity group and activity subgroup combination was provided
        And Categorical response list is not provided
        Then API refuses the request

    Scenario: User must be able to edit an activity instance
        When the user attempts to edit an activity instance with correct values
        Then The activity instance is updated with new values successfully

    Test Coverage:
        |TestFile                                                      | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_edit_activity_instance                  |


    # API test for CRF ODM - API development part of Wizard stepper feature 
    Scenario: User must be able to create an activity instance with relationships to ODM elements (CRF)
        When the user creates an activity instance with correct uids for ODM form, ODM group and ODM item
        Then The activity instance is created successfully

    Test Coverage:
        |TestFile                                                      | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_post_activity_instance                  |

    Scenario: User must be able to edit an activity instance with relationships to ODM elements (CRF)
        When the user edits an activity instance with correct uids for ODM form, ODM group and ODM item
        Then The activity instance is updated with ODM relationships successfully

    Test Coverage:
        |TestFile                                                      | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_edit_activity_instance                  |

    Scenario: User must be able to retrive an activity instance including ODM elements relationships (CRF)
        When the user retrieves an activity instance with correct uid for ODM form, ODM group and ODM item
        Then The activity instance is retrieved successfully including the correct relationships to ODM form, ODM group and ODM item

    Test Coverage:
        |TestFile                                                      | TestID                                                |
        |/tests/integration/api/biomedical_concepts/test_activities.py | @TestID: test_get_activity_instance                   |