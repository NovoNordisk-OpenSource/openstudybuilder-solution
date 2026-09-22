@REQ_ID:1070683
Feature: Manage Library Concept CRF Stylesheet Function in OpenStudyBuilder API
    As an API user, I want to manage the CRF XML Stylesheet function in the Concepts Library API endpoints

    Background: The test user must be able to call the OpenStudyBuilder API and the test data exists
        Given the test user can call the OpenStudyBuilder API

    Scenario: User must be able to get all the names of available XML stylesheets
        When the user calls the API endpoint 'odms/metadata/xmls/stylesheets'
        Then the response must include all names of available XML stylesheets: "blank", "falcon", "with-annotations"

    Test Coverage:
        | TestFile                                               | TestID                                         |
        | /tests/integration/api/old/test_odm_xml_stylesheets.py | @TestID: test_get_available_stylesheet_names   |

    Scenario: User must be able to get the specific XML stylesheets
        When the user calls the API endpoint 'odms/metadata/xmls/stylesheets/blank'
        Then the response must include the blank XML stylesheets

    Test Coverage:
        | TestFile                                               | TestID                                       |
        | /tests/integration/api/old/test_odm_xml_stylesheets.py | @TestID: test_get_specific_stylesheet        |

    Scenario: User must be able to get the error message when the requested stylesheet does not exist 
        When the user calls the API endpoint 'odms/metadata/xmls/stylesheets/wrong'
        Then the response must be an error message that states "Stylesheet 'wrong' does not exist."

    Test Coverage:
        | TestFile                                               | TestID                                                           |
        | /tests/integration/api/old/test_odm_xml_stylesheets.py | @TestID: test_throw_exception_if_stylesheet_doesnt_exist         |
        
    Scenario: User must be able to get the error message when requesting a stylesheet with an invalid name
        When the user calls the API endpoint 'odms/metadata/xmls/stylesheets/_wrong'
        Then the response must be an error message that states "Stylesheet name must only contain letters, numbers and hyphens."

    Test Coverage:
        | TestFile                                               | TestID                                                                                 |
        | /tests/integration/api/old/test_odm_xml_stylesheets.py | @TestID: test_throw_exception_if_stylesheet_name_contains_disallowed_character         |