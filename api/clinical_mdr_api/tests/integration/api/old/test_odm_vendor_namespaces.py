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
    inject_and_clear_db("old.json.test.odm.vendor.namespaces")
    db.cypher_query("MERGE (library:Library {name:'Sponsor', is_editable:true})")

    yield

    drop_db("old.json.test.odm.vendor.namespaces")


def test_getting_empty_list_of_odm_vendor_namespaces(api_client):
    response = api_client.get("odms/vendor-namespaces")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_creating_a_new_odm_vendor_namespace(api_client):
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


def test_getting_non_empty_list_of_odm_vendor_namespaces(api_client):
    response = api_client.get("odms/vendor-namespaces")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "OdmVendorNamespace_000001"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["name"] == "name1"
    assert res["items"][0]["prefix"] == "prefix"
    assert res["items"][0]["url"] == "url1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "Initial version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["vendor_attributes"] == []
    assert res["items"][0]["vendor_elements"] == []
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_possible_header_values_of_odm_vendor_namespaces(api_client):
    response = api_client.get("odms/vendor-namespaces/headers?field_name=name")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == ["name1"]


def test_getting_a_specific_odm_vendor_namespace(api_client):
    response = api_client.get("odms/vendor-namespaces/OdmVendorNamespace_000001")

    assert_response_status_code(response, 200)

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


def test_getting_versions_of_a_specific_odm_vendor_namespace(api_client):
    response = api_client.get(
        "odms/vendor-namespaces/OdmVendorNamespace_000001/versions"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "OdmVendorNamespace_000001"
    assert res[0]["library_name"] == "Sponsor"
    assert res[0]["name"] == "name1"
    assert res[0]["prefix"] == "prefix"
    assert res[0]["url"] == "url1"
    assert res[0]["end_date"] is None
    assert res[0]["status"] == "Draft"
    assert res[0]["version"] == "0.1"
    assert res[0]["change_description"] == "Initial version"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["vendor_attributes"] == []
    assert res[0]["vendor_elements"] == []
    assert res[0]["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_vendor_namespace(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "prefix": "prefix",
        "url": "new url",
        "change_description": "namespace changed to new url",
    }
    response = api_client.patch(
        "odms/vendor-namespaces/OdmVendorNamespace_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmVendorNamespace_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["prefix"] == "prefix"
    assert res["url"] == "new url"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "namespace changed to new url"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_attributes"] == []
    assert res["vendor_elements"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_a_specific_odm_vendor_namespace_in_specific_version(api_client):
    response = api_client.get(
        "odms/vendor-namespaces/OdmVendorNamespace_000001?version=0.1"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmVendorNamespace_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["prefix"] == "prefix"
    assert res["url"] == "url1"
    assert res["end_date"]
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_attributes"] == []
    assert res["vendor_elements"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_approving_an_odm_vendor_namespace(api_client):
    response = api_client.post(
        "odms/vendor-namespaces/OdmVendorNamespace_000001/approvals"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmVendorNamespace_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["prefix"] == "prefix"
    assert res["url"] == "new url"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_attributes"] == []
    assert res["vendor_elements"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_inactivating_a_specific_odm_vendor_namespace(api_client):
    response = api_client.delete(
        "odms/vendor-namespaces/OdmVendorNamespace_000001/activations"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmVendorNamespace_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["prefix"] == "prefix"
    assert res["url"] == "new url"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Inactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_attributes"] == []
    assert res["vendor_elements"] == []
    assert res["possible_actions"] == ["delete", "reactivate"]


def test_reactivating_a_specific_odm_vendor_namespace(api_client):
    response = api_client.post(
        "odms/vendor-namespaces/OdmVendorNamespace_000001/activations"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmVendorNamespace_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["prefix"] == "prefix"
    assert res["url"] == "new url"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_attributes"] == []
    assert res["vendor_elements"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_creating_a_new_odm_vendor_namespace_version(api_client):
    response = api_client.post(
        "odms/vendor-namespaces/OdmVendorNamespace_000001/versions"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmVendorNamespace_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["prefix"] == "prefix"
    assert res["url"] == "new url"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_attributes"] == []
    assert res["vendor_elements"] == []
    assert res["possible_actions"] == ["approve", "edit"]


def test_create_a_new_odm_vendor_namespace_for_deleting_it(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name - delete",
        "prefix": "prefixOne",
        "url": "namespace2",
    }
    response = api_client.post("odms/vendor-namespaces", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmVendorNamespace_000002"
    assert res["name"] == "name - delete"
    assert res["library_name"] == "Sponsor"
    assert res["prefix"] == "prefixOne"
    assert res["url"] == "namespace2"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_attributes"] == []
    assert res["vendor_elements"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_deleting_a_specific_odm_vendor_namespace(api_client):
    response = api_client.delete("odms/vendor-namespaces/OdmVendorNamespace_000002")

    assert_response_status_code(response, 204)


def test_create_a_new_odm_vendor_attribute_with_relation_to_odm_vendor_namespace(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "nameOne",
        "compatible_types": ["FormDef"],
        "data_type": "string",
        "value_regex": None,
        "vendor_namespace_uid": "OdmVendorNamespace_000001",
    }
    response = api_client.post("odms/vendor-attributes", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmVendorAttribute_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "nameOne"
    assert res["compatible_types"] == ["FormDef"]
    assert res["data_type"] == "string"
    assert res["value_regex"] is None
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_namespace"] == {
        "uid": "OdmVendorNamespace_000001",
        "name": "name1",
        "prefix": "prefix",
        "url": "new url",
        "status": "Draft",
        "version": "1.1",
        "possible_actions": ["approve", "edit"],
    }
    assert res["vendor_element"] is None
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_create_a_new_odm_vendor_element1(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "NameTwo",
        "compatible_types": ["FormDef"],
        "vendor_namespace_uid": "OdmVendorNamespace_000001",
    }
    response = api_client.post("odms/vendor-elements", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmVendorElement_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "NameTwo"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["vendor_namespace"] == {
        "uid": "OdmVendorNamespace_000001",
        "name": "name1",
        "prefix": "prefix",
        "url": "new url",
        "status": "Draft",
        "version": "1.1",
        "possible_actions": ["approve", "edit"],
    }
    assert res["vendor_attributes"] == []
    assert res["compatible_types"] == ["FormDef"]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_uids_of_a_specific_odm_vendor_namespaces_active_relationships(
    api_client,
):
    response = api_client.get(
        "odms/vendor-namespaces/OdmVendorNamespace_000001/relationships"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["OdmVendorElement"] == ["OdmVendorElement_000001"]
    assert res["OdmVendorAttribute"] == ["OdmVendorAttribute_000001"]
