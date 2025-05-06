# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.odm.descriptions.negative")
    db.cypher_query("MERGE (library:Library {name:'Sponsor', is_editable:true})")

    yield

    drop_db("old.json.test.odm.descriptions.negative")


def test_creating_a_new_odm_form_with_description(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "sdtm_version": "0.1",
        "repeating": "No",
        "scope_uid": None,
        "descriptions": [
            {
                "name": "name1",
                "library_name": "Sponsor",
                "language": "eng",
                "description": "description1",
                "instruction": "instruction1",
                "sponsor_instruction": "sponsor_instruction1",
            }
        ],
        "alias_uids": [],
    }
    response = api_client.post("concepts/odms/forms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "No"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] is None
    assert res["descriptions"] == [
        {
            "uid": "OdmDescription_000001",
            "name": "name1",
            "language": "eng",
            "description": "description1",
            "instruction": "instruction1",
            "sponsor_instruction": "sponsor_instruction1",
            "version": "0.1",
        }
    ]
    assert res["aliases"] == []
    assert res["activity_groups"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


# def test_cannot_inactivate_an_odm_description_that_is_in_draft_status(api_client):
#     response = api_client.delete(
#         "concepts/odms/descriptions/OdmDescription_000001/activations"
#     )

#     assert_response_status_code(response, 400)

#     res = response.json()

#     assert res["type"] == "BusinessLogicException"
#     assert res["message"] == "Cannot retire draft version."


# def test_cannot_reactivate_an_odm_description_that_is_not_retired(api_client):
#     response = api_client.post(
#         "concepts/odms/descriptions/OdmDescription_000001/activations"
#     )

#     assert_response_status_code(response, 400)

#     res = response.json()

#     assert res["type"] == "BusinessLogicException"
#     assert res["message"] == "Only RETIRED version can be reactivated."


def test_cannot_create_an_odm_form_while_attaching_it_to_a_used_odm_description(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "sdtm_version": "0.1",
        "repeating": "No",
        "descriptions": ["OdmDescription_000001"],
        "alias_uids": [],
    }
    response = api_client.post("concepts/odms/forms", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "ODM Form already exists with UID (OdmForm_000001) and data {'description_uids': ['OdmDescription_000001'], 'alias_uids': [], 'scope_uid': None, 'name': 'name1', 'oid': 'oid1', 'sdtm_version': '0.1', 'repeating': False}"
    )


# def test_cannot_delete_an_odm_description_that_is_being_used(api_client):
#     response = api_client.delete("concepts/odms/descriptions/OdmDescription_000001")

#     assert_response_status_code(response, 400)

#     res = response.json()

#     assert res["type"] == "BusinessLogicException"
#     assert res["message"] == "This ODM Description is in use."


# def test_cannot_delete_non_existent_odm_description(api_client):
#     response = api_client.delete("concepts/odms/descriptions/wrong_uid")

#     assert_response_status_code(response, 404)

#     res = response.json()

#     assert res["type"] == "NotFoundException"
#     assert res["message"] == "ODM Description with UID 'wrong_uid' doesn't exist."
