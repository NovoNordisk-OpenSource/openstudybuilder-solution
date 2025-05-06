# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_CT_TERM,
    STARTUP_ODM_ALIASES,
    STARTUP_ODM_DESCRIPTIONS,
    STARTUP_ODM_ITEM_GROUPS,
    STARTUP_ODM_VENDOR_ATTRIBUTES,
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.odm.forms")
    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_CT_TERM)
    db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
    db.cypher_query(STARTUP_ODM_ALIASES)
    db.cypher_query(STARTUP_ODM_ITEM_GROUPS)
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
    db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
    db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)

    yield

    drop_db("old.json.test.odm.forms")


def test_getting_empty_list_of_odm_forms(api_client):
    response = api_client.get("concepts/odms/forms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_creating_a_new_odm_form(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "sdtm_version": "0.1",
        "repeating": "No",
        "scope_uid": "term1",
        "descriptions": ["odm_description2", "odm_description3"],
        "alias_uids": ["odm_alias1"],
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
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_non_empty_list_of_odm_forms(api_client):
    response = api_client.get("concepts/odms/forms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "OdmForm_000001"
    assert res["items"][0]["name"] == "name1"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["oid"] == "oid1"
    assert res["items"][0]["sdtm_version"] == "0.1"
    assert res["items"][0]["repeating"] == "No"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "Initial version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["items"][0]["activity_groups"] == []
    assert res["items"][0]["item_groups"] == []
    assert res["items"][0]["vendor_elements"] == []
    assert res["items"][0]["vendor_attributes"] == []
    assert res["items"][0]["vendor_element_attributes"] == []
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_possible_header_values_of_odm_forms(api_client):
    response = api_client.get("concepts/odms/forms/headers?field_name=name")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == ["name1"]


def test_getting_a_specific_odm_form(api_client):
    response = api_client.get("concepts/odms/forms/OdmForm_000001")

    assert_response_status_code(response, 200)

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
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_versions_of_a_specific_odm_form(api_client):
    response = api_client.get("concepts/odms/forms/OdmForm_000001/versions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "OdmForm_000001"
    assert res[0]["name"] == "name1"
    assert res[0]["library_name"] == "Sponsor"
    assert res[0]["oid"] == "oid1"
    assert res[0]["sdtm_version"] == "0.1"
    assert res[0]["repeating"] == "No"
    assert res[0]["end_date"] is None
    assert res[0]["status"] == "Draft"
    assert res[0]["version"] == "0.1"
    assert res[0]["change_description"] == "Initial version"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res[0]["activity_groups"] == []
    assert res[0]["item_groups"] == []
    assert res[0]["vendor_elements"] == []
    assert res[0]["vendor_attributes"] == []
    assert res[0]["vendor_element_attributes"] == []
    assert res[0]["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_form(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "sdtm_version": "0.1",
        "repeating": "Yes",
        "change_description": "repeating changed to Yes",
        "scope_uid": "term1",
        "descriptions": ["odm_description2", "odm_description3"],
        "alias_uids": ["odm_alias1"],
    }
    response = api_client.patch("concepts/odms/forms/OdmForm_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "repeating changed to Yes"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_approving_an_odm_form(api_client):
    response = api_client.post("concepts/odms/forms/OdmForm_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_inactivating_a_specific_odm_form(api_client):
    response = api_client.delete("concepts/odms/forms/OdmForm_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Inactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["delete", "reactivate"]


def test_reactivating_a_specific_odm_form(api_client):
    response = api_client.post("concepts/odms/forms/OdmForm_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_adding_activity_groups_to_a_specific_odm_form(api_client):
    data = [{"uid": "activity_group_root1"}]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/activity-groups", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root1", "name": "name1"}]
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_overriding_activity_groups_from_a_specific_odm_form(api_client):
    data = [{"uid": "activity_group_root2"}]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/activity-groups?override=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_adding_odm_item_groups_to_a_specific_odm_form(api_client):
    data = [
        {
            "uid": "odm_item_group1",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "No",
            "collection_exception_condition_oid": "collection_exception_condition_oid1",
            "vendor": {"attributes": [{"uid": "odm_vendor_attribute3", "value": "No"}]},
        }
    ]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/item-groups", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group1",
            "oid": "oid1",
            "name": "name1",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid1",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
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


def test_overriding_odm_item_groups_from_a_specific_odm_form(api_client):
    data = [
        {
            "uid": "odm_item_group2",
            "order_number": 2,
            "mandatory": "Yes",
            "locked": "No",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {"attributes": [{"uid": "odm_vendor_attribute3", "value": "No"}]},
        }
    ]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/item-groups?override=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "order_number": 2,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
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


def test_adding_odm_vendor_element_to_a_specific_odm_form(api_client):
    data = [{"uid": "odm_vendor_element2", "value": "value"}]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/vendor-elements", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "order_number": 2,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
                        "vendor_namespace_uid": "odm_vendor_namespace1",
                    }
                ]
            },
        }
    ]
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element2", "name": "nameTwo", "value": "value"}
    ]
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_overriding_odm_vendor_element_from_a_specific_odm_form(api_client):
    data = [{"uid": "odm_vendor_element1", "value": "value"}]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/vendor-elements?override=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "order_number": 2,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
                        "vendor_namespace_uid": "odm_vendor_namespace1",
                    }
                ]
            },
        }
    ]
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "nameOne", "value": "value"}
    ]
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_adding_odm_vendor_attribute_to_a_specific_odm_form(api_client):
    data = [{"uid": "odm_vendor_attribute3", "value": "value"}]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/vendor-attributes", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "order_number": 2,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
                        "vendor_namespace_uid": "odm_vendor_namespace1",
                    }
                ]
            },
        }
    ]
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


def test_overriding_odm_vendor_attribute_from_a_specific_odm_form(api_client):
    data = [{"uid": "odm_vendor_attribute4", "value": "value"}]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/vendor-attributes?override=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "order_number": 2,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
                        "vendor_namespace_uid": "odm_vendor_namespace1",
                    }
                ]
            },
        }
    ]
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


def test_adding_odm_vendor_element_attribute_to_a_specific_odm_form(api_client):
    data = [{"uid": "odm_vendor_attribute1", "value": "value"}]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/vendor-element-attributes", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "order_number": 2,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
                        "vendor_namespace_uid": "odm_vendor_namespace1",
                    }
                ]
            },
        }
    ]
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


def test_overriding_odm_vendor_element_attribute_from_a_specific_odm_form(api_client):
    data = [{"uid": "odm_vendor_attribute2", "value": "value"}]
    response = api_client.post(
        "concepts/odms/forms/OdmForm_000001/vendor-element-attributes?override=true",
        json=data,
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "order_number": 2,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
                        "vendor_namespace_uid": "odm_vendor_namespace1",
                    }
                ]
            },
        }
    ]
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


def test_managing_odm_vendors_of_a_specific_odm_form(api_client):
    data = {
        "elements": [{"uid": "odm_vendor_element3", "value": "value"}],
        "element_attributes": [{"uid": "odm_vendor_attribute7", "value": "value"}],
        "attributes": [{"uid": "odm_vendor_attribute4", "value": "value"}],
    }
    response = api_client.post("concepts/odms/forms/OdmForm_000001/vendors", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "order_number": 2,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
                        "vendor_namespace_uid": "odm_vendor_namespace1",
                    }
                ]
            },
        }
    ]
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


def test_creating_a_new_odm_form_version(api_client):
    response = api_client.post("concepts/odms/forms/OdmForm_000001/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] == {
        "uid": "term1",
        "code_submission_value": "code_submission_value1",
        "preferred_term": "preferred_term1",
    }
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "order_number": 2,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
                        "vendor_namespace_uid": "odm_vendor_namespace1",
                    }
                ]
            },
        }
    ]
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


def test_create_a_new_odm_form_for_deleting_it(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name - delete",
        "oid": "oid2",
        "sdtm_version": "0.1",
        "repeating": "No",
        "scope": None,
        "descriptions": [
            {
                "name": "name - delete",
                "language": "ENG",
                "description": "description - delete",
                "instruction": "instruction - delete",
                "sponsor_instruction": "sponsor_instruction - delete",
            }
        ],
        "alias_uids": [],
    }
    response = api_client.post("concepts/odms/forms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000002"
    assert res["name"] == "name - delete"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid2"
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
            "name": "name - delete",
            "language": "ENG",
            "description": "description - delete",
            "instruction": "instruction - delete",
            "sponsor_instruction": "sponsor_instruction - delete",
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


def test_deleting_a_specific_odm_form(api_client):
    response = api_client.delete("concepts/odms/forms/OdmForm_000002")

    assert_response_status_code(response, 204)


def test_creating_a_new_odm_form_with_relations(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "string",
        "oid": "string",
        "sdtm_version": "0.1",
        "repeating": "No",
        "scope": None,
        "descriptions": [
            {
                "name": "string2",
                "library_name": "Sponsor",
                "language": "DAN",
                "description": "string2",
                "instruction": "string2",
                "sponsor_instruction": "string2",
            },
        ],
        "alias_uids": [],
    }
    response = api_client.post("concepts/odms/forms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmForm_000003"
    assert res["name"] == "string"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "string"
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
            "uid": "OdmDescription_000002",
            "name": "string2",
            "language": "DAN",
            "description": "string2",
            "instruction": "string2",
            "sponsor_instruction": "string2",
            "version": "0.1",
        },
    ]
    assert res["aliases"] == []
    assert res["activity_groups"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_form_with_relations(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "sdtm_version": "0.1",
        "repeating": "Yes",
        "change_description": "repeating changed to Yes",
        "scope_uid": None,
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
    }
    response = api_client.patch("concepts/odms/forms/OdmForm_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.2"
    assert res["change_description"] == "repeating changed to Yes"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["scope"] is None
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
    assert res["activity_groups"] == [{"uid": "activity_group_root2", "name": "name2"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "order_number": 2,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {
                "attributes": [
                    {
                        "uid": "odm_vendor_attribute3",
                        "name": "nameThree",
                        "data_type": "string",
                        "value_regex": "^[a-zA-Z]+$",
                        "value": "No",
                        "vendor_namespace_uid": "odm_vendor_namespace1",
                    }
                ]
            },
        }
    ]
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


def test_create_a_new_odm_study_event_with_relation_to_odm_form(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "effective_date": "2022-04-21",
        "retired_date": "2022-04-21",
        "description": "description1",
    }
    response = api_client.post("concepts/odms/study-events", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_approve_the_odm_study_event(api_client):
    response = api_client.post(
        "concepts/odms/study-events/OdmStudyEvent_000001/approvals"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_add_the_odm_form_to_the_odm_study_event(api_client):
    data = [
        {
            "uid": "OdmForm_000001",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        }
    ]
    response = api_client.post(
        "concepts/odms/study-events/OdmStudyEvent_000001/forms", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == [
        {
            "uid": "OdmForm_000001",
            "name": "name1",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        }
    ]
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_getting_uids_of_a_specific_odm_forms_active_relationships(api_client):
    response = api_client.get("concepts/odms/forms/OdmForm_000001/relationships")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["OdmStudyEvent"] == ["OdmStudyEvent_000001"]


def test_getting_all_odm_forms_that_belongs_to_an_odm_study_event(api_client):
    response = api_client.get("concepts/odms/forms/study-events")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "OdmForm_000001"
    assert res[0]["name"] == "name1"
    assert res[0]["parent_uids"] == ["OdmStudyEvent_000001"]
