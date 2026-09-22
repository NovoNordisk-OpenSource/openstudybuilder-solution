@REQ_ID:1070683
Feature: Manage ODM Vendor Namespaces in OpenStudyBuilder API
    As an API user, I want to manage ODM Vendor Namespaces through the OpenStudyBuilder API endpoints.

    Background: Test user must be able to call the OpenStudyBuilder API, and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get an empty list of ODM vendor namespaces
        When the user calls the API endpoint 'odms/vendor-namespaces'
        Then the response must include an empty list of ODM vendor namespaces
        And the response status code must be 200
    Test Coverage:
        | TestFile                                                 | TestID                                                    |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_getting_empty_list_of_odm_vendor_namespaces |

    Scenario: User must be able to create a new ODM vendor namespace
        When the user sends a request to create a new ODM vendor namespace with valid data
        Then the response status code must be 201
        And the response must include the newly created ODM vendor namespace
    Test Coverage:
        | TestFile                                                 | TestID                                            |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_creating_a_new_odm_vendor_namespace |

    Scenario: User must be able to get a non-empty list of ODM vendor namespaces
        When the user calls the API endpoint 'odms/vendor-namespaces' to get a non-empty list of ODM vendor namespaces
        Then the response must include ODM vendor namespaces
        And the response status code must be 200
    Test Coverage:
        | TestFile                                                 | TestID                                                        |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_getting_non_empty_list_of_odm_vendor_namespaces |

    Scenario: User must be able to get a specific ODM vendor namespace
        When the user calls the API endpoint 'odms/vendor-namespaces/' to get a specific ODM vendor namespace
        Then the response must include the details of ODM vendor namespace
        And the response status code must be 200
    Test Coverage:
        | TestFile                                                 | TestID                                                |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_getting_a_specific_odm_vendor_namespace |

    Scenario: User must be able to update an existing ODM vendor namespace
        When the user sends a request to update an existing ODM vendor namespace
        Then the response status code must be 200
        And the response must reflect the updated details of the ODM vendor namespace
    Test Coverage:
        | TestFile                                                 | TestID                                                  |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_updating_an_existing_odm_vendor_namespace |

    Scenario: User must be able to get the versions of a specific ODM vendor namespace
        When the user calls the API endpoint 'odms/vendor-namespaces/uid/versions'
        Then the response must include the versions of the ODM vendor namespace
        And the response status code must be 200
    Test Coverage:
        | TestFile                                                 | TestID                                                            |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_getting_versions_of_a_specific_odm_vendor_namespace |

    Scenario: User must be able to approve an ODM vendor namespace
        When the user sends a request to approve the ODM vendor namespace
        Then the response status code must be 201
        And the response must include the approved ODM vendor namespace
    Test Coverage:
        | TestFile                                                 | TestID                                          |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_approving_an_odm_vendor_namespace |

    Scenario: User must be able to inactivate a specific ODM vendor namespace
        When the user sends a request to inactivate the ODM vendor namespace
        Then the response status code must be 200
        And the response must reflect the inactivated details of the ODM vendor namespace
    Test Coverage:
        | TestFile                                                 | TestID                                                     |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_inactivating_a_specific_odm_vendor_namespace |

    Scenario: User must be able to reactivate a specific ODM vendor namespace
        When the user sends a request to reactivate the ODM vendor namespace
        Then the response status code must be 200
        And the response must reflect the reactivated details of the ODM vendor namespace
    Test Coverage:
        | TestFile                                                 | TestID                                                     |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_reactivating_a_specific_odm_vendor_namespace |

    Scenario: User must be able to create a new version of an ODM vendor namespace
        When the user sends a request to create a new version for the ODM vendor namespace
        Then the response status code must be 201
        And the response must include the details of the new version
    Test Coverage:
        | TestFile                                                 | TestID                                                    |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_creating_a_new_odm_vendor_namespace_version |

    Scenario: User must be able to delete a specific ODM vendor namespace
        When the user sends a request to delete the ODM vendor namespace
        Then the response status code must be 204
    Test Coverage:
        | TestFile                                                 | TestID                                                 |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_deleting_a_specific_odm_vendor_namespace |

    Scenario: User must receive an error for retrieving a non-existent ODM vendor namespace
        When the user calls the API endpoint 'odms/vendor-namespaces/' for retrieving a non-existent ODM vendor namespace
        Then the response status code must be 404
        And the response must indicate the ODM vendor namespace does not exist
    Test Coverage:
        | TestFile                                                 | TestID                                                                       |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_getting_error_for_retrieving_non_existent_odm_vendor_namespace |

    Scenario: User must not be able to create a new ODM vendor namespace with existing name, prefix, and URL
        When the user sends a request to create a new ODM vendor namespace with existing name, prefix, and URL
        Then the response status code must be 409
        And the response must indicate that the vendor namespace already exists
    Test Coverage:
        | TestFile                                                 | TestID                                                                                   |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_cannot_create_a_new_odm_vendor_namespace_with_existing_name_prefix_and_url |

    Scenario: User must not be able to inactivate an ODM vendor namespace that is in draft status
        When the user sends a request to inactivate the ODM vendor namespace that is in draft status
        Then the response status code must be 400
        And the response must indicate that draft versions cannot be retired
    Test Coverage:
        | TestFile                                                 | TestID                                                                          |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_cannot_inactivate_an_odm_vendor_namespace_that_is_in_draft_status |

    Scenario: User must not be able to reactivate an ODM vendor namespace that is not retired
        When the user sends a request to reactivate the ODM vendor namespace that is not retired
        Then the response status code must be 400
        And the response must indicate that only retired versions can be reactivated
    Test Coverage:
        | TestFile                                                 | TestID                                                                      |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_cannot_reactivate_an_odm_vendor_namespace_that_is_not_retired |

    Scenario: User must be able to create an ODM vendor element with a relation to the ODM vendor namespace
        When the user sends a request to create a new ODM vendor element with a relation to the ODM vendor namespace
        Then the response status code must be 201
        And the response must include the newly created ODM vendor element
    Test Coverage:
        | TestFile                                                 | TestID                                                                            |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_create_odm_vendor_element_with_relation_to_the_odm_vendor_namespace |

    Scenario: User must not be able to delete an ODM vendor namespace that is being used
        When the user sends a request to delete the ODM vendor namespace that is being used
        Then the response status code must be 400
        And the response must indicate that the ODM vendor namespace is in use
    Test Coverage:
        | TestFile                                                 | TestID                                                                 |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_cannot_delete_an_odm_vendor_namespace_that_is_being_used |

    Scenario: User must not be able to delete a non-existent ODM vendor namespace
        When the user sends a request to delete a non-existent ODM vendor namespace
        Then the response status code must be 404
        And the response must indicate that the ODM vendor namespace does not exist
    Test Coverage:
        | TestFile                                                 | TestID                                                        |
        | /tests/integration/api/old/test_odm_vendor_namespaces.py | @TestID: test_cannot_delete_non_existent_odm_vendor_namespace |