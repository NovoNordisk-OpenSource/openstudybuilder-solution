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
    inject_and_clear_db("old.json.test.odm.item.groups.negative")
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

    drop_db("old.json.test.odm.item.groups.negative")


def test_create_a_new_odm_item_group(api_client):
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
    }
    response = api_client.post("odms/item-groups", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
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
    assert res["vendor_elements"] == []
    assert res["vendor_attributes"] == []
    assert res["vendor_element_attributes"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_cannot_add_odm_vendor_attribute_with_an_invalid_value_to_an_odm_item_group(
    api_client,
):
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
        "vendor_elements": [],
        "vendor_element_attributes": [],
        "vendor_attributes": [{"uid": "odm_vendor_attribute3", "value": "3423"}],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == """Provided values for following attributes don't match their regex pattern:

{'odm_vendor_attribute3': '^[a-zA-Z]+$'}"""
    )


def test_cannot_add_a_non_compatible_odm_vendor_attribute_to_an_odm_item_group(
    api_client,
):
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
        "vendor_elements": [],
        "vendor_element_attributes": [],
        "vendor_attributes": [{"uid": "odm_vendor_attribute5", "value": "value"}],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == """Trying to add non-compatible ODM Vendor:

{'odm_vendor_attribute5': ['NonCompatibleVendor']}"""


def test_cannot_add_a_non_compatible_odm_vendor_element_to_an_odm_item_group(
    api_client,
):
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
        "vendor_elements": [{"uid": "odm_vendor_element4", "value": "value"}],
        "vendor_element_attributes": [],
        "vendor_attributes": [{"uid": "odm_vendor_attribute3", "value": "3423"}],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == """Trying to add non-compatible ODM Vendor:

{'odm_vendor_element4': ['NonCompatibleVendor']}"""


def test_cannot_add_odm_item_that_is_already_connected_to_an_odm_item_group(
    api_client,
):
    response = api_client.post(
        "odms/item-groups",
        json={
            "library_name": "Sponsor",
            "name": "name2",
            "oid": "oid2",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "",
            "origin": "",
            "purpose": "",
            "comment": "",
            "translated_texts": [],
            "aliases": [],
            "sdtm_domain_uids": [],
        },
    )

    assert_response_status_code(response, 201)

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
            "vendor": {"attributes": []},
        }
    ]
    response = api_client.post("odms/item-groups/OdmItemGroup_000002/items", json=data)

    assert_response_status_code(response, 201)

    response = api_client.post("odms/item-groups/OdmItemGroup_000001/items", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "OdmItem with UID 'odm_item1' is already connected to another OdmItemGroup."
    )


def test_cannot_add_odm_item_with_non_compatible_odm_vendor_attribute_to_a_specific_odm_item_group(
    api_client,
):
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
            "vendor": {"attributes": [{"uid": "odm_vendor_attribute5", "value": "No"}]},
        }
    ]
    response = api_client.post("odms/item-groups/OdmItemGroup_000001/items", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == """Trying to add non-compatible ODM Vendor:

{'odm_vendor_attribute5': ['NonCompatibleVendor']}"""


def test_cannot_add_odm_vendor_element_attribute_with_an_invalid_value_to_an_odm_item_group(
    api_client,
):
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
        "vendor_elements": [],
        "vendor_element_attributes": [],
        "vendor_attributes": [{"uid": "odm_vendor_attribute1", "value": "3423"}],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == """Provided values for following attributes don't match their regex pattern:

{'odm_vendor_attribute1': '^[a-zA-Z]+$'}"""
    )


def test_add_odm_vendor_element_to_an_odm_item_group(api_client):
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
        "vendor_elements": [{"uid": "odm_vendor_element1", "value": "value1"}],
        "vendor_element_attributes": [
            {"uid": "odm_vendor_attribute1", "value": "valueOne"}
        ],
        "vendor_attributes": [],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
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
        {"uid": "odm_vendor_element1", "name": "NameOne", "value": "value1"}
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


def test_cannot_create_a_new_odm_item_group_with_same_properties(api_client):
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
    }
    response = api_client.post("odms/item-groups", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "ODM Item Group with OID 'oid1' already exists in library 'Sponsor' with UID (OdmItemGroup_000001)"
    )


def test_cannot_create_an_odm_item_group_connected_to_non_existent_sdtm_domain(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "new name",
        "oid": "new oid",
        "repeating": "No",
        "is_reference_data": "No",
        "sas_dataset_name": "sas_dataset_name1",
        "origin": "origin1",
        "purpose": "purpose1",
        "comment": "comment1",
        "translated_texts": [],
        "aliases": [],
        "sdtm_domain_uids": ["wrong_uid"],
    }
    response = api_client.post("odms/item-groups", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "ODM Item Group tried to connect to non-existent SDTM Domain with UID 'wrong_uid'."
    )


def test_cannot_create_a_new_odm_item_group_without_an_english_description(api_client):
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
                "language": "DAN",
                "text": "description - non-eng",
            },
        ],
        "aliases": [],
        "sdtm_domain_uids": [],
    }
    response = api_client.post("odms/item-groups", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "A Translated Text with text_type Description and language English ('eng' or 'en') must be provided."
    )


def test_getting_error_for_retrieving_non_existent_odm_item_group(api_client):
    response = api_client.get("odms/item-groups/OdmItemGroup_000003")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "OdmItemGroupAR with UID 'OdmItemGroup_000003' doesn't exist or there's no version with requested status or version number."
    )


def test_cannot_inactivate_an_odm_item_group_that_is_in_draft_status(api_client):
    response = api_client.delete("odms/item-groups/OdmItemGroup_000001/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_cannot_reactivate_an_odm_item_group_that_is_not_retired(api_client):
    response = api_client.post("odms/item-groups/OdmItemGroup_000001/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only RETIRED version can be reactivated."


def test_cannot_override_odm_vendor_element_that_has_attributes_connected_this_odm_item_group(
    api_client,
):
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
        "vendor_elements": [{"uid": "odm_vendor_element2", "value": "value"}],
        "vendor_element_attributes": [
            {"uid": "odm_vendor_attribute1", "value": "valueOne"}
        ],
        "vendor_attributes": [],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Cannot remove an ODM Vendor Element whose attributes are connected to this ODM element."
    )


def test_cannot_add_odm_vendor_element_attribute_to_an_odm_item_group_as_an_odm_vendor_attribute(
    api_client,
):
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
        "vendor_elements": [],
        "vendor_element_attributes": [],
        "vendor_attributes": [{"uid": "odm_vendor_attribute1", "value": "value"}],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "ODM Vendor Attribute with UID 'odm_vendor_attribute1' cannot not be added as an Vendor Attribute."
    )


def test_cannot_add_odm_vendor_attribute_to_an_odm_item_group_as_an_odm_vendor_element_attribute(
    api_client,
):
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
        "vendor_elements": [{"uid": "odm_vendor_element1", "value": "value1"}],
        "vendor_element_attributes": [
            {"uid": "odm_vendor_attribute3", "value": "value"}
        ],
        "vendor_attributes": [],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "ODM Vendor Attribute with UID 'odm_vendor_attribute3' cannot not be added as an Vendor Element Attribute."
    )


def test_cannot_add_odm_item_with_an_invalid_value_to_to_an_odm_item_group(api_client):
    data = [
        {
            "uid": "odm_item1",
            "order_number": 1,
            "mandatory": "Yes",
            "data_entry_required": "Yes",
            "sdv": "Yes",
            "locked": "No",
            "key_sequence": "key_sequence1",
            "method_oid": "method_oid1",
            "imputation_method_oid": "imputation_method_oid1",
            "role": "role1",
            "role_codelist_oid": "role_codelist_oid1",
            "collection_exception_condition_oid": "collection_exception_condition_oid1",
            "vendor": {
                "attributes": [{"uid": "odm_vendor_attribute3", "value": "3423"}]
            },
        }
    ]
    response = api_client.post("odms/item-groups/OdmItemGroup_000001/items", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == """Provided values for following attributes don't match their regex pattern:

{'odm_vendor_attribute3': '^[a-zA-Z]+$'}"""
    )


def test_approve_odm_item_group(api_client):
    response = api_client.post("odms/item-groups/OdmItemGroup_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
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
        {"uid": "odm_vendor_element1", "name": "NameOne", "value": "value1"}
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


def test_inactivate_odm_item_group(api_client):
    response = api_client.delete("odms/item-groups/OdmItemGroup_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmItemGroup_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["repeating"] == "No"
    assert res["is_reference_data"] == "No"
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
    assert res["items"] == []
    assert res["vendor_elements"] == [
        {"uid": "odm_vendor_element1", "name": "NameOne", "value": "value1"}
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


def test_cannot_add_odm_item_to_an_odm_item_group_that_is_in_retired_status(
    api_client,
):
    data = [
        {
            "uid": "odm_item1",
            "order_number": 1,
            "mandatory": "Yes",
            "data_entry_required": "Yes",
            "sdv": "Yes",
            "locked": "No",
            "key_sequence": "key_sequence1",
            "method_oid": "method_oid1",
            "imputation_method_oid": "imputation_method_oid1",
            "role": "role1",
            "role_codelist_oid": "role_codelist_oid1",
            "collection_exception_condition_oid": "collection_exception_condition_oid1",
            "vendor": {"attributes": []},
        }
    ]
    response = api_client.post("odms/item-groups/OdmItemGroup_000001/items", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "ODM element is not in Draft."


def test_cannot_add_odm_vendor_element_to_an_odm_item_group_that_is_in_retired_status(
    api_client,
):
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
        "vendor_element_attributes": [],
        "vendor_attributes": [],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "ODM element is not in Draft."


def test_cannot_add_odm_vendor_attribute_to_an_odm_item_group_that_is_in_retired_status(
    api_client,
):
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
        "vendor_elements": [],
        "vendor_element_attributes": [],
        "vendor_attributes": [{"uid": "odm_vendor_attribute1", "value": "value"}],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "ODM element is not in Draft."


def test_cannot_add_odm_vendor_element_attribute_to_an_odm_item_group_that_is_in_retired_status(
    api_client,
):
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
        "vendor_elements": [],
        "vendor_element_attributes": [
            {"uid": "odm_vendor_attribute1", "value": "value"}
        ],
        "vendor_attributes": [],
        "change_description": "desc doesnt change",
    }
    response = api_client.patch("odms/item-groups/OdmItemGroup_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "ODM element is not in Draft."


@pytest.mark.parametrize(
    "text_type",
    [
        pytest.param("Description"),
        pytest.param("Question"),
        pytest.param("osb:DesignNotes"),
        pytest.param("osb:CompletionInstructions"),
        pytest.param("osb:DisplayText"),
    ],
)
def test_cannot_add_duplicate_translated_texts(api_client, text_type: str):
    data = {
        "library_name": "Sponsor",
        "name": "testin",
        "oid": "testin",
        "repeating": "No",
        "is_reference_data": "No",
        "sas_dataset_name": "testing",
        "origin": "testing",
        "purpose": "testing",
        "comment": "testing",
        "translated_texts": [
            {
                "text_type": text_type,
                "language": "eng",
                "text": str(r),
            }
            for r in range(2)
        ],
        "aliases": [],
        "sdtm_domain_uids": [],
    }
    response = api_client.post("odms/item-groups", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == f"Duplicate Translated Text found for text_type '{text_type}' and language 'eng'."
    )
