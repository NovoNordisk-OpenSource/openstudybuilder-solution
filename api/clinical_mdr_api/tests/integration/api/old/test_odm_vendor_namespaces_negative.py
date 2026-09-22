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
    inject_and_clear_db("old.json.test.odm.vendor.namespaces.negative")
    db.cypher_query("MERGE (library:Library {name:'Sponsor', is_editable:true})")

    yield

    drop_db("old.json.test.odm.vendor.namespaces.negative")


def test_create_a_new_odm_vendor_namespace(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "prefix": "prefix",
        "url": "url1",
    }
    response = api_client.post("odms/vendor-namespaces", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmVendorNamespace_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["prefix"] == "prefix"
    assert res["url"] == "url1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_attributes"] == []
    assert res["vendor_elements"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_cannot_create_a_new_odm_vendor_namespace_with_existing_name(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "prefix": "prefix",
        "url": "url",
    }
    response = api_client.post("odms/vendor-namespaces", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "ODM Vendor Namespace with Name 'name1' already exists."


def test_cannot_create_a_new_odm_vendor_namespace_with_existing_prefix(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "name",
        "prefix": "prefix",
        "url": "url",
    }
    response = api_client.post("odms/vendor-namespaces", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "ODM Vendor Namespace with Prefix 'prefix' already exists."


def test_cannot_create_a_new_odm_vendor_namespace_with_existing_url(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "name",
        "prefix": "prefixNew",
        "url": "url1",
    }
    response = api_client.post("odms/vendor-namespaces", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "ODM Vendor Namespace with Url 'url1' already exists."


def test_getting_error_for_retrieving_non_existent_odm_vendor_namespace(api_client):
    response = api_client.get("odms/vendor-namespaces/OdmVendorNamespace_000002")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "OdmVendorNamespaceAR with UID 'OdmVendorNamespace_000002' doesn't exist or there's no version with requested status or version number."
    )


def test_cannot_inactivate_an_odm_vendor_namespace_that_is_in_draft_status(api_client):
    response = api_client.delete(
        "odms/vendor-namespaces/OdmVendorNamespace_000001/activations"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_cannot_reactivate_an_odm_vendor_namespace_that_is_not_retired(api_client):
    response = api_client.post(
        "odms/vendor-namespaces/OdmVendorNamespace_000001/activations"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only RETIRED version can be reactivated."


def test_create_odm_vendor_element_with_relation_to_the_odm_vendor_namespace(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "NewName",
        "compatible_types": ["FormDef"],
        "vendor_namespace_uid": "OdmVendorNamespace_000001",
    }
    response = api_client.post("odms/vendor-elements", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NewName"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_namespace"] == {
        "uid": "OdmVendorNamespace_000001",
        "name": "name1",
        "prefix": "prefix",
        "url": "url1",
        "status": "Draft",
        "version": "0.1",
        "possible_actions": ["approve", "delete", "edit"],
    }
    assert res["vendor_attributes"] == []
    assert res["compatible_types"] == ["FormDef"]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_cannot_delete_an_odm_vendor_namespace_that_is_being_used(api_client):
    response = api_client.delete("odms/vendor-namespaces/OdmVendorNamespace_000001")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "This ODM Vendor Namespace is in use."


def test_cannot_delete_non_existent_odm_vendor_namespace(api_client):
    response = api_client.delete("odms/vendor-namespaces/wrong_uid")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "ODM Vendor Namespace with UID 'wrong_uid' doesn't exist."
