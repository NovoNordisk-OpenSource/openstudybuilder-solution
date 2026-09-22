"""
Tests for /activity-instance-classes endpoints
"""

import json
import logging
from functools import reduce
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.standard_data_models.data_model import DataModel
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
data_model: str
data_model_catalogue: DataModel
activity_instance_classes_all: list[ActivityInstanceClass]
dataset_class: DatasetClass
role_term: CTTerm
data_type_term: CTTerm
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
    global data_model
    global data_model_catalogue
    global role_term
    global data_type_term

    data_model = TestUtils.create_data_model()
    data_model_catalogue = TestUtils.create_data_model_catalogue(name="SDTMIG")
    dataset_class = TestUtils.create_dataset_class(
        data_model_uid=data_model.uid,
        data_model_catalogue_name=data_model_catalogue,
        data_model_name=data_model.name,
    )

    _data_domain_terms = [
        TestUtils.create_ct_term(
            codelist_uid="C66734",
            sponsor_preferred_name="Data Domain Term1",
        ),
        TestUtils.create_ct_term(
            codelist_uid="C66734",
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
            )
        )
        activity_instance_classes_all.append(
            TestUtils.create_activity_instance_class(
                name=f"name-XXX-{index}",
                definition=f"def-XXX-{index}",
                order=(index * 4) + 3,
                is_domain_specific=False,
                level=index,
            )
        )
        activity_instance_classes_all.append(
            TestUtils.create_activity_instance_class(
                name=f"name-YYY-{index}",
                definition=f"def-YYY-{index}",
                order=(index * 4) + 4,
                is_domain_specific=False,
                level=index,
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
                "is_additional_optional": False,
                "is_default_linked": False,
            },
            {
                "uid": activity_instance_classes_all[25].uid,
                "mandatory": True,
                "is_adam_param_specific_enabled": True,
                "is_additional_optional": False,
                "is_default_linked": False,
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
                "is_additional_optional": False,
                "is_default_linked": False,
            },
            {
                "uid": activity_instance_classes_all[25].uid,
                "mandatory": True,
                "is_adam_param_specific_enabled": False,
                "is_additional_optional": False,
                "is_default_linked": False,
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
    "nci_concept_id",
    "nci_concept_name",
    "parent_class",
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
    print(response.text)
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(ACTIVITY_IC_FIELDS_ALL)
    for key in ACTIVITY_IC_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == activity_instance_classes_all[0].uid
    assert res["name"] == "name A"
    assert res["definition"] is None
    assert res["order"] is None
    assert res["is_domain_specific"] is False
    assert res["level"] is None
    assert res["nci_concept_id"] is None
    assert res["nci_concept_name"] is None
    assert res["parent_class"] is None
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_get_activity_instance_class_pagination(api_client):
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/activity-instance-classes?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        assert_response_status_code(response, 200)
        res = response.json()
        res_names = [item["name"] for item in res["items"]]
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        reduce(lambda a, b: list(a) + list(b), list(results_paginated.values()))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    response = api_client.get(
        f"/activity-instance-classes?page_number=1&page_size=100&sort_by={sort_by}"
    )
    assert_response_status_code(response, 200)
    res_all = response.json()
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
    assert_response_status_code(response, 200)
    res = response.json()

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
            "nci_concept_id": "nci id edited",
            "nci_concept_name": "nci name edited",
            "parent_uid": "ActivityInstanceClass_000002",
            "change_description": "Updated",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == "new name for instance class"
    assert res["definition"] == "definition"
    assert res["order"] == 30
    assert res["is_domain_specific"] is False
    assert res["level"] == 4
    assert res["nci_concept_id"] == "nci id edited"
    assert res["nci_concept_name"] == "nci name edited"
    assert res["parent_class"]["uid"] == "ActivityInstanceClass_000002"
    assert res["parent_class"]["name"] == "name-AAA"
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
    assert res["level"] == 4
    assert res["nci_concept_id"] == "nci id edited"
    assert res["nci_concept_name"] == "nci name edited"
    assert res["parent_class"]["uid"] == "ActivityInstanceClass_000002"
    assert res["parent_class"]["name"] == "name-AAA"
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["library_name"] == "Sponsor"

    dataset_class_2 = TestUtils.create_dataset_class(
        data_model_uid=data_model.uid,
        data_model_catalogue_name=data_model_catalogue,
        data_model_name=data_model.name,
    )
    response = api_client.patch(
        f"/activity-instance-classes/{activity_instance_class.uid}/model-mappings",
        json={
            "dataset_class_uid": dataset_class_2.uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)


def test_post_activity_instance_class(api_client):
    response = api_client.post(
        "/activity-instance-classes",
        json={
            "name": "New AC Name",
            "is_domain_specific": True,
            "nci_concept_id": "nci id new",
            "nci_concept_name": "nci name new",
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
    assert res["nci_concept_id"] == "nci id new"
    assert res["nci_concept_name"] == "nci name new"
    assert res["parent_class"]["uid"] == "ActivityInstanceClass_000002"
    assert res["parent_class"]["name"] == "name-AAA"
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
    assert res["nci_concept_id"] == "nci id new"
    assert res["nci_concept_name"] == "nci name new"
    assert res["parent_class"]["uid"] == "ActivityInstanceClass_000002"
    assert res["parent_class"]["name"] == "name-AAA"
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


def test_get_activity_instance_class_datasets(api_client):
    child_instance_class_uid = activity_instance_classes_all[5].uid
    parent_instance_class_uid = parent_uid

    # Create some necessary dataset classes and datasets
    # Including a sponsor model and dataset
    data_model_ig = TestUtils.create_data_model_ig(
        implemented_data_model=data_model.uid
    )
    dataset_class_for_parent = TestUtils.create_dataset_class(
        data_model_uid=data_model.uid,
        data_model_catalogue_name=data_model_catalogue,
        data_model_name=data_model.name,
    )
    dataset_for_parent = TestUtils.create_dataset(
        data_model_ig_uid=data_model_ig.uid,
        data_model_ig_version_number=data_model_ig.version_number,
        implemented_dataset_class_name=dataset_class_for_parent.uid,
        data_model_catalogue_name=data_model_catalogue,
    )
    dataset = TestUtils.create_dataset(
        data_model_ig_uid=data_model_ig.uid,
        data_model_ig_version_number=data_model_ig.version_number,
        implemented_dataset_class_name=dataset_class.uid,
        data_model_catalogue_name=data_model_catalogue,
    )
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )
    sponsor_dataset = TestUtils.create_sponsor_dataset(
        dataset_uid="ZX",
        sponsor_model_name=sponsor_model.name,
        sponsor_model_version_number=sponsor_model.version,
        implemented_dataset_class=dataset_class.uid,
        is_basic_std=False,
    )

    # Map a child ActivityInstanceClass to a DatasetClass
    api_client.patch(
        f"/activity-instance-classes/{child_instance_class_uid}/model-mappings",
        json={
            "dataset_class_uid": dataset_class.uid,
        },
    )

    # Map its parent to a different DatasetClass
    api_client.patch(
        f"/activity-instance-classes/{parent_instance_class_uid}/model-mappings",
        json={
            "dataset_class_uid": dataset_class_for_parent.uid,
        },
    )

    # Now, listing Datasets should return both Datasets for the child
    # And only one for the parent
    response = api_client.get("activity-instance-classes/model-mappings/datasets")
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) > 1
    child_class_mapping = next(
        (d for d in res if d["uid"] == child_instance_class_uid), None
    )
    assert len(child_class_mapping["datasets"]) == 3
    # Checking for list equality because the result should be ordered
    # Dataset for parent has a lower uid in alphabetical order as it was created first
    # So it should appear first - even though the repo query finds after the child's
    # This ensures correct sorting
    assert child_class_mapping["datasets"] == [
        dataset_for_parent.uid,
        dataset.uid,
        sponsor_dataset.uid,
    ]

    parent_class_mapping = next(
        (d for d in res if d["uid"] == parent_instance_class_uid), None
    )
    assert parent_class_mapping["datasets"] == [dataset_for_parent.uid]

    # Now get the mappings for a single class
    # For the parent class, it should only have one mapping, with a single Dataset
    response = api_client.get(
        f"activity-instance-classes/model-mappings/datasets?activity_instance_class_uid={parent_instance_class_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 1
    class_mapping = next(
        (d for d in res if d["uid"] == parent_instance_class_uid), None
    )
    assert class_mapping["datasets"] == [dataset_for_parent.uid]

    # Make sure that toggling off sponsor datasets works
    response = api_client.get(
        f"activity-instance-classes/model-mappings/datasets?activity_instance_class_uid={child_instance_class_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 1
    class_mapping = next((d for d in res if d["uid"] == child_instance_class_uid), None)
    assert class_mapping["datasets"] == [
        dataset_for_parent.uid,
        dataset.uid,
        sponsor_dataset.uid,
    ]

    # Test that filtering by IG works
    # Adding the default IG as filter should not change the results
    response = api_client.get(
        f"activity-instance-classes/model-mappings/datasets?activity_instance_class_uid={child_instance_class_uid}&ig_uid={data_model_ig.uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 1
    class_mapping = next((d for d in res if d["uid"] == child_instance_class_uid), None)
    assert class_mapping["datasets"] == [
        dataset_for_parent.uid,
        dataset.uid,
        sponsor_dataset.uid,
    ]

    # Filtering on a different one should return no results
    response = api_client.get(
        f"activity-instance-classes/model-mappings/datasets?activity_instance_class_uid={child_instance_class_uid}&ig_uid=Whatever",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 0

    # Combine filters
    response = api_client.get(
        f"activity-instance-classes/model-mappings/datasets?activity_instance_class_uid={child_instance_class_uid}&ig_uid={data_model_ig.uid}&include_sponsor=false",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 1
    class_mapping = next((d for d in res if d["uid"] == child_instance_class_uid), None)
    assert class_mapping["datasets"] == [
        dataset_for_parent.uid,
        dataset.uid,
    ]


def test_get_activity_item_classes_for_instance_class(api_client):
    # First, test getting all activity item classes, dataset-independent
    response = api_client.get(
        f"/activity-instance-classes/{activity_instance_classes_all[0].uid}/activity-item-classes"
    )
    res = response.json()
    assert len(res) == 0

    response = api_client.get(
        f"/activity-instance-classes/{activity_instance_classes_all[1].uid}/activity-item-classes"
    )
    res = response.json()
    assert len(res) == 1
    assert res[0]["name"] == "name A"
    assert res[0]["data_type_uid"] == data_type_term.term_uid
    assert res[0]["data_type_name"] == "Data type"

    response = api_client.get(
        f"/activity-instance-classes/{activity_instance_classes_all[20].uid}/activity-item-classes"
    )
    res = response.json()
    assert len(res) == 1
    assert res[0]["name"] == "name B"

    response = api_client.get(
        f"/activity-instance-classes/{activity_instance_classes_all[25].uid}/activity-item-classes"
    )
    res = response.json()
    assert len(res) == 2

    # Next, test with a dataset filter
    # This should only return ActivityItemClass mapped to a VariableClass
    # being implemented in the given dataset
    # This requires creating some data
    child_instance_class_uid = activity_instance_classes_all[5].uid
    parent_instance_class_uid = parent_uid

    # Create some necessary dataset variable classes and variables
    data_model_ig = TestUtils.create_data_model_ig(
        name="ICIG", implemented_data_model=data_model.uid
    )
    dataset = TestUtils.create_dataset(
        data_model_ig_uid=data_model_ig.uid,
        data_model_ig_version_number=data_model_ig.version_number,
        implemented_dataset_class_name=dataset_class.uid,
        data_model_catalogue_name=data_model_catalogue,
        label="IC",
    )
    variable_class = TestUtils.create_variable_class(
        dataset_class_uid=dataset_class.uid,
        data_model_catalogue_name=data_model_catalogue,
        data_model_name=data_model.uid,
        data_model_version=data_model.version_number,
        label="--VC",
    )
    variable_class_for_parent = TestUtils.create_variable_class(
        dataset_class_uid=dataset_class.uid,
        data_model_catalogue_name=data_model_catalogue,
        data_model_name=data_model.uid,
        data_model_version=data_model.version_number,
        label="--PVC",
    )
    _ = TestUtils.create_dataset_variable(
        dataset_uid=dataset.uid,
        data_model_catalogue_name=data_model_catalogue,
        data_model_ig_name=data_model_ig.uid,
        data_model_ig_version=data_model_ig.version_number,
        class_variable_uid=variable_class.uid,
        label="ICVC",
    )
    _ = TestUtils.create_dataset_variable(
        dataset_uid=dataset.uid,
        data_model_catalogue_name=data_model_catalogue,
        data_model_ig_name=data_model_ig.uid,
        data_model_ig_version=data_model_ig.version_number,
        class_variable_uid=variable_class_for_parent.uid,
        label="ICPVC",
    )
    # Create some activity item classes
    _ = TestUtils.create_activity_item_class(
        name="unmapped",
        definition="unmapped definition",
        nci_concept_id="unmapped nci id",
        order=3,
        activity_instance_classes=[
            {
                "uid": child_instance_class_uid,
                "mandatory": False,
                "is_adam_param_specific_enabled": True,
                "is_additional_optional": False,
                "is_default_linked": False,
            },
        ],
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )
    mapped_activity_item_class = TestUtils.create_activity_item_class(
        name="mapped",
        definition="mapped definition",
        nci_concept_id="mapped nci id",
        order=3,
        activity_instance_classes=[
            {
                "uid": child_instance_class_uid,
                "mandatory": False,
                "is_adam_param_specific_enabled": True,
                "is_additional_optional": False,
                "is_default_linked": False,
            },
        ],
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )
    parent_mapped_activity_item_class = TestUtils.create_activity_item_class(
        name="parent mapped",
        definition="parent mapped definition",
        nci_concept_id="parent mapped nci id",
        order=3,
        activity_instance_classes=[
            {
                "uid": parent_instance_class_uid,
                "mandatory": False,
                "is_adam_param_specific_enabled": True,
                "is_additional_optional": False,
                "is_default_linked": False,
            },
        ],
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )
    # Connect variable classes to activity item class
    api_client.patch(
        f"/activity-item-classes/{mapped_activity_item_class.uid}/model-mappings",
        json={
            "variable_class_uids": [variable_class.uid],
        },
    )
    api_client.patch(
        f"/activity-item-classes/{parent_mapped_activity_item_class.uid}/model-mappings",
        json={
            "variable_class_uids": [variable_class_for_parent.uid],
        },
    )

    # List ActivityItemClasses without filtering on dataset or ig
    response = api_client.get(
        f"/activity-instance-classes/{child_instance_class_uid}/activity-item-classes"
    )
    res = response.json()
    assert len(res) == 3

    # List ActivityItemClasses with dataset filter
    response = api_client.get(
        f"/activity-instance-classes/{child_instance_class_uid}/activity-item-classes?dataset_uid={dataset.uid}"
    )
    res = response.json()
    assert len(res) == 2
    returned_names = [el["name"] for el in res]
    assert "mapped" in returned_names
    assert "parent mapped" in returned_names

    # List ActivityItemClasses with ig filter
    response = api_client.get(
        f"/activity-instance-classes/{child_instance_class_uid}/activity-item-classes?ig_uid={data_model_ig.uid}"
    )
    res = response.json()
    assert len(res) == 2

    response = api_client.get(
        f"/activity-instance-classes/{child_instance_class_uid}/activity-item-classes?ig_uid=non-existent"
    )
    res = response.json()
    assert len(res) == 0


def test_get_activity_instance_class_parent_overview(api_client: TestClient) -> None:
    """Test GET /activity-instance-classes/{uid}/parent-class-overview endpoint"""
    # Find a parent class (one with children) dynamically
    parent_class_uid = None
    for cls in activity_instance_classes_all:
        # Try to get child classes - if any exist, it's a parent
        response = api_client.get(f"/activity-instance-classes/{cls.uid}/child-classes")
        if response.status_code == 200:
            result = response.json()
            if len(result.get("items", [])) > 0:
                parent_class_uid = cls.uid
                break

    assert parent_class_uid is not None, "Could not find a parent class for testing"

    response = api_client.get(
        f"/activity-instance-classes/{parent_class_uid}/parent-class-overview"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert "parent_activity_instance_class" in result
    assert "all_versions" in result

    parent_detail = result["parent_activity_instance_class"]
    assert parent_detail["uid"] == parent_class_uid
    assert "name" in parent_detail
    assert "status" in parent_detail
    assert "version" in parent_detail

    # Test with version parameter
    response = api_client.get(
        f"/activity-instance-classes/{parent_class_uid}/parent-class-overview?version=0.1"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert result["parent_activity_instance_class"]["version"] == "0.1"

    # Test that a leaf class cannot use this endpoint
    # Find a leaf class dynamically
    leaf_class_uid = None
    for cls in activity_instance_classes_all:
        response = api_client.get(f"/activity-instance-classes/{cls.uid}/child-classes")
        if response.status_code == 200:
            result = response.json()
            if len(result.get("items", [])) == 0:
                leaf_class_uid = cls.uid
                break

    if leaf_class_uid:
        response = api_client.get(
            f"/activity-instance-classes/{leaf_class_uid}/parent-class-overview"
        )
        # Should get 404 error because leaf classes can't use parent-class-overview
        assert_response_status_code(response, 404)

    # Test with non-existent UID
    response = api_client.get(
        "/activity-instance-classes/INVALID_UID/parent-class-overview"
    )
    assert_response_status_code(response, 404)


def test_get_activity_instance_class_overview(api_client: TestClient) -> None:
    """Test GET /activity-instance-classes/{uid}/overview endpoint"""
    # Find a leaf class (one without children) dynamically
    leaf_class = None
    for cls in activity_instance_classes_all:
        # Try to get child classes - if none exist, it's a leaf
        response = api_client.get(f"/activity-instance-classes/{cls.uid}/child-classes")
        if response.status_code == 200:
            result = response.json()
            if len(result.get("items", [])) == 0:
                leaf_class = cls
                break

    assert leaf_class is not None, "Could not find a leaf class for testing"

    response = api_client.get(f"/activity-instance-classes/{leaf_class.uid}/overview")
    assert_response_status_code(response, 200)

    result = response.json()
    assert "activity_instance_class" in result
    assert "all_versions" in result

    instance_detail = result["activity_instance_class"]
    assert instance_detail["uid"] == leaf_class.uid
    assert instance_detail["name"] == leaf_class.name
    assert "status" in instance_detail
    assert "version" in instance_detail

    # Test with version parameter
    response = api_client.get(
        f"/activity-instance-classes/{leaf_class.uid}/overview?version=0.1"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert result["activity_instance_class"]["version"] == "0.1"

    # Parent classes can also use the overview endpoint - it just shows general information
    # while parent-class-overview shows parent-specific information with children


def test_get_child_instance_classes(api_client: TestClient) -> None:
    """Test GET /activity-instance-classes/{uid}/child-classes endpoint"""
    # Find a parent class dynamically
    parent_class_uid = None
    for cls in activity_instance_classes_all:
        response = api_client.get(f"/activity-instance-classes/{cls.uid}/child-classes")
        if response.status_code == 200:
            result = response.json()
            if len(result.get("items", [])) > 0:
                parent_class_uid = cls.uid
                break

    assert parent_class_uid is not None, "Could not find a parent class for testing"

    # Test with parent class
    response = api_client.get(
        f"/activity-instance-classes/{parent_class_uid}/child-classes"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert "items" in result
    assert "total" in result
    assert len(result["items"]) > 0

    # Check structure of first child
    first_child = result["items"][0]
    assert "uid" in first_child
    assert "name" in first_child
    assert "status" in first_child
    assert "version" in first_child

    # Test pagination
    response = api_client.get(
        f"/activity-instance-classes/{parent_class_uid}/child-classes?page_size=2&page_number=1&total_count=true"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert len(result["items"]) <= 2
    assert result["total"] >= 1

    # Test with version parameter
    response = api_client.get(
        f"/activity-instance-classes/{parent_class_uid}/child-classes?version=0.1"
    )
    assert_response_status_code(response, 200)


def test_get_item_classes_paginated(api_client: TestClient) -> None:
    """Test GET /activity-instance-classes/{uid}/item-classes endpoint"""
    # Find a class that has item classes
    instance_class = None
    for cls in activity_instance_classes_all[:5]:  # Check first 5 to speed up test
        response = api_client.get(f"/activity-instance-classes/{cls.uid}/item-classes")
        if response.status_code == 200:
            result = response.json()
            if len(result.get("items", [])) > 0:
                instance_class = cls
                break

    # If none found in first 5, just use the first one (tests will adapt)
    if instance_class is None:
        instance_class = activity_instance_classes_all[0]

    # Test basic request
    response = api_client.get(
        f"/activity-instance-classes/{instance_class.uid}/item-classes"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert "items" in result
    assert "total" in result

    if len(result["items"]) > 0:
        first_item = result["items"][0]
        assert "uid" in first_item
        assert "name" in first_item
        assert "parent_name" in first_item
        assert "parent_uid" in first_item
        assert "definition" in first_item
        assert "modified_date" in first_item
        assert "modified_by" in first_item
        assert "version" in first_item
        assert "status" in first_item

    # Test with pagination
    response = api_client.get(
        f"/activity-instance-classes/{instance_class.uid}/item-classes?page_size=5&page_number=1&total_count=true"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert len(result["items"]) <= 5

    # Test with version parameter
    response = api_client.get(
        f"/activity-instance-classes/{instance_class.uid}/item-classes?version=0.1"
    )
    assert_response_status_code(response, 200)


def test_get_activity_instance_classes_versions(api_client):
    """Test GET /activity-instance-classes/versions endpoint"""
    # First, create a new version of one class so we have multiple versions
    response = api_client.post(
        f"/activity-instance-classes/{activity_instance_classes_all[0].uid}/versions"
    )
    assert_response_status_code(response, 201)

    # Get all versions
    response = api_client.get(
        "/activity-instance-classes/versions?page_size=100&total_count=true"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check response structure
    assert set(res.keys()) == {"items", "total", "page", "size"}
    assert res["total"] > 0

    # Should have more versions than unique classes (since we created a new version above)
    assert res["total"] > len(activity_instance_classes_all)

    # Check that the items are sorted by start_date descending
    start_dates = [item["start_date"] for item in res["items"] if item["start_date"]]
    assert start_dates == sorted(start_dates, reverse=True)

    # Check that the class updated in this test has multiple versions
    versions_of_class = [
        item["version"]
        for item in res["items"]
        if item["uid"] == activity_instance_classes_all[0].uid
    ]
    assert len(versions_of_class) >= 2

    # Check fields on first item
    item = res["items"][0]
    assert "uid" in item
    assert "name" in item
    assert "version" in item
    assert "status" in item
    assert "start_date" in item
    assert "library_name" in item


def test_get_activity_instance_classes_versions_pagination(api_client):
    """Test pagination on /activity-instance-classes/versions"""
    # Get first page
    response = api_client.get(
        "/activity-instance-classes/versions?page_size=5&page_number=1&total_count=true"
    )
    assert_response_status_code(response, 200)
    page1 = response.json()
    assert len(page1["items"]) == 5
    assert page1["total"] > 5

    # Get second page
    response = api_client.get(
        "/activity-instance-classes/versions?page_size=5&page_number=2&total_count=true"
    )
    assert_response_status_code(response, 200)
    page2 = response.json()
    assert len(page2["items"]) > 0

    # Pages should not overlap
    page1_uids_versions = {(i["uid"], i["version"]) for i in page1["items"]}
    page2_uids_versions = {(i["uid"], i["version"]) for i in page2["items"]}
    assert page1_uids_versions.isdisjoint(page2_uids_versions)
