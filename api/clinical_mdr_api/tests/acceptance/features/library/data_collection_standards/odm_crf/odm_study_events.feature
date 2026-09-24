@REQ_ID:1070683
Feature: Manage ODM Study Events in OpenStudyBuilder API
    As an API user, I want to manage ODM Study Events through the OpenStudyBuilder API endpoints.

    Background: Test user must be able to call the OpenStudyBuilder API, and the test data exists
        Given The test user can call the OpenStudyBuilder API

    Scenario: User must be able to get an empty list of ODM study events
        When the user calls the API endpoint 'odms/study-events'
        Then the response must include an empty list of ODM study events
        And the response status code must be 200
    Test Coverage:
        | TestFile                                            | TestID                                               |
        | /tests/integration/api/old/test_odm_study_events.py | @TestID: test_getting_empty_list_of_odm_study_events |

    Scenario: User must be able to create a new ODM study event
        When the user sends a request to create a new ODM study event with valid data
        Then the response status code must be 201
        And the response must include the newly created ODM study event
    Test Coverage:
        | TestFile                                            | TestID                                       |
        | /tests/integration/api/old/test_odm_study_events.py | @TestID: test_creating_a_new_odm_study_event |

    Scenario: User must be able to get a non-empty list of ODM study events
        When the user calls the API endpoint 'odms/study-events'
        Then the response must include the list of ODM study events
        And the response status code must be 200
    Test Coverage:
        | TestFile                                            | TestID                                                   |
        | /tests/integration/api/old/test_odm_study_events.py | @TestID: test_getting_non_empty_list_of_odm_study_events |

    Scenario: User must be able to get a specific ODM study event
        When the user calls the API endpoint 'odms/study-events/' to get a specific ODM study event
        Then the response status code must be 200
        And the response must include the ODM study event
    Test Coverage:
        | TestFile                                            | TestID                                           |
        | /tests/integration/api/old/test_odm_study_events.py | @TestID: test_getting_a_specific_odm_study_event |

    Scenario: User must be able to get possible header values of ODM study events
        When the user calls the API endpoint 'odms/study-events/headers?field_name=name'
        Then the response status code must be 200
        And the response must include the list ["name1"]
    Test Coverage:
        | TestFile                                            | TestID                                                           |
        | /tests/integration/api/old/test_odm_study_events.py | @TestID: test_getting_possible_header_values_of_odm_study_events |

    Scenario: User must be able to update an existing ODM study event
        When the user sends a request to update an existing ODM study event 
        Then the response status code must be 200
        And the response must reflect the updated ODM study event
    Test Coverage:
        | TestFile                                            | TestID                                             |
        | /tests/integration/api/old/test_odm_study_events.py | @TestID: test_updating_an_existing_odm_study_event |

    Scenario: User cannot create a new ODM study event with the same properties
        When the user sends a request to create a new ODM study event with the same properties
        Then the response status code must be 409
        And the response must include the message like "ODM Study Event already exists with UID (OdmStudyEvent_000001)..."
    Test Coverage:
        | TestFile                                                     | TestID                                                                 |
        | /tests/integration/api/old/test_odm_study_events_negative.py | @TestID: test_cannot_create_a_new_odm_study_event_with_same_properties |

    Scenario: User cannot create an ODM study event without an English description
        When the user sends a request to create a new ODM study event without an English description
        Then the response status code must be 400
        And the response must include the message "A Translated Text with text_type Description and language English ('eng' or 'en') must be provided."
    Test Coverage:
        | TestFile                                                     | TestID                                                                           |
        | /tests/integration/api/old/test_odm_study_events_negative.py | @TestID: test_cannot_create_a_new_odm_study_event_without_an_english_description |

    Scenario: User receives an error for retrieving a non-existent ODM study event
        When the user calls the API endpoint 'odms/study-events/' for retrieving a non-existent ODM study event
        Then the response status code must be 404
        And the response must include the message like "OdmStudyEventAR with UID 'OdmStudyEvent_000002' doesn't exist ..."
    Test Coverage:
        | TestFile                                                     | TestID                                                                  |
        | /tests/integration/api/old/test_odm_study_events_negative.py | @TestID: test_getting_error_for_retrieving_non_existent_odm_study_event |

    Scenario: User cannot inactivate an ODM study event that is in draft status
        When the user sends a request to inactivate the ODM study event that is in draft status
        Then the response status code must be 400
        And the response must include the message "Cannot retire draft version."
    Test Coverage:
        | TestFile                                                     | TestID                                                                     |
        | /tests/integration/api/old/test_odm_study_events_negative.py | @TestID: test_cannot_inactivate_an_odm_study_event_that_is_in_draft_status |

    Scenario: User cannot reactivate an ODM study event that is not retired
        When the user sends a request to reactivate the ODM study event that is not retired
        Then the response status code must be 400
        And the response must include the message "Only RETIRED version can be reactivated."
    Test Coverage:
        | TestFile                                                     | TestID                                                                 |
        | /tests/integration/api/old/test_odm_study_events_negative.py | @TestID: test_cannot_reactivate_an_odm_study_event_that_is_not_retired |