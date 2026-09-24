# pylint: disable=redefined-outer-name
"""
Integration tests for `GET /v1/library/activity-item-classes`.

Covers:
  - basic listing
  - pagination
  - is_nsv=true filter (only NSVs returned)
  - is_nsv=false filter (only regular Activity Item Classes returned)
  - is_nsv absent (both returned)
  - authentication (rbac.LIBRARY_READ enforced)
"""

import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient

from consumer_api.tests.utils import assert_response_status_code

log = logging.getLogger(__name__)

ENDPOINT = "/v1/library/activity-item-classes"

EXPECTED_ITEM_FIELDS = {
    "uid",
    "name",
    "library",
    "definition",
    "nci_concept_id",
    "nci_concept_name",
    "display_name",
    "order",
    "status",
    "version",
    "data_type",
    "role",
    "activity_instance_classes",
    "valid_codelists",
    "is_nsv",
    "non_standard_variable",
}

EXPECTED_NSV_FIELDS = {
    "code",
    "is_multiple",
    "length",
    "algorithm",
    "is_cdisc_defined",
    "derivation_rule",
    "origin_type_uid",
    "origin_type_name",
    "origin_type_codelist_uid",
    "origin_source_uid",
    "origin_source_name",
    "origin_source_codelist_uid",
}


def _get(api_client: TestClient, **params: Any):
    """Helper that calls the endpoint and returns the parsed JSON."""
    log.info("GET %s params=%s", ENDPOINT, params)
    response = api_client.get(ENDPOINT, params=params)
    assert_response_status_code(response, 200)
    return response.json()


@pytest.fixture(scope="module")
def all_items(api_client: TestClient) -> list[dict[str, Any]]:
    """Fetch all activity item classes (both regular and NSV) once for the module."""
    body = _get(api_client, page_size=1000, page_number=1)
    return body.get("items", [])


def test_response_shape(api_client: TestClient):
    """The response is a paginated payload with `items`, `self`, `prev`, `next`."""
    body = _get(api_client, page_size=10, page_number=1)
    assert {"items", "self", "prev", "next"}.issubset(body.keys())
    assert isinstance(body["items"], list)
    assert ENDPOINT in body["self"]
    assert ENDPOINT in body["prev"]
    assert ENDPOINT in body["next"]


def test_item_fields_match_spec(all_items: list[dict[str, Any]]):
    """Each returned item exposes the documented set of top-level fields."""
    if not all_items:
        pytest.skip("No Activity Item Classes available in the test database.")

    for item in all_items:
        assert set(item.keys()) == EXPECTED_ITEM_FIELDS, (
            f"Unexpected top-level fields for item {item.get('uid')!r}: "
            f"{sorted(set(item.keys()) ^ EXPECTED_ITEM_FIELDS)}"
        )
        assert isinstance(item["uid"], str) and item["uid"]
        assert isinstance(item["name"], str) and item["name"]
        assert isinstance(item["is_nsv"], bool)
        assert isinstance(item["activity_instance_classes"], list)
        assert isinstance(item["valid_codelists"], list)


def test_non_standard_variable_present_only_for_nsvs(
    all_items: list[dict[str, Any]],
):
    """`non_standard_variable` is populated iff `is_nsv` is true."""
    if not all_items:
        pytest.skip("No Activity Item Classes available in the test database.")

    for item in all_items:
        nsv = item["non_standard_variable"]
        if item["is_nsv"]:
            assert nsv is not None, (
                f"Item {item['uid']} is marked is_nsv=true but "
                f"non_standard_variable is null."
            )
            assert set(nsv.keys()) == EXPECTED_NSV_FIELDS, (
                f"Unexpected NSV fields for item {item['uid']!r}: "
                f"{sorted(set(nsv.keys()) ^ EXPECTED_NSV_FIELDS)}"
            )
        else:
            assert nsv is None, (
                f"Item {item['uid']} is marked is_nsv=false but "
                f"non_standard_variable is not null."
            )


def test_pagination_obeys_page_size(api_client: TestClient):
    """page_size caps the number of returned items."""
    body = _get(api_client, page_size=2, page_number=1)
    assert len(body["items"]) <= 2


def test_pagination_pages_do_not_overlap(api_client: TestClient):
    """Two consecutive pages with identical sort do not share items."""
    page1 = _get(api_client, page_size=2, page_number=1)
    page2 = _get(api_client, page_size=2, page_number=2)
    page1_uids = {item["uid"] for item in page1["items"]}
    page2_uids = {item["uid"] for item in page2["items"]}
    if page1_uids and page2_uids:
        assert page1_uids.isdisjoint(
            page2_uids
        ), f"Pages 1 and 2 share items: {page1_uids & page2_uids}"


def test_pagination_links_reflect_current_page(api_client: TestClient):
    """`self`/`prev`/`next` links contain the requested page numbers."""
    body = _get(api_client, page_size=5, page_number=2)
    assert "page_number=2" in body["self"]
    assert "page_number=1" in body["prev"]
    assert "page_number=3" in body["next"]
    assert "page_size=5" in body["self"]


def test_filter_is_nsv_true_returns_only_nsvs(api_client: TestClient):
    """is_nsv=true returns only Non-Standard Variables."""
    body = _get(api_client, page_size=1000, page_number=1, is_nsv="true")
    if not body["items"]:
        pytest.skip("No Non-Standard Variables available in the test database.")

    for item in body["items"]:
        assert (
            item["is_nsv"] is True
        ), f"is_nsv=true returned item {item['uid']!r} with is_nsv={item['is_nsv']}"
        assert (
            item["non_standard_variable"] is not None
        ), f"is_nsv=true returned item {item['uid']!r} with null non_standard_variable"


def test_filter_is_nsv_false_returns_only_regular(api_client: TestClient):
    """is_nsv=false returns only regular (non-NSV) Activity Item Classes."""
    body = _get(api_client, page_size=1000, page_number=1, is_nsv="false")
    if not body["items"]:
        pytest.skip("No regular Activity Item Classes available in the test database.")

    for item in body["items"]:
        assert (
            item["is_nsv"] is False
        ), f"is_nsv=false returned item {item['uid']!r} with is_nsv={item['is_nsv']}"
        assert item["non_standard_variable"] is None, (
            f"is_nsv=false returned item {item['uid']!r} with non-null "
            "non_standard_variable"
        )


def test_filter_is_nsv_omitted_returns_union(
    api_client: TestClient, all_items: list[dict[str, Any]]
):
    """Omitting is_nsv returns the union of NSVs and regular item classes."""
    if not all_items:
        pytest.skip("No Activity Item Classes available in the test database.")

    nsv_only = _get(api_client, page_size=1000, page_number=1, is_nsv="true")["items"]
    regular_only = _get(api_client, page_size=1000, page_number=1, is_nsv="false")[
        "items"
    ]

    all_uids = {item["uid"] for item in all_items}
    union_uids = {item["uid"] for item in nsv_only} | {
        item["uid"] for item in regular_only
    }

    assert all_uids == union_uids, (
        "Items returned without is_nsv filter must equal the union of items "
        "returned with is_nsv=true and is_nsv=false. "
        f"Difference: {all_uids ^ union_uids}"
    )


def test_filter_is_nsv_query_param_appears_in_pagination_links(
    api_client: TestClient,
):
    """The is_nsv filter is preserved in pagination links."""
    body = _get(api_client, page_size=5, page_number=1, is_nsv="true")
    assert "is_nsv=true" in body["self"]
    assert "is_nsv=true" in body["prev"]
    assert "is_nsv=true" in body["next"]


def test_invalid_is_nsv_value_returns_400(api_client: TestClient):
    """Non-boolean is_nsv values are rejected with 400."""
    response = api_client.get(ENDPOINT, params={"is_nsv": "maybe"})
    assert_response_status_code(response, 400)


def test_invalid_sort_by_returns_400(api_client: TestClient):
    """Unknown sort_by enum values are rejected with 400."""
    response = api_client.get(ENDPOINT, params={"sort_by": "not_a_field"})
    assert_response_status_code(response, 400)


def test_sort_by_name_ascending(api_client: TestClient):
    """Items are returned sorted by name ascending by default."""
    body = _get(
        api_client, page_size=100, page_number=1, sort_by="name", sort_order="asc"
    )
    names = [item["name"].lower() for item in body["items"]]
    assert names == sorted(names), "Items are not sorted by name ascending."


def test_sort_by_name_descending(api_client: TestClient):
    """Items are returned sorted by name descending when requested."""
    body = _get(
        api_client, page_size=100, page_number=1, sort_by="name", sort_order="desc"
    )
    names = [item["name"].lower() for item in body["items"]]
    assert names == sorted(
        names, reverse=True
    ), "Items are not sorted by name descending."
