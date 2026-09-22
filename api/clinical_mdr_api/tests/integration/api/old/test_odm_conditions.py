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
    inject_and_clear_db("old.json.test.odm.conditions")

    db.cypher_query("""CREATE (library:Library {name:"Sponsor", is_editable:true})""")

    yield

    drop_db("old.json.test.odm.conditions")


def test_getting_empty_list_of_odm_conditions(api_client):
    response = api_client.get("odms/conditions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_creating_a_new_odm_condition(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
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
    response = api_client.post("odms/conditions", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmCondition_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
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


def test_getting_non_empty_list_of_odm_conditions(api_client):
    response = api_client.get("odms/conditions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "OdmCondition_000001"
    assert res["items"][0]["name"] == "name1"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["oid"] == "oid1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "Initial version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["formal_expressions"] == [
        {"context": "context1", "expression": "expression1"}
    ]
    assert res["items"][0]["translated_texts"] == [
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
    assert res["items"][0]["aliases"] == [{"context": "context1", "name": "name1"}]
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_possible_header_values_of_odm_conditions(api_client):
    response = api_client.get("odms/conditions/headers?field_name=name")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == ["name1"]


def test_getting_a_specific_odm_condition(api_client):
    response = api_client.get("odms/conditions/OdmCondition_000001")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmCondition_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
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


def test_getting_versions_of_a_specific_odm_condition(api_client):
    response = api_client.get("odms/conditions/OdmCondition_000001/versions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "OdmCondition_000001"
    assert res[0]["name"] == "name1"
    assert res[0]["library_name"] == "Sponsor"
    assert res[0]["oid"] == "oid1"
    assert res[0]["end_date"] is None
    assert res[0]["status"] == "Draft"
    assert res[0]["version"] == "0.1"
    assert res[0]["change_description"] == "Initial version"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["formal_expressions"] == [
        {"context": "context1", "expression": "expression1"}
    ]
    assert res[0]["translated_texts"] == [
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
    assert res[0]["aliases"] == [{"context": "context1", "name": "name1"}]
    assert res[0]["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_condition(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name10",
        "oid": "oid1",
        "formal_expressions": [{"context": "context1", "expression": "expression1"}],
        "change_description": "name changed",
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
    response = api_client.patch("odms/conditions/OdmCondition_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmCondition_000001"
    assert res["name"] == "name10"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "name changed"
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


def test_getting_a_specific_odm_condition_in_specific_version(api_client):
    response = api_client.get("odms/conditions/OdmCondition_000001?version=0.1")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmCondition_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["end_date"]
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


def test_approving_an_odm_condition(api_client):
    response = api_client.post("odms/conditions/OdmCondition_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmCondition_000001"
    assert res["name"] == "name10"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
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
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_inactivating_a_specific_odm_condition(api_client):
    response = api_client.delete("odms/conditions/OdmCondition_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmCondition_000001"
    assert res["name"] == "name10"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Inactivated version"
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
    assert res["possible_actions"] == ["delete", "reactivate"]


def test_reactivating_a_specific_odm_condition(api_client):
    response = api_client.post("odms/conditions/OdmCondition_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmCondition_000001"
    assert res["name"] == "name10"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
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
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_creating_a_new_odm_condition_version(api_client):
    response = api_client.post("odms/conditions/OdmCondition_000001/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmCondition_000001"
    assert res["name"] == "name10"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
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
    assert res["possible_actions"] == ["approve", "edit"]


def test_create_a_new_odm_condition_for_deleting_it(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name - delete",
        "oid": "oid2",
        "formal_expressions": [],
        "translated_texts": [
            {
                "text_type": "Description",
                "language": "eng",
                "text": "name - delete",
            }
        ],
        "aliases": [],
    }
    response = api_client.post("odms/conditions", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmCondition_000002"
    assert res["name"] == "name - delete"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid2"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["formal_expressions"] == []
    assert res["translated_texts"] == [
        {
            "text_type": "Description",
            "language": "eng",
            "text": "name - delete",
        }
    ]
    assert res["aliases"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_deleting_a_specific_odm_condition(api_client):
    response = api_client.delete("odms/conditions/OdmCondition_000002")

    assert_response_status_code(response, 204)


def test_creating_a_new_odm_condition_with_relations(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "string",
        "oid": "string",
        "formal_expressions": [{"context": "string", "expression": "string"}],
        "translated_texts": [
            {"text_type": "Description", "language": "eng", "text": "string2"},
            {
                "text_type": "osb:CompletionInstructions",
                "language": "eng",
                "text": "string2",
            },
            {"text_type": "osb:DesignNotes", "language": "eng", "text": "string2"},
            {"text_type": "osb:DisplayText", "language": "eng", "text": "string2"},
        ],
        "aliases": [],
    }
    response = api_client.post("odms/conditions", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmCondition_000003"
    assert res["name"] == "string"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "string"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["formal_expressions"] == [{"context": "string", "expression": "string"}]
    assert res["translated_texts"] == [
        {"text_type": "Description", "language": "eng", "text": "string2"},
        {
            "text_type": "osb:CompletionInstructions",
            "language": "eng",
            "text": "string2",
        },
        {"text_type": "osb:DesignNotes", "language": "eng", "text": "string2"},
        {"text_type": "osb:DisplayText", "language": "eng", "text": "string2"},
    ]
    assert res["aliases"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_condition_with_relations(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name10",
        "oid": "oid1",
        "change_description": "name changed",
        "formal_expressions": [
            {"context": "context1", "expression": "expression1"},
            {"context": "context4", "expression": "expression4"},
        ],
        "translated_texts": [
            {"text_type": "Description", "language": "eng", "text": "string3"},
            {
                "text_type": "osb:CompletionInstructions",
                "language": "eng",
                "text": "string3",
            },
            {"text_type": "osb:DesignNotes", "language": "eng", "text": "string3"},
            {"text_type": "osb:DisplayText", "language": "eng", "text": "string3"},
        ],
        "aliases": [{"context": "context1", "name": "name1"}],
    }
    response = api_client.patch("odms/conditions/OdmCondition_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmCondition_000001"
    assert res["name"] == "name10"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.2"
    assert res["change_description"] == "name changed"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["formal_expressions"] == [
        {"context": "context1", "expression": "expression1"},
        {"context": "context4", "expression": "expression4"},
    ]
    assert res["translated_texts"] == [
        {"text_type": "Description", "language": "eng", "text": "string3"},
        {
            "text_type": "osb:CompletionInstructions",
            "language": "eng",
            "text": "string3",
        },
        {"text_type": "osb:DesignNotes", "language": "eng", "text": "string3"},
        {"text_type": "osb:DisplayText", "language": "eng", "text": "string3"},
    ]
    assert res["aliases"] == [{"context": "context1", "name": "name1"}]
    assert res["possible_actions"] == ["approve", "edit"]


def test_getting_uids_of_a_specific_odm_conditions_active_relationships(api_client):
    response = api_client.get("odms/conditions/OdmCondition_000001/relationships")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {}
