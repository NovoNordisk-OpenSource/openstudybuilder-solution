# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.odm.vendor.attributes.negative")
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
    db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)

    yield

    drop_db("old.json.test.odm.vendor.attributes.negative")


def test_create_a_new_odm_vendor_attribute_of_vendor_namespace(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "nameOne",
        "compatible_types": ["FormDef", "ItemRef"],
        "data_type": "string",
        "value_regex": None,
        "vendor_namespace_uid": "odm_vendor_namespace1",
    }
    response = api_client.post("concepts/odms/vendor-attributes", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmVendorAttribute_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "nameOne"
    assert res["compatible_types"] == ["FormDef", "ItemRef"]
    assert res["data_type"] == "string"
    assert res["value_regex"] is None
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
    assert res["vendor_element"] is None
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_create_a_new_odm_vendor_attribute_of_vendor_element(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "nameOne",
        "compatible_types": [],
        "data_type": "string",
        "value_regex": None,
        "vendor_element_uid": "odm_vendor_element1",
    }
    response = api_client.post("concepts/odms/vendor-attributes", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmVendorAttribute_000002"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "nameOne"
    assert res["compatible_types"] == []
    assert res["data_type"] == "string"
    assert res["value_regex"] is None
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_namespace"] is None
    assert res["vendor_element"] == {
        "uid": "odm_vendor_element1",
        "name": "nameOne",
        "compatible_types": ["FormDef", "ItemGroupDef", "ItemDef"],
        "status": "Final",
        "version": "1.0",
        "possible_actions": ["inactivate", "new_version"],
    }
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_error_for_retrieving_non_existent_odm_vendor_attribute(api_client):
    response = api_client.get(
        "concepts/odms/vendor-attributes/OdmVendorAttribute_000003"
    )

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "OdmVendorAttributeAR with UID 'OdmVendorAttribute_000003' doesn't exist or there's no version with requested status or version number."
    )


def test_cannot_create_a_new_odm_vendor_attribute_belonging_to_odm_vendor_namespace_without_providing_compatible_types(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "nameTwo",
        "compatible_types": [],
        "data_type": "string",
        "value_regex": None,
        "vendor_namespace_uid": "odm_vendor_namespace1",
    }
    response = api_client.post("concepts/odms/vendor-attributes", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "compatible_types must be provided for ODM Vendor Attributes belonging to ODM Vendor Namespace."
    )


def test_cannot_create_a_new_odm_vendor_attribute_belonging_to_odm_vendor_element_when_providing_compatible_types(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "nameTwo",
        "compatible_types": ["FormDef"],
        "data_type": "string",
        "value_regex": None,
        "vendor_element_uid": "odm_vendor_element1",
    }
    response = api_client.post("concepts/odms/vendor-attributes", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "compatible_types must not be provided for ODM Vendor Attributes belonging to ODM Vendor Element."
    )


def test_cannot_create_a_new_odm_vendor_attribute_with_invalid_regex(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "nameOne",
        "compatible_types": ["FormDef"],
        "data_type": "string",
        "value_regex": "(*'*(!'",
        "vendor_namespace_uid": "odm_vendor_namespace1",
    }
    response = api_client.post("concepts/odms/vendor-attributes", json=data)

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["detail"] == [
        {
            "type": "value_error",
            "loc": ["body", "value_regex"],
            "msg": "Value error, Provided regex value '(*'*(!'' for field 'value_regex' is invalid.",
            "input": "(*'*(!'",
            "ctx": {"error": {}},
        }
    ]


def test_cannot_create_a_new_odm_vendor_attribute_of_vendor_namespace_with_existing_name(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "nameOne",
        "compatible_types": ["FormDef"],
        "data_type": "string",
        "vendor_namespace_uid": "odm_vendor_namespace1",
    }
    response = api_client.post("concepts/odms/vendor-attributes", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "ODM Vendor Attribute with Name 'nameOne' already exists."


def test_cannot_create_a_new_odm_vendor_attribute_of_vendor_element_with_existing_name(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "nameOne",
        "compatible_types": [],
        "data_type": "string",
        "vendor_element_uid": "odm_vendor_element1",
    }
    response = api_client.post("concepts/odms/vendor-attributes", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "ODM Vendor Attribute with Name 'nameOne' already exists."


def test_cannot_inactivate_an_odm_vendor_attribute_that_is_in_draft_status(api_client):
    response = api_client.delete(
        "concepts/odms/vendor-attributes/OdmVendorAttribute_000001/activations"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_cannot_reactivate_an_odm_vendor_attribute_that_is_not_retired(api_client):
    response = api_client.post(
        "concepts/odms/vendor-attributes/OdmVendorAttribute_000001/activations"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only RETIRED version can be reactivated."
