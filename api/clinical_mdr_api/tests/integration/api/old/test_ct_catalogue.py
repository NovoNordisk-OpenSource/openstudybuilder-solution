# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.catalogue")
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

    yield

    drop_db("old.json.test.ct.catalogue")


def test_get_catalogue_changes_returned_valid_data(api_client):
    response = api_client.get(
        "http://testserver/ct/catalogues/changes?catalogue_name=catalogue&comparison_type=attributes&start_datetime=2020-03-28T00:00:00&end_datetime=2020-06-27T00:00:00"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["start_datetime"] == "2020-03-28T00:00:00"
    assert res["end_datetime"] == "2020-06-27T00:00:00"
    assert res["new_codelists"] == [
        {
            "value_node": {
                "name": "new_name",
                "definition": "codelist_added",
                "extensible": False,
            },
            "uid": "added_codelist_uid",
            "change_date": "2020-06-26T00:00:00Z",
            "is_change_of_codelist": True,
        }
    ]
    assert res["deleted_codelists"] == []
    assert res["updated_codelists"] == [
        {
            "value_node": {
                "left_only": {},
                "in_common": {"extensible": False},
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
            "change_date": "2020-06-26T00:00:00Z",
            "value_node": {
                "name": "new_name",
                "definition": "codelist_added",
                "extensible": False,
            },
        },
    ]
    assert res["new_terms"] == [
        {
            "uid": "added_term_uid",
            "change_date": "2020-06-26T00:00:00Z",
            "value_node": {"preferred_term": "added_preferred_term"},
            "codelists": ["added_codelist_uid"],
        }
    ]
    assert res["deleted_terms"] == []
    assert res["updated_terms"] == [
        {
            "uid": "updated_term_uid",
            "change_date": "2020-06-26T00:00:00Z",
            "value_node": {
                "left_only": {"preferred_term": "old_preferred_term"},
                "in_common": {},
                "different": {
                    "concept_id": {"left": "original_cid", "right": "new_cid"}
                },
                "right_only": {"definition": "new_definition"},
            },
            "codelists": ["updated_codelist_uid"],
        }
    ]
