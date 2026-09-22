"""
Tests for clinical_programmes endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.odms.form import OdmForm
from clinical_mdr_api.models.odms.item import OdmItem
from clinical_mdr_api.models.odms.item_group import OdmItemGroup
from clinical_mdr_api.models.odms.study_event import OdmStudyEvent
from clinical_mdr_api.models.odms.vendor_attribute import OdmVendorAttribute
from clinical_mdr_api.models.odms.vendor_element import OdmVendorElement
from clinical_mdr_api.models.odms.vendor_namespace import OdmVendorNamespace
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CODMDT_CODELIST,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study_event: OdmStudyEvent
forms: list[OdmForm]
item_groups: list[OdmItemGroup]
items: list[OdmItem]
vendor_namespace: OdmVendorNamespace
vendor_elements: list[OdmVendorElement]
vendor_attributes: list[OdmVendorAttribute]

URL = "odms"


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db("odm.versioning.api")
    inject_base_data()

    db.cypher_query(STARTUP_CODMDT_CODELIST)

    global study_event
    global forms
    global item_groups
    global items
    global vendor_namespace
    global vendor_elements
    global vendor_attributes

    forms = []
    item_groups = []
    items = []
    vendor_elements = []
    vendor_attributes = []

    study_event = TestUtils.create_odm_study_event(
        name="StudyEvent 1", oid="SE1", approve=False
    )

    forms.append(TestUtils.create_odm_form(name="Form 1", oid="F1", approve=False))
    forms.append(TestUtils.create_odm_form(name="Form 2", oid="F2", approve=False))

    item_groups.append(
        TestUtils.create_odm_item_group(name="Group 1", oid="G1", approve=False)
    )
    item_groups.append(
        TestUtils.create_odm_item_group(name="Group 2", oid="G2", approve=False)
    )

    items.append(
        TestUtils.create_odm_item(
            name="Item 1", oid="I1", datatype_uid="string_uid", length=2, approve=False
        )
    )
    items.append(
        TestUtils.create_odm_item(
            name="Item 2", oid="I2", datatype_uid="string_uid", length=2, approve=False
        )
    )

    vendor_namespace = TestUtils.create_odm_vendor_namespace(
        name="OSB", prefix="osb", url="https://osb.example.com"
    )

    vendor_elements.append(
        TestUtils.create_odm_vendor_element(
            name="VEF",
            compatible_types=["FormDef"],
            vendor_namespace_uid=vendor_namespace.uid,
            approve=False,
        )
    )
    vendor_elements.append(
        TestUtils.create_odm_vendor_element(
            name="VEIG",
            compatible_types=["ItemGroupDef"],
            vendor_namespace_uid=vendor_namespace.uid,
            approve=False,
        )
    )
    vendor_elements.append(
        TestUtils.create_odm_vendor_element(
            name="VEI",
            compatible_types=["ItemDef"],
            vendor_namespace_uid=vendor_namespace.uid,
            approve=False,
        )
    )
    vendor_elements.append(
        TestUtils.create_odm_vendor_element(
            name="VEA",
            compatible_types=["FormDef", "ItemGroupDef", "ItemDef"],
            vendor_namespace_uid=vendor_namespace.uid,
            approve=False,
        )
    )

    vendor_attributes.append(
        TestUtils.create_odm_vendor_attribute(
            name="vAF",
            compatible_types=["FormDef"],
            data_type="string",
            vendor_namespace_uid=vendor_namespace.uid,
            approve=False,
        )
    )
    vendor_attributes.append(
        TestUtils.create_odm_vendor_attribute(
            name="vAIG",
            compatible_types=["ItemGroupDef"],
            data_type="string",
            vendor_namespace_uid=vendor_namespace.uid,
            approve=False,
        )
    )
    vendor_attributes.append(
        TestUtils.create_odm_vendor_attribute(
            name="vAI",
            compatible_types=["ItemDef"],
            data_type="string",
            vendor_namespace_uid=vendor_namespace.uid,
            approve=False,
        )
    )
    vendor_attributes.append(
        TestUtils.create_odm_vendor_attribute(
            name="vAE",
            data_type="string",
            vendor_element_uid=vendor_elements[3].uid,
            approve=False,
        )
    )

    yield


def test_add_odm_forms_to_odm_study_event(api_client):
    data = [
        {
            "uid": forms[0].uid,
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        },
        {
            "uid": forms[1].uid,
            "order_number": 2,
            "mandatory": "No",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        },
    ]

    response = api_client.post(f"odms/study-events/{study_event.uid}/forms", json=data)
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["forms"] == [
        {
            "uid": "OdmForm_000001",
            "oid": "F1",
            "name": "Form 1",
            "version": "0.1",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        },
        {
            "uid": "OdmForm_000002",
            "oid": "F2",
            "name": "Form 2",
            "version": "0.1",
            "order_number": 2,
            "mandatory": "No",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        },
    ]


def test_add_odm_item_groups_odm_forms(api_client):
    data = [
        {
            "uid": item_groups[0].uid,
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
        {
            "uid": item_groups[1].uid,
            "order_number": 2,
            "mandatory": "No",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]

    response = api_client.post(f"odms/forms/{forms[0].uid}/item-groups", json=data)
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == "OdmForm_000001"
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["item_groups"] == [
        {
            "uid": "OdmItemGroup_000001",
            "oid": "G1",
            "name": "Group 1",
            "version": "0.1",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
        {
            "uid": "OdmItemGroup_000002",
            "oid": "G2",
            "name": "Group 2",
            "version": "0.1",
            "order_number": 2,
            "mandatory": "No",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]

    response = api_client.post(f"odms/forms/{forms[1].uid}/item-groups", json=data)
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == "OdmForm_000002"
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["item_groups"] == [
        {
            "uid": "OdmItemGroup_000001",
            "oid": "G1",
            "name": "Group 1",
            "version": "0.1",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
        {
            "uid": "OdmItemGroup_000002",
            "oid": "G2",
            "name": "Group 2",
            "version": "0.1",
            "order_number": 2,
            "mandatory": "No",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]


def test_add_odm_items_to_odm_item_group(api_client):
    response = api_client.post(
        f"odms/item-groups/{item_groups[0].uid}/items",
        json=[
            {
                "uid": items[0].uid,
                "order_number": 1,
                "mandatory": "Yes",
                "key_sequence": "None",
                "method_oid": "None",
                "imputation_method_oid": "None",
                "role": "None",
                "role_codelist_oid": "None",
                "collection_exception_condition_oid": "None",
                "vendor": {"attributes": []},
            },
        ],
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == "OdmItemGroup_000001"
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["items"] == [
        {
            "uid": "OdmItem_000001",
            "oid": "I1",
            "name": "Item 1",
            "version": "0.1",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "None",
            "method_oid": "None",
            "imputation_method_oid": "None",
            "role": "None",
            "role_codelist_oid": "None",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]

    response = api_client.post(
        f"odms/item-groups/{item_groups[1].uid}/items",
        json=[
            {
                "uid": items[1].uid,
                "order_number": 2,
                "mandatory": "No",
                "key_sequence": "None",
                "method_oid": "None",
                "imputation_method_oid": "None",
                "role": "None",
                "role_codelist_oid": "None",
                "collection_exception_condition_oid": "None",
                "vendor": {"attributes": []},
            },
        ],
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == "OdmItemGroup_000002"
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["items"] == [
        {
            "uid": "OdmItem_000002",
            "oid": "I2",
            "name": "Item 2",
            "version": "0.1",
            "order_number": 1,
            "mandatory": "No",
            "key_sequence": "None",
            "method_oid": "None",
            "imputation_method_oid": "None",
            "role": "None",
            "role_codelist_oid": "None",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]


def test_approve_study_event_with_cascade_effect(api_client):
    response = api_client.post(f"odms/study-events/{study_event.uid}/approvals")
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["forms"] == [
        {
            "uid": "OdmForm_000001",
            "oid": "F1",
            "name": "Form 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        },
        {
            "uid": "OdmForm_000002",
            "oid": "F2",
            "name": "Form 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        },
    ]

    response = api_client.get(f"odms/study-events/{study_event.uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["forms"] == [
        {
            "uid": "OdmForm_000001",
            "oid": "F1",
            "name": "Form 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        },
        {
            "uid": "OdmForm_000002",
            "oid": "F2",
            "name": "Form 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        },
    ]

    response = api_client.get(f"odms/forms/{forms[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmForm_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["item_groups"] == [
        {
            "uid": "OdmItemGroup_000001",
            "oid": "G1",
            "name": "Group 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
        {
            "uid": "OdmItemGroup_000002",
            "oid": "G2",
            "name": "Group 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]

    response = api_client.get(f"odms/forms/{forms[1].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmForm_000002"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["item_groups"] == [
        {
            "uid": "OdmItemGroup_000001",
            "oid": "G1",
            "name": "Group 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
        {
            "uid": "OdmItemGroup_000002",
            "oid": "G2",
            "name": "Group 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]

    response = api_client.get(f"odms/item-groups/{item_groups[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmItemGroup_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["items"] == [
        {
            "uid": "OdmItem_000001",
            "oid": "I1",
            "name": "Item 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "None",
            "method_oid": "None",
            "imputation_method_oid": "None",
            "role": "None",
            "role_codelist_oid": "None",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]

    response = api_client.get(f"odms/item-groups/{item_groups[1].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmItemGroup_000002"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["items"] == [
        {
            "uid": "OdmItem_000002",
            "oid": "I2",
            "name": "Item 2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "No",
            "key_sequence": "None",
            "method_oid": "None",
            "imputation_method_oid": "None",
            "role": "None",
            "role_codelist_oid": "None",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]


def test_perseverance_of_final_versions_relationship_between_item_group_and_item(
    api_client,
):
    response = api_client.post(f"odms/items/{items[0].uid}/versions")
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == "OdmItem_000001"
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"

    response = api_client.get(f"odms/item-groups/{item_groups[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmItemGroup_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["items"] == [
        {
            "uid": "OdmItem_000001",
            "oid": "I1",
            "name": "Item 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "None",
            "method_oid": "None",
            "imputation_method_oid": "None",
            "role": "None",
            "role_codelist_oid": "None",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]


def test_perseverance_of_final_versions_relationship_between_form_and_item_group(
    api_client,
):
    response = api_client.post(f"odms/item-groups/{item_groups[0].uid}/versions")
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == "OdmItemGroup_000001"
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["items"] == [
        {
            "uid": "OdmItem_000001",
            "oid": "I1",
            "name": "Item 1",
            "version": "1.1",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "None",
            "method_oid": "None",
            "imputation_method_oid": "None",
            "role": "None",
            "role_codelist_oid": "None",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]

    response = api_client.get(f"odms/forms/{forms[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmForm_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["item_groups"] == [
        {
            "uid": "OdmItemGroup_000001",
            "oid": "G1",
            "name": "Group 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
        {
            "uid": "OdmItemGroup_000002",
            "oid": "G2",
            "name": "Group 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]


def test_perseverance_of_final_versions_relationship_between_study_event_and_form(
    api_client,
):
    response = api_client.post(f"odms/forms/{forms[0].uid}/versions")
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == "OdmForm_000001"
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["item_groups"] == [
        {
            "uid": "OdmItemGroup_000001",
            "oid": "G1",
            "name": "Group 1",
            "version": "1.1",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
        {
            "uid": "OdmItemGroup_000002",
            "oid": "G2",
            "name": "Group 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]

    response = api_client.get(f"odms/study-events/{study_event.uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["forms"] == [
        {
            "uid": "OdmForm_000001",
            "oid": "F1",
            "name": "Form 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        },
        {
            "uid": "OdmForm_000002",
            "oid": "F2",
            "name": "Form 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        },
    ]


def test_latest_perseverance_of_relationship_based_on_latest_versions(api_client):
    response = api_client.get(f"odms/study-events/{study_event.uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["forms"] == [
        {
            "uid": "OdmForm_000001",
            "oid": "F1",
            "name": "Form 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        },
        {
            "uid": "OdmForm_000002",
            "oid": "F2",
            "name": "Form 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        },
    ]

    response = api_client.get(f"odms/forms/{forms[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmForm_000001"
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["item_groups"] == [
        {
            "uid": "OdmItemGroup_000001",
            "oid": "G1",
            "name": "Group 1",
            "version": "1.1",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
        {
            "uid": "OdmItemGroup_000002",
            "oid": "G2",
            "name": "Group 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]

    response = api_client.get(f"odms/item-groups/{item_groups[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmItemGroup_000001"
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["items"] == [
        {
            "uid": "OdmItem_000001",
            "oid": "I1",
            "name": "Item 1",
            "version": "1.1",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "None",
            "method_oid": "None",
            "imputation_method_oid": "None",
            "role": "None",
            "role_codelist_oid": "None",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]


def test_latest_perseverance_of_relationship_based_on_specific_versions(api_client):
    response = api_client.get(f"odms/study-events/{study_event.uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["forms"] == [
        {
            "uid": "OdmForm_000001",
            "oid": "F1",
            "name": "Form 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        },
        {
            "uid": "OdmForm_000002",
            "oid": "F2",
            "name": "Form 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        },
    ]

    response = api_client.get(f"odms/forms/{forms[0].uid}?version=1.0")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmForm_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["item_groups"] == [
        {
            "uid": "OdmItemGroup_000001",
            "oid": "G1",
            "name": "Group 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
        {
            "uid": "OdmItemGroup_000002",
            "oid": "G2",
            "name": "Group 2",
            "version": "1.0",
            "order_number": 2,
            "mandatory": "No",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]

    response = api_client.get(f"odms/item-groups/{item_groups[0].uid}?version=1.0")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == "OdmItemGroup_000001"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["items"] == [
        {
            "uid": "OdmItem_000001",
            "oid": "I1",
            "name": "Item 1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "key_sequence": "None",
            "method_oid": "None",
            "imputation_method_oid": "None",
            "role": "None",
            "role_codelist_oid": "None",
            "collection_exception_condition_oid": "None",
            "vendor": {"attributes": []},
        },
    ]


def test_add_odm_vendor_element_to_odm_form(api_client):
    response = api_client.patch(
        f"odms/forms/{forms[0].uid}",
        json={
            "name": forms[0].name,
            "oid": forms[0].oid,
            "sdtm_version": forms[0].sdtm_version,
            "repeating": forms[0].repeating,
            "translated_texts": [],
            "aliases": [],
            "vendor_elements": [{"uid": vendor_elements[0].uid, "value": "value1"}],
            "vendor_element_attributes": [],
            "vendor_attributes": [],
            "change_description": "desc doesnt change",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_elements"] == [
        {"uid": "OdmVendorElement_000001", "name": "VEF", "value": "value1"}
    ]

    response = api_client.get(f"odms/forms/{forms[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_elements"] == [
        {"uid": "OdmVendorElement_000001", "name": "VEF", "value": "value1"}
    ]

    response = api_client.patch(
        "odms/vendor-elements/OdmVendorElement_000001",
        json={
            "name": "VEFNew",
            "compatible_types": ["FormDef"],
            "change_description": "name changed to VEFNew",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"odms/forms/{forms[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_elements"] == [
        {"uid": "OdmVendorElement_000001", "name": "VEFNew", "value": "value1"}
    ]


def test_add_odm_vendor_element_to_odm_item_group(api_client):
    response = api_client.patch(
        f"odms/item-groups/{item_groups[0].uid}",
        json={
            "name": item_groups[0].name,
            "oid": item_groups[0].oid,
            "repeating": item_groups[0].repeating,
            "is_reference_data": item_groups[0].is_reference_data,
            "sas_dataset_name": item_groups[0].sas_dataset_name,
            "origin": item_groups[0].origin,
            "purpose": item_groups[0].purpose,
            "comment": item_groups[0].comment,
            "translated_texts": [],
            "aliases": [],
            "sdtm_domain_uids": [],
            "vendor_elements": [{"uid": vendor_elements[1].uid, "value": "value1"}],
            "vendor_element_attributes": [],
            "vendor_attributes": [],
            "change_description": "desc doesnt change",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_elements"] == [
        {"uid": "OdmVendorElement_000002", "name": "VEIG", "value": "value1"}
    ]

    response = api_client.get(f"odms/item-groups/{item_groups[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_elements"] == [
        {"uid": "OdmVendorElement_000002", "name": "VEIG", "value": "value1"}
    ]

    response = api_client.patch(
        "odms/vendor-elements/OdmVendorElement_000002",
        json={
            "name": "VEIGNew",
            "compatible_types": ["ItemDef"],
            "change_description": "name changed to VEIGNew",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"odms/item-groups/{item_groups[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_elements"] == [
        {"uid": "OdmVendorElement_000002", "name": "VEIGNew", "value": "value1"}
    ]


def test_add_odm_vendor_element_to_odm_item(api_client):
    response = api_client.patch(
        f"odms/items/{items[0].uid}",
        json={
            "name": items[0].name,
            "oid": items[0].oid,
            "prompt": items[0].prompt,
            "datatype_uid": items[0].datatype.uid,
            "length": items[0].length,
            "significant_digits": items[0].significant_digits,
            "sas_field_name": items[0].sas_field_name,
            "sds_var_name": items[0].sds_var_name,
            "origin": items[0].origin,
            "comment": items[0].comment,
            "translated_texts": [],
            "aliases": [],
            "unit_definitions": [],
            "external_question": None,
            "codelist": None,
            "terms": [],
            "vendor_elements": [{"uid": vendor_elements[2].uid, "value": "value1"}],
            "vendor_element_attributes": [],
            "vendor_attributes": [],
            "change_description": "desc doesnt change",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_elements"] == [
        {"uid": "OdmVendorElement_000003", "name": "VEI", "value": "value1"}
    ]

    response = api_client.get(f"odms/items/{items[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_elements"] == [
        {"uid": "OdmVendorElement_000003", "name": "VEI", "value": "value1"}
    ]

    response = api_client.patch(
        "odms/vendor-elements/OdmVendorElement_000003",
        json={
            "name": "VEINew",
            "compatible_types": ["ItemDef"],
            "change_description": "name changed to VEINew",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"odms/items/{items[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_elements"] == [
        {"uid": "OdmVendorElement_000003", "name": "VEINew", "value": "value1"}
    ]


def test_add_odm_vendor_attribute_to_odm_form(api_client):
    response = api_client.patch(
        f"odms/forms/{forms[0].uid}",
        json={
            "name": forms[0].name,
            "oid": forms[0].oid,
            "sdtm_version": forms[0].sdtm_version,
            "repeating": forms[0].repeating,
            "translated_texts": [],
            "aliases": [],
            "vendor_elements": [],
            "vendor_element_attributes": [],
            "vendor_attributes": [{"uid": vendor_attributes[0].uid, "value": "value1"}],
            "change_description": "desc doesnt change",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_attributes"] == [
        {
            "uid": "OdmVendorAttribute_000001",
            "name": "vAF",
            "data_type": "string",
            "value_regex": None,
            "value": "value1",
            "vendor_namespace_uid": "OdmVendorNamespace_000001",
        }
    ]

    response = api_client.get(f"odms/forms/{forms[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_attributes"] == [
        {
            "uid": "OdmVendorAttribute_000001",
            "name": "vAF",
            "data_type": "string",
            "value_regex": None,
            "value": "value1",
            "vendor_namespace_uid": "OdmVendorNamespace_000001",
        }
    ]

    response = api_client.patch(
        "odms/vendor-attributes/OdmVendorAttribute_000001",
        json={
            "name": "vAFNew",
            "compatible_types": ["FormDef"],
            "data_type": "string",
            "value_regex": None,
            "change_description": "name changed to vAFNew",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"odms/forms/{forms[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_attributes"] == [
        {
            "uid": "OdmVendorAttribute_000001",
            "name": "vAFNew",
            "data_type": "string",
            "value_regex": None,
            "value": "value1",
            "vendor_namespace_uid": "OdmVendorNamespace_000001",
        }
    ]


def test_add_odm_vendor_attribute_to_odm_item_group(api_client):
    response = api_client.patch(
        f"odms/item-groups/{item_groups[0].uid}",
        json={
            "name": item_groups[0].name,
            "oid": item_groups[0].oid,
            "repeating": item_groups[0].repeating,
            "is_reference_data": item_groups[0].is_reference_data,
            "sas_dataset_name": item_groups[0].sas_dataset_name,
            "origin": item_groups[0].origin,
            "purpose": item_groups[0].purpose,
            "comment": item_groups[0].comment,
            "translated_texts": [],
            "aliases": [],
            "sdtm_domain_uids": [],
            "vendor_elements": [],
            "vendor_element_attributes": [],
            "vendor_attributes": [{"uid": vendor_attributes[1].uid, "value": "value1"}],
            "change_description": "desc doesnt change",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_attributes"] == [
        {
            "uid": "OdmVendorAttribute_000002",
            "name": "vAIG",
            "value": "value1",
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace_uid": "OdmVendorNamespace_000001",
        }
    ]

    response = api_client.get(f"odms/item-groups/{item_groups[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_attributes"] == [
        {
            "uid": "OdmVendorAttribute_000002",
            "name": "vAIG",
            "value": "value1",
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace_uid": "OdmVendorNamespace_000001",
        }
    ]

    response = api_client.patch(
        "odms/vendor-attributes/OdmVendorAttribute_000002",
        json={
            "name": "vAIGNew",
            "compatible_types": ["ItemDef"],
            "data_type": "string",
            "value_regex": None,
            "change_description": "name changed to vAIGNew",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"odms/item-groups/{item_groups[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_attributes"] == [
        {
            "uid": "OdmVendorAttribute_000002",
            "name": "vAIGNew",
            "value": "value1",
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace_uid": "OdmVendorNamespace_000001",
        }
    ]


def test_add_odm_vendor_attribute_to_odm_item(api_client):
    response = api_client.patch(
        f"odms/items/{items[0].uid}",
        json={
            "name": items[0].name,
            "oid": items[0].oid,
            "prompt": items[0].prompt,
            "datatype_uid": items[0].datatype.uid,
            "length": items[0].length,
            "significant_digits": items[0].significant_digits,
            "sas_field_name": items[0].sas_field_name,
            "sds_var_name": items[0].sds_var_name,
            "origin": items[0].origin,
            "comment": items[0].comment,
            "translated_texts": [],
            "aliases": [],
            "unit_definitions": [],
            "external_question": None,
            "codelist": None,
            "terms": [],
            "vendor_elements": [],
            "vendor_element_attributes": [],
            "vendor_attributes": [{"uid": vendor_attributes[2].uid, "value": "value1"}],
            "change_description": "desc doesnt change",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_attributes"] == [
        {
            "uid": "OdmVendorAttribute_000003",
            "name": "vAI",
            "value": "value1",
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace_uid": "OdmVendorNamespace_000001",
        }
    ]

    response = api_client.get(f"odms/items/{items[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_attributes"] == [
        {
            "uid": "OdmVendorAttribute_000003",
            "name": "vAI",
            "data_type": "string",
            "value_regex": None,
            "value": "value1",
            "vendor_namespace_uid": "OdmVendorNamespace_000001",
        }
    ]

    response = api_client.patch(
        "odms/vendor-attributes/OdmVendorAttribute_000003",
        json={
            "name": "vAINew",
            "compatible_types": ["ItemDef"],
            "data_type": "string",
            "value_regex": None,
            "change_description": "name changed to vAINew",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"odms/items/{items[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_attributes"] == [
        {
            "uid": "OdmVendorAttribute_000003",
            "name": "vAINew",
            "value": "value1",
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace_uid": "OdmVendorNamespace_000001",
        }
    ]


def test_odm_vendor_attribute_and_odm_vendor_element(api_client):
    response = api_client.patch(
        f"odms/vendor-attributes/{vendor_attributes[3].uid}",
        json={
            "name": "vAENew",
            "data_type": "string",
            "value_regex": None,
            "compatible_types": [],
            "vendor_element_uid": vendor_elements[3].uid,
            "change_description": "name changed to vAENew",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"odms/vendor-elements/{vendor_elements[3].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["vendor_attributes"] == [
        {
            "compatible_types": [],
            "data_type": "string",
            "name": "vAENew",
            "possible_actions": [
                "approve",
                "delete",
                "edit",
            ],
            "status": "Draft",
            "uid": "OdmVendorAttribute_000004",
            "version": "0.2",
        },
    ]
