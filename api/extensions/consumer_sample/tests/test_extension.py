"""consumer_sample extension against the Neo4j test database."""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.services.controlled_terminologies.ct_term_name import (
    CTTermNameService,
)
from clinical_mdr_api.tests.fixtures.auth import mock_auth_context  # noqa: F401
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from extensions.extensions_api import app

CODELIST_SUBMISSION_VALUE = "SMPLCL"
TERM_COUNT = 3
DRAFT_TERM_NAME = "Consumer sample draft term"
REVISED_TERM_NAME = "Consumer sample revised term"


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data: a codelist with three Final terms, a never approved (Draft)
    term, and a Final term whose name is being revised (new Draft version)"""
    db_name = "extensions.consumer-sample"
    inject_and_clear_db(db_name)
    inject_base_data()

    codelist = TestUtils.create_ct_codelist(
        name="Consumer sample codelist",
        submission_value=CODELIST_SUBMISSION_VALUE,
        extensible=True,
        approve=True,
    )
    for i in range(TERM_COUNT):
        TestUtils.create_ct_term(
            sponsor_preferred_name=f"Consumer sample term {i}",
            codelist_uid=codelist.codelist_uid,
        )
    TestUtils.create_ct_term(
        sponsor_preferred_name=DRAFT_TERM_NAME,
        codelist_uid=codelist.codelist_uid,
        approve=False,
    )
    revised_term = TestUtils.create_ct_term(
        sponsor_preferred_name=REVISED_TERM_NAME,
        codelist_uid=codelist.codelist_uid,
    )
    CTTermNameService().create_new_version(term_uid=revised_term.term_uid)

    yield
    drop_db(db_name)


@pytest.fixture(scope="module")
def api_client(test_data, mock_auth_context):  # noqa: F811
    """Extensions API test client on the test database"""
    yield TestClient(app)


def test_ct_terms_by_codelist_submission_value(api_client):
    """The Final terms of the codelist are returned with their name and attributes."""
    response = api_client.get(
        "/consumer-sample/ct-terms",
        params={"codelist_submission_value": CODELIST_SUBMISSION_VALUE},
    )
    assert response.status_code == 200, response.text
    res = response.json()

    assert res.keys() == {"self", "prev", "next", "total", "items"}
    assert res["total"] == TERM_COUNT
    assert len(res["items"]) == TERM_COUNT
    term_uids = [item["term_uid"] for item in res["items"]]
    assert term_uids == sorted(term_uids)
    assert {item["sponsor_preferred_name"] for item in res["items"]} == {
        f"Consumer sample term {i}" for i in range(TERM_COUNT)
    }
    returned_names = {item["sponsor_preferred_name"] for item in res["items"]}
    assert DRAFT_TERM_NAME not in returned_names
    assert REVISED_TERM_NAME not in returned_names
    for item in res["items"]:
        assert item["name_status"] == "Final"
        assert item["attributes_status"] == "Final"
    assert res["self"].startswith("/consumer-sample/ct-terms?")
    assert f"codelist_submission_value={CODELIST_SUBMISSION_VALUE}" in res["next"]


def test_ct_terms_pagination(api_client):
    """Pages are consecutive slices of the same ordered list."""
    params = {"codelist_submission_value": CODELIST_SUBMISSION_VALUE}
    all_terms = api_client.get("/consumer-sample/ct-terms", params=params).json()[
        "items"
    ]

    first = api_client.get(
        "/consumer-sample/ct-terms", params={**params, "page_size": 2, "page_number": 1}
    )
    second = api_client.get(
        "/consumer-sample/ct-terms", params={**params, "page_size": 2, "page_number": 2}
    )
    third = api_client.get(
        "/consumer-sample/ct-terms", params={**params, "page_size": 2, "page_number": 3}
    )

    assert first.status_code == second.status_code == third.status_code == 200
    assert first.json()["total"] == second.json()["total"] == TERM_COUNT
    assert first.json()["items"] == all_terms[:2]
    assert second.json()["items"] == all_terms[2:]
    assert third.json()["items"] == []
    assert "page_number=3" in second.json()["next"]


@pytest.mark.parametrize(
    "sort_by",
    [
        "term_uid",
        "submission_value",
        "sponsor_preferred_name",
        "nci_preferred_name",
        "concept_id",
    ],
)
def test_ct_terms_sort(api_client, sort_by):
    """Descending is the reverse of ascending, and the values come out in order."""
    params = {
        "codelist_submission_value": CODELIST_SUBMISSION_VALUE,
        "sort_by": sort_by,
    }
    asc = api_client.get(
        "/consumer-sample/ct-terms", params={**params, "sort_order": "asc"}
    )
    desc = api_client.get(
        "/consumer-sample/ct-terms", params={**params, "sort_order": "desc"}
    )

    assert asc.status_code == desc.status_code == 200, asc.text + desc.text
    asc_items = asc.json()["items"]
    values = [item[sort_by].lower() for item in asc_items]
    assert values == sorted(values)
    assert desc.json()["items"] == asc_items[::-1]
    assert f"sort_by={sort_by}&sort_order=desc" in desc.json()["self"]


def test_ct_terms_sorted_pages_are_slices_of_the_sorted_list(api_client):
    """Sorting applies before paging, and total does not depend on the page."""
    params = {
        "codelist_submission_value": CODELIST_SUBMISSION_VALUE,
        "sort_by": "sponsor_preferred_name",
        "sort_order": "desc",
    }
    all_terms = api_client.get("/consumer-sample/ct-terms", params=params).json()[
        "items"
    ]
    page = api_client.get(
        "/consumer-sample/ct-terms", params={**params, "page_size": 1, "page_number": 2}
    ).json()

    assert page["items"] == all_terms[1:2]
    assert page["total"] == TERM_COUNT


def test_ct_terms_unknown_submission_value_empty_page(api_client):
    """An unknown submission value gives an empty page."""
    response = api_client.get(
        "/consumer-sample/ct-terms",
        params={"codelist_submission_value": "NOSUCHCL"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["items"] == []
    assert response.json()["total"] == 0
