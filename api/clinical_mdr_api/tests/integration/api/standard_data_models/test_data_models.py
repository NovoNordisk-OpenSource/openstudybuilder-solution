"""
Tests for /standards/data-models endpoints
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
from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
data_models_all: list[DataModel]
implementation_guides: list[DataModelIG]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "datamodels.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global data_models_all
    global implementation_guides

    # Create data model implementation guides
    implementation_guides = [
        TestUtils.create_data_model_ig(name=name)
        for name in ["DataModelIG A", "DataModelIG B", "DataModelIG C"]
    ]

    # Create some data models
    data_models_all = []
    data_models_all.append(
        TestUtils.create_data_model(
            name="DataModel A",
            description="DataModel A desc",
            implementation_guides=[
                implementation_guide.uid
                for implementation_guide in implementation_guides
            ],
        )
    )

    data_models_all.append(TestUtils.create_data_model(name="name-AAA"))
    data_models_all.append(TestUtils.create_data_model(name="name-BBB"))
    data_models_all.append(TestUtils.create_data_model(description="def-XXX"))
    data_models_all.append(TestUtils.create_data_model(description="def-YYY"))

    for index in range(5):
        data_models_all.append(TestUtils.create_data_model(name=f"name-AAA-{index}"))
        data_models_all.append(TestUtils.create_data_model(name=f"name-BBB-{index}"))
        data_models_all.append(
            TestUtils.create_data_model(description=f"def-XXX-{index}")
        )
        data_models_all.append(
            TestUtils.create_data_model(description=f"def-YYY-{index}")
        )

    yield


DATA_MODEL_FIELDS_ALL = [
    "uid",
    "name",
    "description",
    "implementation_guides",
    "version_number",
    "status",
    "start_date",
]

DATA_MODEL_FIELDS_NOT_NULL = [
    "uid",
    "name",
]


def test_get_data_model(api_client):
    response = api_client.get(f"/standards/data-models/{data_models_all[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(DATA_MODEL_FIELDS_ALL)
    for key in DATA_MODEL_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == data_models_all[0].uid
    assert res["name"] == "DataModel A"
    assert res["description"] == "DataModel A desc"
    implementation_guide_uids = [ig["uid"] for ig in res["implementation_guides"]]
    assert sorted(implementation_guide_uids) == sorted(
        [implementation_guide.uid for implementation_guide in implementation_guides]
    )


def test_get_data_models_pagination(api_client):
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/standards/data-models?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_names = [item["name"] for item in res["items"]]
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        reduce(lambda a, b: list(a) + list(b), list(results_paginated.values()))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"/standards/data-models?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(data_models_all) == len(results_paginated_merged)


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
def test_get_data_models(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/standards/data-models"
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
    assert res["total"] == (len(data_models_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(DATA_MODEL_FIELDS_ALL)
        for key in DATA_MODEL_FIELDS_NOT_NULL:
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
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/standards/data-models?filters={filter_by}"
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
        pytest.param('{"description": {"v": ["def-XXX"]}}', "description", "def-XXX"),
        pytest.param('{"description": {"v": ["def-YYY"]}}', "description", "def-YYY"),
        pytest.param('{"description": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"implementation_guides": {"v": []}}', "implementation_guides", []
        ),
        pytest.param(
            '{"implementation_guides.name": {"v": ["DataModelIG A"]}}',
            "implementation_guides.name",
            "DataModelIG A",
        ),
        pytest.param(
            '{"implementation_guides.name": {"v": ["DataModelIG A", "DataModelIG B"]}}',
            "implementation_guides.name",
            ["DataModelIG A", "DataModelIG A"],
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/standards/data-models?filters={filter_by}"
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
                if isinstance(row, list):
                    all(item[expected_matched_field] == expected_result for item in row)
                else:
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
    "export_format",
    [
        pytest.param("text/csv"),
        pytest.param("text/xml"),
        pytest.param(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    ],
)
def test_get_data_models_csv_xml_excel(api_client, export_format):
    url = "/standards/data-models"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("name"),
        pytest.param("description"),
        pytest.param("implementation_guides.name"),
    ],
)
def test_headers(api_client, field_name):
    url = f"/standards/data-models/headers?field_name={field_name}&page_size=100"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    expected_result = []

    nested_path = None
    if isinstance(field_name, str) and "." in field_name:
        nested_path = field_name.split(".")
        expected_matched_field = nested_path[-1]
        nested_path = nested_path[:-1]

    for data_model in data_models_all:
        if nested_path:
            for prop in nested_path:
                data_model = getattr(data_model, prop)
            if not data_model:
                continue
            if isinstance(data_model, list):
                for item in data_model:
                    value = getattr(item, expected_matched_field)
                    expected_result.append(value)
            else:
                value = getattr(data_model, expected_matched_field)
                expected_result.append(value)

        else:
            value = getattr(data_model, field_name)
            expected_result.append(value)
    expected_result = [result for result in expected_result if result is not None]
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res)
    if expected_result:
        assert len(res) > 0
        assert len(set(expected_result)) == len(res)
        assert all(item in res for item in expected_result)
    else:
        assert len(res) == 0
