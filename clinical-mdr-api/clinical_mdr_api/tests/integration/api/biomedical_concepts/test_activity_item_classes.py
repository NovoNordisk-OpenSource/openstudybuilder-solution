"""
Tests for /activity-item-classes endpoints
"""

import json
import logging
from functools import reduce

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
)
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.standard_data_models.variable_class import VariableClass
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import CT_CODELIST_UIDS, TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
activity_item_classes_all: list[ActivityItemClass]
activity_instance_class: ActivityInstanceClass
activity_instance_class2: ActivityInstanceClass
role_term: CTTerm
data_type_term: CTTerm
variable_class: VariableClass


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db("activity-item-class.api")
    inject_base_data()

    global activity_item_classes_all
    global activity_instance_class
    global activity_instance_class2
    global data_type_term
    global role_term
    global variable_class

    activity_instance_class = TestUtils.create_activity_instance_class(
        name="Activity Instance Class name1"
    )
    activity_instance_class2 = TestUtils.create_activity_instance_class(
        name="Activity Instance Class name2"
    )
    data_type_term = TestUtils.create_ct_term(sponsor_preferred_name="Data type")
    role_term = TestUtils.create_ct_term(sponsor_preferred_name="Role")
    data_model = TestUtils.create_data_model()
    data_model_catalogue = TestUtils.create_data_model_catalogue()
    dataset_class = TestUtils.create_dataset_class(
        data_model_uid=data_model.uid,
        data_model_catalogue_name=data_model_catalogue,
    )
    variable_class = TestUtils.create_variable_class(
        dataset_class_uid=dataset_class.uid,
        data_model_catalogue_name=data_model_catalogue,
        data_model_name=data_model.uid,
        data_model_version=data_model.version_number,
    )

    # Create some activity item classes
    activity_item_classes_all = [
        TestUtils.create_activity_item_class(
            name="name A",
            definition="definition A",
            nci_concept_id="nci id A",
            order=1,
            activity_instance_classes=[
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                },
                {
                    "uid": activity_instance_class2.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                },
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
            codelist_uids=[CT_CODELIST_UIDS.default],
        ),
        TestUtils.create_activity_item_class(
            name="name-AAA",
            definition="definition AAA",
            nci_concept_id="nci id AAA",
            order=2,
            activity_instance_classes=[
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                }
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="name-BBB",
            definition="definition BBB",
            nci_concept_id="nci id BBB",
            order=3,
            activity_instance_classes=[
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                }
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="name XXX",
            definition="definition XXX",
            nci_concept_id="nci id XXX",
            order=4,
            activity_instance_classes=[
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                }
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="name YYY",
            definition="definition YYY",
            nci_concept_id="nci id YYY",
            order=5,
            activity_instance_classes=[
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                }
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
    ]

    for index in range(5):
        activity_item_classes_all.append(
            TestUtils.create_activity_item_class(
                name=f"name-AAA-{index}",
                definition=f"definition AAA-{index}",
                nci_concept_id=f"nci id AAA-{index}",
                order=(index * 4) + 1,
                activity_instance_classes=[
                    {
                        "uid": activity_instance_class.uid,
                        "mandatory": False,
                        "is_adam_param_specific_enabled": False,
                    }
                ],
                role_uid=role_term.term_uid,
                data_type_uid=data_type_term.term_uid,
            )
        )
        activity_item_classes_all.append(
            TestUtils.create_activity_item_class(
                name=f"name-BBB-{index}",
                definition=f"definition BBB-{index}",
                nci_concept_id=f"nci id BBB-{index}",
                order=(index * 4) + 2,
                activity_instance_classes=[
                    {
                        "uid": activity_instance_class.uid,
                        "mandatory": False,
                        "is_adam_param_specific_enabled": False,
                    },
                ],
                role_uid=role_term.term_uid,
                data_type_uid=data_type_term.term_uid,
            )
        )
        activity_item_classes_all.append(
            TestUtils.create_activity_item_class(
                name=f"name-XXX-{index}",
                definition=f"definition XXX-{index}",
                nci_concept_id=f"nci id XXX-{index}",
                order=(index * 4) + 3,
                activity_instance_classes=[
                    {
                        "uid": activity_instance_class.uid,
                        "mandatory": False,
                        "is_adam_param_specific_enabled": False,
                    },
                ],
                role_uid=role_term.term_uid,
                data_type_uid=data_type_term.term_uid,
            )
        )
        activity_item_classes_all.append(
            TestUtils.create_activity_item_class(
                name=f"name-YYY-{index}",
                definition=f"definition YYY-{index}",
                nci_concept_id=f"nci id YYY-{index}",
                order=(index * 4) + 4,
                activity_instance_classes=[
                    {
                        "uid": activity_instance_class.uid,
                        "mandatory": False,
                        "is_adam_param_specific_enabled": False,
                    },
                ],
                role_uid=role_term.term_uid,
                data_type_uid=data_type_term.term_uid,
            )
        )


ACTIVITY_IC_FIELDS_ALL = [
    "uid",
    "name",
    "definition",
    "nci_concept_id",
    "order",
    "activity_instance_classes",
    "data_type",
    "role",
    "variable_classes",
    "codelists",
    "library_name",
    "start_date",
    "end_date",
    "status",
    "version",
    "change_description",
    "author_username",
    "possible_actions",
]

ACTIVITY_IC_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "order",
    "activity_instance_classes",
    "data_type",
    "role",
]


def test_get_activity_item_class(api_client):
    response = api_client.get(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(list(res.keys())) == set(ACTIVITY_IC_FIELDS_ALL)
    for key in ACTIVITY_IC_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == activity_item_classes_all[0].uid
    assert res["name"] == "name A"
    assert res["definition"] == "definition A"
    assert res["nci_concept_id"] == "nci id A"
    assert res["order"] == 1
    assert sorted(
        instance_class["uid"] for instance_class in res["activity_instance_classes"]
    ) == [activity_instance_class.uid, activity_instance_class2.uid]
    assert sorted(
        instance_class["name"] for instance_class in res["activity_instance_classes"]
    ) == [activity_instance_class.name, activity_instance_class2.name]
    assert res["role"]["uid"] == role_term.term_uid
    assert res["data_type"]["uid"] == data_type_term.term_uid
    assert res["codelists"][0]["uid"] == CT_CODELIST_UIDS.default
    assert res["codelists"][0]["name"] == "C66737 NAME"
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_get_activity_item_class_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/activity-item-classes?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_names = list(map(lambda x: x["name"], res["items"]))
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        list(reduce(lambda a, b: a + b, list(results_paginated.values())))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"/activity-item-classes?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(activity_item_classes_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 5),  # Total number of data models is 25
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_activity_item_classes(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/activity-item-classes"
    query_params = []
    if page_size:
        query_params.append(f"page_size={page_size}")
    if page_number:
        query_params.append(f"page_number={page_number}")
    if total_count:
        query_params.append(f"total_count={total_count}")
    if sort_by:
        query_params.append(f"sort_by={sort_by}")

    if query_params:
        url = f"{url}?{'&'.join(query_params)}"

    log.info("GET %s", url)
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    assert res["total"] == (len(activity_item_classes_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVITY_IC_FIELDS_ALL)
        for key in ACTIVITY_IC_FIELDS_NOT_NULL:
            assert item[key] is not None

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = list(sort_by_dict.keys())[0]
        sort_order_ascending: bool = list(sort_by_dict.values())[0]

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = list(map(lambda x: x[sort_field], res["items"]))
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        # This asser fails due to API issue with sorting coupled with pagination
        # assert result_vals == result_vals_sorted_locally


@pytest.mark.parametrize(
    "export_format",
    [
        pytest.param("text/csv"),
        pytest.param("text/xml"),
        pytest.param(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    ],
)
def test_get_activity_item_classes_csv_xml_excel(api_client, export_format):
    url = "activity-item-classes"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param(
            '{"*": {"v": ["Activity Instance Class name1"]}}',
            "activity_instance_classes.name",
            "Activity Instance Class name1",
        ),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/activity-item-classes?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result_prefix:
        assert len(res["items"]) > 0
        nested_path = None

        # if we expect a nested property to be equal to specified value
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        # Each returned row has a field that starts with the specified filter value
        for row in res["items"]:
            if nested_path:
                for prop in nested_path:
                    row = row[prop]
            if isinstance(row, list):
                any(
                    item[expected_matched_field].startswith(expected_result_prefix)
                    for item in row
                )
            else:
                assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param('{"name": {"v": ["name-AAA"]}}', "name", "name-AAA"),
        pytest.param('{"name": {"v": ["name-BBB"]}}', "name", "name-BBB"),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param('{"order": {"v": [1]}}', "order", 1),
        pytest.param(
            '{"activity_instance_classes.uid": {"v": ["ActivityInstanceClass_000001"]}}',
            "activity_instance_classes.uid",
            "ActivityInstanceClass_000001",
        ),
        pytest.param(
            '{"activity_instance_classes.name": {"v": ["Activity Instance Class name1"]}}',
            "activity_instance_classes.name",
            "Activity Instance Class name1",
        ),
        pytest.param(
            '{"activity_instance_classes.mandatory": {"v": [true]}}',
            "activity_instance_classes.mandatory",
            True,
        ),
        pytest.param(
            '{"data_type.name": {"v": ["Data type"]}}',
            "data_type.name",
            "Data type",
        ),
        pytest.param(
            '{"role.name": {"v": ["Role"]}}',
            "role.name",
            "Role",
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/activity-item-classes?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result:
        assert len(res["items"]) > 0

        # if we expect a nested property to be equal to specified value
        nested_path = None
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            if nested_path:
                for prop in nested_path:
                    row = row[prop]
            if isinstance(expected_result, list):
                assert all(
                    item in row[expected_matched_field] for item in expected_result
                )
            else:
                if isinstance(row, list):
                    all(item[expected_matched_field] == expected_result for item in row)
                else:
                    assert row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0


def test_edit_activity_item_class(api_client):
    activity_instance_class_after_edit = TestUtils.create_activity_instance_class(
        name="Activity IC after edit"
    )
    activity_item_class = TestUtils.create_activity_item_class(
        name="New item class",
        order=30,
        activity_instance_classes=[
            {
                "uid": activity_instance_class.uid,
                "mandatory": True,
                "is_adam_param_specific_enabled": True,
            }
        ],
        approve=False,
        data_type_uid=data_type_term.term_uid,
        role_uid=role_term.term_uid,
    )
    response = api_client.patch(
        f"/activity-item-classes/{activity_item_class.uid}",
        json={
            "name": "new name for item class",
            "definition": "new definition for item class",
            "nci_concept_id": "new nci concept id",
            "order": 45,
            "activity_instance_classes": [
                {
                    "uid": activity_instance_class_after_edit.uid,
                    "mandatory": False,
                    "is_adam_param_specific_enabled": False,
                }
            ],
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == "new name for item class"
    assert res["definition"] == "new definition for item class"
    assert res["nci_concept_id"] == "new nci concept id"
    assert res["order"] == 45
    assert res["activity_instance_classes"][0]["name"] == "Activity IC after edit"
    assert res["activity_instance_classes"][0]["mandatory"] is False
    assert (
        res["activity_instance_classes"][0]["is_adam_param_specific_enabled"] is False
    )
    assert res["codelists"] == []
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["library_name"] == "Sponsor"

    response = api_client.patch(
        f"/activity-item-classes/{activity_item_class.uid}/model-mappings",
        json={
            "variable_class_uids": [variable_class.uid],
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["variable_classes"] == [{"uid": variable_class.uid}]


def test_post_activity_item_class(api_client):
    response = api_client.post(
        "/activity-item-classes",
        json={
            "name": "New AIC Name",
            "definition": "New AIC Def",
            "nci_concept_id": "New nci id",
            "order": 36,
            "library_name": "Sponsor",
            "activity_instance_classes": [
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                }
            ],
            "role_uid": role_term.term_uid,
            "data_type_uid": data_type_term.term_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["name"] == "New AIC Name"
    assert res["definition"] == "New AIC Def"
    assert res["nci_concept_id"] == "New nci id"
    assert res["order"] == 36
    assert res["activity_instance_classes"][0]["uid"] == activity_instance_class.uid
    assert res["activity_instance_classes"][0]["name"] == activity_instance_class.name
    assert res["activity_instance_classes"][0]["mandatory"] is True
    assert res["activity_instance_classes"][0]["is_adam_param_specific_enabled"] is True
    assert res["codelists"] == []
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["library_name"] == "Sponsor"


def test_activity_item_class_versioning(api_client):
    activity_item_class = TestUtils.create_activity_item_class(
        name="New item",
        order=2,
        activity_instance_classes=[
            {
                "uid": activity_instance_class.uid,
                "mandatory": False,
                "is_adam_param_specific_enabled": False,
            }
        ],
        approve=False,
        data_type_uid=data_type_term.term_uid,
        role_uid=role_term.term_uid,
    )

    # not successful create new version
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/versions"
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == "New draft version can be created only for FINAL versions."

    # successful approve
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # not successful approve
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/approvals"
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == "The object isn't in draft status."

    # not successful reactivate
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/activations"
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "Only RETIRED version can be reactivated."

    # successful inactivate
    response = api_client.delete(
        f"/activity-item-classes/{activity_item_class.uid}/activations"
    )
    assert_response_status_code(response, 200)

    # successful reactivate
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/activations"
    )
    assert_response_status_code(response, 200)

    # successful new version
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/versions"
    )
    assert_response_status_code(response, 201)

    activity_ic_to_delete = TestUtils.create_activity_item_class(
        name="activity ic to delete",
        order=2,
        activity_instance_classes=[
            {
                "uid": activity_instance_class.uid,
                "mandatory": False,
                "is_adam_param_specific_enabled": False,
            },
        ],
        approve=False,
        data_type_uid=data_type_term.term_uid,
        role_uid=role_term.term_uid,
    )
    # successful delete
    response = api_client.delete(f"/activity-item-classes/{activity_ic_to_delete.uid}")
    assert_response_status_code(response, 204)


def test_get_activity_item_class_terms(api_client):
    response = api_client.get(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/terms"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["items"] == [
        {
            "code_submission_value": None,
            "codelist_submission_value": "C66737 SUMBVAL",
            "codelist_uid": "C66737",
            "name": "C123631_PDPSTINDname",
            "name_submission_value": None,
            "term_uid": "C123631_PDPSTIND",
        },
        {
            "code_submission_value": None,
            "codelist_submission_value": "C66737 SUMBVAL",
            "codelist_uid": "C66737",
            "name": "C123632_PDSTINDname",
            "name_submission_value": None,
            "term_uid": "C123632_PDSTIND",
        },
        {
            "code_submission_value": None,
            "codelist_submission_value": "C66737 SUMBVAL",
            "codelist_uid": "C66737",
            "name": "C126069_PIPINDname",
            "name_submission_value": None,
            "term_uid": "C126069_PIPIND",
        },
        {
            "code_submission_value": None,
            "codelist_submission_value": "C66737 SUMBVAL",
            "codelist_uid": "C66737",
            "name": "C126070_RDINDname",
            "name_submission_value": None,
            "term_uid": "C126070_RDIND",
        },
        {
            "code_submission_value": None,
            "codelist_submission_value": "C66737 SUMBVAL",
            "codelist_uid": "C66737",
            "name": "C139274_EXTTINDname",
            "name_submission_value": None,
            "term_uid": "C139274_EXTTIND",
        },
        {
            "code_submission_value": None,
            "codelist_submission_value": "C66737 SUMBVAL",
            "codelist_uid": "C66737",
            "name": "C139275_PASSINDname",
            "name_submission_value": None,
            "term_uid": "C139275_PASSIND",
        },
        {
            "code_submission_value": None,
            "codelist_submission_value": "C66737 SUMBVAL",
            "codelist_uid": "C66737",
            "name": "C146995_ADAPTname",
            "name_submission_value": None,
            "term_uid": "C146995_ADAPT",
        },
        {
            "code_submission_value": None,
            "codelist_submission_value": "C66737 SUMBVAL",
            "codelist_uid": "C66737",
            "name": "C25196_RANDOMname",
            "name_submission_value": None,
            "term_uid": "C25196_RANDOM",
        },
        {
            "code_submission_value": None,
            "codelist_submission_value": "C66737 SUMBVAL",
            "codelist_uid": "C66737",
            "name": "C49703_ADDONname",
            "name_submission_value": None,
            "term_uid": "C49703_ADDON",
        },
        {
            "code_submission_value": None,
            "codelist_submission_value": "C66737 SUMBVAL",
            "codelist_uid": "C66737",
            "name": "C98737_HLTSUBJIname",
            "name_submission_value": None,
            "term_uid": "C98737_HLTSUBJI",
        },
    ]


def test_edit_activity_item_class_codelist_relationship(api_client):
    api_client.post(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/versions"
    )
    response = api_client.patch(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}",
        json={"codelist_uids": [CT_CODELIST_UIDS.frequency]},
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res["codelists"]) == 1
    assert res["codelists"][0]["uid"] == CT_CODELIST_UIDS.frequency

    response = api_client.get(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}"
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res["codelists"]) == 1
    assert res["codelists"][0]["uid"] == CT_CODELIST_UIDS.frequency
