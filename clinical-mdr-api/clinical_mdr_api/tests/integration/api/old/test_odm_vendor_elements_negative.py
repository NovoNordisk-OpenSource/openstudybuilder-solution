# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ODM_VENDOR_NAMESPACES,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.odm.vendor.elements.negative")
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)

    yield

    drop_db("old.json.test.odm.vendor.elements.negative")


def test_create_a_new_odm_vendor_element(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "nameTwo",
        "compatible_types": ["FormDef"],
        "vendor_namespace_uid": "odm_vendor_namespace1",
    }
    response = api_client.post("concepts/odms/vendor-elements", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["compatible_types"] == ["FormDef"]
    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "nameTwo"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_namespace"] == {
        "uid": "odm_vendor_namespace1",
        "name": "nameOne",
        "prefix": "prefix",
        "url": "url1",
        "status": "Final",
        "version": "1.0",
        "possible_actions": ["inactivate", "new_version"],
    }
    assert res["vendor_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_error_for_retrieving_non_existent_odm_vendor_element(api_client):
    response = api_client.get("concepts/odms/vendor-elements/OdmVendorElement_000002")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "OdmVendorElementAR with UID 'OdmVendorElement_000002' doesn't exist or there's no version with requested status or version number."
    )


def test_cannot_create_a_new_odm_vendor_element_without_providing_compatible_types(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "nameTwo",
        "compatible_types": [],
        "vendor_namespace_uid": "odm_vendor_namespace1",
    }
    response = api_client.post("concepts/odms/vendor-elements", json=data)

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["detail"] == [
        {
            "type": "too_short",
            "loc": ["body", "compatible_types"],
            "msg": "List should have at least 1 item after validation, not 0",
            "input": [],
            "ctx": {"field_type": "List", "min_length": 1, "actual_length": 0},
        }
    ]


def test_cannot_create_a_new_odm_vendor_element_if_odm_vendor_namespace_doesnt_exist(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "nameTwo",
        "compatible_types": ["FormDef"],
        "vendor_namespace_uid": "wrong_uid",
    }
    response = api_client.post("concepts/odms/vendor-elements", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == """ODM Vendor Element tried to connect to non-existent concepts [('Concept Name: ODM Vendor Namespace', "uids: {'wrong_uid'}")]."""
    )


def test_cannot_create_a_new_odm_vendor_element_with_existing_name(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "nameTwo",
        "compatible_types": ["FormDef"],
        "vendor_namespace_uid": "odm_vendor_namespace1",
    }
    response = api_client.post("concepts/odms/vendor-elements", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "ODM Vendor Element with Name 'nameTwo' already exists."


def test_cannot_inactivate_an_odm_vendor_element_that_is_in_draft_status(api_client):
    response = api_client.delete(
        "concepts/odms/vendor-elements/OdmVendorElement_000001/activations"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_cannot_reactivate_an_odm_vendor_element_that_is_not_retired(api_client):
    response = api_client.post(
        "concepts/odms/vendor-elements/OdmVendorElement_000001/activations"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only RETIRED version can be reactivated."


def test_create_an_odm_form(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "sdtm_version": "0.1",
        "repeating": "No",
        "descriptions": [],
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
    assert res["descriptions"] == []
    assert res["aliases"] == []
    assert res["activity_groups"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_add_odm_vendor_element_to_the_odm_form(api_client):
    data = [{"uid": "OdmVendorElement_000001", "value": "value1"}]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/vendor-elements", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "No"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["sdtm_version"] == "0.1"
    assert res["scope"] is None
    assert res["descriptions"] == []
    assert res["aliases"] == []
    assert res["activity_groups"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == [
        {"uid": "OdmVendorElement_000001", "name": "nameTwo", "value": "value1"}
    ]
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_cannot_delete_an_odm_vendor_element_that_is_being_used(api_client):
    response = api_client.delete(
        "concepts/odms/vendor-elements/OdmVendorElement_000001"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "This ODM Vendor Element is in use."


def test_cannot_delete_non_existent_odm_vendor_element(api_client):
    response = api_client.delete("concepts/odms/vendor-elements/wrong_uid")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "ODM Vendor Element with UID 'wrong_uid' doesn't exist."
