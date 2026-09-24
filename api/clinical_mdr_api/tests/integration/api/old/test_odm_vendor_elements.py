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
    inject_and_clear_db("old.json.test.odm.vendor.elements")
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)

    yield

    drop_db("old.json.test.odm.vendor.elements")


def test_getting_empty_list_of_odm_vendor_elements(api_client):
    response = api_client.get("odms/vendor-elements")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_creating_a_new_odm_vendor_element(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "NameTwo",
        "compatible_types": ["FormDef"],
        "vendor_namespace_uid": "odm_vendor_namespace1",
    }
    response = api_client.post("odms/vendor-elements", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["compatible_types"] == ["FormDef"]
    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NameTwo"
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


def test_creating_a_new_odm_vendor_element_with_relation_to_odm_vendor_element(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "NameThree",
        "compatible_types": ["FormDef"],
        "vendor_namespace_uid": "odm_vendor_namespace1",
    }
    response = api_client.post("odms/vendor-elements", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["compatible_types"] == ["FormDef"]
    assert res["uid"] == "OdmVendorElement_000002"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NameThree"
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


def test_getting_non_empty_list_of_odm_vendor_elements(api_client):
    response = api_client.get("odms/vendor-elements")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["compatible_types"] == ["FormDef"]
    assert res["items"][0]["uid"] == "OdmVendorElement_000001"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["name"] == "NameTwo"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "Initial version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["vendor_namespace"] == {
        "uid": "odm_vendor_namespace1",
        "name": "nameOne",
        "prefix": "prefix",
        "url": "url1",
        "status": "Final",
        "version": "1.0",
        "possible_actions": ["inactivate", "new_version"],
    }
    assert res["items"][0]["vendor_attributes"] == []
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]
    assert res["items"][1]["compatible_types"] == ["FormDef"]
    assert res["items"][1]["end_date"] is None
    assert res["items"][1]["status"] == "Draft"
    assert res["items"][1]["version"] == "0.1"
    assert res["items"][1]["author_username"] == "unknown-user@example.com"
    assert res["items"][1]["change_description"] == "Initial version"
    assert res["items"][1]["uid"] == "OdmVendorElement_000002"
    assert res["items"][1]["name"] == "NameThree"
    assert res["items"][1]["library_name"] == "Sponsor"
    assert res["items"][1]["vendor_namespace"] == {
        "uid": "odm_vendor_namespace1",
        "name": "nameOne",
        "prefix": "prefix",
        "url": "url1",
        "status": "Final",
        "version": "1.0",
        "possible_actions": ["inactivate", "new_version"],
    }
    assert res["items"][1]["vendor_attributes"] == []
    assert res["items"][1]["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_possible_header_values_of_odm_vendor_elements(api_client):
    response = api_client.get("odms/vendor-elements/headers?field_name=name")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == ["NameThree", "NameTwo"]


def test_getting_a_specific_odm_vendor_element(api_client):
    response = api_client.get("odms/vendor-elements/OdmVendorElement_000001")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["compatible_types"] == ["FormDef"]
    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NameTwo"
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


def test_getting_versions_of_a_specific_odm_vendor_element(api_client):
    response = api_client.get("odms/vendor-elements/OdmVendorElement_000001/versions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["compatible_types"] == ["FormDef"]
    assert res[0]["uid"] == "OdmVendorElement_000001"
    assert res[0]["library_name"] == "Sponsor"
    assert res[0]["name"] == "NameTwo"
    assert res[0]["end_date"] is None
    assert res[0]["status"] == "Draft"
    assert res[0]["version"] == "0.1"
    assert res[0]["change_description"] == "Initial version"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["vendor_namespace"] == {
        "uid": "odm_vendor_namespace1",
        "name": "nameOne",
        "prefix": "prefix",
        "url": "url1",
        "status": "Final",
        "version": "1.0",
        "possible_actions": ["inactivate", "new_version"],
    }
    assert res[0]["vendor_attributes"] == []
    assert res[0]["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_vendor_element(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "NewName",
        "compatible_types": ["ItemDef"],
        "vendor_namespace_uid": "odm_vendor_namespace1",
        "change_description": "name changed to NewName",
    }
    response = api_client.patch(
        "odms/vendor-elements/OdmVendorElement_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["compatible_types"] == ["ItemDef"]
    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NewName"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "name changed to NewName"
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


def test_getting_a_specific_odm_vendor_element_in_specific_version(api_client):
    response = api_client.get(
        "odms/vendor-elements/OdmVendorElement_000001?version=0.1"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["compatible_types"] == ["FormDef"]
    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NameTwo"
    assert res["end_date"]
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


def test_approving_an_odm_vendor_element(api_client):
    response = api_client.post("odms/vendor-elements/OdmVendorElement_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["compatible_types"] == ["ItemDef"]
    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NewName"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
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
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_inactivating_a_specific_odm_vendor_element(api_client):
    response = api_client.delete(
        "odms/vendor-elements/OdmVendorElement_000001/activations"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["compatible_types"] == ["ItemDef"]
    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NewName"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Inactivated version"
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
    assert res["possible_actions"] == ["delete", "reactivate"]


def test_reactivating_a_specific_odm_vendor_element(api_client):
    response = api_client.post(
        "odms/vendor-elements/OdmVendorElement_000001/activations"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["compatible_types"] == ["ItemDef"]
    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NewName"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
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
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_creating_a_new_odm_vendor_element_version(api_client):
    response = api_client.post("odms/vendor-elements/OdmVendorElement_000001/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["compatible_types"] == ["ItemDef"]
    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NewName"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
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
    assert res["possible_actions"] == ["approve", "edit"]


def test_create_a_new_odm_vendor_element_for_deleting_it(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "NameDelete",
        "compatible_types": ["FormDef"],
        "vendor_namespace_uid": "odm_vendor_namespace1",
    }
    response = api_client.post("odms/vendor-elements", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["compatible_types"] == ["FormDef"]
    assert res["uid"] == "OdmVendorElement_000003"
    assert res["name"] == "NameDelete"
    assert res["library_name"] == "Sponsor"
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


def test_deleting_a_specific_odm_vendor_element(api_client):
    response = api_client.delete("odms/vendor-elements/OdmVendorElement_000002")

    assert_response_status_code(response, 204)


def test_create_a_new_odm_vendor_attribute_with_relation_to_odm_vendor_element(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "nameOne",
        "compatible_types": [],
        "data_type": "string",
        "value_regex": None,
        "vendor_element_uid": "OdmVendorElement_000001",
    }
    response = api_client.post("odms/vendor-attributes", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmVendorAttribute_000001"
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
        "uid": "OdmVendorElement_000001",
        "name": "NewName",
        "compatible_types": ["ItemDef"],
        "status": "Draft",
        "version": "1.1",
        "possible_actions": ["approve", "edit"],
    }
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_uids_of_a_specific_odm_vendor_elements_active_relationships(
    api_client,
):
    response = api_client.get(
        "odms/vendor-elements/OdmVendorElement_000001/relationships"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["OdmVendorNamespace"] == ["odm_vendor_namespace1"]
    assert res["OdmVendorAttribute"] == ["OdmVendorAttribute_000001"]
