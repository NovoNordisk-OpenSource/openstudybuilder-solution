"""
Table-driven regression tests for simple `filters` / `sort_by` on:

  GET /ct/codelists/{uid}/terms   (format_codelist_term_filter_sort_keys)
  GET /ct/codelists               (format_codelist_filter_sort_keys)

These two mappers diverge: the terms listing aliases columns 1:1 with the
response model and has no `value_node` Cypher variable, while the aggregated
codelist listing projects `value_node_name` / `value_node_attributes` /
`rel_data_name`. This module pins every simple key of both public contracts
to a 200, so a future rewire of one listing onto the other mapper fails loudly
instead of 400/500ing in production.

Nested Trial Summary parameter fields and paired-codelist fields are covered
in test_ct_term_ts_properties.py and test_paired_codelists.py respectively —
not duplicated here.
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import json
import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

CATALOGUE_NAME = "SDTM CT"
LIBRARY_NAME = "Sponsor"

CODELIST: object
TERM_1: object
TERM_2: object


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """
    One approved Sponsor codelist and two approved terms on it, with unique
    (MCP-prefixed) values for every simple filter/sort key under test, plus a
    third Draft term so name_status/attributes_status filtering is selective.
    """
    db_name = "ct-listing-simple-filters.api"
    inject_and_clear_db(db_name)
    inject_base_data(inject_unit_subset=False)

    global CODELIST, TERM_1, TERM_2

    CODELIST = TestUtils.create_ct_codelist(
        catalogue_name=CATALOGUE_NAME,
        name="MCP simple filter codelist",
        submission_value="MCPSIMPLECL",
        nci_preferred_name="MCP Simple CL NCI Preferred",
        sponsor_preferred_name="MCP Simple CL Sponsor Preferred",
        definition="MCP simple filter codelist definition",
        library_name=LIBRARY_NAME,
        extensible=True,
        approve=True,
    )

    TERM_1 = TestUtils.create_ct_term(
        catalogue_name=CATALOGUE_NAME,
        codelist_uid=CODELIST.codelist_uid,
        submission_value="MCPTERM1",
        nci_preferred_name="MCP Term1 NCI Preferred",
        definition="MCP term1 definition",
        sponsor_preferred_name="MCP Term1 Sponsor Preferred",
        sponsor_preferred_name_sentence_case="mcp term1 sponsor preferred",
        concept_id="MCPTERM1CID",
        order=3,
        library_name=LIBRARY_NAME,
        approve=True,
    )
    TERM_2 = TestUtils.create_ct_term(
        catalogue_name=CATALOGUE_NAME,
        codelist_uid=CODELIST.codelist_uid,
        submission_value="MCPTERM2",
        nci_preferred_name="MCP Term2 NCI Preferred",
        definition="MCP term2 definition",
        sponsor_preferred_name="MCP Term2 Sponsor Preferred",
        sponsor_preferred_name_sentence_case="mcp term2 sponsor preferred",
        concept_id="MCPTERM2CID",
        order=17,
        library_name=LIBRARY_NAME,
        approve=True,
    )
    # Draft term (name/attributes not approved), so name_status/attributes_status
    # "Draft" is selective against TERM_1/TERM_2's "Final".
    TestUtils.create_ct_term(
        catalogue_name=CATALOGUE_NAME,
        codelist_uid=CODELIST.codelist_uid,
        submission_value="MCPTERM3DRAFT",
        nci_preferred_name="MCP Term3 NCI Preferred",
        definition="MCP term3 draft definition",
        sponsor_preferred_name="MCP Term3 Sponsor Preferred",
        sponsor_preferred_name_sentence_case="mcp term3 sponsor preferred",
        concept_id="MCPTERM3CID",
        order=29,
        library_name=LIBRARY_NAME,
        approve=False,
    )

    yield


def _get_nested(item: dict[str, Any], dotted_key: str) -> Any:
    value: Any = item
    for part in dotted_key.split("."):
        value = value[part]
    return value


# ---------- GET /ct/codelists/{uid}/terms — simple filter/sort matrix ----------

TERMS_SIMPLE_FILTER_CASES = [
    ("term_uid", lambda: TERM_1.term_uid),
    ("submission_value", lambda: "MCPTERM1"),
    ("definition", lambda: "MCP term1 definition"),
    ("concept_id", lambda: "MCPTERM1CID"),
    ("nci_preferred_name", lambda: "MCP Term1 NCI Preferred"),
    ("sponsor_preferred_name", lambda: "MCP Term1 Sponsor Preferred"),
    ("library_name", lambda: LIBRARY_NAME),
    ("order", lambda: 3),
    ("name_status", lambda: "Final"),
    ("attributes_status", lambda: "Final"),
]

TERMS_SORT_KEYS = [key for key, _ in TERMS_SIMPLE_FILTER_CASES]


@pytest.mark.parametrize("key,value_fn", TERMS_SIMPLE_FILTER_CASES)
def test_get_codelist_terms_simple_eq_filter(api_client, key, value_fn):
    """Every simple filter key on GET /ct/codelists/{uid}/terms must 200 and
    return only items matching the filtered value."""
    value = value_fn()
    filters = json.dumps({key: {"v": [value], "op": "eq"}})

    response = api_client.get(
        f"/ct/codelists/{CODELIST.codelist_uid}/terms",
        params={"page_size": 100, "filters": filters},
    )

    assert_response_status_code(response, 200)
    body = response.json()
    assert "unsupported filters" not in json.dumps(body).lower()
    items = body["items"]
    assert len(items) >= 1, f"Expected at least one item for {key}={value!r}"
    for item in items:
        assert _get_nested(item, key) == value, (key, item)


@pytest.mark.parametrize("key", TERMS_SORT_KEYS)
@pytest.mark.parametrize("ascending", [True, False])
def test_get_codelist_terms_simple_sort(api_client, key, ascending):
    """Every simple sort key on GET /ct/codelists/{uid}/terms must 200 in both
    directions and return a plain item list."""
    response = api_client.get(
        f"/ct/codelists/{CODELIST.codelist_uid}/terms",
        params={"page_size": 100, "sort_by": json.dumps({key: ascending})},
    )

    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert isinstance(items, list)
    assert len(items) >= 2


def test_get_codelist_terms_sort_by_order_respects_direction(api_client):
    response_asc = api_client.get(
        f"/ct/codelists/{CODELIST.codelist_uid}/terms",
        params={"page_size": 100, "sort_by": json.dumps({"order": True})},
    )
    assert_response_status_code(response_asc, 200)
    orders_asc = [item["order"] for item in response_asc.json()["items"]]

    response_desc = api_client.get(
        f"/ct/codelists/{CODELIST.codelist_uid}/terms",
        params={"page_size": 100, "sort_by": json.dumps({"order": False})},
    )
    assert_response_status_code(response_desc, 200)
    orders_desc = [item["order"] for item in response_desc.json()["items"]]

    assert orders_asc == sorted(orders_asc)
    assert orders_desc == sorted(orders_desc, reverse=True)


def test_get_codelist_terms_invalid_filter_key_returns_400(api_client):
    filters = json.dumps({"not a valid key!": {"v": ["x"], "op": "eq"}})

    response = api_client.get(
        f"/ct/codelists/{CODELIST.codelist_uid}/terms",
        params={"page_size": 100, "filters": filters},
    )

    assert_response_status_code(response, 400)


# ---------- GET /ct/codelists — nested simple filter/sort matrix ----------

CODELISTS_SIMPLE_FILTER_CASES = [
    ("name.name", lambda: "MCP Simple CL Sponsor Preferred"),
    ("attributes.submission_value", lambda: "MCPSIMPLECL"),
    ("attributes.definition", lambda: "MCP simple filter codelist definition"),
    ("attributes.nci_preferred_name", lambda: "MCP Simple CL NCI Preferred"),
    ("name.status", lambda: "Final"),
]

CODELISTS_SORT_KEYS = [key for key, _ in CODELISTS_SIMPLE_FILTER_CASES]


@pytest.mark.parametrize("key,value_fn", CODELISTS_SIMPLE_FILTER_CASES)
def test_get_codelists_nested_simple_eq_filter(api_client, key, value_fn):
    """Every nested simple filter key on GET /ct/codelists must 200 and return
    only items matching the filtered value."""
    value = value_fn()
    filters = json.dumps({key: {"v": [value], "op": "eq"}})

    response = api_client.get(
        "/ct/codelists",
        params={"page_size": 100, "filters": filters},
    )

    assert_response_status_code(response, 200)
    body = response.json()
    assert "unsupported filters" not in json.dumps(body).lower()
    items = body["items"]
    assert len(items) >= 1, f"Expected at least one item for {key}={value!r}"
    for item in items:
        assert _get_nested(item, key) == value, (key, item)


@pytest.mark.parametrize("key", CODELISTS_SORT_KEYS)
@pytest.mark.parametrize("ascending", [True, False])
def test_get_codelists_nested_simple_sort(api_client, key, ascending):
    """Every nested simple sort key on GET /ct/codelists must 200 in both
    directions and return a plain item list."""
    response = api_client.get(
        "/ct/codelists",
        params={"page_size": 100, "sort_by": json.dumps({key: ascending})},
    )

    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert isinstance(items, list)
