@REQ_ID:1070683
Feature: Manage ODM Vendor Elements in OpenStudyBuilder API
    As an API user, I want to manage ODM Vendor Elements through the OpenStudyBuilder API endpoints.

    Background: Test user must be able to call the OpenStudyBuilder API, and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get an empty list of ODM vendor elements
        When the user calls the API endpoint 'odms/vendor-elements'
        Then the response must include an empty list of ODM vendor elements
        And the response status code must be 200
    Test Coverage:
        | TestFile                                               | TestID                                                  |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_getting_empty_list_of_odm_vendor_elements |

    Scenario: User must be able to create a new ODM vendor element
        When the user sends a request to create a new ODM vendor element with valid data
        Then the response status code must be 201
        And the response must include the newly created ODM vendor element with uid 'OdmVendorElement_000001'
    Test Coverage:
        | TestFile                                               | TestID                                          |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_creating_a_new_odm_vendor_element |

    Scenario: User must be able to get a non-empty list of ODM vendor elements
        When the user calls the API endpoint 'odms/vendor-elements' to get a non-empty list of ODM vendor elements
        Then the response must include ODM vendor elements
        And the response status code must be 200
    Test Coverage:
        | TestFile                                               | TestID                                                      |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_getting_non_empty_list_of_odm_vendor_elements |

    Scenario: User must be able to get a specific ODM vendor element
        When the user calls the API endpoint 'odms/vendor-elements/' to get a specific ODM vendor element
        Then the response must include the details of ODM vendor element
        And the response status code must be 200
    Test Coverage:
        | TestFile                                               | TestID                                              |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_getting_a_specific_odm_vendor_element |

    Scenario: User must be able to update an existing ODM vendor element
        When the user sends a request to update an existing ODM vendor element
        Then the response status code must be 200
        And the response must reflect the updated details of the ODM vendor element
    Test Coverage:
        | TestFile                                               | TestID                                                |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_updating_an_existing_odm_vendor_element |

    Scenario: User must be able to delete a specific ODM vendor element
        When the user sends a request to delete the ODM vendor element
        Then the response status code must be 204
    Test Coverage:
        | TestFile                                               | TestID                                               |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_deleting_a_specific_odm_vendor_element |

    Scenario: User must receive an error for retrieving a non-existent ODM vendor element
        When the user calls the API endpoint 'odms/vendor-elements/' for retrieving a non-existent ODM vendor element
        Then the response status code must be 404
        And the response must indicate the ODM vendor element does not exist
    Test Coverage:
        | TestFile                                               | TestID                                                                     |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_getting_error_for_retrieving_non_existent_odm_vendor_element |

    Scenario: User must not be able to create an ODM vendor element without providing compatible types
        When the user sends a request to create an ODM vendor element without compatible types
        Then the response status code must be 400
        And the response must indicate a validation error for compatible types
    Test Coverage:
        | TestFile                                               | TestID                                                                                  |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_cannot_create_a_new_odm_vendor_element_without_providing_compatible_types |

    Scenario: User must not be able to create a new ODM vendor element if the ODM vendor namespace doesn't exist
        When the user sends a request to create a new ODM vendor element with an incorrect namespace uid
        Then the response status code must be 400
        And the response must indicate a business logic error
    Test Coverage:
        | TestFile                                               | TestID                                                                                    |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_cannot_create_a_new_odm_vendor_element_if_odm_vendor_namespace_doesnt_exist |

    Scenario: User must not be able to create a new ODM vendor element with an existing name
        When the user sends a request to create a new ODM vendor element with an existing name
        Then the response status code must be 409
        And the response must indicate the element already exists
    Test Coverage:
        | TestFile                                               | TestID                                                                  |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_cannot_create_a_new_odm_vendor_element_with_existing_name |

    Scenario: User must not be able to inactivate an ODM vendor element that is in draft status
        When the user sends a request to delete an active ODM vendor element that is in draft status
        Then the response status code must be 400
        And the response must indicate that draft versions cannot be retired
    Test Coverage:
        | TestFile                                               | TestID                                                                        |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_cannot_inactivate_an_odm_vendor_element_that_is_in_draft_status |

    Scenario: User must not be able to reactivate an ODM vendor element that is not retired
        When the user sends a request to reactivate the ODM vendor element that is not retired
        Then the response status code must be 400
        And the response must indicate that only retired versions can be reactivated
    Test Coverage:
        | TestFile                                               | TestID                                                                    |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_cannot_reactivate_an_odm_vendor_element_that_is_not_retired |

    Scenario: User must be able to create a new ODM vendor attribute with a relation to an ODM vendor element
        When the user sends a request to create a new ODM vendor attribute with a relation to an ODM vendor element
        Then the response status code must be 201
        And the response must include the newly created ODM vendor attribute
    Test Coverage:
        | TestFile                                               | TestID                                                                              |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_create_a_new_odm_vendor_attribute_with_relation_to_odm_vendor_element |

    Scenario: User must be able to get the active relationships of a specific ODM vendor element
        When the user calls the API endpoint 'odms/vendor-elements/uid/relationships'
        Then the response must include the active relationships of the ODM vendor element
        And the response status code must be 200
    Test Coverage:
        | TestFile                                               | TestID                                                                            |
        | /tests/integration/api/old/test_odm_vendor_elements.py | @TestID: test_getting_uids_of_a_specific_odm_vendor_elements_active_relationships |