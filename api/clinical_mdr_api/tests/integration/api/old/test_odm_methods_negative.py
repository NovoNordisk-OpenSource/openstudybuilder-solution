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
    inject_and_clear_db("old.json.test.odm.methods.negative")

    db.cypher_query("""CREATE (library:Library {name:"Sponsor", is_editable:true})""")

    yield

    drop_db("old.json.test.odm.methods.negative")


def test_create_a_new_odm_method(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "method_type": "type1",
        "formal_expressions": [{"context": "context1", "expression": "expression1"}],
        "translated_texts": [
            {
                "text_type": "Description",
                "language": "eng",
                "text": "description2",
            },
            {
                "text_type": "Description",
                "language": "dan",
                "text": "description3",
            },
            {
                "text_type": "osb:CompletionInstructions",
                "language": "eng",
                "text": "instruction2",
            },
            {
                "text_type": "osb:CompletionInstructions",
                "language": "dan",
                "text": "instruction3",
            },
            {
                "text_type": "osb:DesignNotes",
                "language": "eng",
                "text": "sponsor_instruction2",
            },
            {
                "text_type": "osb:DesignNotes",
                "language": "dan",
                "text": "sponsor_instruction3",
            },
            {
                "text_type": "osb:DisplayText",
                "language": "eng",
                "text": "name2",
            },
            {
                "text_type": "osb:DisplayText",
                "language": "dan",
                "text": "name3",
            },
        ],
        "aliases": [{"context": "context1", "name": "name1"}],
    }
    response = api_client.post("odms/methods", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmMethod_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["method_type"] == "type1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["formal_expressions"] == [
        {"context": "context1", "expression": "expression1"}
    ]
    assert res["translated_texts"] == [
        {
            "text_type": "Description",
            "language": "eng",
            "text": "description2",
        },
        {
            "text_type": "Description",
            "language": "dan",
            "text": "description3",
        },
        {
            "text_type": "osb:CompletionInstructions",
            "language": "eng",
            "text": "instruction2",
        },
        {
            "text_type": "osb:CompletionInstructions",
            "language": "dan",
            "text": "instruction3",
        },
        {
            "text_type": "osb:DesignNotes",
            "language": "eng",
            "text": "sponsor_instruction2",
        },
        {
            "text_type": "osb:DesignNotes",
            "language": "dan",
            "text": "sponsor_instruction3",
        },
        {
            "text_type": "osb:DisplayText",
            "language": "eng",
            "text": "name2",
        },
        {
            "text_type": "osb:DisplayText",
            "language": "dan",
            "text": "name3",
        },
    ]
    assert res["aliases"] == [{"context": "context1", "name": "name1"}]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_cannot_create_a_new_odm_method_with_same_properties(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "method_type": "type1",
        "formal_expressions": [{"context": "context1", "expression": "expression1"}],
        "translated_texts": [
            {
                "text_type": "Description",
                "language": "eng",
                "text": "description2",
            },
            {
                "text_type": "Description",
                "language": "dan",
                "text": "description3",
            },
            {
                "text_type": "osb:CompletionInstructions",
                "language": "eng",
                "text": "instruction2",
            },
            {
                "text_type": "osb:CompletionInstructions",
                "language": "dan",
                "text": "instruction3",
            },
            {
                "text_type": "osb:DesignNotes",
                "language": "eng",
                "text": "sponsor_instruction2",
            },
            {
                "text_type": "osb:DesignNotes",
                "language": "dan",
                "text": "sponsor_instruction3",
            },
            {
                "text_type": "osb:DisplayText",
                "language": "eng",
                "text": "name2",
            },
            {
                "text_type": "osb:DisplayText",
                "language": "dan",
                "text": "name3",
            },
        ],
        "aliases": [{"context": "context1", "name": "name1"}],
    }
    response = api_client.post("odms/methods", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "ODM Method already exists with UID (OdmMethod_000001) and data {'name': 'name1', 'oid': 'oid1', 'method_type': 'type1'}"
    )


def test_cannot_create_a_new_odm_method_without_an_english_description(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name2",
        "oid": "oid2",
        "type": "type2",
        "formal_expressions": [],
        "translated_texts": [
            {
                "text_type": "Description",
                "language": "DAN",
                "text": "text - non-eng",
            }
        ],
        "aliases": [],
    }
    response = api_client.post("odms/methods", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "A Translated Text with text_type Description and language English ('eng' or 'en') must be provided."
    )


def test_getting_error_for_retrieving_non_existent_odm_method(api_client):
    response = api_client.get("odms/methods/OdmMethod_000002")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "OdmMethodAR with UID 'OdmMethod_000002' doesn't exist or there's no version with requested status or version number."
    )


def test_cannot_inactivate_an_odm_method_that_is_in_draft_status(api_client):
    response = api_client.delete("odms/methods/OdmMethod_000001/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_cannot_reactivate_an_odm_method_that_is_not_retired(api_client):
    response = api_client.post("odms/methods/OdmMethod_000001/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only RETIRED version can be reactivated."


@pytest.mark.parametrize(
    "text_type",
    [
        pytest.param("Description"),
        pytest.param("Question"),
        pytest.param("osb:DesignNotes"),
        pytest.param("osb:CompletionInstructions"),
        pytest.param("osb:DisplayText"),
    ],
)
def test_cannot_add_duplicate_translated_texts(api_client, text_type: str):
    data = {
        "library_name": "Sponsor",
        "name": "testing",
        "oid": "testing",
        "formal_expressions": [{"context": "context1", "expression": "expression1"}],
        "translated_texts": [
            {
                "text_type": text_type,
                "language": "eng",
                "text": str(r),
            }
            for r in range(2)
        ],
        "aliases": [],
    }
    response = api_client.post("odms/methods", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == f"Duplicate Translated Text found for text_type '{text_type}' and language 'eng'."
    )
