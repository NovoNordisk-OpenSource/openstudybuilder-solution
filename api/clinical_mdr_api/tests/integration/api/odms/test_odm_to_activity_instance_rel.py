"""
Tests for clinical_programmes endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
)
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
)
from clinical_mdr_api.models.concepts.activities.activity import Activity
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.concepts.activities.activity_item import ActivityItem
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.odms.form import OdmForm
from clinical_mdr_api.models.odms.item import OdmItem
from clinical_mdr_api.models.odms.item_group import OdmItemGroup
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
base_test_data: dict[str, Any]
forms: list[OdmForm]
item_groups: list[OdmItemGroup]
items: list[OdmItem]

activity_group: ActivityGroup
activity_subgroup: ActivitySubGroup
activities: list[Activity]
activity_instance_classes: list[ActivityInstanceClass]
activity_items: list[ActivityItem]
activity_instances: list[ActivityInstance]
activity_item_classes: list[ActivityItemClass]
codelist: CTCodelist
ct_terms: list[CTTerm]
role_term: CTTerm
data_type_term: CTTerm


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data(api_client):
    """Initialize test data"""
    inject_and_clear_db("odm.activity.api")
    db.cypher_query(STARTUP_CODMDT_CODELIST)

    global base_test_data
    _, base_test_data = inject_base_data(inject_unit_dimension=True)

    global forms
    global item_groups
    global items
    global activity_group
    global activity_subgroup
    global activities
    global activity_instance_classes
    global activity_items
    global activity_instances
    global activity_item_classes
    global codelist
    global ct_terms
    global role_term
    global data_type_term

    activity_group = TestUtils.create_activity_group(name="activity_group")
    activity_subgroup = TestUtils.create_activity_subgroup(name="activity_subgroup")
    activities = [
        TestUtils.create_activity(
            name="Activity",
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
        ),
        TestUtils.create_activity(
            name="Second activity",
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
        ),
    ]

    activity_instance_classes = [
        TestUtils.create_activity_instance_class(
            name="Activity instance class 1",
            definition="def Activity instance class 1",
            is_domain_specific=True,
            level=1,
        ),
        TestUtils.create_activity_instance_class(
            name="Activity instance class 2",
            definition="def Activity instance class 2",
            is_domain_specific=True,
            level=2,
            parent_uid="ActivityInstanceClass_000001",
        ),
        TestUtils.create_activity_instance_class(
            name="Activity instance class 3",
            definition="def Activity instance class 3",
            is_domain_specific=True,
            level=3,
            parent_uid="ActivityInstanceClass_000002",
        ),
        TestUtils.create_activity_instance_class(name="NumericFindings"),
    ]

    data_type_codelist = TestUtils.create_ct_codelist(
        name="DATATYPE", submission_value="DATATYPE", extensible=True, approve=True
    )
    data_type_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Data type", codelist_uid=data_type_codelist.codelist_uid
    )
    role_codelist = TestUtils.create_ct_codelist(
        name="ROLE", submission_value="ROLE", extensible=True, approve=True
    )
    role_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Role", codelist_uid=role_codelist.codelist_uid
    )

    activity_item_classes = [
        TestUtils.create_activity_item_class(
            name="Activity Item Class name1",
            order=1,
            activity_instance_classes=[
                {
                    "uid": activity_instance_classes[0].uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                    "is_additional_optional": True,
                    "is_default_linked": True,
                }
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="Activity Item Class name2",
            order=2,
            activity_instance_classes=[
                {
                    "uid": activity_instance_classes[1].uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                    "is_additional_optional": True,
                    "is_default_linked": True,
                }
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="Activity Item Class name3",
            order=3,
            activity_instance_classes=[
                {
                    "uid": activity_instance_classes[2].uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": False,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                }
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
    ]

    codelist = TestUtils.create_ct_codelist(extensible=True, approve=True)
    ct_terms = [
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Activity item term",
        ),
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Activity item term2",
        ),
    ]

    activity_items = [
        {
            "activity_item_class_uid": activity_item_classes[0].uid,
            "ct_terms": [],
            "unit_definition_uids": [
                base_test_data["day_unit"].uid,
            ],
            "is_adam_param_specific": True,
        },
        {
            "activity_item_class_uid": activity_item_classes[1].uid,
            "ct_terms": [
                {
                    "term_uid": ct_terms[1].term_uid,
                    "codelist_uid": codelist.codelist_uid,
                }
            ],
            "unit_definition_uids": [],
            "is_adam_param_specific": False,
        },
        {
            "activity_item_class_uid": activity_item_classes[2].uid,
            "ct_terms": [
                {
                    "term_uid": ct_terms[0].term_uid,
                    "codelist_uid": codelist.codelist_uid,
                },
                {
                    "term_uid": ct_terms[1].term_uid,
                    "codelist_uid": codelist.codelist_uid,
                },
            ],
            "unit_definition_uids": [],
            "is_adam_param_specific": False,
        },
    ]

    activity_instances = []
    activity_instances.append(
        TestUtils.create_activity_instance(
            name="name A",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            definition="def A",
            abbreviation="abbr A",
            nci_concept_id="NCIID",
            nci_concept_name="NCINAME",
            name_sentence_case="name A",
            topic_code="topic code A",
            is_research_lab=True,
            adam_param_code="adam_code_a",
            is_required_for_activity=True,
            activities=[activities[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0]],
        )
    )

    forms = []
    item_groups = []
    items = []

    forms.append(TestUtils.create_odm_form(name="Form 1", oid="F1", approve=False))

    item_groups.append(
        TestUtils.create_odm_item_group(name="Group 1", oid="G1", approve=False)
    )

    items.append(
        TestUtils.create_odm_item(
            name="Item 1", oid="I1", datatype_uid="string_uid", length=1, approve=False
        )
    )

    api_client.post(
        f"odms/forms/{forms[0].uid}/item-groups",
        json=[
            {
                "uid": item_groups[0].uid,
                "order_number": 1,
                "mandatory": "Yes",
                "locked": "No",
                "collection_exception_condition_oid": "collection_exception_condition_oid1",
                "vendor": {"attributes": []},
            }
        ],
    )

    api_client.post(
        f"odms/item-groups/{item_groups[0].uid}/items",
        json=[
            {
                "uid": items[0].uid,
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
        ],
    )

    yield


def test_get_odm_item_without_activity_instance_relationship(api_client):
    response = api_client.get(f"odms/items/{items[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == items[0].uid
    assert res["version"] == "0.1"
    assert len(res["activity_instances"]) == 0


def test_add_activity_instance_relationship_to_odm_item(api_client):
    response = api_client.patch(
        f"odms/items/{items[0].uid}",
        json={
            "name": "name1",
            "oid": "oid1",
            "datatype_uid": "string_uid",
            "prompt": "prompt1",
            "length": 123,
            "significant_digits": 456,
            "sas_field_name": "sas_field_name1",
            "sds_var_name": "sds_var_name1",
            "origin": "origin1",
            "comment": "comment1",
            "translated_texts": [],
            "aliases": [],
            "unit_definitions": [],
            "external_question": None,
            "codelist": None,
            "terms": [],
            "activity_instances": [
                {
                    "activity_instance_uid": activity_instances[0].uid,
                    "activity_item_class_uid": activity_item_classes[0].uid,
                    "odm_form_uid": forms[0].uid,
                    "odm_item_group_uid": item_groups[0].uid,
                    "order": 1,
                    "primary": True,
                    "preset_response_value": "preset_response_value1",
                    "value_condition": "value_condition1",
                    "value_dependent_map": "value_dependent_map1",
                }
            ],
            "vendor_elements": [],
            "vendor_element_attributes": [],
            "vendor_attributes": [],
            "change_description": "Adding activity instance relationship",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == items[0].uid
    assert res["version"] == "0.2"
    assert len(res["activity_instances"]) == 1
    assert (
        res["activity_instances"][0]["activity_instance_uid"]
        == activity_instances[0].uid
    )
    assert (
        res["activity_instances"][0]["activity_item_class_uid"]
        == activity_item_classes[0].uid
    )
    assert (
        res["activity_instances"][0]["activity_item_class_name"]
        == activity_item_classes[0].name
    )
    assert res["activity_instances"][0]["order"] == 1
    assert res["activity_instances"][0]["primary"] is True
    assert (
        res["activity_instances"][0]["preset_response_value"]
        == "preset_response_value1"
    )
    assert res["activity_instances"][0]["value_condition"] == "value_condition1"
    assert res["activity_instances"][0]["value_dependent_map"] == "value_dependent_map1"


def test_get_odm_item_with_activity_instance_relationship(api_client):
    response = api_client.get(f"odms/items/{items[0].uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == items[0].uid
    assert res["version"] == "0.2"
    assert len(res["activity_instances"]) == 1
    assert (
        res["activity_instances"][0]["activity_instance_uid"]
        == activity_instances[0].uid
    )
    assert res["activity_instances"][0]["activity_instance_name"] == "name A"
    assert (
        res["activity_instances"][0]["activity_instance_adam_param_code"]
        == "adam_code_a"
    )
    assert (
        res["activity_instances"][0]["activity_instance_topic_code"] == "topic code A"
    )
    assert (
        res["activity_instances"][0]["activity_item_class_uid"]
        == activity_item_classes[0].uid
    )
    assert (
        res["activity_instances"][0]["activity_item_class_name"]
        == activity_item_classes[0].name
    )
    assert res["activity_instances"][0]["order"] == 1
    assert res["activity_instances"][0]["primary"] is True
    assert (
        res["activity_instances"][0]["preset_response_value"]
        == "preset_response_value1"
    )
    assert res["activity_instances"][0]["value_condition"] == "value_condition1"
    assert res["activity_instances"][0]["value_dependent_map"] == "value_dependent_map1"


def test_get_odm_items_list_with_activity_instance_relationship(api_client):
    response = api_client.get(
        f'odms/items?filters={{"uid": {{"v": ["{items[0].uid}"]}}}}'
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 1
    item = res["items"][0]
    assert item["uid"] == items[0].uid
    assert len(item["activity_instances"]) == 1
    assert (
        item["activity_instances"][0]["activity_instance_uid"]
        == activity_instances[0].uid
    )
    assert (
        item["activity_instances"][0]["activity_item_class_uid"]
        == activity_item_classes[0].uid
    )
    assert (
        item["activity_instances"][0]["activity_item_class_name"]
        == activity_item_classes[0].name
    )


def test_activity_instance_relationship_to_odm_item(api_client):
    response = api_client.patch(
        f"odms/forms/{forms[0].uid}",
        json={
            "name": "name1",
            "oid": "oid1",
            "sdtm_version": "123",
            "repeating": "No",
            "translated_texts": [],
            "aliases": [],
            "vendor_elements": [],
            "vendor_element_attributes": [],
            "vendor_attributes": [],
            "change_description": "Adding activity instance relationship",
        },
    )
    assert_response_status_code(response, 200)


def test_remove_activity_instance_relationship_from_odm_item(api_client):
    response = api_client.patch(
        f"odms/items/{items[0].uid}",
        json={
            "name": "name1",
            "oid": "oid1",
            "datatype_uid": "string_uid",
            "prompt": "prompt1",
            "length": 123,
            "significant_digits": 456,
            "sas_field_name": "sas_field_name1",
            "sds_var_name": "sds_var_name1",
            "origin": "origin1",
            "comment": "comment1",
            "translated_texts": [],
            "aliases": [],
            "unit_definitions": [],
            "external_question": None,
            "codelist": None,
            "terms": [],
            "activity_instances": [],
            "vendor_elements": [],
            "vendor_element_attributes": [],
            "vendor_attributes": [],
            "change_description": "Removing activity instance relationship",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == items[0].uid
    assert res["version"] == "0.3"
    assert len(res["activity_instances"]) == 0


def test_cannot_add_more_than_one_same_activity_instance_to_odm_item(api_client):
    response = api_client.patch(
        f"odms/items/{items[0].uid}",
        json={
            "name": "name1",
            "oid": "oid1",
            "datatype_uid": "string_uid",
            "prompt": "prompt1",
            "length": 123,
            "significant_digits": 456,
            "sas_field_name": "sas_field_name1",
            "sds_var_name": "sds_var_name1",
            "origin": "origin1",
            "comment": "comment1",
            "translated_texts": [],
            "aliases": [],
            "unit_definitions": [],
            "external_question": None,
            "codelist": None,
            "terms": [],
            "activity_instances": [
                {
                    "activity_instance_uid": activity_instances[0].uid,
                    "activity_item_class_uid": activity_item_classes[0].uid,
                    "order": 1,
                    "primary": True,
                    "preset_response_value": "preset_response_value1",
                    "value_condition": "value_condition1",
                    "value_dependent_map": "value_dependent_map1",
                },
                {
                    "activity_instance_uid": activity_instances[0].uid,
                    "activity_item_class_uid": activity_item_classes[0].uid,
                    "order": 2,
                    "primary": False,
                    "preset_response_value": "preset_response_value2",
                    "value_condition": "value_condition2",
                    "value_dependent_map": "value_dependent_map2",
                },
            ],
            "vendor_elements": [],
            "vendor_element_attributes": [],
            "vendor_attributes": [],
            "change_description": "Adding more than one same activity instance",
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "The request failed due to validation errors"
    assert res["details"][0]["msg"] == (
        "Value error, Activity Instances must be unique. Following duplicates were found: ('ActivityInstance_000001', 'ActivityItemClass_000001')"
    )
