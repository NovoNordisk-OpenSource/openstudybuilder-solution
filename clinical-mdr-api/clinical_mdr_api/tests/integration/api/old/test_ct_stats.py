# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER,
    STARTUP_CT_CODELISTS_NAME_CYPHER,
    STARTUP_CT_PACKAGE_CYPHER,
    STARTUP_CT_TERM_NAME_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.stats")
    db.cypher_query(STARTUP_CT_PACKAGE_CYPHER)
    db.cypher_query(STARTUP_CT_CODELISTS_NAME_CYPHER)
    db.cypher_query(STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER)
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

    yield

    drop_db("old.json.test.ct.stats")


def test_ct_stats(api_client):
    response = api_client.get("/ct/stats")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["catalogues"] == 2
    assert res["packages"] == 2
    assert res["codelist_counts"] == [
        {"library_name": "Sponsor", "count": 3},
        {"library_name": "CDISC", "count": 2},
    ]
    assert res["term_counts"] == [
        {"library_name": "Sponsor", "count": 3},
        {"library_name": "CDISC", "count": 2},
    ]
    assert res["codelist_change_percentage"] == 0.0
    assert res["term_change_percentage"] == 0.0
    assert res["codelist_change_details"] == []
    assert res["term_change_details"] == []
    assert res["latest_added_codelists"] == [
        {
            "catalogue_name": "SDTM CT",
            "codelist_uid": "ct_codelist_root1",
            "library_name": "Sponsor",
            "parent_codelist_uid": None,
            "child_codelist_uids": [],
            "name": {
                "catalogue_name": None,
                "codelist_uid": None,
                "name": "tp_codelist_name_value",
                "template_parameter": True,
                "library_name": None,
                "start_date": "2020-06-26T00:00:00Z",
                "end_date": None,
                "status": "Final",
                "version": "1.0",
                "change_description": "Approved version",
                "author_username": "unknown-user@example.com",
                "possible_actions": ["new_version"],
            },
            "attributes": {
                "catalogue_name": None,
                "codelist_uid": None,
                "parent_codelist_uid": None,
                "child_codelist_uids": [],
                "name": "codelist attributes value1",
                "submission_value": "codelist submission value1",
                "nci_preferred_name": "codelist preferred term",
                "definition": "codelist definition",
                "extensible": False,
                "library_name": None,
                "start_date": "2020-06-26T00:00:00Z",
                "end_date": None,
                "status": "Final",
                "version": "1.0",
                "change_description": "Approved version",
                "author_username": "unknown-user@example.com",
                "possible_actions": ["new_version"],
            },
        },
        {
            "catalogue_name": "SDTM CT",
            "codelist_uid": "ct_codelist_root2",
            "library_name": "CDISC",
            "parent_codelist_uid": None,
            "child_codelist_uids": [],
            "name": {
                "catalogue_name": None,
                "codelist_uid": None,
                "name": "not_tp_codelist_name_value",
                "template_parameter": False,
                "library_name": None,
                "start_date": "2020-06-26T00:00:00Z",
                "end_date": None,
                "status": "Draft",
                "version": "1.1",
                "change_description": "latest draft",
                "author_username": "unknown-user@example.com",
                "possible_actions": ["approve", "edit"],
            },
            "attributes": {
                "catalogue_name": None,
                "codelist_uid": None,
                "parent_codelist_uid": None,
                "child_codelist_uids": [],
                "name": "codelist attributes value2",
                "submission_value": "codelist submission value2",
                "nci_preferred_name": "codelist preferred term",
                "definition": "codelist definition",
                "extensible": False,
                "library_name": None,
                "start_date": "2020-06-26T00:00:00Z",
                "end_date": None,
                "status": "Draft",
                "version": "1.1",
                "change_description": "latest draft",
                "author_username": "unknown-user@example.com",
                "possible_actions": [],
            },
        },
        {
            "catalogue_name": "SDTM CT",
            "codelist_uid": "ct_codelist_root3",
            "library_name": "Sponsor",
            "parent_codelist_uid": None,
            "child_codelist_uids": [],
            "name": {
                "catalogue_name": None,
                "codelist_uid": None,
                "name": "codelist_name_value",
                "template_parameter": False,
                "library_name": None,
                "start_date": "2020-06-26T00:00:00Z",
                "end_date": None,
                "status": "Final",
                "version": "1.0",
                "change_description": "Approved version",
                "author_username": "unknown-user@example.com",
                "possible_actions": ["new_version"],
            },
            "attributes": {
                "catalogue_name": None,
                "codelist_uid": None,
                "parent_codelist_uid": None,
                "child_codelist_uids": [],
                "name": "codelist attributes value3",
                "submission_value": "codelist submission value3",
                "nci_preferred_name": "codelist preferred term",
                "definition": "codelist definition",
                "extensible": False,
                "library_name": None,
                "start_date": "2020-06-26T00:00:00Z",
                "end_date": None,
                "status": "Draft",
                "version": "0.1",
                "change_description": "latest draft",
                "author_username": "unknown-user@example.com",
                "possible_actions": ["approve", "edit"],
            },
        },
    ]
