@REQ_ID:1070679 @REQ_ID:1070680

Feature: Manage Sponsor CT Packages of sponsor names and sponsor extensions for CDISC CT Packages

    Background: Test user must be able to call the OpenStudyBuilder API and test data must exist
        Given The test user can call the OpenStudyBuilder API
        And a test data identified by 'uid' exists in the library

    Rule: As an API user
        I want the API to generate Sponsor CT Packages as a reference snapshot of a CDISC CT Package including sponsor names and sponsor extensions
        So that a persisten reference can be made to sponsor names and extesions for a study

        Scenario: API must support creating a Sponsor CT Package
            When The POST API endpoint /ct/packages/sponsor is called to create a Sponsor CT Package
            Then The API must ensure the Sponsor CT Package is created with a name as the datetime string at the creation
            And A reference to the parent CDISC CT Package
            And A reference to the user creating the Sponsor CT Package as the modified user
            And A datetime field for the creation as the modified datetime
            # We should keep this as the modified user/datetime - even it is only creation date

        Examples:
            |TestFile                                                                    | TestID                                   |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_post_sponsor_ct_package     |

        Scenario: API must support get codelist content for a Sponsor CT Package
            When The GET API endpoint /ct/codelists?package=<Test Sponsor CT Package> is called to get codelists content of a Sponsor CT Package
            Then The API must return all codelists content related to a Sponsor CT Package

        Examples:
            |TestFile                                                                    | TestID                                            |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_get_codelists_sponsor_ct_package     |

        Scenario: API must support get CT terms content for a Sponsor CT Package
            When The GET API endpoint /ct/terms?package=<Test Sponsor CT Package> is called to get CT Terms content of a Sponsor CT Package
            Then The API must return all terms content related to a Sponsor CT Package

        Examples:
            |TestFile                                                                    | TestID                                            |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_get_terms_sponsor_ct_package         |

        ###! Note, deletion of a sponsor CT package will be added in a later release, so placeholder for these scearios are commented out.
        #@TestID:test_delete_notused_sponsor_ct_package
        # Scenario: API must support deleting a Sponsor CT Package if it is not refered to by any studies

        #@TestID:test_delete_used_sponsor_ct_package
        #Scenario: API must return error code when deleting a Sponsor CT Package used by a study


       ### First test content is returned as is when no changes is made yet

        Scenario: API must support get identical codelists content for a Sponsor CT Package and current codelists when no changes is made
            When The GET API endpoint /ct/codelists?package=<Test Sponsor CT Package> is called to get codelists content of a Sponsor CT Package
            And No changes has been made to codelists
            Then The API must return all codelists content related to a Sponsor CT Package identical to the return from GET /ct/codelists

        Examples:
            |TestFile                                                                    | TestID                                                                    |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_get_codelists_identical_sponsor_ct_package_nochanges         |

        Scenario: API must support get identical CT terms content for a Sponsor CT Package and current CT terms when no changes is made
            When The GET API endpoint /ct/terms?package=<Test Sponsor CT Package> is called to get CT Terms content of a Sponsor CT Package
            And No changes has been made to CT Terms
            Then The API must return all CT Terms content related to a Sponsor CT Package identical to the return from GET /ct/terms

        Examples:
            |TestFile                                                                    | TestID                                                               |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_get_terms_identical_sponsor_ct_package_nochanges        |

       ### Second test persistent content is returned after updates have been made

        Scenario: API must support persistent reference to codelists for a Sponsor codelist in a Sponsor CT Package
        Given A Sponsor CT Package exist for a CT Catalouge related to a CDISC CT Package
        When The POST API endpoint /ct/codelists/ is called to create a new Sponsor Codelist not related to the test Sponsor CT Package
        Then The call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package> with a reference to the test Sponsor CT Package will not return the newly created Sponsor codelist

        Examples:
            |TestFile                                                                    | TestID                                                                  |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_sponsor_ct_package_is_persistent_sponsor_codelists         |

        Scenario: API must support persistent reference to CT Terms for a Sponsor term in a Sponsor CT Package
        Given a Sponsor CT Package exist for a CT Catalouge related to a CDISC CT Package
        When the POST API endpoint /ct/terms/ is called to create a new Sponsor CT Term not related to the test Sponsor CT Package
        Then the call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package> with a reference to the test Sponsor CT Package will not return the newly created Sponsor CT Term

        Examples:
            |TestFile                                                                    | TestID                                                              |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_sponsor_ct_package_is_persistent_sponsor_terms         |

        Scenario: API must support persistent reference to sponsor codelists name for a CDISC codelist in a Sponsor CT Package
        Given A Sponsor CT Package exist for a CT Catalouge related to a CDISC CT Package
        When The PATCH API endpoint /ct/codelists/<Test CDISC Codelist uid>/names is called to update sponsor name for a CDISC Codelist related to the test Sponsor CT Package
        Then The call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package> with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value for the updated CDISC codelist

        Examples:
            |TestFile                                                                    | TestID                                                                             |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_sponsor_ct_package_is_persistent_sponsor_name_cdisc_codelists         |

        Scenario: API must support persistent reference to sponsor codelists name for a Sponsor codelist in a Sponsor CT Package
        Given A Sponsor CT Package exist for a CT Catalouge related to a CDISC CT Package
        When The PATCH API endpoint /ct/codelists/<Test Sponsor Codelist uid>/names is called to update sponsor name for a Sponsor Codelist related to the test Sponsor CT Package
        Then The call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package> with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value for the updated Sponsor codelist

        Examples:
            |TestFile                                                                    | TestID                                                                               |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_sponsor_ct_package_is_persistent_sponsor_name_sponsor_codelists         |

        Scenario: API must support persistent reference to codelists attributes for a Sponsor codelist in a Sponsor CT Package
        Given A Sponsor CT Package exist for a CT Catalouge related to a CDISC CT Package
        When The PATCH API endpoint /ct/codelists/<Test Sponsor Codelist uid>/attributes is called to update attributes for a Sponsor Codelist related to the test Sponsor CT Package
        Then The call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package> with a reference to the test Sponsor CT Package will return the original attribute values for the updated Sponsor codelist

        Examples:
            |TestFile                                                                    | TestID                                                                             |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_sponsor_ct_package_is_persistent_attributes_sponsor_codelists         |

        Scenario: API must support persistent reference to sponsor term names for a CDISC CT term in a Sponsor CT Package
        Given A Sponsor CT Package exist for a CT Catalouge related to a CDISC CT Package
        When The PATCH API endpoint /ct/terms/<Test CDISC Term uid>/names is called to update sponsor name for a CDISC CT Term related to the test Sponsor CT Package
        Then The call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package> with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value for the updated CDISC CT Term

        Examples:
            |TestFile                                                                    | TestID                                                                         |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_sponsor_ct_package_is_persistent_sponsor_name_cdisc_terms         |

        Scenario: API must support persistent reference to sponsor term names for a Sponsor CT term in a Sponsor CT Package
        Given A Sponsor CT Package exist for a CT Catalouge related to a CDISC CT Package
        When The PATCH API endpoint /ct/terms/<Test Sponsor Term uid>/names is called to update sponsor name for a Sponsor CT Term related to the test Sponsor CT Package
        Then The call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package> with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value for the updated Sponsor CT Term

        Examples:
            |TestFile                                                                    | TestID                                                                          |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_sponsor_ct_package_is_persistent_sponsor_name_sponsor_terms        |

        Scenario: API must support persistent reference to attributes for a Sponsor CT term in a Sponsor CT Package
        Given A Sponsor CT Package exist for a CT Catalouge related to a CDISC CT Package
        When The PATCH API endpoint /ct/terms/<Test Sponsor Term uid>/attributes is called to update attributes for a Sponsor CT Term related to the test Sponsor CT Package
        Then The call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package> with a reference to the test Sponsor CT Package will return the original attribute values for the updated Sponsor CT Term

        Examples:
            |TestFile                                                                    | TestID                                                                         |
            |/tests/integration/api/controlled_terminologies/test_sponsor_ct_packages.py | @TestID:test_sponsor_ct_package_is_persistent_attributes_sponsor_terms         |

    # Test CDISC/Sponsor CT terms added + removed to/from CDSIC extensible codelists
    # Test CDISC/Sponsor CT terms added + removed to/from sponsor codelists
