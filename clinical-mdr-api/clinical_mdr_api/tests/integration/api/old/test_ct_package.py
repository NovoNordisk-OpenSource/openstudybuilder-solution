# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_PACKAGE_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.package")
    db.cypher_query(STARTUP_CT_PACKAGE_CYPHER)

    yield

    drop_db("old.json.test.ct.package")


def test_get_packages_changes_returned_valid_data(api_client):
    response = api_client.get(
        "/ct/packages/changes?catalogue_name=catalogue&old_package_date=2020-03-27&new_package_date=2020-06-26"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["from_package"] == "old_package"
    assert res["to_package"] == "new_package"
    assert res["new_codelists"] == [
        {
            "value_node": {"name": "new_name", "definition": "codelist_added"},
            "uid": "added_codelist_uid",
            "change_date": "2020-06-26T00:00:00Z",
            "is_change_of_codelist": True,
        }
    ]
    assert res["deleted_codelists"] == [
        {
            "value_node": {"name": "old_name", "extensible": False},
            "uid": "deleted_codelist_uid",
            "change_date": "2020-03-27T00:00:00Z",
            "is_change_of_codelist": True,
        }
    ]
    assert res["updated_codelists"] == [
        {
            "value_node": {
                "left_only": {"extensible": False},
                "in_common": {},
                "different": {"name": {"left": "old_name", "right": "new_name"}},
                "right_only": {"definition": "new_definition"},
            },
            "uid": "updated_codelist_uid",
            "change_date": "2020-06-26T00:00:00Z",
            "is_change_of_codelist": True,
        },
        {
            "uid": "added_codelist_uid",
            "is_change_of_codelist": False,
            "value_node": {"name": "new_name", "definition": "codelist_added"},
            "change_date": "2020-06-26T00:00:00Z",
        },
    ]
    assert res["new_terms"] == [
        {
            "uid": "added_term_uid",
            "change_date": "2020-06-26T00:00:00Z",
            "value_node": {
                "preferred_term": "old_preferred_term",
                "name_submission_value": "old_submission_value",
            },
            "codelists": ["added_codelist_uid"],
        }
    ]
    assert res["deleted_terms"] == [
        {
            "uid": "deleted_term_uid",
            "change_date": "2020-03-27T00:00:00Z",
            "value_node": {
                "preferred_term": "old_preferred_term",
                "name_submission_value": "old_submission_value",
            },
            "codelists": ["deleted_codelist_uid"],
        }
    ]
    assert res["updated_terms"] == [
        {
            "uid": "updated_term_uid",
            "change_date": "2020-06-26T00:00:00Z",
            "value_node": {
                "left_only": {"preferred_term": "old_preferred_term"},
                "in_common": {},
                "different": {
                    "name_submission_value": {
                        "left": "old_submission_value",
                        "right": "new_submission_value",
                    }
                },
                "right_only": {"definition": "new_definition"},
            },
            "codelists": ["updated_codelist_uid"],
        }
    ]


def test_get_packages_changes_for_a_specific_codelist_returned_valid_data(api_client):
    response = api_client.get(
        "/ct/packages/updated_codelist_uid/changes?catalogue_name=catalogue&old_package_date=2020-03-27&new_package_date=2020-06-26"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["from_package"] == "old_package"
    assert res["to_package"] == "new_package"
    assert res["new_codelists"] == []
    assert res["deleted_codelists"] == []
    assert res["updated_codelists"] == [
        {
            "value_node": {
                "left_only": {"extensible": False},
                "in_common": {},
                "different": {"name": {"left": "old_name", "right": "new_name"}},
                "right_only": {"definition": "new_definition"},
            },
            "uid": "updated_codelist_uid",
            "change_date": "2020-06-26T00:00:00Z",
            "is_change_of_codelist": True,
        }
    ]
    assert res["new_terms"] == []
    assert res["deleted_terms"] == []
    assert res["updated_terms"] == [
        {
            "uid": "updated_term_uid",
            "change_date": "2020-06-26T00:00:00Z",
            "value_node": {
                "left_only": {"preferred_term": "old_preferred_term"},
                "in_common": {},
                "different": {
                    "name_submission_value": {
                        "left": "old_submission_value",
                        "right": "new_submission_value",
                    }
                },
                "right_only": {"definition": "new_definition"},
            },
            "codelists": ["updated_codelist_uid"],
        }
    ]
    assert res["not_modified_terms"] == [
        {
            "uid": "not_modified_term_uid",
            "change_date": "2020-03-27T00:00:00Z",
            "value_node": {
                "preferred_term": "not_modified_preferred_term",
                "name_submission_value": "not_modified_submission_value",
            },
            "codelists": ["updated_codelist_uid"],
        }
    ]


def test_get_packages_dates_valid_data_returned(api_client):
    response = api_client.get("/ct/packages/dates?catalogue_name=catalogue")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["catalogue_name"] == "catalogue"
    assert res["effective_dates"] == ["2020-03-27", "2020-06-26"]
