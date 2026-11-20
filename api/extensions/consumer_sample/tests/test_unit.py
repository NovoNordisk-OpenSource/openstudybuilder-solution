"""consumer_sample extension without a database.

The database function is replaced; authentication is overridden with the dummy user without
persisting it, so no Neo4j database is needed.
"""

# pylint: disable=redefined-outer-name
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette_context import context

from common.auth.dependencies import (
    dummy_access_token_claims,
    dummy_auth_object,
    dummy_user_auth,
    validate_token,
)
from extensions.consumer_sample import consumer_sample_main, db, models
from extensions.extensions_api import app

TERM = {
    "codelist_uid": "C1",
    "term_uid": "T1",
    "order": 1,
    "ordinal": None,
    "submission_value": "TERM1",
    "sponsor_preferred_name": "Term 1",
    "concept_id": None,
    "nci_preferred_name": None,
    "library_name": "Sponsor",
    "name_status": "Final",
    "name_version": "1.0",
    "attributes_status": "Final",
    "attributes_version": "1.0",
}


def _dummy_auth_without_db() -> None:
    """Like `dummy_user_auth`, without persisting the user in Neo4j"""
    context["auth"] = dummy_auth_object(dummy_access_token_claims())


@pytest.fixture
def db_calls(monkeypatch):
    """Records the calls to the database function and answers with one term out of 42"""
    calls: list[dict[str, Any]] = []

    def fake_get_ct_terms(**kwargs: Any) -> tuple[list[dict[str, Any]], int]:
        calls.append(kwargs)
        return [TERM], 42

    monkeypatch.setattr(consumer_sample_main.DB, "get_ct_terms", fake_get_ct_terms)
    return calls


@pytest.fixture
def api_client():
    """Extensions API test client with authentication bypassed"""
    overrides: dict[Callable[..., Any], Callable[..., Any]] = {
        dummy_user_auth: _dummy_auth_without_db,
        validate_token: _dummy_auth_without_db,
    }
    app.dependency_overrides.update(overrides)
    yield TestClient(app)
    for key in overrides:
        app.dependency_overrides.pop(key, None)


def test_ct_terms_passes_request_to_database(api_client, db_calls):
    """The submission value, sort and page are passed on; the rows become the page items."""
    response = api_client.get(
        "/consumer-sample/ct-terms",
        params={
            "codelist_submission_value": "TIMELB",
            "sort_by": "submission_value",
            "sort_order": "desc",
            "page_size": 10,
            "page_number": 2,
        },
    )

    assert response.status_code == 200, response.text
    assert db_calls == [
        {
            "codelist_submission_value": "TIMELB",
            "sort_by": models.SortByCTTerms.SUBMISSION_VALUE,
            "sort_order": models.SortOrder.DESC,
            "page_size": 10,
            "page_number": 2,
        }
    ]
    res = response.json()
    assert res["items"] == [TERM]
    assert res["total"] == 42
    assert "sort_by=submission_value&sort_order=desc" in res["self"]
    assert "page_number=2" in res["self"]
    assert "page_number=1" in res["prev"]
    assert "page_number=3" in res["next"]


def test_ct_terms_default_page(api_client, db_calls):
    """Without page parameters the first page of the default size is asked."""
    response = api_client.get(
        "/consumer-sample/ct-terms", params={"codelist_submission_value": "TIMELB"}
    )

    assert response.status_code == 200, response.text
    assert db_calls[0]["page_number"] == 1
    assert db_calls[0]["page_size"] > 0
    assert db_calls[0]["sort_by"] == models.SortByCTTerms.TERM_UID
    assert db_calls[0]["sort_order"] == models.SortOrder.ASC


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"codelist_submission_value": "TIMELB", "page_size": 0},
        {"codelist_submission_value": "TIMELB", "page_number": 0},
        {"codelist_submission_value": "TIMELB", "page_size": "many"},
        {"codelist_submission_value": "TIMELB", "sort_by": "uid); MATCH (n"},
        {"codelist_submission_value": "TIMELB", "sort_order": "sideways"},
    ],
)
def test_invalid_request_gives_400(api_client, db_calls, params):
    """A missing submission value, an invalid sort or page is refused before the database."""
    response = api_client.get("/consumer-sample/ct-terms", params=params)

    assert response.status_code == 400, response.text
    assert not db_calls


def test_database_query_is_parameterised(monkeypatch):
    """The submission value and the page reach the queries as parameters."""
    captured: list[tuple[str, dict[str, Any]]] = []

    def fake_query(cypher_query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        captured.append((cypher_query, params))
        return [{"total": 7}] if "count(*)" in cypher_query else []

    monkeypatch.setattr(db, "query", fake_query)

    rows, total = db.get_ct_terms(
        "TIMELB'; MATCH (n) DETACH DELETE n //",
        models.SortByCTTerms.SUBMISSION_VALUE,
        models.SortOrder.DESC,
        5,
        3,
    )

    assert (rows, total) == ([], 7)
    (rows_query, rows_params), (count_query, count_params) = captured
    submission_params = {
        "codelist_submission_value": "TIMELB'; MATCH (n) DETACH DELETE n //",
        "status": "Final",
    }
    assert rows_params == {
        **submission_params,
        "pagination_skip": 10,
        "pagination_limit": 5,
    }
    assert count_params == submission_params
    assert "DETACH DELETE" not in rows_query + count_query
    assert "ORDER BY toLower(toString(submission_value)) desc" in rows_query
    assert rows_query.rstrip().endswith("SKIP $pagination_skip LIMIT $pagination_limit")
    assert count_query.rstrip().endswith("RETURN count(*) AS total")


def test_database_total_is_zero_without_rows(monkeypatch):
    """No matching codelist gives an empty page and a zero total."""
    monkeypatch.setattr(db, "query", lambda cypher_query, params: [])

    assert db.get_ct_terms(
        "NOSUCHCL", models.SortByCTTerms.TERM_UID, models.SortOrder.ASC, 5, 1
    ) == ([], 0)
