# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM,
    STARTUP_ODM_ITEMS,
    STARTUP_ODM_VENDOR_ATTRIBUTES,
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.odm.item.groups")
    db.cypher_query(STARTUP_ODM_ITEMS)
    db.cypher_query(STARTUP_CT_TERM)
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
    db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
    db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)
    catalogue_name = "SDTM CT"
    library_name = "Sponsor"
    codelist = create_codelist(
        name="SDTM Domain Abbreviation",
        uid="C66734",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="DOMAIN",
    )
    create_ct_term(
        name="domain",
        uid="domain001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "XX",
            }
        ],
    )
    yield

    drop_db("old.json.test.odm.item.groups")


def test_getting_empty_list_of_odm_item_groups(api_client):
    response = api_client.get("odms/item-groups")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_creating_a_new_odm_item_group(api_client):
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
        "sdtm_domain_uids": ["domain001"],
        "vendor_elements": [{"uid": "odm_vendor_element1", "value": "value"}],
        "vendor_element_attributes": [
            {"uid": "odm_vendor_attribute2", "value": "value"}
        ],
        "vendor_attributes": [{"uid": "odm_vendor_attribute4", "value": "value"}],
    }
    response = api_client.post("odms/item-groups", json=data)

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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == []
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


def test_getting_non_empty_list_of_odm_item_groups(api_client):
    response = api_client.get("odms/item-groups")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "OdmItemGroup_000001"
    assert res["items"][0]["name"] == "name1"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["oid"] == "oid1"
    assert res["items"][0]["repeating"] == "No"
    assert res["items"][0]["is_reference_data"] == "No"
    assert res["items"][0]["sas_dataset_name"] == "sas_dataset_name1"
    assert res["items"][0]["origin"] == "origin1"
    assert res["items"][0]["purpose"] == "purpose1"
    assert res["items"][0]["comment"] == "comment1"
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
    assert res["items"][0]["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"][0]["items"] == []
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


def test_getting_possible_header_values_of_odm_item_groups(api_client):
    response = api_client.get("odms/item-groups/headers?field_name=name")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == ["name1"]


def test_getting_a_specific_odm_item_group(api_client):
    response = api_client.get("odms/item-groups/OdmItemGroup_000001")

    assert_response_status_code(response, 200)

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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == []
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


def test_getting_versions_of_a_specific_odm_item_group(api_client):
    response = api_client.get("odms/item-groups/OdmItemGroup_000001/versions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "OdmItemGroup_000001"
    assert res[0]["name"] == "name1"
    assert res[0]["library_name"] == "Sponsor"
    assert res[0]["oid"] == "oid1"
    assert res[0]["repeating"] == "No"
    assert res[0]["is_reference_data"] == "No"
    assert res[0]["sas_dataset_name"] == "sas_dataset_name1"
    assert res[0]["origin"] == "origin1"
    assert res[0]["purpose"] == "purpose1"
    assert res[0]["comment"] == "comment1"
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
    assert res[0]["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res[0]["items"] == []
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


def test_updating_an_existing_odm_item_group(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "repeating": "Yes",
        "is_reference_data": "Yes",
        "sas_dataset_name": "sas_dataset_name1",
        "origin": "origin1",
        "purpose": "purpose1",
        "comment": "comment1",
        "change_description": "repeating and is_reference_data changed to Yes",
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
        "sdtm_domain_uids": ["domain001"],
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
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "Yes"
    assert res["is_reference_data"] == "Yes"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "repeating and is_reference_data changed to Yes"
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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == []
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


def test_getting_a_specific_odm_item_group_in_specific_version(api_client):
    response = api_client.get("odms/item-groups/OdmItemGroup_000001?version=0.1")

    assert_response_status_code(response, 200)

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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_adding_odm_items_to_a_specific_odm_item_group(api_client):
    data = [
        {
            "uid": "odm_item1",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "key_sequence1",
            "method_oid": "method_oid1",
            "imputation_method_oid": "imputation_method_oid1",
            "role": "role1",
            "role_codelist_oid": "role_codelist_oid1",
            "collection_exception_condition_oid": "collection_exception_condition_oid1",
            "vendor": {
                "attributes": [{"uid": "odm_vendor_attribute3", "value": "Yes"}]
            },
        }
    ]
    response = api_client.post("odms/item-groups/OdmItemGroup_000001/items", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "Yes"
    assert res["is_reference_data"] == "Yes"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "repeating and is_reference_data changed to Yes"
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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == [
        {
            "uid": "odm_item1",
            "oid": "oid1",
            "name": "name1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "key_sequence1",
            "method_oid": "method_oid1",
            "imputation_method_oid": "imputation_method_oid1",
            "role": "role1",
            "role_codelist_oid": "role_codelist_oid1",
            "collection_exception_condition_oid": "collection_exception_condition_oid1",
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


def test_overriding_odm_items_from_a_specific_odm_item_group(api_client):
    data = [
        {
            "uid": "odm_item2",
            "order_number": 2,  # this order number should be overridden by the API to 1, since it's the only form in the request
            "mandatory": "Yes",
            "key_sequence": "key_sequence2",
            "method_oid": "method_oid2",
            "imputation_method_oid": "imputation_method_oid2",
            "role": "role2",
            "role_codelist_oid": "role_codelist_oid2",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
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
    response = api_client.post(
        "odms/item-groups/OdmItemGroup_000001/items?override=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "Yes"
    assert res["is_reference_data"] == "Yes"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "repeating and is_reference_data changed to Yes"
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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == [
        {
            "uid": "odm_item2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "key_sequence2",
            "method_oid": "method_oid2",
            "imputation_method_oid": "imputation_method_oid2",
            "role": "role2",
            "role_codelist_oid": "role_codelist_oid2",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
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


def test_approving_an_odm_item_group(api_client):
    response = api_client.post("odms/item-groups/OdmItemGroup_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "Yes"
    assert res["is_reference_data"] == "Yes"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == [
        {
            "uid": "odm_item2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "key_sequence2",
            "method_oid": "method_oid2",
            "imputation_method_oid": "imputation_method_oid2",
            "role": "role2",
            "role_codelist_oid": "role_codelist_oid2",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
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
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_inactivating_a_specific_odm_item_group(api_client):
    response = api_client.delete("odms/item-groups/OdmItemGroup_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "Yes"
    assert res["is_reference_data"] == "Yes"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == [
        {
            "uid": "odm_item2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "key_sequence2",
            "method_oid": "method_oid2",
            "imputation_method_oid": "imputation_method_oid2",
            "role": "role2",
            "role_codelist_oid": "role_codelist_oid2",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
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
    assert res["possible_actions"] == ["delete", "reactivate"]


def test_reactivating_a_specific_odm_item_group(api_client):
    response = api_client.post("odms/item-groups/OdmItemGroup_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "Yes"
    assert res["is_reference_data"] == "Yes"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == [
        {
            "uid": "odm_item2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "key_sequence2",
            "method_oid": "method_oid2",
            "imputation_method_oid": "imputation_method_oid2",
            "role": "role2",
            "role_codelist_oid": "role_codelist_oid2",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
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
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_getting_minimal_response_for_item_groups(api_client):
    response = api_client.get(
        "odms/item-groups/OdmItemGroup_000001?fields=oid,name,sdtm_domains,translated_texts,aliases,vendor_elements,vendor_attributes,vendor_element_attributes,items"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
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
    assert res["sdtm_domains"] == [
        {
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
            "submission_value": "XX",
        }
    ]
    assert res["items"] == [
        {
            "uid": "odm_item2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "key_sequence2",
            "method_oid": "method_oid2",
            "imputation_method_oid": "imputation_method_oid2",
            "role": "role2",
            "role_codelist_oid": "role_codelist_oid2",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
            "vendor": {"attributes": []},
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
        },
    ]
    assert res["vendor_element_attributes"] == [
        {
            "data_type": "string",
            "name": "nameSeven",
            "uid": "odm_vendor_attribute7",
            "value": "value",
            "value_regex": None,
        },
    ]


def test_creating_a_new_odm_item_group_version(api_client):
    response = api_client.post("odms/item-groups/OdmItemGroup_000001/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "Yes"
    assert res["is_reference_data"] == "Yes"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == [
        {
            "uid": "odm_item2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "key_sequence2",
            "method_oid": "method_oid2",
            "imputation_method_oid": "imputation_method_oid2",
            "role": "role2",
            "role_codelist_oid": "role_codelist_oid2",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
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
    assert res["possible_actions"] == ["approve", "edit"]


def test_create_a_new_odm_item_group_for_deleting_it(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1 - delete",
        "oid": "oid2",
        "repeating": "No",
        "is_reference_data": "No",
        "sas_dataset_name": "sas_dataset_name1",
        "origin": "origin1",
        "purpose": "purpose1",
        "comment": "comment1",
        "translated_texts": [
            {
                "text_type": "Description",
                "language": "eng",
                "text": "name - delete",
            }
        ],
        "aliases": [],
        "sdtm_domain_uids": [],
    }
    response = api_client.post("odms/item-groups", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000002"
    assert res["name"] == "name1 - delete"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid2"
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
    assert res["translated_texts"] == [
        {
            "text_type": "Description",
            "language": "eng",
            "text": "name - delete",
        }
    ]
    assert res["aliases"] == []
    assert res["sdtm_domains"] == []
    assert res["items"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_deleting_a_specific_odm_item_group(api_client):
    response = api_client.delete("odms/item-groups/OdmItemGroup_000002")

    assert_response_status_code(response, 204)


def test_creating_a_new_odm_item_group_with_relations(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "string",
        "oid": "string",
        "repeating": "No",
        "is_reference_data": "No",
        "sas_dataset_name": "string",
        "origin": "string",
        "purpose": "string",
        "comment": "string",
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
        "sdtm_domain_uids": [],
    }
    response = api_client.post("odms/item-groups", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000003"
    assert res["name"] == "string"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "string"
    assert res["repeating"] == "No"
    assert res["is_reference_data"] == "No"
    assert res["sas_dataset_name"] == "string"
    assert res["origin"] == "string"
    assert res["purpose"] == "string"
    assert res["comment"] == "string"
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
    assert res["sdtm_domains"] == []
    assert res["items"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_item_group_with_relations(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "repeating": "Yes",
        "is_reference_data": "Yes",
        "sas_dataset_name": "sas_dataset_name1",
        "origin": "origin1",
        "purpose": "purpose1",
        "comment": "comment1",
        "change_description": "repeating and is_reference_data changed to Yes",
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
        "sdtm_domain_uids": ["domain001"],
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
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "Yes"
    assert res["is_reference_data"] == "Yes"
    assert res["sas_dataset_name"] == "sas_dataset_name1"
    assert res["origin"] == "origin1"
    assert res["purpose"] == "purpose1"
    assert res["comment"] == "comment1"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "3.2"
    assert res["change_description"] == "repeating and is_reference_data changed to Yes"
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
    assert res["sdtm_domains"] == [
        {
            "codelist_name": "SDTM Domain Abbreviation",
            "codelist_submission_value": "DOMAIN",
            "codelist_uid": "C66734",
            "date_conflict": False,
            "order": 1,
            "queried_effective_date": None,
            "submission_value": "XX",
            "preferred_term": "test",
            "term_name": "domain",
            "term_uid": "domain001",
        }
    ]
    assert res["items"] == [
        {
            "uid": "odm_item2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "key_sequence2",
            "method_oid": "method_oid2",
            "imputation_method_oid": "imputation_method_oid2",
            "role": "role2",
            "role_codelist_oid": "role_codelist_oid2",
            "collection_exception_condition_oid": "collection_exception_condition_oid2",
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
    assert res["possible_actions"] == ["approve", "edit"]


def test_create_a_new_odm_form_with_relation_to_odm_item_group(api_client):
    data: dict[str, str | list[Any] | None] = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "sdtm_version": "0.1",
        "repeating": "No",
        "translated_texts": [],
        "aliases": [],
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
    assert res["translated_texts"] == []
    assert res["aliases"] == []
    assert res["item_groups"] == []
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_add_the_odm_item_group_to_the_odm_form(api_client):
    data = [
        {
            "uid": "OdmItemGroup_000001",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
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
    response = api_client.post("odms/forms/OdmForm_000001/item-groups", json=data)

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
    assert res["translated_texts"] == []
    assert res["aliases"] == []
    assert res["item_groups"] == [
        {
            "uid": "OdmItemGroup_000001",
            "oid": "oid1",
            "name": "name1",
            "version": "3.2",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
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
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_uids_of_a_specific_odm_item_groups_active_relationships(api_client):
    response = api_client.get("odms/item-groups/OdmItemGroup_000001/relationships")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["OdmForm"] == ["OdmForm_000001"]


def test_getting_all_odm_item_groups_that_belongs_to_an_odm_form(api_client):
    response = api_client.get("odms/item-groups/forms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "OdmItemGroup_000001"
    assert res[0]["name"] == "name1"
    assert res[0]["parent_uids"] == ["OdmForm_000001"]
