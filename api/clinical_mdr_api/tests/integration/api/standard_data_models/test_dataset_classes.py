"""
Tests for /standards/dataset-classes endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import json
import logging
from functools import reduce
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.standard_data_models.data_model import DataModel
from clinical_mdr_api.models.standard_data_models.dataset_class import DatasetClass
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
dataset_classes: list[DatasetClass]
data_model_catalogue_name: str
data_models: list[DataModel]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "dataset-classes.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global dataset_classes
    global data_model_catalogue_name
    global data_models

    data_model_catalogue_name = TestUtils.create_data_model_catalogue(
        name="DataModelCatalogue name"
    )
    data_models = [
        TestUtils.create_data_model(name=name)
        for name in ["DataModel A", "DataModel B", "DataModel C"]
    ]

    # Create some dataset classes
    dataset_classes = []
    dataset_classes.append(
        TestUtils.create_dataset_class(
            label="DatasetClass A label",
            title="DatasetClass A title",
            description="DatasetClass A desc",
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_uid=data_models[0].uid,
            data_model_name=data_models[0].name,
        )
    )

    dataset_classes.append(
        TestUtils.create_dataset_class(
            label="name-AAA",
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_uid=data_models[1].uid,
            data_model_name=data_models[1].name,
        )
    )
    dataset_classes.append(
        TestUtils.create_dataset_class(
            label="name-BBB",
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_uid=data_models[1].uid,
            data_model_name=data_models[1].name,
        )
    )
    dataset_classes.append(
        TestUtils.create_dataset_class(
            description="def-XXX",
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_uid=data_models[1].uid,
            data_model_name=data_models[1].name,
        )
    )
    dataset_classes.append(
        TestUtils.create_dataset_class(
            description="def-YYY",
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_uid=data_models[1].uid,
            data_model_name=data_models[1].name,
        )
    )

    for index in range(5):
        dataset_classes.append(
            TestUtils.create_dataset_class(
                label=f"name-AAA-{index}",
                data_model_catalogue_name=data_model_catalogue_name,
                data_model_uid=data_models[2].uid,
                data_model_name=data_models[2].name,
            )
        )
        dataset_classes.append(
            TestUtils.create_dataset_class(
                label=f"name-BBB-{index}",
                data_model_catalogue_name=data_model_catalogue_name,
                data_model_uid=data_models[2].uid,
                data_model_name=data_models[2].name,
            )
        )
        dataset_classes.append(
            TestUtils.create_dataset_class(
                description=f"def-XXX-{index}",
                data_model_catalogue_name=data_model_catalogue_name,
                data_model_uid=data_models[2].uid,
                data_model_name=data_models[2].name,
            )
        )
        dataset_classes.append(
            TestUtils.create_dataset_class(
                description=f"def-YYY-{index}",
                data_model_catalogue_name=data_model_catalogue_name,
                data_model_uid=data_models[2].uid,
                data_model_name=data_models[2].name,
            )
        )

    yield


DATASET_CLASS_FIELDS_ALL = [
    "uid",
    "label",
    "title",
    "description",
    "catalogue_name",
    "data_model",
    "parent_class_name",
]

DATASET_CLASS_FIELDS_NOT_NULL = [
    "uid",
    "label",
    "catalogue_name",
    "data_model",
]


def test_get_dataset_class(api_client):
    response = api_client.get(
        f"/standards/dataset-classes/{dataset_classes[0].uid}?data_model_name={data_models[0].name}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(DATASET_CLASS_FIELDS_ALL)
    for key in DATASET_CLASS_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == dataset_classes[0].uid
    assert res["label"] == "DatasetClass A label"
    assert res["description"] == "DatasetClass A desc"
    assert res["catalogue_name"] == data_model_catalogue_name
    assert res["data_model"]["data_model_name"] == data_models[0].name


def test_get_dataset_classes_pagination(api_client):
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"uid": true}'
    for page_number in range(1, 4):
        url = f"/standards/dataset-classes?data_model_name={data_models[2].name}&page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_uids = [item["uid"] for item in res["items"]]
        results_paginated[page_number] = res_uids
        log.info("Page %s: %s", page_number, res_uids)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        reduce(lambda a, b: list(a) + list(b), list(results_paginated.values()))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"/standards/dataset-classes?data_model_name={data_models[2].name}&page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = [item["uid"] for item in res_all["items"]]
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(results_paginated_merged) == len(
        [
            dc
            for dc in dataset_classes
            if dc.data_model.data_model_name == data_models[2].name
        ]
    )


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 1, True, '{"label": false}', 10),
        pytest.param(10, 2, True, '{"label": true}', 10),
    ],
)
def test_get_dataset_classes(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/standards/dataset-classes"
    query_params = [f"data_model_name={data_models[2].name}"]
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
    assert res["total"] == (
        len(
            [
                dc
                for dc in dataset_classes
                if dc.data_model.data_model_name == data_models[2].name
            ]
        )
        if total_count
        else 0
    )
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(DATASET_CLASS_FIELDS_ALL)
        for key in DATASET_CLASS_FIELDS_NOT_NULL:
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
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "label", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "label", "name-BBB"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/standards/dataset-classes?data_model_name={data_models[2].name}&filters={filter_by}"
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
        pytest.param('{"label": {"v": ["name-AAA"]}}', "label", "name-AAA"),
        pytest.param('{"label": {"v": ["name-BBB"]}}', "label", "name-BBB"),
        pytest.param('{"label": {"v": ["cc"]}}', None, None),
        pytest.param('{"description": {"v": ["def-XXX"]}}', "description", "def-XXX"),
        pytest.param('{"description": {"v": ["def-YYY"]}}', "description", "def-YYY"),
        pytest.param('{"description": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"catalogue_name": {"v": ["DataModelCatalogue name"]}}',
            "catalogue_name",
            "DataModelCatalogue name",
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/standards/dataset-classes?data_model_name={data_models[1].name}&filters={filter_by}"
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


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("label"),
        pytest.param("description"),
        pytest.param("catalogue_name"),
    ],
)
def test_headers(api_client, field_name):
    url = f"/standards/dataset-classes/headers?data_model_name={data_models[2].name}&field_name={field_name}&page_size=100"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    expected_result = []

    nested_path = None
    if isinstance(field_name, str) and "." in field_name:
        nested_path = field_name.split(".")
        expected_matched_field = nested_path[-1]
        nested_path = nested_path[:-1]

    for dataset_class in [
        dc
        for dc in dataset_classes
        if dc.data_model.data_model_name == data_models[2].name
    ]:
        if nested_path:
            for prop in nested_path:
                dataset_class = getattr(dataset_class, prop)
            if isinstance(dataset_class, list):
                for item in dataset_class:
                    value = getattr(item, expected_matched_field)
                    expected_result.append(value)
            else:
                value = getattr(dataset_class, expected_matched_field)
                expected_result.append(value)

        else:
            value = getattr(dataset_class, field_name)
            expected_result.append(value)
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res)
    if expected_result:
        assert len(res) > 0
        assert len(set(expected_result)) == len(res)
        assert all(item in res for item in expected_result)
    else:
        assert len(res) == 0


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
def test_get_dataset_classes_csv_xml_excel(api_client, export_format):
    url = "/standards/dataset-classes?data_model_name={data_models[2].name}&"
    TestUtils.verify_exported_data_format(api_client, export_format, url)
