@REQ_ID:1070683
Feature: Manage ODM Vendor Attributes in OpenStudyBuilder API
    As an API user, I want to manage ODM Vendor Attributes through the OpenStudyBuilder API endpoints.

    Background: Test user must be able to call the OpenStudyBuilder API, and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get an empty list of ODM vendor attributes
        When the user calls the API endpoint 'odms/vendor-attributes'
        Then the response must include an empty list of ODM vendor attributes
        And the response status code must be 200
    Test Coverage:
        | TestFile                                                 | TestID                                                    |
        | /tests/integration/api/old/test_odm_vendor_attributes.py | @TestID: test_getting_empty_list_of_odm_vendor_attributes |

    Scenario: User must be able to create a new ODM vendor attribute with relation to an ODM vendor namespace
        When the user sends a request to create a new ODM vendor attribute with valid data
        Then the response status code must be 201
        And the response must include the newly created ODM vendor attribute
    Test Coverage:
        | TestFile                                                 | TestID                                                                                  |
        | /tests/integration/api/old/test_odm_vendor_attributes.py | @TestID: test_creating_a_new_odm_vendor_attribute_with_relation_to_odm_vendor_namespace |

    Scenario: User must be able to get a non-empty list of ODM vendor attributes
        When the user calls the API endpoint 'odms/vendor-attributes' get a non-empty list of ODM vendor attributes
        Then the response must include the list of ODM vendor attributes that were created
        And the response status code must be 200
    Test Coverage:
        | TestFile                                                 | TestID                                                        |
        | /tests/integration/api/old/test_odm_vendor_attributes.py | @TestID: test_getting_non_empty_list_of_odm_vendor_attributes |

    Scenario: User must be able to get a specific ODM vendor attribute
        When the user calls the API endpoint 'odms/vendor-attributes/' to get a specific ODM vendor attribute
        Then the response status code must be 200
        And the response must include the ODM vendor attribute
    Test Coverage:
        | TestFile                                                 | TestID                                                |
        | /tests/integration/api/old/test_odm_vendor_attributes.py | @TestID: test_getting_a_specific_odm_vendor_attribute |

    Scenario: User must be able to get possible header values of ODM vendor attributes
        When the user calls the API endpoint 'odms/vendor-attributes/headers?field_name=name'
        Then the response status code must be 200
        And the response must include the list ["nameOne"]
    Test Coverage:
        | TestFile                                                 | TestID                                                                |
        | /tests/integration/api/old/test_odm_vendor_attributes.py | @TestID: test_getting_possible_header_values_of_odm_vendor_attributes |

    Scenario: User must be able to update an existing ODM vendor attribute
        When the user sends a request to update an existing ODM vendor attribute
        Then the response status code must be 200
        And the response must reflect the updated ODM vendor attribute
    Test Coverage:
        | TestFile                                                 | TestID                                                  |
        | /tests/integration/api/old/test_odm_vendor_attributes.py | @TestID: test_updating_an_existing_odm_vendor_attribute |

    Scenario: User cannot create a new ODM vendor attribute with the same properties
        When the user sends a request to create a new ODM vendor attribute with the same properties
        Then the response status code must be 409
        And the response must include the message like "ODM Vendor Attribute already exists with UID (OdmVendorAttribute_000001)..."
    Test Coverage:
        | TestFile                                                          | TestID                                                                      |
        | /tests/integration/api/old/test_odm_vendor_attributes_negative.py | @TestID: test_cannot_create_a_new_odm_vendor_attribute_with_same_properties |

    Scenario: User cannot create a new ODM vendor attribute without an English description
        When the user sends a request to create an ODM vendor attribute without an English description
        Then the response status code must be 400
        And the response must include the message "A Translated Text with text_type Description and language English ('eng' or 'en') must be provided."
    Test Coverage:
        | TestFile                                                          | TestID                                                                                |
        | /tests/integration/api/old/test_odm_vendor_attributes_negative.py | @TestID: test_cannot_create_a_new_odm_vendor_attribute_without_an_english_description |

    Scenario: User receives an error for retrieving a non-existent ODM vendor attribute
        When the user calls the API endpoint 'odms/vendor-attributes/' for retrieving a non-existent ODM vendor attribute
        Then the response status code must be 404
        And the response must include the message like "OdmVendorAttributeAR with UID 'OdmVendorAttribute_000003' doesn't exist ..."
    Test Coverage:
        | TestFile                                                          | TestID                                                                       |
        | /tests/integration/api/old/test_odm_vendor_attributes_negative.py | @TestID: test_getting_error_for_retrieving_non_existent_odm_vendor_attribute |

    Scenario: User cannot inactivate an ODM vendor attribute that is in draft status
        When the user sends a request to inactivate the ODM vendor attribute that is in draft status
        Then the response status code must be 400
        And the response must include the message "Cannot retire draft version."
    Test Coverage:
        | TestFile                                                          | TestID                                                                          |
        | /tests/integration/api/old/test_odm_vendor_attributes_negative.py | @TestID: test_cannot_inactivate_an_odm_vendor_attribute_that_is_in_draft_status |

    Scenario: User cannot reactivate an ODM vendor attribute that is not retired
        When the user sends a request to reactivate the ODM vendor attribute that is not retired
        Then the response status code must be 400
        And the response must include the message "Only RETIRED version can be reactivated."
    Test Coverage:
        | TestFile                                                          | TestID                                                                      |
        | /tests/integration/api/old/test_odm_vendor_attributes_negative.py | @TestID: test_cannot_reactivate_an_odm_vendor_attribute_that_is_not_retired |