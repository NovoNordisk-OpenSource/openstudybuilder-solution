@REQ_ID:2383812

Feature: Manage Library Admin definitions for Data Suppliers in OpenStudyBuilder API 

    As an API user, I want to manage the Data Suppliers by using the Library API endpoints

    Background: Test user must be able to call the OpenStudyBuilder API and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get a specific data supplier details
        When the user requests to get the details of a data supplier with a specific UID
        Then the response should include the following attributes for the data supplier:
            | uid                       |
            | name                      |
            | description               |
            | order                     |
            | supplier_type             |
            | origin_source             |
            | origin_type               |
            | api_base_url              |
            | ui_base_url               |
            | library_name              |
            | possible_actions          |
            | version                   |
            | status                    |
            | start_date                |
            | end_date                  |
            | change_description        |
            | author_username           |

    Test Coverage:
        |TestFile                                     | TestID                            |
        |/tests/integration/api/test_data_supplier.py | @TestID: test_get_data_supplier   |

    Scenario Outline: User can retrieve paginated data suppliers with sorting
        Given there are multiple data suppliers available
        When the user requests data suppliers with page_number, page_size, and sort_by
        Then the response should have a status code of 200
        And the response should include the keys "items", "total", "page", and "size"
        And the number of items in the response should be <expected_result_len>
        And the total count of data suppliers should be <total_count>
        And the current page number in the response should be <page_number>
        And the size of the page in the response should be <page_size>
        And the items in the response should be sorted by "<sort_field>" in <sort_order> order

    Examples:
    | page_size | page_number | total_count | sort_by                | expected_result_len | sort_field | sort_order |
    |    None   |     None    |     None    | None                   |          10         |            |            |
    |     3     |      1      |     True    | '{"name": true}'       |          3          | name       | ascending  |
    |     3     |      2      |     True    | '{"name": true}'       |          3          | name       | ascending  |
    |    10     |      2      |     True    | '{"name": true}'       |          10         | name       | ascending  |
    |    10     |      3      |     True    | '{"name": true}'       |          5          | name       | ascending  |
    |    10     |      1      |     True    | '{"name": false}'      |          10         | name       | descending |
    |    10     |      2      |     True    | '{"name": true}'       |          10         | name       | ascending  |

    Test Coverage:
        |TestFile                                     | TestID                                       |
        |/tests/integration/api/test_data_supplier.py | @TestID: test_get_data_supplier_pagination   |

    Scenario: User can retrieve all data suppliers in one request
        Given there are multiple data suppliers available
        When the user requests data suppliers with page_size 100 and page_number 1
        Then the response should have a status code of 200
        And the number of items in the response should match the total count of data suppliers

     Test Coverage:
        |TestFile                                     | TestID                            |
        |/tests/integration/api/test_data_supplier.py | @TestID: test_get_data_suppliers  |

    Scenario: User must be able to get a requested format with correct data
        When the user requests to get data supplier with specific parameters in csv, xml and excel formats
        Then the response should be in the requested format with correct data

    Test Coverage:
        |TestFile                                     | TestID                                          |
        |/tests/integration/api/test_data_supplier.py | @TestID: test_get_data_suppliers_csv_xml_excel  |    

    Scenario: User must be able to get all available values of a specific field
        When the user requests to get all available values for the field like uid, name, description, orders
        Then the response should include all the available values for the specified field

    Test Coverage:
        |TestFile                                     | TestID                            |
        |/tests/integration/api/test_data_supplier.py | @TestID: test_headers             |
    
    Scenario: User must be able to get all versions of a specific data supplier
        When the user requests to get all versions of a specific data supplier
        Then the response should include all versions of the this specific data supplier

    Test Coverage:
        |TestFile                                     | TestID                                    |
        |/tests/integration/api/test_data_supplier.py | @TestID: test_get_data_supplier_versions  |

    Scenario: User must be able to filter data suppliers
        When the user requests to filter on a specific field of the data supplier
        Then the response should include only the data supplier that match the specified filter
        When the user requests to filter with wildcard
        Then the response should include only the data suppliers that match the specified filters

    Test Coverage:
        |TestFile                                      | TestID                                                |
        |/tests/integration/api/test_data_supplier.py  | @TestID: test_filtering_wildcard      |
        |/tests/integration/api/test_data_supplier.py  | @TestID: test_filtering_exact         |

    Scenario: User must be able to edit a data supplier
        When the user attempts to edit a data supplier with valid values
        Then The data supplier is updated with new values successfully
        And The data supplier status should be final

    Test Coverage:
        |TestFile                                      | TestID                                                |
        |/tests/integration/api/test_data_supplier.py  | @TestID: test_edit_data_supplier  |

    Scenario: User must be able to create a data supplier when all valid data is provided
        When the user creates a data supplier with mandatory field, like name and supplier type. 
        And optionally provide other values, like order, description, etc. 
        Then The data supplier is created successfully
        And The data supplier status should be final

    Test Coverage:
        |TestFile                                      | TestID                                                |
        |/tests/integration/api/test_data_supplier.py  | @TestID: test_post_data_supplier  |

    Scenario: User must be able to inactivate and reactivate the data supplier
        When the user inactivates a final data supplier
        Then The data supplier status is changed to retired successfully
        When the user reactivates an inactive (Retired) data supplier
        Then The data supplier status is changed to final successfully
        When The user reactivate a Final data supplier
        Then The error will be returned with message as 'Only RETIRED version can be reactivated'

    Test Coverage:
        |TestFile                                      | TestID                                                |
        |/tests/integration/api/test_data_supplier.py  | @TestID: test_data_supplier_versioning |
