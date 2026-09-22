@REQ_ID:1070683
Feature: Manage ODM Methods in OpenStudyBuilder API
    As an API user, I want to manage ODM Methods through the OpenStudyBuilder API endpoints.

    Background: Test user must be able to call the OpenStudyBuilder API, and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get an empty list of ODM methods
        When the user calls the API endpoint 'odms/methods'
        Then the response must include an empty list of ODM methods
        And the response status code must be 200
    Test Coverage:
        | TestFile                                         | TestID                                          |
        | /tests/integration/api/old/test_odm_methods.py   | @TestID: test_getting_empty_list_of_odm_methods |

    Scenario: User must be able to create a new ODM method
        When the user sends a request to create a new ODM method with valid data
        Then the response status code must be 201
        And the response must include the newly created ODM method
    Test Coverage:
        | TestFile                                         | TestID                                  |
        | /tests/integration/api/old/test_odm_methods.py   | @TestID: test_creating_a_new_odm_method |

    Scenario: User must be able to get a non-empty list of ODM methods
        When the user calls the API endpoint 'odms/methods'
        Then the response must include the list of ODM methods that were created
        And the response status code must be 200
    Test Coverage:
        | TestFile                                         | TestID                                              |
        | /tests/integration/api/old/test_odm_methods.py   | @TestID: test_getting_non_empty_list_of_odm_methods |

    Scenario: User must be able to get a specific ODM method
        When the user calls the API endpoint 'odms/methods/' to get a specific ODM method
        Then the response status code must be 200
        And the response must include the ODM method
    Test Coverage:
        | TestFile                                         | TestID                                      |
        | /tests/integration/api/old/test_odm_methods.py   | @TestID: test_getting_a_specific_odm_method |

    Scenario: User must be able to get possible header values of ODM methods
        When the user calls the API endpoint 'odms/methods/headers?field_name=name'
        Then the response status code must be 200
        And the response must include the list ["name1"]
    Test Coverage:
        | TestFile                                         | TestID                                                      |
        | /tests/integration/api/old/test_odm_methods.py   | @TestID: test_getting_possible_header_values_of_odm_methods |

    Scenario: User must be able to update an existing ODM method
        When the user sends a request to update an existing ODM method
        Then the response status code must be 200
        And the response must reflect the updated ODM method
    Test Coverage:
        | TestFile                                         | TestID                                        |
        | /tests/integration/api/old/test_odm_methods.py   | @TestID: test_updating_an_existing_odm_method |

    Scenario: User cannot create a new ODM method with the same properties
        When the user sends a request to create a new ODM method with the same properties
        Then the response status code must be 409
        And the response must include the message like "ODM Method already exists with UID (OdmMethod_000001)..."
    Test Coverage:
        | TestFile                                                | TestID                                                            |
        | /tests/integration/api/old/test_odm_methods_negative.py | @TestID: test_cannot_create_a_new_odm_method_with_same_properties |

    Scenario: User cannot create a new ODM method without an English description
        When the user sends a request to create an ODM method without an English description
        Then the response status code must be 400
        And the response must include the message "A Translated Text with text_type Description and language English ('eng' or 'en') must be provided."
    Test Coverage:
        | TestFile                                                | TestID                                                                      |
        | /tests/integration/api/old/test_odm_methods_negative.py | @TestID: test_cannot_create_a_new_odm_method_without_an_english_description |

    Scenario: User receives an error for retrieving a non-existent ODM method
        When the user calls the API endpoint 'odms/methods/' for retrieving a non-existent ODM method
        Then the response status code must be 404
        And the response must include the message like "OdmMethodAR with UID 'OdmMethod_000002' doesn't exist ..."
    Test Coverage:
        | TestFile                                                | TestID                                                             |
        | /tests/integration/api/old/test_odm_methods_negative.py | @TestID: test_getting_error_for_retrieving_non_existent_odm_method |

    Scenario: User cannot inactivate an ODM method that is in draft status
        When the user sends a request to inactivate the ODM method that is in draft status
        Then the response status code must be 400
        And the response must include the message "Cannot retire draft version."
    Test Coverage:
        | TestFile                                                | TestID                                                                |
        | /tests/integration/api/old/test_odm_methods_negative.py | @TestID: test_cannot_inactivate_an_odm_method_that_is_in_draft_status |

    Scenario: User cannot reactivate an ODM method that is not retired
        When the user sends a request to reactivate the ODM method that is not retired
        Then the response status code must be 400
        And the response must include the message "Only RETIRED version can be reactivated."
    Test Coverage:
        | TestFile                                                | TestID                                                            |
        | /tests/integration/api/old/test_odm_methods_negative.py | @TestID: test_cannot_reactivate_an_odm_method_that_is_not_retired |