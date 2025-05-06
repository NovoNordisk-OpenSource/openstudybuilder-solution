# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
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
    inject_and_clear_db("old.json.test.odm.items.negative")
    db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)
    db.cypher_query(STARTUP_UNIT_DEFINITIONS)
    db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
    db.cypher_query(STARTUP_ODM_ALIASES)
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
    db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
    db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)

    yield

    drop_db("old.json.test.odm.items.negative")


def test_create_a_new_odm_item(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "prompt": "prompt1",
        "datatype": "datatype1",
        "length": 11,
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
    assert res["length"] == 11
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


def test_cannot_add_odm_vendor_attribute_with_an_invalid_value_to_an_odm_item(
    api_client,
):
    data = [{"uid": "odm_vendor_attribute3", "value": "3423"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-attributes", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == """Provided values for following attributes don't match their regex pattern:

{'odm_vendor_attribute3': '^[a-zA-Z]+$'}"""
    )


def test_cannot_add_a_non_compatible_odm_vendor_attribute_to_an_odm_item(api_client):
    data = [{"uid": "odm_vendor_attribute5", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-attributes", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == """Trying to add non-compatible ODM Vendor:

{'odm_vendor_attribute5': ['NonCompatibleVendor']}"""
    )


def test_cannot_add_a_non_compatible_odm_vendor_element_to_an_odm_item(api_client):
    data = [{"uid": "odm_vendor_element4", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-elements", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == """Trying to add non-compatible ODM Vendor:

{'odm_vendor_element4': ['NonCompatibleVendor']}"""
    )


def test_cannot_add_odm_vendor_element_attribute_with_an_invalid_value_to_an_odm_item(
    api_client,
):
    data = [{"uid": "odm_vendor_attribute1", "value": "3423"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-element-attributes", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == """Provided values for following attributes don't match their regex pattern:

{'odm_vendor_attribute1': '^[a-zA-Z]+$'}"""
    )


def test_add_odm_vendor_element_to_an_odm_item(api_client):
    data = [{"uid": "odm_vendor_element1", "value": "value1"}]
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
    assert res["length"] == 11
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
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "nameOne", "value": "value1"}
    ]
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_add_odm_vendor_element_attribute_to_an_odm_item(api_client):
    data = [{"uid": "odm_vendor_attribute1", "value": "valueOne"}]
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
    assert res["length"] == 11
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
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "nameOne", "value": "value1"}
    ]
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute1",
            "name": "nameOne",
            "data_type": "string",
            "value_regex": "^[a-zA-Z]+$",
            "value": "valueOne",
            "vendor_element_uid": "odm_vendor_element1",
        }
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_cannot_create_a_new_odm_item_with_same_properties(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "prompt": "prompt1",
        "datatype": "datatype1",
        "length": 11,
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

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "ODM Item already exists with UID (OdmItem_000001) and data {'description_uids': ['odm_description2', 'odm_description3'], 'alias_uids': ['odm_alias1'], 'unit_definition_uids': ['unit_definition_root1'], 'codelist_uid': 'editable_cr', 'term_uids': ['term_root_final'], 'name': 'name1', 'oid': 'oid1', 'datatype': 'datatype1', 'prompt': 'prompt1', 'length': 11, 'significant_digits': 11, 'sas_field_name': 'sas_field_name1', 'sds_var_name': 'sds_var_name1', 'origin': 'origin1', 'comment': 'comment1'}"
    )


def test_cannot_create_an_odm_item_connected_to_non_existent_concepts(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "new name",
        "oid": "new oid",
        "prompt": "prompt1",
        "datatype": "datatype1",
        "length": 11,
        "significant_digits": 11,
        "sas_field_name": "sas_field_name1",
        "sds_var_name": "sds_var_name1",
        "origin": "origin1",
        "comment": "comment1",
        "descriptions": ["wrong_uid"],
        "alias_uids": ["wrong_uid"],
        "unit_definitions": [{"uid": "wrong_uid"}],
        "codelist_uid": None,
        "terms": [],
    }
    response = api_client.post("concepts/odms/items", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == """ODM Item tried to connect to non-existent concepts [('Concept Name: ODM Description', "uids: {'wrong_uid'}"), ('Concept Name: ODM Alias', "uids: {'wrong_uid'}"), ('Concept Name: Unit Definition', "uids: {'wrong_uid'}")]."""
    )


def test_cannot_create_an_odm_item_connected_to_non_existent_codelist(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "new name",
        "oid": "new oid",
        "prompt": "prompt1",
        "datatype": "datatype1",
        "length": 11,
        "significant_digits": 11,
        "sas_field_name": "sas_field_name1",
        "sds_var_name": "sds_var_name1",
        "origin": "origin1",
        "comment": "comment1",
        "descriptions": [],
        "alias_uids": [],
        "unit_definitions": [],
        "codelist_uid": "wrong_uid",
        "terms": [],
    }
    response = api_client.post("concepts/odms/items", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "ODM Item tried to connect to non-existent Codelist with UID 'wrong_uid'."
    )


def test_cannot_create_an_odm_item_connected_to_ct_terms_without_providing_a_codelist(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "new name",
        "oid": "new oid",
        "prompt": "prompt1",
        "datatype": "datatype1",
        "length": 11,
        "significant_digits": 11,
        "sas_field_name": "sas_field_name1",
        "sds_var_name": "sds_var_name1",
        "origin": "origin1",
        "comment": "comment1",
        "descriptions": [],
        "alias_uids": [],
        "unit_definitions": [],
        "codelist_uid": None,
        "terms": [{"uid": "term_root_final"}],
    }
    response = api_client.post("concepts/odms/items", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "To add terms you need to specify a codelist."


def test_cannot_create_an_odm_item_connected_to_ct_terms_belonging_to_a_codelist_not_provided(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "new name",
        "oid": "new oid",
        "prompt": "prompt1",
        "datatype": "datatype1",
        "length": 11,
        "significant_digits": 11,
        "sas_field_name": "sas_field_name1",
        "sds_var_name": "sds_var_name1",
        "origin": "origin1",
        "comment": "comment1",
        "descriptions": [],
        "alias_uids": [],
        "unit_definitions": [],
        "codelist_uid": "editable_cr",
        "terms": [{"uid": "wrong_uid"}],
    }
    response = api_client.post("concepts/odms/items", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Term with UID 'wrong_uid' doesn't belong to the specified Codelist with UID 'editable_cr'."
    )


def test_getting_error_for_retrieving_non_existent_odm_item(api_client):
    response = api_client.get("concepts/odms/items/OdmItem_000002")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "OdmItemAR with UID 'OdmItem_000002' doesn't exist or there's no version with requested status or version number."
    )


def test_cannot_inactivate_an_odm_item_that_is_in_draft_status(api_client):
    response = api_client.delete("concepts/odms/items/OdmItem_000001/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_cannot_reactivate_an_odm_item_that_is_not_retired(api_client):
    response = api_client.post("concepts/odms/items/OdmItem_000001/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only RETIRED version can be reactivated."


def test_cannot_override_odm_vendor_element_that_has_attributes_connected_this_odm_item(
    api_client,
):
    data = [{"uid": "odm_vendor_element2", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-elements?override=true", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Cannot remove an ODM Vendor Element whose attributes are connected to this ODM element."
    )


def test_cannot_add_odm_vendor_element_attribute_to_an_odm_item_as_an_odm_vendor_attribute(
    api_client,
):
    data = [{"uid": "odm_vendor_attribute1", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-attributes", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "ODM Vendor Attribute with UID 'odm_vendor_attribute1' cannot not be added as an Vendor Attribute."
    )


def test_cannot_add_odm_vendor_attribute_to_an_odm_item_as_an_odm_vendor_element_attribute(
    api_client,
):
    data = [{"uid": "odm_vendor_attribute3", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-element-attributes", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "ODM Vendor Attribute with UID 'odm_vendor_attribute3' cannot not be added as an Vendor Element Attribute."
    )


def test_approve_odm_item(api_client):
    response = api_client.post("concepts/odms/items/OdmItem_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 11
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "comment1"
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
            "display_text": None,
            "version": "1.0",
        }
    ]
    assert res["activity"] is None
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "nameOne", "value": "value1"}
    ]
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute1",
            "name": "nameOne",
            "data_type": "string",
            "value_regex": "^[a-zA-Z]+$",
            "value": "valueOne",
            "vendor_element_uid": "odm_vendor_element1",
        }
    ]
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_inactivate_odm_item(api_client):
    response = api_client.delete("concepts/odms/items/OdmItem_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItem_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["prompt"] == "prompt1"
    assert res["datatype"] == "datatype1"
    assert res["length"] == 11
    assert res["significant_digits"] == 11
    assert res["sas_field_name"] == "sas_field_name1"
    assert res["sds_var_name"] == "sds_var_name1"
    assert res["origin"] == "origin1"
    assert res["comment"] == "comment1"
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
            "display_text": None,
            "version": "1.0",
        }
    ]
    assert res["activity"] is None
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "nameOne", "value": "value1"}
    ]
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute1",
            "name": "nameOne",
            "data_type": "string",
            "value_regex": "^[a-zA-Z]+$",
            "value": "valueOne",
            "vendor_element_uid": "odm_vendor_element1",
        }
    ]
    assert res["possible_actions"] == ["delete", "reactivate"]


def test_cannot_add_odm_activities_to_an_odm_item_that_is_in_retired_status(api_client):
    data = {"uid": "activity_root1"}
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/activities", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object is inactive"


def test_cannot_add_odm_vendor_element_to_an_odm_item_that_is_in_retired_status(
    api_client,
):
    data = [{"uid": "odm_vendor_element1", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-elements", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object is inactive"


def test_cannot_add_odm_vendor_attribute_to_an_odm_item_that_is_in_retired_status(
    api_client,
):
    data = [{"uid": "odm_vendor_attribute1", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-attributes", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object is inactive"


def test_cannot_add_odm_vendor_element_attribute_to_an_odm_item_that_is_in_retired_status(
    api_client,
):
    data = [{"uid": "odm_vendor_attribute1", "value": "value"}]
    response = api_client.post(
        "concepts/odms/items/OdmItem_000001/vendor-element-attributes", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object is inactive"
