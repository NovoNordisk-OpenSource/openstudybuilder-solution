"""
Tests for /data-suppliers endpoints
"""

import json
import logging
from functools import reduce
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.data_suppliers.data_supplier import DataSupplier
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
data_suppliers_all: list[DataSupplier]
supplier_type: CTTerm
supplier_type_codelist: CTCodelist
origin_source: CTTerm
origin_source_codelist: CTCodelist
origin_type: CTTerm
origin_type_codelist: CTCodelist


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db("data-supplier.api")
    inject_base_data()

    global data_suppliers_all
    global supplier_type
    global origin_source
    global origin_type
    global supplier_type_codelist
    global origin_source_codelist
    global origin_type_codelist

    supplier_type_codelist = TestUtils.create_ct_codelist(
        name="Data Supplier Type",
        sponsor_preferred_name="Data Supplier Type",
        extensible=True,
        approve=True,
        submission_value="DATA_SUPPLIER_TYPE",
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    supplier_type = TestUtils.create_ct_term(
        codelist_uid=supplier_type_codelist.codelist_uid,
        sponsor_preferred_name_sentence_case="type",
        sponsor_preferred_name="Type",
    )

    origin_source_codelist = TestUtils.create_ct_codelist(
        name="Origin Source",
        sponsor_preferred_name="Origin Source",
        extensible=True,
        approve=True,
        submission_value="ORIGINS",
        catalogue_name=settings.sdtm_ct_catalogue_name,
        codelist_uid="C170450",
    )
    origin_source = TestUtils.create_ct_term(
        codelist_uid=origin_source_codelist.codelist_uid,
        sponsor_preferred_name="Origin Source",
    )
    origin_type_codelist = TestUtils.create_ct_codelist(
        name="Origin Type",
        sponsor_preferred_name="Origin Type",
        extensible=True,
        approve=True,
        submission_value="ORIGINT",
        catalogue_name=settings.sdtm_ct_catalogue_name,
        codelist_uid="C170449",
    )
    origin_type = TestUtils.create_ct_term(
        codelist_uid=origin_type_codelist.codelist_uid,
        sponsor_preferred_name="Origin Type",
    )

    # Create some data suppliers
    data_suppliers_all = [
        TestUtils.create_data_supplier(
            name="name A",
            order=1,
            description="Description A",
            api_base_url="api_base_url",
            ui_base_url="ui_base_url",
            supplier_type_uid=supplier_type.term_uid,
            origin_source_uid=origin_source.term_uid,
            origin_type_uid=origin_type.term_uid,
        ),
        TestUtils.create_data_supplier(
            name="name-AAA",
            order=2,
            description="Description AAA",
            api_base_url="api_base_url",
            ui_base_url="ui_base_url",
            supplier_type_uid=supplier_type.term_uid,
            origin_source_uid=origin_source.term_uid,
            origin_type_uid=origin_type.term_uid,
        ),
        TestUtils.create_data_supplier(
            name="name-BBB",
            order=3,
            description="Description BBB",
            api_base_url="api_base_url",
            ui_base_url="ui_base_url",
            supplier_type_uid=supplier_type.term_uid,
            origin_source_uid=origin_source.term_uid,
            origin_type_uid=origin_type.term_uid,
        ),
        TestUtils.create_data_supplier(
            name="name XXX",
            order=4,
            description="Description XXX",
            api_base_url="api_base_url",
            ui_base_url="ui_base_url",
            supplier_type_uid=supplier_type.term_uid,
            origin_source_uid=origin_source.term_uid,
            origin_type_uid=origin_type.term_uid,
        ),
        TestUtils.create_data_supplier(
            name="name YYY",
            order=5,
            description="Description YYY",
            api_base_url="api_base_url",
            ui_base_url="ui_base_url",
            supplier_type_uid=supplier_type.term_uid,
            origin_source_uid=origin_source.term_uid,
            origin_type_uid=origin_type.term_uid,
        ),
    ]

    for index in range(5):
        data_suppliers_all.append(
            TestUtils.create_data_supplier(
                name=f"name-AAA-{index}",
                order=(index * 4) + 1,
                description=f"Description AAA {index}",
                api_base_url="api_base_url",
                ui_base_url="ui_base_url",
                supplier_type_uid=supplier_type.term_uid,
                origin_source_uid=origin_source.term_uid,
                origin_type_uid=origin_type.term_uid,
            )
        )
        data_suppliers_all.append(
            TestUtils.create_data_supplier(
                name=f"name-BBB-{index}",
                order=(index * 4) + 1,
                description=f"Description BBB {index}",
                api_base_url="api_base_url",
                ui_base_url="ui_base_url",
                supplier_type_uid=supplier_type.term_uid,
                origin_source_uid=origin_source.term_uid,
                origin_type_uid=origin_type.term_uid,
            )
        )
        data_suppliers_all.append(
            TestUtils.create_data_supplier(
                name=f"name-XXX-{index}",
                order=(index * 4) + 1,
                description=f"Description XXX {index}",
                api_base_url="api_base_url",
                ui_base_url="ui_base_url",
                supplier_type_uid=supplier_type.term_uid,
                origin_source_uid=origin_source.term_uid,
                origin_type_uid=origin_type.term_uid,
            )
        )
        data_suppliers_all.append(
            TestUtils.create_data_supplier(
                name=f"name-YYY-{index}",
                order=(index * 4) + 1,
                description=f"Description YYY {index}",
                api_base_url="api_base_url",
                ui_base_url="ui_base_url",
                supplier_type_uid=supplier_type.term_uid,
                origin_source_uid=origin_source.term_uid,
                origin_type_uid=origin_type.term_uid,
            )
        )


DATA_SUPPLIER_FIELDS_ALL = [
    "uid",
    "name",
    "description",
    "order",
    "supplier_type",
    "origin_source",
    "origin_type",
    "api_base_url",
    "ui_base_url",
    "library_name",
    "possible_actions",
    "version",
    "status",
    "start_date",
    "end_date",
    "change_description",
    "author_username",
]

DATA_SUPPLIER_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "order",
    "start_date",
]


def test_get_data_supplier(api_client):
    response = api_client.get(f"/data-suppliers/{data_suppliers_all[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(DATA_SUPPLIER_FIELDS_ALL)
    for key in DATA_SUPPLIER_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == data_suppliers_all[0].uid
    assert res["name"] == "name A"
    assert res["order"] > 0
    assert res["description"] == "Description A"
    assert res["api_base_url"] == "api_base_url"
    assert res["ui_base_url"] == "ui_base_url"
    assert res["supplier_type"]["uid"] == supplier_type.term_uid
    assert res["origin_source"]["uid"] == origin_source.term_uid
    assert res["origin_type"]["uid"] == origin_type.term_uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["edit", "inactivate"]


def test_get_data_supplier_pagination(api_client):
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = (
            f"/data-suppliers?page_number={page_number}&page_size=10&sort_by={sort_by}"
        )
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
        f"/data-suppliers?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = [x["name"] for x in res_all["items"]]
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(data_suppliers_all) == len(results_paginated_merged)


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
def test_get_data_suppliers(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/data-suppliers"
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
    assert res["total"] == (len(data_suppliers_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(item.keys()) == set(DATA_SUPPLIER_FIELDS_ALL)
        for key in DATA_SUPPLIER_FIELDS_NOT_NULL:
            assert item[key] is not None

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = list(sort_by_dict.keys())[0]
        sort_order_ascending: bool = list(sort_by_dict.values())[0]

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = [x[sort_field] for x in res["items"]]
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)


def test_get_data_supplier_versions(api_client):
    response = api_client.get("data-suppliers/DataSupplier_000001/versions")
    res = response.json()

    assert_response_status_code(response, 200)

    assert len(res) == 2
    assert res[0]["uid"] == "DataSupplier_000001"
    assert res[0]["status"] == "Final"
    assert res[0]["version"] == "1.0"

    assert res[1]["uid"] == "DataSupplier_000001"
    assert res[1]["status"] == "Draft"
    assert res[1]["version"] == "0.1"


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("uid"),
        pytest.param("name"),
        pytest.param("description"),
        pytest.param("order"),
    ],
)
def test_headers(api_client, field_name):
    response = api_client.get(
        f"/data-suppliers/headers?field_name={field_name}&page_size=100"
    )
    res = response.json()

    assert_response_status_code(response, 200)
    expected_result = []
    for data_supplier in data_suppliers_all:
        value = getattr(data_supplier, field_name)
        if value:
            expected_result.append(value)
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res)
    if expected_result:
        assert len(res) > 0
        if field_name == "order":
            # Order values are bumped to be unique in the database
            assert len(res) == len(data_suppliers_all)
        else:
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
def test_get_data_suppliers_csv_xml_excel(api_client, export_format):
    url = "data-suppliers"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


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
    url = f"/data-suppliers?filters={filter_by}"
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
            '{"supplier_type.name": {"v": ["Type"]}}',
            "supplier_type.name",
            "Type",
        ),
        pytest.param(
            '{"origin_type.name": {"v": ["Origin Type"]}}',
            "origin_type.name",
            "Origin Type",
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/data-suppliers?filters={filter_by}"
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


def test_edit_data_supplier(api_client):
    data_supplier = TestUtils.create_data_supplier(
        name="New data supplier",
        order=30,
        supplier_type_uid=supplier_type.term_uid,
        origin_source_uid=origin_source.term_uid,
    )

    _supplier_type = TestUtils.create_ct_term(
        codelist_uid=supplier_type_codelist.codelist_uid, sponsor_preferred_name="_Type"
    )
    _supplier_origin_source = TestUtils.create_ct_term(
        codelist_uid=origin_source_codelist.codelist_uid,
        sponsor_preferred_name="_Origin Source",
    )
    _supplier_origin_type = TestUtils.create_ct_term(
        codelist_uid=origin_type_codelist.codelist_uid,
        sponsor_preferred_name="_Origin Type",
    )
    response = api_client.patch(
        f"/data-suppliers/{data_supplier.uid}",
        json={
            "name": "new name for data supplier",
            "order": 45,
            "description": "new description for data supplier",
            "supplier_type_uid": _supplier_type.term_uid,
            "origin_source_uid": _supplier_origin_source.term_uid,
            "origin_type_uid": _supplier_origin_type.term_uid,
            "api_base_url": None,
            "ui_base_url": None,
            "change_description": "Updated via API",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == "new name for data supplier"
    assert res["order"] == 45
    assert res["description"] == "new description for data supplier"
    assert res["supplier_type"]["uid"] == _supplier_type.term_uid
    assert res["origin_source"]["uid"] == _supplier_origin_source.term_uid
    assert res["origin_type"]["uid"] == _supplier_origin_type.term_uid
    assert res["version"] == "2.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["edit", "inactivate"]
    assert res["library_name"] == "Sponsor"


def test_post_data_supplier(api_client):
    response = api_client.post(
        "/data-suppliers",
        json={
            "name": "New Data Supplier Name",
            "order": 36,
            "description": "New Data Supplier Desc",
            "supplier_type_uid": supplier_type.term_uid,
            "origin_source_uid": origin_source.term_uid,
            "origin_type_uid": origin_type.term_uid,
            "library_name": "Sponsor",
            "api_base_url": None,
            "ui_base_url": None,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["name"] == "New Data Supplier Name"
    assert res["order"] == 36
    assert res["description"] == "New Data Supplier Desc"
    assert res["supplier_type"]["uid"] == supplier_type.term_uid
    assert res["origin_source"]["uid"] == origin_source.term_uid
    assert res["origin_type"]["uid"] == origin_type.term_uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["edit", "inactivate"]
    assert res["library_name"] == "Sponsor"


def test_data_supplier_versioning(api_client):
    data_supplier = TestUtils.create_data_supplier(
        name="New data supplier",
        order=2,
        supplier_type_uid=supplier_type.term_uid,
        origin_source_uid=origin_source.term_uid,
        origin_type_uid=origin_type.term_uid,
    )

    # not successful reactivate
    response = api_client.post(f"/data-suppliers/{data_supplier.uid}/activations")
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "Only RETIRED version can be reactivated."

    # successful inactivate
    response = api_client.delete(f"/data-suppliers/{data_supplier.uid}/activations")
    assert_response_status_code(response, 200)

    # successful reactivate
    response = api_client.post(f"/data-suppliers/{data_supplier.uid}/activations")
    assert_response_status_code(response, 200)


# =============================================================================
# Ordering Tests
# =============================================================================


def _create_supplier_with_order(
    api_client, name: str, order: int | None, type_uid: str
):
    """Helper to create a supplier with a specific order."""
    # Make name unique by appending part of type_uid (unique per test)
    unique_name = f"{name}_{type_uid[-8:]}"
    payload = {
        "name": unique_name,
        "description": f"Description for {name}",
        "supplier_type_uid": type_uid,
        "origin_source_uid": origin_source.term_uid,
        "origin_type_uid": origin_type.term_uid,
        "api_base_url": None,
        "ui_base_url": None,
        "library_name": "Sponsor",
    }
    if order is not None:
        payload["order"] = order
    return api_client.post("/data-suppliers", json=payload)


def _get_supplier_order(api_client, uid: str) -> int:
    """Get the current order of a supplier by UID."""
    response = api_client.get(f"/data-suppliers/{uid}")
    return response.json()["order"]


@pytest.fixture(scope="function")
def ordering_test_type():
    """Create a fresh supplier type term for each ordering test."""
    # Reuse the existing supplier_type_codelist from module setup
    return TestUtils.create_ct_term(
        codelist_uid=supplier_type_codelist.codelist_uid,
        sponsor_preferred_name=f"OrderTestType_{TestUtils.random_str()}",
    )


class TestDataSupplierOrderingCreate:
    """Tests for data supplier ordering on create."""

    def test_create_with_auto_assigned_order(self, api_client, ordering_test_type):
        """Create without order - should auto-assign next available."""
        # Create first supplier without order
        response = _create_supplier_with_order(
            api_client, "Auto1", None, ordering_test_type.term_uid
        )
        assert_response_status_code(response, 201)
        assert response.json()["order"] == 1

        # Create second supplier without order
        response = _create_supplier_with_order(
            api_client, "Auto2", None, ordering_test_type.term_uid
        )
        assert_response_status_code(response, 201)
        assert response.json()["order"] == 2

    def test_create_with_order_last_plus_one(self, api_client, ordering_test_type):
        """Create with order = last + 1 - no bumping needed."""
        # Create two suppliers first
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        r2 = _create_supplier_with_order(
            api_client, "Second", 2, ordering_test_type.term_uid
        )

        # Create at last + 1 (order 3)
        response = _create_supplier_with_order(
            api_client, "Third", 3, ordering_test_type.term_uid
        )
        assert_response_status_code(response, 201)
        assert response.json()["order"] == 3

        # Verify no bumping occurred - original orders should be unchanged
        assert _get_supplier_order(api_client, r1.json()["uid"]) == 1
        assert _get_supplier_order(api_client, r2.json()["uid"]) == 2

    def test_create_with_order_last(self, api_client, ordering_test_type):
        """Create with order = same as last - should bump last."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        r2 = _create_supplier_with_order(
            api_client, "Second", 2, ordering_test_type.term_uid
        )

        # Create at same order as last (2)
        response = _create_supplier_with_order(
            api_client, "NewSecond", 2, ordering_test_type.term_uid
        )
        assert_response_status_code(response, 201)
        assert response.json()["order"] == 2

        # Verify bumping: First unchanged, Second bumped to 3
        assert _get_supplier_order(api_client, r1.json()["uid"]) == 1
        assert _get_supplier_order(api_client, r2.json()["uid"]) == 3

    def test_create_with_order_in_between(self, api_client, ordering_test_type):
        """Create with order in between - should bump items >= order."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        r2 = _create_supplier_with_order(
            api_client, "Second", 2, ordering_test_type.term_uid
        )
        r3 = _create_supplier_with_order(
            api_client, "Third", 3, ordering_test_type.term_uid
        )

        # Create at order 2 (in between)
        response = _create_supplier_with_order(
            api_client, "NewMiddle", 2, ordering_test_type.term_uid
        )
        assert_response_status_code(response, 201)
        assert response.json()["order"] == 2

        # Verify: First unchanged, Second->3, Third->4
        assert _get_supplier_order(api_client, r1.json()["uid"]) == 1
        assert _get_supplier_order(api_client, r2.json()["uid"]) == 3
        assert _get_supplier_order(api_client, r3.json()["uid"]) == 4

    def test_create_with_order_first(self, api_client, ordering_test_type):
        """Create with order = 1 (first) - should bump all."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        r2 = _create_supplier_with_order(
            api_client, "Second", 2, ordering_test_type.term_uid
        )
        r3 = _create_supplier_with_order(
            api_client, "Third", 3, ordering_test_type.term_uid
        )

        # Create at order 1 (first position)
        response = _create_supplier_with_order(
            api_client, "NewFirst", 1, ordering_test_type.term_uid
        )
        assert_response_status_code(response, 201)
        assert response.json()["order"] == 1

        # Verify all others bumped
        assert _get_supplier_order(api_client, r1.json()["uid"]) == 2
        assert _get_supplier_order(api_client, r2.json()["uid"]) == 3
        assert _get_supplier_order(api_client, r3.json()["uid"]) == 4

    def test_create_with_order_zero_fails(self, api_client, ordering_test_type):
        """Create with order = 0 should fail validation."""
        response = _create_supplier_with_order(
            api_client, "Invalid", 0, ordering_test_type.term_uid
        )
        assert_response_status_code(response, 400)

    def test_create_with_negative_order_fails(self, api_client, ordering_test_type):
        """Create with negative order should fail validation."""
        response = _create_supplier_with_order(
            api_client, "Invalid", -1, ordering_test_type.term_uid
        )
        assert_response_status_code(response, 400)


class TestDataSupplierOrderingUpdate:
    """Tests for data supplier ordering on update."""

    def _update_order(self, api_client, uid: str, new_order: int):
        """Helper to update a supplier's order."""
        return api_client.patch(
            f"/data-suppliers/{uid}",
            json={"order": new_order, "change_description": "Order update"},
        )

    def test_update_order_to_last_plus_one(self, api_client, ordering_test_type):
        """Update order from first to last + 1."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        r2 = _create_supplier_with_order(
            api_client, "Second", 2, ordering_test_type.term_uid
        )
        r3 = _create_supplier_with_order(
            api_client, "Third", 3, ordering_test_type.term_uid
        )
        first_uid = r1.json()["uid"]

        # Move first to position 4 (last + 1)
        response = self._update_order(api_client, first_uid, 4)
        assert_response_status_code(response, 200)
        assert response.json()["order"] == 4

        # Verify orders shifted: 2->1, 3->2
        assert _get_supplier_order(api_client, r2.json()["uid"]) == 1
        assert _get_supplier_order(api_client, r3.json()["uid"]) == 2

    def test_update_order_to_same_position(self, api_client, ordering_test_type):
        """Update to same order - no change."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        r2 = _create_supplier_with_order(
            api_client, "Second", 2, ordering_test_type.term_uid
        )
        first_uid = r1.json()["uid"]

        # Update to same order
        response = self._update_order(api_client, first_uid, 1)
        assert_response_status_code(response, 200)
        assert response.json()["order"] == 1

        # Second should stay at 2
        assert _get_supplier_order(api_client, r2.json()["uid"]) == 2

    def test_update_order_move_down(self, api_client, ordering_test_type):
        """Update order moving down (1 -> 3)."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        r2 = _create_supplier_with_order(
            api_client, "Second", 2, ordering_test_type.term_uid
        )
        r3 = _create_supplier_with_order(
            api_client, "Third", 3, ordering_test_type.term_uid
        )
        first_uid = r1.json()["uid"]

        # Move first to position 3
        response = self._update_order(api_client, first_uid, 3)
        assert_response_status_code(response, 200)
        assert response.json()["order"] == 3

        # Second->1, Third->2
        assert _get_supplier_order(api_client, r2.json()["uid"]) == 1
        assert _get_supplier_order(api_client, r3.json()["uid"]) == 2

    def test_update_order_move_up(self, api_client, ordering_test_type):
        """Update order moving up (3 -> 1)."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        r2 = _create_supplier_with_order(
            api_client, "Second", 2, ordering_test_type.term_uid
        )
        r3 = _create_supplier_with_order(
            api_client, "Third", 3, ordering_test_type.term_uid
        )
        third_uid = r3.json()["uid"]

        # Move third to position 1
        response = self._update_order(api_client, third_uid, 1)
        assert_response_status_code(response, 200)
        assert response.json()["order"] == 1

        # First->2, Second->3
        assert _get_supplier_order(api_client, r1.json()["uid"]) == 2
        assert _get_supplier_order(api_client, r2.json()["uid"]) == 3

    def test_update_order_in_between(self, api_client, ordering_test_type):
        """Update order from last to middle."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        r2 = _create_supplier_with_order(
            api_client, "Second", 2, ordering_test_type.term_uid
        )
        r3 = _create_supplier_with_order(
            api_client, "Third", 3, ordering_test_type.term_uid
        )
        r4 = _create_supplier_with_order(
            api_client, "Fourth", 4, ordering_test_type.term_uid
        )
        fourth_uid = r4.json()["uid"]

        # Move fourth to position 2
        response = self._update_order(api_client, fourth_uid, 2)
        assert_response_status_code(response, 200)
        assert response.json()["order"] == 2

        # First stays at 1, Second->3, Third->4
        assert _get_supplier_order(api_client, r1.json()["uid"]) == 1
        assert _get_supplier_order(api_client, r2.json()["uid"]) == 3
        assert _get_supplier_order(api_client, r3.json()["uid"]) == 4

    def test_update_order_to_zero_fails(self, api_client, ordering_test_type):
        """Update to order 0 should fail validation."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        first_uid = r1.json()["uid"]

        response = self._update_order(api_client, first_uid, 0)
        assert_response_status_code(response, 400)

    def test_update_order_to_negative_fails(self, api_client, ordering_test_type):
        """Update to negative order should fail validation."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        first_uid = r1.json()["uid"]

        response = self._update_order(api_client, first_uid, -1)
        assert_response_status_code(response, 400)


class TestDataSupplierOrderingDelete:
    """Tests for data supplier ordering on delete (inactivate)."""

    def test_inactivate_does_not_affect_other_orders(
        self, api_client, ordering_test_type
    ):
        """Inactivating a supplier should not change other suppliers' orders."""
        r1 = _create_supplier_with_order(
            api_client, "First", 1, ordering_test_type.term_uid
        )
        r2 = _create_supplier_with_order(
            api_client, "Second", 2, ordering_test_type.term_uid
        )
        r3 = _create_supplier_with_order(
            api_client, "Third", 3, ordering_test_type.term_uid
        )
        second_uid = r2.json()["uid"]

        # Inactivate the middle one
        response = api_client.delete(f"/data-suppliers/{second_uid}/activations")
        assert_response_status_code(response, 200)

        # First and Third should keep their orders
        assert _get_supplier_order(api_client, r1.json()["uid"]) == 1
        assert _get_supplier_order(api_client, r3.json()["uid"]) == 3
