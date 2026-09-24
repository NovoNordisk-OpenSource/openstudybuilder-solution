@REQ_ID:1070683
Feature: Manage Library Concept CRF XML Exporter Function in OpenStudyBuilder API

    As an API user, I want to manage the CRF XML Exporter function in the Concepts Library API endpoints

    Background: Test user must be able to call the OpenStudyBuilder API and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get the xml representation of the requsted odm forms
        When the user calls the API endpoint with uids of odm forms 'odms/metadata/xmls/export?targets=odm_form1&targets=odm_form2&target_type=form'
        Then the response must include the exact xml representation of the requested odm forms

    Test Coverage:
        |TestFile                                            | TestID                              |
        |/tests/integration/api/old/test_odm_xml_exporter.py | @TestID: test_get_odm_xml_forms     |
        
    Scenario: User must be able to get the xml representation of the requsted odm item group
        When the user calls the API endpoint with uids of odm item group 'odms/metadata/xmls/export?targets=odm_item_group1&target_type=item_group'
        Then the response must include the exact xml representation of the requested odm item group

    Test Coverage:
        |TestFile                                            | TestID                                |
        |/tests/integration/api/old/test_odm_xml_exporter.py | @TestID: test_get_odm_xml_item_group  |

    Scenario: User must be able to get the xml representation of the requsted odm item
        When the user calls the API endpoint with uids of odm item 'odms/metadata/xmls/export?targets=odm_item1&target_type=item'
        Then the response must include the exact xml representation of the requested odm item

    Test Coverage:
        |TestFile                                            | TestID                              |
        |/tests/integration/api/old/test_odm_xml_exporter.py | @TestID: test_get_odm_xml_item      |

    Scenario: User must be able to get the xml representation of the requsted odm item
        When the user calls the API endpoint with uids of odm item 'odms/metadata/xmls/export?targets=odm_item1&target_type=item'
        Then the response must include the exact xml representation of the requested odm item

    Test Coverage:
        |TestFile                                            | TestID                              |
        |/tests/integration/api/old/test_odm_xml_exporter.py | @TestID: test_get_odm_xml_item      |

    Scenario: User must be able to get the pdf representation of the requsted odm elmenet
        When the user calls the API endpoint with uids of odm element 'odms/metadata/xmls/export?target_type=form&targets=odm_form1&pdf=true&stylesheet=blank'
        Then the response must include the exact pdf representation of the requested odm element

    Test Coverage:
        |TestFile                                            | TestID                                 |
        |/tests/integration/api/old/test_odm_xml_exporter.py | @TestID: test_get_odm_xml_pdf_version  |

    Scenario: User must be able to get error message when the requested odm target type is not supported 
        When the user calls the API endpoint 'odms/metadata/xmls/export?targets=study&target_type=study'
        Then the response must get error message 'Requested target type not supported.'

    Test Coverage:
        |TestFile                                            | TestID                                                              |
        |/tests/integration/api/old/test_odm_xml_exporter.py | @TestID: test_throw_exception_if_target_type_is_not_supported       |