# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM,
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
    db.cypher_query(STARTUP_CT_TERM)
    db.cypher_query(STARTUP_ODM_ITEM_GROUPS)
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
    db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
    db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)

    yield

    drop_db("old.json.test.odm.forms")


def test_getting_empty_list_of_odm_forms(api_client):
    response = api_client.get("odms/forms")

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
        "vendor_elements": [{"uid": "odm_vendor_element1", "value": "value"}],
        "vendor_element_attributes": [
            {"uid": "odm_vendor_attribute2", "value": "value"}
        ],
        "vendor_attributes": [{"uid": "odm_vendor_attribute4", "value": "value"}],
    }
    response = api_client.post("odms/forms", json=data)

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
    assert res["item_groups"] == []
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "NameOne", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "value": "value",
            "value_regex": None,
            "data_type": "string",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute2",
            "name": "nameTwo",
            "value": "value",
            "value_regex": None,
            "data_type": "string",
            "vendor_element_uid": "odm_vendor_element1",
        }
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_non_empty_list_of_odm_forms(api_client):
    response = api_client.get("odms/forms")

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
    assert res["items"][0]["item_groups"] == []
    assert res["items"][0]["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "NameOne", "value": "value"}
    ]
    assert res["items"][0]["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "value": "value",
            "value_regex": None,
            "data_type": "string",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res["items"][0]["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute2",
            "name": "nameTwo",
            "value": "value",
            "value_regex": None,
            "data_type": "string",
            "vendor_element_uid": "odm_vendor_element1",
        }
    ]
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_possible_header_values_of_odm_forms(api_client):
    response = api_client.get("odms/forms/headers?field_name=name")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == ["name1"]


def test_getting_a_specific_odm_form(api_client):
    response = api_client.get("odms/forms/OdmForm_000001")

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
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "NameOne", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "value": "value",
            "value_regex": None,
            "data_type": "string",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute2",
            "name": "nameTwo",
            "value": "value",
            "value_regex": None,
            "data_type": "string",
            "vendor_element_uid": "odm_vendor_element1",
        }
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_versions_of_a_specific_odm_form(api_client):
    response = api_client.get("odms/forms/OdmForm_000001/versions")

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
    assert res[0]["item_groups"] == []
    assert res[0]["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "NameOne", "value": "value"}
    ]
    assert res[0]["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "value": "value",
            "value_regex": None,
            "data_type": "string",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        }
    ]
    assert res[0]["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute2",
            "name": "nameTwo",
            "value": "value",
            "value_regex": None,
            "data_type": "string",
            "vendor_element_uid": "odm_vendor_element1",
        }
    ]
    assert res[0]["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_form(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "sdtm_version": "0.1",
        "repeating": "Yes",
        "change_description": "repeating changed to Yes",
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
        "vendor_elements": [
            {"uid": "odm_vendor_element3", "value": "value"},
        ],
        "vendor_element_attributes": [
            {"uid": "odm_vendor_attribute7", "value": "value"},
        ],
        "vendor_attributes": [
            {"uid": "odm_vendor_attribute3", "value": "value"},
        ],
    }
    response = api_client.patch("odms/forms/OdmForm_000001", json=data)

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
    assert res["item_groups"] == []
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element3", "name": "NameThree", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "data_type": "string",
            "name": "nameThree",
            "uid": "odm_vendor_attribute3",
            "value": "value",
            "value_regex": "^[a-zA-Z]+$",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        },
    ]
    assert res["vendor_element_attributes"] == [
        {
            "data_type": "string",
            "name": "nameSeven",
            "uid": "odm_vendor_attribute7",
            "value": "value",
            "value_regex": None,
            "vendor_element_uid": "odm_vendor_element3",
        },
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_a_specific_odm_form_in_specific_version(api_client):
    response = api_client.get("odms/forms/OdmForm_000001?version=0.1")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "No"
    assert res["end_date"]
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
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
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


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
    response = api_client.post("odms/forms/OdmForm_000001/item-groups", json=data)

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
    assert res["version"] == "0.2"
    assert res["change_description"] == "repeating changed to Yes"
    assert res["author_username"] == "unknown-user@example.com"
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
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group1",
            "oid": "oid1",
            "name": "name1",
            "version": "1.0",
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
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element3", "name": "NameThree", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "data_type": "string",
            "name": "nameThree",
            "uid": "odm_vendor_attribute3",
            "value": "value",
            "value_regex": "^[a-zA-Z]+$",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        },
    ]
    assert res["vendor_element_attributes"] == [
        {
            "data_type": "string",
            "name": "nameSeven",
            "uid": "odm_vendor_attribute7",
            "value": "value",
            "value_regex": None,
            "vendor_element_uid": "odm_vendor_element3",
        },
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_overriding_odm_item_groups_from_a_specific_odm_form(api_client):
    data = [
        {
            "uid": "odm_item_group2",
            "order_number": 2,  # this order number should be overridden by the API to 1, since it's the only form in the request
            "mandatory": "Yes",
            "locked": "No",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {"attributes": [{"uid": "odm_vendor_attribute3", "value": "No"}]},
        }
    ]
    response = api_client.post(
        "odms/forms/OdmForm_000001/item-groups?override=true", json=data
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
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "repeating changed to Yes"
    assert res["author_username"] == "unknown-user@example.com"
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
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
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
        {"uid": "odm_vendor_element3", "name": "NameThree", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "data_type": "string",
            "name": "nameThree",
            "uid": "odm_vendor_attribute3",
            "value": "value",
            "value_regex": "^[a-zA-Z]+$",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        },
    ]
    assert res["vendor_element_attributes"] == [
        {
            "data_type": "string",
            "name": "nameSeven",
            "uid": "odm_vendor_attribute7",
            "value": "value",
            "value_regex": None,
            "vendor_element_uid": "odm_vendor_element3",
        },
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_managing_odm_vendors_of_a_specific_odm_form(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "sdtm_version": "0.1",
        "repeating": "Yes",
        "change_description": "repeating changed to Yes",
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
        "vendor_elements": [{"uid": "odm_vendor_element3", "value": "value"}],
        "vendor_element_attributes": [
            {"uid": "odm_vendor_attribute7", "value": "value"}
        ],
        "vendor_attributes": [{"uid": "odm_vendor_attribute4", "value": "value"}],
    }
    response = api_client.patch("odms/forms/OdmForm_000001", json=data)

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
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
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
        {"uid": "odm_vendor_element3", "name": "NameThree", "value": "value"}
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
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_approving_an_odm_form(api_client):
    response = api_client.post("odms/forms/OdmForm_000001/approvals")

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
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
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
        {"uid": "odm_vendor_element3", "name": "NameThree", "value": "value"}
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


def test_inactivating_a_specific_odm_form(api_client):
    response = api_client.delete("odms/forms/OdmForm_000001/activations")

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
    assert res["version"] == "2.0"
    assert res["change_description"] == "Inactivated version"
    assert res["author_username"] == "unknown-user@example.com"
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
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
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
        {"uid": "odm_vendor_element3", "name": "NameThree", "value": "value"}
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
    assert res["possible_actions"] == ["delete", "reactivate"]


def test_reactivating_a_specific_odm_form(api_client):
    response = api_client.post("odms/forms/OdmForm_000001/activations")

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
    assert res["version"] == "3.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
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
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
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
        {"uid": "odm_vendor_element3", "name": "NameThree", "value": "value"}
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


def test_getting_minimal_response_for_form(api_client):
    response = api_client.get(
        "odms/forms/OdmForm_000001?fields=oid,name,sdtm_version,repeating,translated_texts,aliases,vendor_elements,vendor_attributes,vendor_element_attributes,item_groups"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmForm_000001"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["sdtm_version"] == "0.1"
    assert res["repeating"] == "Yes"
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
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {"attributes": []},
        }
    ]
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element3", "name": "NameThree", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "uid": "odm_vendor_attribute4",
            "name": "nameFour",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
        }
    ]
    assert res["vendor_element_attributes"] == [
        {
            "uid": "odm_vendor_attribute7",
            "name": "nameSeven",
            "data_type": "string",
            "value_regex": None,
            "value": "value",
        }
    ]


def test_creating_a_new_odm_form_version(api_client):
    response = api_client.post("odms/forms/OdmForm_000001/versions")

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
    assert res["version"] == "3.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
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
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
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
        {"uid": "odm_vendor_element3", "name": "NameThree", "value": "value"}
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
        "translated_texts": [
            {
                "text_type": "Description",
                "language": "eng",
                "text": "name - delete",
            }
        ],
        "aliases": [],
    }
    response = api_client.post("odms/forms", json=data)

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
    assert res["translated_texts"] == [
        {
            "text_type": "Description",
            "language": "eng",
            "text": "name - delete",
        }
    ]
    assert res["aliases"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_deleting_a_specific_odm_form(api_client):
    response = api_client.delete("odms/forms/OdmForm_000002")

    assert_response_status_code(response, 204)


def test_creating_a_new_odm_form_with_relations(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "string",
        "oid": "string",
        "sdtm_version": "0.1",
        "repeating": "No",
        "translated_texts": [
            {"text_type": "Description", "language": "eng", "text": "string1"},
            {"text_type": "Description", "language": "dan", "text": "string2"},
            {
                "text_type": "osb:CompletionInstructions",
                "language": "eng",
                "text": "string1",
            },
            {
                "text_type": "osb:CompletionInstructions",
                "language": "dan",
                "text": "string2",
            },
            {"text_type": "osb:DesignNotes", "language": "eng", "text": "string1"},
            {"text_type": "osb:DesignNotes", "language": "dan", "text": "string2"},
            {"text_type": "osb:DisplayText", "language": "eng", "text": "string1"},
            {"text_type": "osb:DisplayText", "language": "dan", "text": "string2"},
        ],
        "aliases": [],
    }
    response = api_client.post("odms/forms", json=data)

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
    assert res["translated_texts"] == [
        {"text_type": "Description", "language": "eng", "text": "string1"},
        {"text_type": "Description", "language": "dan", "text": "string2"},
        {
            "text_type": "osb:CompletionInstructions",
            "language": "eng",
            "text": "string1",
        },
        {
            "text_type": "osb:CompletionInstructions",
            "language": "dan",
            "text": "string2",
        },
        {"text_type": "osb:DesignNotes", "language": "eng", "text": "string1"},
        {"text_type": "osb:DesignNotes", "language": "dan", "text": "string2"},
        {"text_type": "osb:DisplayText", "language": "eng", "text": "string1"},
        {"text_type": "osb:DisplayText", "language": "dan", "text": "string2"},
    ]
    assert res["aliases"] == []
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
        "translated_texts": [
            {"text_type": "Description", "language": "eng", "text": "string2"},
            {"text_type": "Description", "language": "ara", "text": "string3"},
            {
                "text_type": "osb:CompletionInstructions",
                "language": "eng",
                "text": "string2",
            },
            {
                "text_type": "osb:CompletionInstructions",
                "language": "dan",
                "text": "string3",
            },
            {"text_type": "osb:DesignNotes", "language": "eng", "text": "string2"},
            {"text_type": "osb:DesignNotes", "language": "ara", "text": "string3"},
            {"text_type": "osb:DisplayText", "language": "eng", "text": "string2"},
            {"text_type": "osb:DisplayText", "language": "ara", "text": "string3"},
        ],
        "aliases": [{"context": "context1", "name": "name1"}],
        "vendor_elements": [
            {"uid": "odm_vendor_element3", "value": "value"},
        ],
        "vendor_element_attributes": [
            {"uid": "odm_vendor_attribute7", "value": "value"},
        ],
        "vendor_attributes": [
            {"uid": "odm_vendor_attribute3", "value": "value"},
        ],
    }
    response = api_client.patch("odms/forms/OdmForm_000001", json=data)

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
    assert res["version"] == "3.2"
    assert res["change_description"] == "repeating changed to Yes"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["translated_texts"] == [
        {"text_type": "Description", "language": "eng", "text": "string2"},
        {"text_type": "Description", "language": "ara", "text": "string3"},
        {
            "text_type": "osb:CompletionInstructions",
            "language": "eng",
            "text": "string2",
        },
        {
            "text_type": "osb:CompletionInstructions",
            "language": "dan",
            "text": "string3",
        },
        {"text_type": "osb:DesignNotes", "language": "eng", "text": "string2"},
        {"text_type": "osb:DesignNotes", "language": "ara", "text": "string3"},
        {"text_type": "osb:DisplayText", "language": "eng", "text": "string2"},
        {"text_type": "osb:DisplayText", "language": "ara", "text": "string3"},
    ]
    assert res["aliases"] == [{"context": "context1", "name": "name1"}]
    assert res["item_groups"] == [
        {
            "uid": "odm_item_group2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
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
        {"uid": "odm_vendor_element3", "name": "NameThree", "value": "value"}
    ]
    assert res["vendor_attributes"] == [
        {
            "data_type": "string",
            "name": "nameThree",
            "uid": "odm_vendor_attribute3",
            "value": "value",
            "value_regex": "^[a-zA-Z]+$",
            "vendor_namespace_uid": "odm_vendor_namespace1",
        },
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
    response = api_client.post("odms/study-events", json=data)

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
        "odms/study-events/OdmStudyEvent_000001/forms", json=data
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
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == [
        {
            "uid": "OdmForm_000001",
            "oid": "oid1",
            "name": "name1",
            "version": "3.2",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        }
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_uids_of_a_specific_odm_forms_active_relationships(api_client):
    response = api_client.get("odms/forms/OdmForm_000001/relationships")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["OdmStudyEvent"] == ["OdmStudyEvent_000001"]


def test_getting_all_odm_forms_that_belongs_to_an_odm_study_event(api_client):
    response = api_client.get("odms/forms/study-events")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "OdmForm_000001"
    assert res[0]["name"] == "name1"
    assert res[0]["parent_uids"] == ["OdmStudyEvent_000001"]
