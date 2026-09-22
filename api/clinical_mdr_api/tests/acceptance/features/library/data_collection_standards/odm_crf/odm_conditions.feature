@REQ_ID:1070683
Feature: Manage ODM Conditions in OpenStudyBuilder API
    As an API user, I want to manage ODM Conditions through the OpenStudyBuilder API endpoints.
    
    Background: Test user must be able to call the OpenStudyBuilder API, and the test data exists
        Given The test user can call the OpenStudyBuilder API
        
    Scenario: User must be able to get an empty list of ODM conditions
        When the user calls the API endpoint 'odms/conditions'
        Then the response must include an empty list of ODM conditions
        And the response status code must be 200
    Test Coverage:
        | TestFile                                          | TestID                                             |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_getting_empty_list_of_odm_conditions |

    Scenario: User must be able to create a new ODM condition
        When the user sends a request to create a new ODM condition with valid data
        Then the response status code must be 201
        And the response must include the newly created ODM condition
    Test Coverage:
        | TestFile                                          | TestID                                     |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_creating_a_new_odm_condition |

    Scenario: User must be able to get a list of ODM conditions
        When the user calls the API endpoint 'odms/conditions'
        Then the response must include the list of ODM conditions
        And the response status code must be 200
    Test Coverage:
        | TestFile                                          | TestID                                                 |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_getting_non_empty_list_of_odm_conditions |

    Scenario: User must be able to get a specific ODM condition
        When the user calls the API endpoint 'odms/conditions/'
        Then the response status code must be 200
        And the response must include the ODM condition
    Test Coverage:
        | TestFile                                          | TestID                                         |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_getting_a_specific_odm_condition |

    Scenario: User must be able to get possible header values of ODM conditions
        When the user calls the API endpoint 'odms/conditions/headers?field_name=name'
        Then the response status code must be 200
        And the response must include the list ["name1"]
    Test Coverage:
        | TestFile                                          | TestID                                                         |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_getting_possible_header_values_of_odm_conditions |

    Scenario: User must be able to update an existing ODM condition
        When the user sends a request to update an existing ODM condition
        Then the response status code must be 200
        And the response must reflect the updated ODM condition
    Test Coverage:
        | TestFile                                          | TestID                                           |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_updating_an_existing_odm_condition |

    Scenario: User must be able to approve an ODM condition
        When the user sends a request to approve the ODM condition
        Then the response status code must be 201
        And the response must indicate the ODM condition has been approved
    Test Coverage:
        | TestFile                                          | TestID                                   |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_approving_an_odm_condition |

    Scenario: User must be able to inactivate a specific ODM condition
        When the user sends a request to inactivate the ODM condition
        Then the response status code must be 200
        And the response must indicate the ODM condition has been inactivated
    Test Coverage:
        | TestFile                                          | TestID                                              |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_inactivating_a_specific_odm_condition |

    Scenario: User must be able to reactivate a specific ODM condition
        When the user sends a request to reactivate the ODM condition
        Then the response status code must be 200
        And the response must indicate the ODM condition has been reactivated
    Test Coverage:
        | TestFile                                          | TestID                                              |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_reactivating_a_specific_odm_condition |

    Scenario: User must be able to create a new version of an existing ODM condition
        When the user sends a request to create a new version for the ODM condition
        Then the response status code must be 201
        And the response must include the new version of the ODM condition
    Test Coverage:
        | TestFile                                          | TestID                                             |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_creating_a_new_odm_condition_version |

    Scenario: User must be able to delete a specific ODM condition
        When the user sends a request to delete the ODM condition
        Then the response status code must be 204
    Test Coverage:
        | TestFile                                          | TestID                                          |
        | /tests/integration/api/old/test_odm_conditions.py | @TestID: test_deleting_a_specific_odm_condition |

    Scenario: User cannot create a new ODM condition with the same properties
        When the user sends a request to create a new ODM condition with same properties as an existing one
        Then the response status code must be 409
        And the response must include the message "ODM Condition already exists ..."
    Test Coverage:
        | TestFile                                                   | TestID                                                               |
        | /tests/integration/api/old/test_odm_conditions_negative.py | @TestID: test_cannot_create_a_new_odm_condition_with_same_properties |

    Scenario: User cannot create a new ODM condition without an English description
        When the user sends a request to create a new ODM condition without an Egnlish description
        Then the response status code must be 400
        And the response must include the message "A Translated Text with text_type Description and language English ('eng' or 'en') must be provided."
    Test Coverage:
        | TestFile                                                   | TestID                                                                         |
        | /tests/integration/api/old/test_odm_conditions_negative.py | @TestID: test_cannot_create_a_new_odm_condition_without_an_english_description |

    Scenario: User receives an error for retrieving a non-existent ODM condition
        When the user calls the API endpoint 'odms/conditions/' for retrieving a non-existent ODM condition
        Then the response status code must be 404
        And the response must include the message like "OdmConditionAR with UID 'OdmCondition_000002' doesn't exist or there's no version with requested status or version number."
    Test Coverage:
        | TestFile                                                   | TestID                                                                |
        | /tests/integration/api/old/test_odm_conditions_negative.py | @TestID: test_getting_error_for_retrieving_non_existent_odm_condition |

    Scenario: User cannot inactivate an ODM condition that is in draft status
        When the user sends a request to inactivate the ODM condition with draft status
        Then the response status code must be 400
        And the response must include the message "Cannot retire draft version."
    Test Coverage:
        | TestFile                                                   | TestID                                                                   |
        | /tests/integration/api/old/test_odm_conditions_negative.py | @TestID: test_cannot_inactivate_an_odm_condition_that_is_in_draft_status |

    Scenario: User cannot reactivate an ODM condition that is not retired
        When the user sends a request to reactivate the ODM condition that is
        Then the response status code must be 400
        And the response must include the message "Only RETIRED version can be reactivated."
    Test Coverage:
        | TestFile                                                   | TestID                                                               |
        | /tests/integration/api/old/test_odm_conditions_negative.py | @TestID: test_cannot_reactivate_an_odm_condition_that_is_not_retired |