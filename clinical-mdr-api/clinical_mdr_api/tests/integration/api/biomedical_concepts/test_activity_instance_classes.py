"""
Tests for /activity-instance-classes endpoints
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
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.standard_data_models.dataset_class import DatasetClass
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
activity_instance_classes_all: list[ActivityInstanceClass]
dataset_class: DatasetClass
data_domain_terms: list[CTTerm]

parent_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "activity-instance-class.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global activity_instance_classes_all
    global parent_uid
    global dataset_class
    global data_domain_terms

    data_model = TestUtils.create_data_model()
    data_model_catalogue = TestUtils.create_data_model_catalogue()
    dataset_class = TestUtils.create_dataset_class(
        data_model_uid=data_model.uid,
        data_model_catalogue_name=data_model_catalogue,
    )

    codelist = TestUtils.create_ct_codelist(extensible=True, approve=True)
    data_domain_terms = [
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Data Domain Term1",
        ),
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Data Domain Term2",
        ),
    ]

    # Create some activity instance classes
    activity_instance_classes_all = [
        TestUtils.create_activity_instance_class(name="name A"),
        TestUtils.create_activity_instance_class(name="name-AAA", definition="def-AAA"),
        TestUtils.create_activity_instance_class(name="name-BBB", definition="def-BBB"),
        TestUtils.create_activity_instance_class(name="name XXX", definition="def-XXX"),
        TestUtils.create_activity_instance_class(name="name YYY", definition="def-YYY"),
    ]
    parent_uid = activity_instance_classes_all[0].uid
    for index in range(5):
        activity_instance_classes_all.append(
            TestUtils.create_activity_instance_class(
                name=f"name-AAA-{index}",
                definition=f"def-AAA-{index}",
                order=(index * 4) + 1,
                is_domain_specific=True,
                level=index,
                data_domain_uids=[data_domain_terms[0].term_uid],
                parent_uid=parent_uid,
            )
        )
        activity_instance_classes_all.append(
            TestUtils.create_activity_instance_class(
                name=f"name-BBB-{index}",
                definition=f"def-BBB-{index}",
                order=(index * 4) + 2,
                is_domain_specific=True,
                level=index,
                data_domain_uids=[data_domain_terms[0].term_uid],
            )
        )
        activity_instance_classes_all.append(
            TestUtils.create_activity_instance_class(
                name=f"name-XXX-{index}",
                definition=f"def-XXX-{index}",
                order=(index * 4) + 3,
                is_domain_specific=False,
                level=index,
                data_domain_uids=[data_domain_terms[0].term_uid],
            )
        )
        activity_instance_classes_all.append(
            TestUtils.create_activity_instance_class(
                name=f"name-YYY-{index}",
                definition=f"def-YYY-{index}",
                order=(index * 4) + 4,
                is_domain_specific=False,
                level=index,
                data_domain_uids=[data_domain_terms[0].term_uid],
            )
        )

    activity_instance_classes_all.append(
        TestUtils.create_activity_instance_class(
            name="name-with-parent",
            definition="def-with-parent",
            order=999,
            is_domain_specific=False,
            parent_uid=activity_instance_classes_all[20].uid,
        )
    )
    data_type_term = TestUtils.create_ct_term(sponsor_preferred_name="Data type")
    role_term = TestUtils.create_ct_term(sponsor_preferred_name="Role")
    TestUtils.create_activity_item_class(
        name="name A",
        definition="definition A",
        nci_concept_id="nci id A",
        order=1,
        activity_instance_classes=[
            {
                "uid": activity_instance_classes_all[1].uid,
                "mandatory": True,
                "is_adam_param_specific_enabled": True,
            },
            {
                "uid": activity_instance_classes_all[25].uid,
                "mandatory": True,
                "is_adam_param_specific_enabled": True,
            },
        ],
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )
    TestUtils.create_activity_item_class(
        name="name B",
        definition="definition B",
        nci_concept_id="nci id B",
        order=2,
        activity_instance_classes=[
            {
                "uid": activity_instance_classes_all[20].uid,
                "mandatory": True,
                "is_adam_param_specific_enabled": False,
            },
            {
                "uid": activity_instance_classes_all[25].uid,
                "mandatory": True,
                "is_adam_param_specific_enabled": False,
            },
        ],
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )

    yield


ACTIVITY_IC_FIELDS_ALL = [
    "uid",
    "name",
    "definition",
    "order",
    "is_domain_specific",
    "level",
    "parent_class",
    "dataset_class",
    "activity_item_classes",
    "data_domains",
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
]


def test_get_activity_instance_class(api_client):
    response = api_client.get(
        f"/activity-instance-classes/{activity_instance_classes_all[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(list(res.keys())) == set(ACTIVITY_IC_FIELDS_ALL)
    for key in ACTIVITY_IC_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == activity_instance_classes_all[0].uid
    assert res["name"] == "name A"
    assert res["definition"] is None
    assert res["order"] is None
    assert res["is_domain_specific"] is None
    assert res["level"] is None
    assert res["parent_class"] is None
    assert res["dataset_class"] is None
    assert res["activity_item_classes"] is None
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_get_activity_instance_class_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/activity-instance-classes?page_number={page_number}&page_size=10&sort_by={sort_by}"
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
        f"/activity-instance-classes?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(activity_instance_classes_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 6),  # Total number of data models is 25
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_activity_instance_classes(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/activity-instance-classes"
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

    print(f"******** GET {url} \n\n")
    log.info("GET %s", url)
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    assert res["total"] == (len(activity_instance_classes_all) if total_count else 0)
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
def test_get_activity_instance_classes_csv_xml_excel(api_client, export_format):
    url = "activity-instance-classes"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param('{"*": {"v": ["aaa"]}}', "definition", "def-AAA"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/activity-instance-classes?filters={filter_by}"
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
            assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param('{"name": {"v": ["name-AAA"]}}', "name", "name-AAA"),
        pytest.param('{"name": {"v": ["name-BBB"]}}', "name", "name-BBB"),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param('{"definition": {"v": ["def-XXX"]}}', "definition", "def-XXX"),
        pytest.param('{"definition": {"v": ["def-YYY"]}}', "definition", "def-YYY"),
        pytest.param('{"definition": {"v": ["cc"]}}', None, None),
        pytest.param('{"order": {"v": [1]}}', "order", 1),
        pytest.param(
            '{"is_domain_specific": {"v": [true]}}', "is_domain_specific", True
        ),
        pytest.param('{"level": {"v": [4]}}', "level", 4),
        pytest.param(
            '{"parent_class.uid": {"v": ["ActivityInstanceClass_000001"]}}',
            "parent_class.uid",
            "ActivityInstanceClass_000001",
        ),
        pytest.param(
            '{"parent_class.name": {"v": ["name A"]}}',
            "parent_class.name",
            "name A",
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/activity-instance-classes?filters={filter_by}"
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
                assert row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0


def test_edit_activity_instance_class(api_client):
    activity_instance_class = TestUtils.create_activity_instance_class(
        name="New instance class",
        definition="definition",
        order=30,
        is_domain_specific=True,
        approve=False,
    )
    response = api_client.patch(
        f"/activity-instance-classes/{activity_instance_class.uid}",
        json={
            "name": "new name for instance class",
            "is_domain_specific": False,
            "level": 4,
            "parent_uid": "ActivityInstanceClass_000002",
            "dataset_class_uid": "DatasetClass_000001",
            "data_domain_uids": [
                data_domain_terms[0].term_uid,
                data_domain_terms[1].term_uid,
            ],
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == "new name for instance class"
    assert res["definition"] == "definition"
    assert res["order"] == 30
    assert res["is_domain_specific"] is False
    assert res["level"] == 4
    assert res["parent_class"]["uid"] == "ActivityInstanceClass_000002"
    assert res["parent_class"]["name"] == "name-AAA"
    assert res["parent_class"]["activity_item_classes"] == [
        {
            "uid": "ActivityItemClass_000001",
            "name": "name A",
            "mandatory": True,
            "is_adam_param_specific_enabled": True,
        }
    ]
    assert res["dataset_class"]["uid"] == "DatasetClass_000001"
    assert res["dataset_class"]["title"] == "title"
    assert res["activity_item_classes"] == []
    assert res["data_domains"][0]["uid"] == data_domain_terms[0].term_uid
    assert res["data_domains"][0]["name"] == data_domain_terms[0].sponsor_preferred_name
    assert res["data_domains"][1]["uid"] == data_domain_terms[1].term_uid
    assert res["data_domains"][1]["name"] == data_domain_terms[1].sponsor_preferred_name
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["library_name"] == "Sponsor"

    response = api_client.get(
        f"/activity-instance-classes/{activity_instance_class.uid}"
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == "new name for instance class"
    assert res["definition"] == "definition"
    assert res["order"] == 30
    assert res["is_domain_specific"] is False
    assert res["parent_class"]["uid"] == "ActivityInstanceClass_000002"
    assert res["parent_class"]["name"] == "name-AAA"
    assert res["parent_class"]["activity_item_classes"] == [
        {
            "uid": "ActivityItemClass_000001",
            "name": "name A",
            "mandatory": True,
            "is_adam_param_specific_enabled": True,
        }
    ]
    assert res["dataset_class"]["uid"] == "DatasetClass_000001"
    assert res["dataset_class"]["title"] == "title"
    assert res["activity_item_classes"] is None
    assert res["data_domains"][0]["uid"] == data_domain_terms[0].term_uid
    assert res["data_domains"][0]["name"] == data_domain_terms[0].sponsor_preferred_name
    assert res["data_domains"][1]["uid"] == data_domain_terms[1].term_uid
    assert res["data_domains"][1]["name"] == data_domain_terms[1].sponsor_preferred_name
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["library_name"] == "Sponsor"


def test_post_activity_instance_class(api_client):
    response = api_client.post(
        "/activity-instance-classes",
        json={
            "name": "New AC Name",
            "is_domain_specific": True,
            "library_name": "Sponsor",
            "parent_uid": "ActivityInstanceClass_000002",
            "dataset_class_uid": "DatasetClass_000001",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["name"] == "New AC Name"
    assert res["definition"] is None
    assert res["order"] is None
    assert res["is_domain_specific"] is True
    assert res["level"] is None
    assert res["parent_class"]["uid"] == "ActivityInstanceClass_000002"
    assert res["parent_class"]["name"] == "name-AAA"
    assert res["parent_class"]["activity_item_classes"] == [
        {
            "uid": "ActivityItemClass_000001",
            "name": "name A",
            "mandatory": True,
            "is_adam_param_specific_enabled": True,
        }
    ]
    assert res["dataset_class"]["uid"] == "DatasetClass_000001"
    assert res["dataset_class"]["title"] == "title"
    assert res["activity_item_classes"] == []
    assert res["data_domains"] == []
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["library_name"] == "Sponsor"

    response = api_client.get(f"/activity-instance-classes/{res['uid']}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["name"] == "New AC Name"
    assert res["definition"] is None
    assert res["order"] is None
    assert res["is_domain_specific"] is True
    assert res["parent_class"]["uid"] == "ActivityInstanceClass_000002"
    assert res["parent_class"]["name"] == "name-AAA"
    assert res["parent_class"]["activity_item_classes"] == [
        {
            "uid": "ActivityItemClass_000001",
            "name": "name A",
            "mandatory": True,
            "is_adam_param_specific_enabled": True,
        }
    ]
    assert res["dataset_class"]["uid"] == "DatasetClass_000001"
    assert res["dataset_class"]["title"] == "title"
    assert res["activity_item_classes"] is None
    assert res["data_domains"] is None
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["library_name"] == "Sponsor"


def test_activity_instance_class_versioning(api_client):
    activity_instance_class = TestUtils.create_activity_instance_class(
        name="New class", approve=False
    )

    # not successful create new version
    response = api_client.post(
        f"/activity-instance-classes/{activity_instance_class.uid}/versions"
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == "New draft version can be created only for FINAL versions."

    # successful approve
    response = api_client.post(
        f"/activity-instance-classes/{activity_instance_class.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # not successful approve
    response = api_client.post(
        f"/activity-instance-classes/{activity_instance_class.uid}/approvals"
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == "The object isn't in draft status."

    # not successful reactivate
    response = api_client.post(
        f"/activity-instance-classes/{activity_instance_class.uid}/activations"
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "Only RETIRED version can be reactivated."

    # successful inactivate
    response = api_client.delete(
        f"/activity-instance-classes/{activity_instance_class.uid}/activations"
    )
    assert_response_status_code(response, 200)

    # successful reactivate
    response = api_client.post(
        f"/activity-instance-classes/{activity_instance_class.uid}/activations"
    )
    assert_response_status_code(response, 200)

    # successful new version
    response = api_client.post(
        f"/activity-instance-classes/{activity_instance_class.uid}/versions"
    )
    assert_response_status_code(response, 201)

    activity_ic_to_delete = TestUtils.create_activity_instance_class(
        name="activity ic to delete", approve=False
    )
    # successful delete
    response = api_client.delete(
        f"/activity-instance-classes/{activity_ic_to_delete.uid}"
    )
    assert_response_status_code(response, 204)


def test_filter_activity_instance_class_on_parent_activity_item_class(api_client):
    response = api_client.get(
        '/activity-instance-classes?filters={"parent_class.activity_item_classes.name": {"v":["name B"]}}'
    )
    res = response.json()

    assert len(res["items"]) == 1

    assert_response_status_code(response, 200)
    assert res["items"][0]["uid"] == activity_instance_classes_all[25].uid
    assert res["items"][0]["name"] == "name-with-parent"
    assert res["items"][0]["definition"] == "def-with-parent"
    assert res["items"][0]["order"] == 999
    assert res["items"][0]["is_domain_specific"] is False
    assert res["items"][0]["parent_class"] == {
        "activity_item_classes": [
            {
                "uid": "ActivityItemClass_000002",
                "name": "name B",
                "mandatory": True,
                "is_adam_param_specific_enabled": False,
            }
        ],
        "name": "name-YYY-3",
        "uid": "ActivityInstanceClass_000021",
        "data_domains": [
            {
                "code_submission_value": data_domain_terms[0].code_submission_value,
                "name": "Data Domain Term1",
                "uid": "CTTerm_000005",
            }
        ],
    }
    assert res["items"][0]["dataset_class"] is None
    assert res["items"][0]["activity_item_classes"] == [
        {
            "is_adam_param_specific_enabled": False,
            "mandatory": True,
            "name": "name B",
            "uid": "ActivityItemClass_000002",
        },
        {
            "uid": "ActivityItemClass_000001",
            "name": "name A",
            "mandatory": True,
            "is_adam_param_specific_enabled": True,
        },
    ]
    assert res["items"][0]["version"] == "1.0"
    assert res["items"][0]["status"] == "Final"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["possible_actions"] == ["inactivate", "new_version"]
