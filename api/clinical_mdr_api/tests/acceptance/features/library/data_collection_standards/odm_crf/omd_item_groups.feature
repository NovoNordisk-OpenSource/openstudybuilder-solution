@REQ_ID:1070683
Feature: Manage ODM Item Groups in OpenStudyBuilder API
    As an API user, I want to manage ODM Item Groups through the OpenStudyBuilder API endpoints.

    Background: Test user must be able to call the OpenStudyBuilder API, and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get an empty list of ODM item groups
        When the user calls the API endpoint 'odms/item-groups'
        Then the response must include an empty list of ODM item groups
        And the response status code must be 200
    Test Coverage:
        | TestFile                                           | TestID                                              |
        | /tests/integration/api/old/test_odm_item_groups.py | @TestID: test_getting_empty_list_of_odm_item_groups |

    Scenario: User must be able to create a new ODM item group
        When the user sends a request to create a new ODM item group with valid data
        Then the response status code must be 201
        And the response must include the newly created ODM item group
    Test Coverage:
        | TestFile                                           | TestID                                      |
        | /tests/integration/api/old/test_odm_item_groups.py | @TestID: test_creating_a_new_odm_item_group |

    Scenario: User must be able to get a list of ODM item groups
        When the user calls the API endpoint 'odms/item-groups' to get a list of ODM item groups
        Then the response must include the list of ODM item groups
        And the response status code must be 200
    Test Coverage:
        | TestFile                                           | TestID                                                  |
        | /tests/integration/api/old/test_odm_item_groups.py | @TestID: test_getting_non_empty_list_of_odm_item_groups |

    Scenario: User must be able to get a specific ODM item group
        When the user calls the API endpoint 'odms/item-groups/' to get a specific ODM item group
        Then the response status code must be 200
        And the response must include the ODM item group
    Test Coverage:
        | TestFile                                           | TestID                                          |
        | /tests/integration/api/old/test_odm_item_groups.py | @TestID: test_getting_a_specific_odm_item_group |

    Scenario: User must be able to get possible header values of ODM item groups
        When the user calls the API endpoint 'odms/item-groups/headers?field_name=name'
        Then the response status code must be 200
        And the response must include the list ["name1"]
    Test Coverage:
        | TestFile                                           | TestID                                                          |
        | /tests/integration/api/old/test_odm_item_groups.py | @TestID: test_getting_possible_header_values_of_odm_item_groups |

    Scenario: User must be able to update an existing ODM item group
        When the user sends a request to update an existing ODM item group with valid data
        Then the response status code must be 200
        And the response must reflect the updated ODM item group
    Test Coverage:
        | TestFile                                           | TestID                                            |
        | /tests/integration/api/old/test_odm_item_groups.py | @TestID: test_updating_an_existing_odm_item_group |

    Scenario: User cannot add ODM vendor attribute with an invalid value to an ODM item group
        When the user sends a request to add an ODM vendor attribute with an invalid value
            | uid                  | odm_vendor_attribute3 |
            | value                | 3423                  |
        Then the response status code must be 400
        And the response must include the message "Provided values for following attributes don't match their regex pattern ... "
    Test Coverage:
        | TestFile                                                    | TestID                                                                                   |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_add_odm_vendor_attribute_with_an_invalid_value_to_an_odm_item_group |

    Scenario: User cannot add a non-compatible ODM vendor attribute to an ODM item group
        When the user sends a request to add a non-compatible ODM vendor attribute to an ODM item group
        Then the response status code must be 400
        And the response must include the message "Trying to add non-compatible ODM Vendor ... "
    Test Coverage:
        | TestFile                                                    | TestID                                                                              |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_add_a_non_compatible_odm_vendor_attribute_to_an_odm_item_group |

    Scenario: User cannot add a non-compatible ODM vendor element to an ODM item group
        When the user sends a request to add a non-compatible ODM vendor element to an ODM item group
        Then the response status code must be 400
        And the response must include the message "Trying to add non-compatible ODM Vendor ... "
    Test Coverage:
        | TestFile                                                    | TestID                                                                            |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_add_a_non_compatible_odm_vendor_element_to_an_odm_item_group |

    Scenario: User cannot add ODM items with an invalid value to an ODM item group
        When the user sends a request to add ODM items with an invalid value to an ODM item group
        Then the response status code must be 400
        And the response must include the message "Provided values for following attributes don't match their regex pattern ... "
    Test Coverage:
        | TestFile                                                    | TestID                                                                           |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_add_odm_items_with_an_invalid_value_to_to_an_odm_item_group |

    Scenario: User must be able to add an ODM vendor element to a specific ODM item group
        When the user sends a request to add an ODM vendor element with valid data
        Then the response status code must be 201
        And the response must indicate the ODM vendor element has been added to the ODM item group
    Test Coverage:
        | TestFile                                           | TestID                                                               |
        | /tests/integration/api/old/test_odm_item_groups.py | @TestID: test_adding_odm_vendor_element_to_a_specific_odm_item_group |

    Scenario: User must be able to add an ODM vendor element attribute to a specific ODM item group
        When the user sends a request to add an ODM vendor element attribute  to a specific ODM item group
        Then the response status code must be 201
        And the response must indicate the ODM vendor element attribute has been added to the ODM item group
    Test Coverage:      
        | TestFile                                           | TestID                                                                         |
        | /tests/integration/api/old/test_odm_item_groups.py | @TestID: test_adding_odm_vendor_element_attribute_to_a_specific_odm_item_group |

    Scenario: User cannot create a new ODM item group with the same properties
        When the user sends a request to create a new ODM item group with the same properties
        Then the response status code must be 409
        And the response must include the message like "ODM Item Group already exists with UID (OdmItemGroup_000001) ..."
    Test Coverage:
        | TestFile                                                    | TestID                                                                |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_create_a_new_odm_item_group_with_same_properties |

    Scenario: User cannot create an ODM item group connected to a non-existent SDTM domain
        When the user sends a request to create an ODM item group to a non-existent SDTM domain
        Then the response status code must be 400
        And the response must include the message "ODM Item Group tried to connect to non-existent SDTM Domain with UID 'wrong_uid'."
    Test Coverage:
        | TestFile                                                    | TestID                                                                              |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_create_an_odm_item_group_connected_to_non_existent_sdtm_domain |

    Scenario: User cannot create an ODM item group without an English description
        When the user sends a request to create an ODM item group without an English description
        Then the response status code must be 400
        And the response must include the message "A Translated Text with text_type Description and language English ('eng' or 'en') must be provided."
    Test Coverage:
        | TestFile                                                    | TestID                                                                          |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_create_a_new_odm_item_group_without_an_english_description |

    Scenario: User receives an error for retrieving a non-existent ODM item group
        When the user calls the API endpoint 'odms/item-groups/' for retrieving a non-existent ODM item group
        Then the response status code must be 404
        And the response must include the message like "OdmItemGroupAR with UID 'OdmItemGroup_000002' doesn't exist ..."
    Test Coverage:
        | TestFile                                                    | TestID                                                                 |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_getting_error_for_retrieving_non_existent_odm_item_group |

    Scenario: User cannot inactivate an ODM item group that is in draft status
        When the user sends a request to inactivate the ODM item group that is in draft status
        Then the response status code must be 400
        And the response must include the message "Cannot retire draft version."
    Test Coverage:
        | TestFile                                                    | TestID                                                                    |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_inactivate_an_odm_item_group_that_is_in_draft_status |

    Scenario: User cannot reactivate an ODM item group that is not retired
        When the user sends a request to reactivate the ODM item group that is not retired
        Then the response status code must be 400
        And the response must include the message "Only RETIRED version can be reactivated."
    Test Coverage:
        | TestFile                                                    | TestID                                                                |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_reactivate_an_odm_item_group_that_is_not_retired |

    Scenario: User cannot override an ODM vendor element that has attributes connected to this ODM item group
        When the user sends a request to override the ODM vendor element that has attributes connected to this ODM item group
        Then the response status code must be 400
        And the response must include the message "Cannot remove an ODM Vendor Element whose attributes are connected to this ODM element."
    Test Coverage:
        | TestFile                                                    | TestID                                                                                             |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_override_odm_vendor_element_that_has_attributes_connected_this_odm_item_group |

    Scenario: User cannot add ODM vendor element attribute to an ODM item group as an ODM vendor attribute
        When the user sends a request to add an ODM vendor element attribute to an ODM item group as an ODM vendor attribute
        Then the response status code must be 400
        And the response must include the message "ODM Vendor Attribute with UID 'odm_vendor_attribute1' cannot not be added as an Vendor Attribute."
    Test Coverage:
        | TestFile                                                    | TestID                                                                                                |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_add_odm_vendor_element_attribute_to_an_odm_item_group_as_an_odm_vendor_attribute |

    Scenario: User cannot add ODM vendor attribute to an ODM item group as an ODM vendor element attribute
        When the user sends a request to add an ODM vendor attribute to an ODM item group as an ODM vendor element attribute
        Then the response status code must be 400
        And the response must include the message "ODM Vendor Attribute with UID 'odm_vendor_attribute3' cannot not be added as an Vendor Element Attribute."
    Test Coverage:
        | TestFile                                                    | TestID                                                                                                |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_add_odm_vendor_attribute_to_an_odm_item_group_as_an_odm_vendor_element_attribute |

    Scenario: User cannot add ODM items to an ODM item group that is in retired status
        When the user sends a request to add ODM items to the ODM item group that is in retired status
        Then the response status code must be 400
        And the response must include the message "ODM element is not in Draft."
    Test Coverage:
        | TestFile                                                    | TestID                                                                            |
        | /tests/integration/api/old/test_odm_item_groups_negative.py | @TestID: test_cannot_add_odm_items_to_an_odm_item_group_that_is_in_retired_status |

    Scenario: User must be able to approve an ODM item group
        When the user sends a request to approve the ODM item group
        Then the response status code must be 201
        And the response must indicate the ODM item group has been approved
    Test Coverage:
        | TestFile                                           | TestID                               |
        | /tests/integration/api/old/test_odm_item_groups.py | @TestID: test_approve_odm_item_group |

    Scenario: User must be able to deactivate a specific ODM item group
        When the user sends a request to deactivate the ODM item group
        Then the response status code must be 200
        And the response must indicate the ODM item group has been deactivated
    Test Coverage:
        | TestFile                                           | TestID                                  |
        | /tests/integration/api/old/test_odm_item_groups.py | @TestID: test_inactivate_odm_item_group |