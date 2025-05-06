# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITIES,
    STARTUP_CT_TERM_ATTRIBUTES_CYPHER,
    STARTUP_ODM_ALIASES,
    STARTUP_ODM_DESCRIPTIONS,
    STARTUP_ODM_VENDOR_ATTRIBUTES,
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
    STARTUP_UNIT_DEFINITIONS,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.odm.items")
    db.cypher_query(STARTUP_ACTIVITIES)
    db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)
    db.cypher_query(STARTUP_UNIT_DEFINITIONS)
    db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
    db.cypher_query(STARTUP_ODM_ALIASES)
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
    db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
    db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)

    yield

    drop_db("old.json.test.odm.items")


def test_getting_empty_list_of_odm_items(api_client):
    response = api_client.get("concepts/odms/items")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_creating_a_new_odm_item(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "prompt": "prompt1",
        "datatype": "datatype1",
        "length": 1,
        "significant_digits": 11,
        "sas_field_name": "sas_field_name1",
        "sds_var_name": "sds_var_name1",
        "origin": "origin1",
        "comment": "comment1",
        "descriptions": ["odm_description2", "odm_description3"],
        "alias_uids": ["odm_alias1"],
        "unit_definitions": [
            {"uid": "unit_definition_root1", "mandatory": False, "order": 1}
        ],
        "codelist_uid": "editable_cr",
        "terms": [
            {
                "uid": "term_root_final",
                "mandatory": True,
                "order": 1,
                "display_text": None,
                "version": "1.0",
            }
        ],
    }
    response = api_client.post("concepts/odms/items", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 1
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "comment1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "0.1",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "0.1",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": None,
            "version": "1.0",
        }
    ]
    assert res["activity"] is None
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_non_empty_list_of_odm_items(api_client):
    response = api_client.get("concepts/odms/items")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "OdmItem_000001"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["name"] == "name1"
    assert res["items"][0]["oid"] == "oid1"
    assert res["items"][0]["prompt"] == "prompt1"
    assert res["items"][0]["datatype"] == "datatype1"
    assert res["items"][0]["length"] == 1
    assert res["items"][0]["significant_digits"] == 11
    assert res["items"][0]["sas_field_name"] == "sas_field_name1"
    assert res["items"][0]["sds_var_name"] == "sds_var_name1"
    assert res["items"][0]["origin"] == "origin1"
    assert res["items"][0]["comment"] == "comment1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "Initial version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "0.1",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "0.1",
        },
    ]
    assert res["items"][0]["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["items"][0]["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["items"][0]["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["items"][0]["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": None,
            "version": "1.0",
        }
    ]
    assert res["items"][0]["activity"] is None
    assert res["items"][0]["vendor_elements"] == []
    assert res["items"][0]["vendor_attributes"] == []
    assert res["items"][0]["vendor_element_attributes"] == []
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_possible_header_values_of_odm_items(api_client):
    response = api_client.get("concepts/odms/items/headers?field_name=name")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == ["name1"]


def test_getting_a_specific_odm_item(api_client):
    response = api_client.get("concepts/odms/items/OdmItem_000001")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 1
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "comment1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "0.1",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "0.1",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": None,
            "version": "1.0",
        }
    ]
    assert res["activity"] is None
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_versions_of_a_specific_odm_item(api_client):
    response = api_client.get("concepts/odms/items/OdmItem_000001/versions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "OdmItem_000001"
    assert res[0]["library_name"] == "Sponsor"
    assert res[0]["name"] == "name1"
    assert res[0]["oid"] == "oid1"
    assert res[0]["prompt"] == "prompt1"
    assert res[0]["datatype"] == "datatype1"
    assert res[0]["length"] == 1
    assert res[0]["significant_digits"] == 11
    assert res[0]["sas_field_name"] == "sas_field_name1"
    assert res[0]["sds_var_name"] == "sds_var_name1"
    assert res[0]["origin"] == "origin1"
    assert res[0]["comment"] == "comment1"
    assert res[0]["end_date"] is None
    assert res[0]["status"] == "Draft"
    assert res[0]["version"] == "0.1"
    assert res[0]["change_description"] == "Initial version"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "0.1",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "0.1",
        },
    ]
    assert res[0]["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res[0]["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res[0]["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res[0]["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": None,
            "version": "1.0",
        }
    ]
    assert res[0]["activity"] is None
    assert res[0]["vendor_elements"] == []
    assert res[0]["vendor_attributes"] == []
    assert res[0]["vendor_element_attributes"] == []
    assert res[0]["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_item(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "prompt": "prompt1",
        "datatype": "datatype1",
        "length": None,
        "significant_digits": 11,
        "sas_field_name": "sas_field_name1",
        "sds_var_name": "sds_var_name1",
        "origin": "origin1",
        "comment": "new comment",
        "change_description": "comment added",
        "descriptions": ["odm_description2", "odm_description3"],
        "alias_uids": ["odm_alias1"],
        "unit_definitions": [
            {"uid": "unit_definition_root1", "mandatory": False, "order": 1}
        ],
        "codelist_uid": "editable_cr",
        "terms": [
            {
                "uid": "term_root_final",
                "mandatory": True,
                "order": 1,
                "display_text": "display text",
                "version": "1.0",
            }
        ],
    }
    response = api_client.patch("concepts/odms/items/OdmItem_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "comment added"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "0.1",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "0.1",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] is None
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_approving_an_odm_item(api_client):
    response = api_client.post("concepts/odms/items/OdmItem_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] is None
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_inactivating_a_specific_odm_item(api_client):
    response = api_client.delete("concepts/odms/items/OdmItem_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Inactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] is None
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["delete", "reactivate"]


def test_reactivating_a_specific_odm_item(api_client):
    response = api_client.post("concepts/odms/items/OdmItem_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] is None
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_adding_activity_to_a_specific_odm_item(api_client):
    data = {"uid": "activity_root1"}
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/activities", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root1", "name": "name1"}
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_overriding_activity_from_a_specific_odm_item(api_client):
    data = {"uid": "activity_root2"}
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/activities?override=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root2", "name": "name2"}
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_adding_odm_vendor_element_to_a_specific_odm_item(api_client):
    data = [{"uid": "odm_vendor_element2", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-elements", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root2", "name": "name2"}
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element2", "name": "nameTwo", "value": "value"}
    ]
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_overriding_odm_vendor_element_from_a_specific_odm_item(api_client):
    data = [{"uid": "odm_vendor_element1", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-elements?override=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root2", "name": "name2"}
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "nameOne", "value": "value"}
    ]
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_adding_odm_vendor_attribute_to_a_specific_odm_item(api_client):
    data = [{"uid": "odm_vendor_attribute3", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-attributes", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root2", "name": "name2"}
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "nameOne", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute3",
            "name": "nameThree",
            "data_type": "string",
            "value_regex": "^[a-zA-Z]+$",
            "value": "value",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_overriding_odm_vendor_attribute_from_a_specific_odm_item(api_client):
    data = [{"uid": "odm_vendor_attribute4", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-attributes?override=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root2", "name": "name2"}
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "nameOne", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_adding_odm_vendor_element_attribute_to_a_specific_odm_item(api_client):
    data = [{"uid": "odm_vendor_attribute1", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-element-attributes", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root2", "name": "name2"}
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "nameOne", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute1",
            "name": "nameOne",
            "data_type": "string",
            "value_regex": "^[a-zA-Z]+$",
            "value": "value",
            "vendor_element_uid": "odm_vendor_element1",
        }
    ]
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_overriding_odm_vendor_element_attribute_from_a_specific_odm_item(api_client):
    data = [{"uid": "odm_vendor_attribute2", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-element-attributes?override=true",
        json=data,
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root2", "name": "name2"}
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "nameOne", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute2",
            "name": "nameTwo",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
            "vendor_element_uid": "odm_vendor_element1",
        }
    ]
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_overriding_odm_vendor_element_attribute_from_a_specific_odm_item1(api_client):
    data = {
        "elements": [{"uid": "odm_vendor_element3", "value": "value"}],
        "element_attributes": [{"uid": "odm_vendor_attribute7", "value": "value"}],
        "attributes": [{"uid": "odm_vendor_attribute4", "value": "value"}],
    }
    response = api_client.post("concepts/odms/items/OdmItem_000001/vendors", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.0",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.0",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root2", "name": "name2"}
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element3", "name": "nameThree", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute7",
            "name": "nameSeven",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
            "vendor_element_uid": "odm_vendor_element3",
        }
    ]
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_creating_a_new_odm_item_version(api_client):
    response = api_client.post("concepts/odms/items/OdmItem_000001/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "odm_description2",
            "name": "name2",
            "language": "language2",
            "description": "description2",
            "instruction": "instruction2",
            "sponsor_instruction": "sponsor_instruction2",
            "version": "1.1",
        },
        {
            "uid": "odm_description3",
            "name": "name3",
            "language": "ENG",
            "description": "description3",
            "instruction": "instruction3",
            "sponsor_instruction": "sponsor_instruction3",
            "version": "1.1",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": "display text",
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root2", "name": "name2"}
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element3", "name": "nameThree", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute7",
            "name": "nameSeven",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
            "vendor_element_uid": "odm_vendor_element3",
        }
    ]
    assert res["possible_actions"] == ["approve", "edit"]


def test_create_a_new_odm_item_for_deleting_it(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1 - delete",
        "oid": "oid2",
        "prompt": "prompt1",
        "datatype": "datatype1",
        "length": 1,
        "significant_digits": 11,
        "sas_field_name": "sas_field_name1",
        "sds_var_name": "sds_var_name1",
        "origin": "origin1",
        "comment": "comment1",
        "descriptions": [
            {
                "name": "name3 - delete",
                "language": "ENG",
                "description": "description3 - delete",
                "instruction": "instruction3 - delete",
                "sponsor_instruction": "sponsor_instruction3 - delete",
            }
        ],
        "alias_uids": [],
        "unit_definitions": [
            {"uid": "unit_definition_root1", "mandatory": False, "order": 1}
        ],
        "codelist_uid": None,
        "terms": [],
    }
    response = api_client.post("concepts/odms/items", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000002"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1 - delete"
    assert res["oid"] == "oid2"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 1
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "comment1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "OdmDescription_000001",
            "name": "name3 - delete",
            "language": "ENG",
            "description": "description3 - delete",
            "instruction": "instruction3 - delete",
            "sponsor_instruction": "sponsor_instruction3 - delete",
            "version": "0.1",
        }
    ]
    assert res["aliases"] == []
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] is None
    assert res["terms"] == []
    assert res["activity"] is None
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_deleting_a_specific_odm_item(api_client):
    response = api_client.delete("concepts/odms/items/OdmItem_000002")

    assert_response_status_code(response, 204)


def test_creating_a_new_odm_item_with_relations(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "string",
        "oid": "string",
        "prompt": "string",
        "datatype": "string",
        "length": 0,
        "significant_digits": 11,
        "sas_field_name": "string",
        "sds_var_name": "string",
        "origin": "string",
        "comment": "string",
        "descriptions": [
            {
                "name": "string1",
                "library_name": "Sponsor",
                "language": "DAN",
                "description": "string1",
                "instruction": "string1",
                "sponsor_instruction": "string1",
            },
        ],
        "alias_uids": [],
        "unit_definitions": [],
        "codelist_uid": None,
        "terms": [],
    }
    response = api_client.post("concepts/odms/items", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000003"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "string"
    assert res["oid"] == "string"
    assert res["prompt"] == "string"
    assert res["datatype"] == "string"
    assert res["length"] is None
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "string"
    assert res["sds_var_name"] == "string"
    assert res["origin"] == "string"
    assert res["comment"] == "string"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "OdmDescription_000002",
            "name": "string1",
            "language": "DAN",
            "description": "string1",
            "instruction": "string1",
            "sponsor_instruction": "string1",
            "version": "0.1",
        },
    ]
    assert res["aliases"] == []
    assert res["unit_definitions"] == []
    assert res["codelist"] is None
    assert res["terms"] == []
    assert res["activity"] is None
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_item_with_relations(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "prompt": "prompt1",
        "datatype": "datatype1",
        "length": None,
        "significant_digits": 11,
        "sas_field_name": "sas_field_name1",
        "sds_var_name": "sds_var_name1",
        "origin": "origin1",
        "comment": "new comment",
        "change_description": "comment added",
        "descriptions": [
            {
                "name": "string3",
                "library_name": "Sponsor",
                "language": "ARA",
                "description": "string3",
                "instruction": "string3",
                "sponsor_instruction": "string3",
            },
        ],
        "alias_uids": ["odm_alias1"],
        "unit_definitions": [
            {"uid": "unit_definition_root1", "mandatory": False, "order": 1}
        ],
        "codelist_uid": "editable_cr",
        "terms": [{"uid": "term_root_final", "mandatory": True, "order": 1}],
    }
    response = api_client.patch("concepts/odms/items/OdmItem_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 22
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "new comment"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.2"
    assert res["change_description"] == "comment added"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == [
        {
            "uid": "OdmDescription_000003",
            "name": "string3",
            "language": "ARA",
            "description": "string3",
            "instruction": "string3",
            "sponsor_instruction": "string3",
            "version": "0.1",
        },
    ]
    assert res["aliases"] == [
        {"uid": "odm_alias1", "context": "context1", "name": "name1", "version": "0.1"}
    ]
    assert res["unit_definitions"] == [
        {
            "uid": "unit_definition_root1",
            "name": "name1",
            "mandatory": False,
            "order": 1,
            "ucum": {
                "term_uid": "term_root1_uid",
                "name": "name1",
                "dictionary_id": "dictionary_id1",
            },
            "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
        }
    ]
    assert res["codelist"] == {
        "uid": "editable_cr",
        "name": "codelist attributes value1",
        "submission_value": "codelist submission value1",
        "preferred_term": "codelist preferred term",
    }
    assert res["terms"] == [
        {
            "term_uid": "term_root_final",
            "name": "term_value_name1",
            "mandatory": True,
            "order": 1,
            "display_text": None,
            "version": "1.0",
        }
    ]
    assert res["activity"] == {"uid": "activity_root2", "name": "name2"}
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element3", "name": "nameThree", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute7",
            "name": "nameSeven",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
            "vendor_element_uid": "odm_vendor_element3",
        }
    ]
    assert res["possible_actions"] == ["approve", "edit"]


def test_create_a_new_odm_item_group_with_relation_to_odm_item(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "repeating": "No",
        "is_reference_data": "No",
        "sas_dataset_name": "sas_dataset_name1",
        "origin": "origin1",
        "purpose": "purpose1",
        "comment": "comment1",
        "descriptions": [],
        "alias_uids": [],
        "sdtm_domain_uids": [],
    }
    response = api_client.post("concepts/odms/item-groups", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "No"
    assert res["is_reference_data"] == "No"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == []
    assert res["aliases"] == []
    assert res["sdtm_domains"] == []
    assert res["activity_subgroups"] == []
    assert res["items"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_approve_the_odm_item_group(api_client):
    response = api_client.post(
        "concepts/odms/item-groups/OdmItemGroup_000001/approvals"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "No"
    assert res["is_reference_data"] == "No"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == []
    assert res["aliases"] == []
    assert res["sdtm_domains"] == []
    assert res["activity_subgroups"] == []
    assert res["items"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_add_the_odm_item_to_the_odm_item_group(api_client):
    data = [
        {
            "uid": "OdmItem_000001",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "None",
            "method_oid": "None",
            "imputation_method_oid": "None",
            "role": "role1",
            "role_codelist_oid": "None",
            "collection_exception_condition_oid": "None",
            "vendor": {
                "attributes": [{"uid": "odm_vendor_attribute3", "value": "Yes"}]
            },
        }
    ]
    response = api_client.post(
        "concepts/odms/item-groups/OdmItemGroup_000001/items", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "No"
    assert res["is_reference_data"] == "No"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["descriptions"] == []
    assert res["aliases"] == []
    assert res["sdtm_domains"] == []
    assert res["activity_subgroups"] == []
    assert res["items"] == [
        {
            "uid": "OdmItem_000001",
            "oid": "oid1",
            "name": "name1",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "None",
            "method_oid": "None",
            "imputation_method_oid": "None",
            "role": "role1",
            "role_codelist_oid": "None",
            "collection_exception_condition_oid": "None",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "Yes",
                        "vendor_namespace_uid": "odm_vendor_namespace1",
                    }
                ]
            },
        }
    ]
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_getting_uids_of_a_specific_odm_items_active_relationships(api_client):
    response = api_client.get("concepts/odms/items/OdmItem_000001/relationships")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["OdmItemGroup"] == ["OdmItemGroup_000001"]


def test_getting_all_odm_items_that_belongs_to_an_odm_item_groups(api_client):
    response = api_client.get("concepts/odms/items/item-groups")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "OdmItem_000001"
    assert res[0]["name"] == "name1"
    assert res[0]["parent_uids"] == ["OdmItemGroup_000001"]
