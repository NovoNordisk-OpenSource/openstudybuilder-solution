@REQ_ID:1070683
Feature: Manage ODM Forms in OpenStudyBuilder API
    As an API user, I want to manage ODM Forms through the OpenStudyBuilder API endpoints.

    Background: Test user must be able to call the OpenStudyBuilder API, and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get an empty list of ODM forms
        When the user calls the API endpoint 'odms/forms'
        Then the response must include an empty list of ODM forms
        And the response status code must be 200
    Test Coverage:
        | TestFile                                       | TestID                                        |
        | /tests/integration/api/old/test_odm_forms.py   | @TestID: test_getting_empty_list_of_odm_forms |

    Scenario: User must be able to create a new ODM form
        When the user sends a request to create a new ODM form with the valid data
        Then the response status code must be 201
        And the response must include the newly created ODM form with correct data
    Test Coverage:
        | TestFile                                       | TestID                                |
        | /tests/integration/api/old/test_odm_forms.py   | @TestID: test_creating_a_new_odm_form |

    Scenario: User must be able to get a list of ODM forms
        When the user calls the API endpoint 'odms/forms'
        Then the response must include the list of ODM forms
        And the response status code must be 200
    Test Coverage:
        | TestFile                                       | TestID                                            |
        | /tests/integration/api/old/test_odm_forms.py   | @TestID: test_getting_non_empty_list_of_odm_forms |

    Scenario: User must be able to get a specific ODM form
        When the user calls the API endpoint 'odms/forms/' to get a specific ODM form
        Then the response status code must be 200
        And the response must include the ODM form
    Test Coverage:
        | TestFile                                          | TestID                                    |
        | /tests/integration/api/old/test_odm_forms.py      | @TestID: test_getting_a_specific_odm_form |

    Scenario: User must be able to get possible header values of ODM forms
        When the user calls the API endpoint 'odms/forms/headers?field_name=name'
        Then the response status code must be 200
        And the response must include the list ["name1"]
    Test Coverage:
        | TestFile                                          | TestID                                                    |
        | /tests/integration/api/old/test_odm_forms.py      | @TestID: test_getting_possible_header_values_of_odm_forms |

    Scenario: User must be able to update an existing ODM form
        When the user sends a request to update the existing ODM form with valid data
        Then the response status code must be 200
        And the response must reflect the updated ODM form
    Test Coverage:
        | TestFile                                          | TestID                                      |
        | /tests/integration/api/old/test_odm_forms.py      | @TestID: test_updating_an_existing_odm_form |

    Scenario: User must be able to approve an ODM form
        When the user sends a request to approve the ODM form
        Then the response status code must be 201
        And the response must indicate the ODM form has been approved
    Test Coverage:
        | TestFile                                          | TestID                              |
        | /tests/integration/api/old/test_odm_forms.py      | @TestID: test_approving_an_odm_form |

    Scenario: User must be able to inactivate a specific ODM form
        When the user sends a request to inactivate the ODM form
        Then the response status code must be 200
        And the response must indicate the ODM form has been inactivated
    Test Coverage:
        | TestFile                                          | TestID                                         |
        | /tests/integration/api/old/test_odm_forms.py      | @TestID: test_inactivating_a_specific_odm_form |

    Scenario: User must be able to reactivate a specific ODM form
        When the user sends a request to reactivate the ODM form
        Then the response status code must be 200
        And the response must indicate the ODM form has been reactivated
    Test Coverage:
        | TestFile                                          | TestID                                         |
        | /tests/integration/api/old/test_odm_forms.py      | @TestID: test_reactivating_a_specific_odm_form |

    Scenario: User must be able to create a new version of an existing ODM form
        When the user sends a request to create a new version for an existing ODM form
        Then the response status code must be 201
        And the response must include the new version of the ODM form
    Test Coverage:
        | TestFile                                          | TestID                                        |
        | /tests/integration/api/old/test_odm_forms.py      | @TestID: test_creating_a_new_odm_form_version |

    Scenario: User cannot create a new ODM form with the same properties
        When the user sends a request to create a new ODM form with the same properties as an existing ODM form
        Then the response status code must be 409
        And the response must include the message "ODM Form already exists ..."
    Test Coverage:
        | TestFile                                              | TestID                                                          |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_create_a_new_odm_form_with_same_properties |

    Scenario: User cannot create a new ODM form without an English description
        When the user sends a request to create a new ODM form without an English description
        Then the response status code must be 400
        And the response must include the message "A Translated Text with text_type Description and language English ('eng' or 'en') must be provided."
    Test Coverage:
        | TestFile                                               | TestID                                                                    |
        | /tests/integration/api/old/test_odm_forms_negative.py  | @TestID: test_cannot_create_a_new_odm_form_without_an_english_description |

    Scenario: User receives an error for retrieving a non-existent ODM form
        When the user calls the API endpoint 'odms/forms/' for retrieving a non-existent ODM form
        Then the response status code must be 404
        And the response must include the message like "OdmFormAR with UID 'OdmForm_000002' doesn't exist or there's no version with requested status or version number."
    Test Coverage:
        | TestFile                                              | TestID                                                           |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_getting_error_for_retrieving_non_existent_odm_form |

    Scenario: User cannot inactivate an ODM form that is in draft status
        When the user sends a request to inactivate the ODM form that is in draft status
        Then the response status code must be 400
        And the response must include the message "Cannot retire draft version."
    Test Coverage:
        | TestFile                                              | TestID                                                              |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_inactivate_an_odm_form_that_is_in_draft_status |

    Scenario: User cannot reactivate an ODM form that is not retired
        When the user sends a request to reactivate the ODM form that is not retired
        Then the response status code must be 400
        And the response must include the message "Only RETIRED version can be reactivated."
    Test Coverage:
        | TestFile                                              | TestID                                                          |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_reactivate_an_odm_form_that_is_not_retired |

    Scenario: User cannot add ODM item groups with an invalid value to an ODM form
        When the user sends a request to add ODM item groups with an invalid value
        Then the response status code must be 400
        And the response must include the message "Provided values for following attributes don't match their regex pattern: {'odm_vendor_attribute3': '^[a-zA-Z]+$'}"
    Test Coverage:
        | TestFile                                              | TestID                                                                        |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_add_odm_item_groups_with_an_invalid_value_to_an_odm_form |

    Scenario: User cannot add an ODM vendor attribute that is incompatible to an ODM form
        When the user sends a request to add an ODM vendor attribute to the ODM form with incompatible vendor
            | uid                  | odm_vendor_attribute5  |
            | value                | value                  |
        Then the response status code must be 400
        And the response must include the message like "Trying to add non-compatible ODM Vendor ..."
    Test Coverage:
        | TestFile                                              | TestID                                                                        |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_add_a_non_compatible_odm_vendor_attribute_to_an_odm_form |

    Scenario: User cannot add an ODM vendor element attribute to an ODM form as an ODM vendor attribute
        When the user sends a request to add an ODM vendor element attribute to an ODM form as an ODM vendor attribute
        Then the response status code must be 400
        And the response must include the message like "ODM Vendor Attribute with UID 'odm_vendor_attribute1' cannot not be added as an Vendor Attribute."
    Test Coverage:
        | TestFile                                              | TestID                                                                                          |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_add_odm_vendor_element_attribute_to_an_odm_form_as_an_odm_vendor_attribute |

    Scenario: User cannot add an ODM vendor attribute to an ODM form as an ODM vendor element attribute
        When the user sends a request to add an ODM vendor attribute to an ODM form as an ODM vendor element attribute
        Then the response status code must be 400
        And the response must include the message "ODM Vendor Attribute with UID 'odm_vendor_attribute3' cannot not be added as an Vendor Element Attribute."
    Test Coverage:
        | TestFile                                              | TestID                                                                                          |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_add_odm_vendor_attribute_to_an_odm_form_as_an_odm_vendor_element_attribute |

    Scenario: User cannot add ODM vendor elements that are incompatible to an ODM form
        When the user sends a request to add an ODM vendor element that are incompatible to an ODM form
        Then the response status code must be 400
        And the response must include the message "Trying to add non-compatible ODM Vendor ... "
    Test Coverage:
        | TestFile                                              | TestID                                                                      |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_add_a_non_compatible_odm_vendor_element_to_an_odm_form |

    Scenario: User cannot add ODM item groups with non-compatible ODM vendor attribute to a specific ODM form
        When the user sends a request to add ODM item groups with non-compatible ODM vendor attribute to a specific ODM form
        Then the response status code must be 400
        And the response must include the message "Trying to add non-compatible ODM Vendor ..."
    Test Coverage:
        | TestFile                                              | TestID                                                                                                   |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_add_odm_item_groups_with_non_compatible_odm_vendor_attribute_to_a_specific_odm_form |

    Scenario: User must be able to manage ODM vendors of a specific ODM form
        When the user sends a request to manage ODM vendors for of a specific ODM form
        Then the response status code must be 201
        And the response must indicate the vendors have been managed for the ODM form
    Test Coverage:
        | TestFile                                          | TestID                                                    |
        | /tests/integration/api/old/test_odm_forms.py      | @TestID: test_managing_odm_vendors_of_a_specific_odm_form |

    Scenario: User cannot add ODM item groups that belong to an ODM form that is in retired status
        When the user sends a request to add ODM item groups to the ODM form that is in retired status
        Then the response status code must be 400
        And the response must include the message "ODM element is not in Draft."
    Test Coverage:
        | TestFile                                              | TestID                                                                            |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_add_odm_item_groups_to_an_odm_form_that_is_in_retired_status |

    Scenario: User cannot add ODM vendor elements to an ODM form that is in retired status
        When the user sends a request to add an ODM vendor element to an ODM form that is in retired status
        Then the response status code must be 400
        And the response must include the message "ODM element is not in Draft."
    Test Coverage:
        | TestFile                                              | TestID                                                                               |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_add_odm_vendor_element_to_an_odm_form_that_is_in_retired_status |

    Scenario: User cannot add ODM vendor attributes to an ODM form that is in retired status
        When the user sends a request to add an ODM vendor attribute to an ODM form that is in retired status
        Then the response status code must be 400
        And the response must include the message "ODM element is not in Draft."
    Test Coverage:
        | TestFile                                              | TestID                                                                                 |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_add_odm_vendor_attribute_to_an_odm_form_that_is_in_retired_status |

    Scenario: User cannot add ODM vendor element attributes to an ODM form that is in retired status
        When the user sends a request to add an ODM vendor element attribute to an ODM form that is in retired status
        Then the response status code must be 400
        And the response must include the message "ODM element is not in Draft."
    Test Coverage:
        | TestFile                                              | TestID                                                                                         |
        | /tests/integration/api/old/test_odm_forms_negative.py | @TestID: test_cannot_add_odm_vendor_element_attribute_to_an_odm_form_that_is_in_retired_status |