"""
Tests for full-text search on codelists and codelists by term
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

import logging

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
codelist_ordinal: CTCodelist
codelist_non_ordinal: CTCodelist
codelist_with_special_chars: CTCodelist
term_alpha: CTTerm
term_beta: CTTerm
term_gamma: CTTerm

URL = "/ct/codelists"


def create_fulltext_indexes():
    """Create the full-text indexes needed for the search endpoints"""
    # Index on CTCodelistNameValue and CTCodelistAttributesValue
    db.cypher_query("""
        CREATE FULLTEXT INDEX codelist_fulltext_index IF NOT EXISTS
        FOR (n:CTCodelistNameValue|CTCodelistAttributesValue)
        ON EACH [n.name, n.submission_value]
        """)
    # Index on CTTermNameValue and CTTermAttributesValue
    db.cypher_query("""
        CREATE FULLTEXT INDEX term_fulltext_index IF NOT EXISTS
        FOR (n:CTTermNameValue|CTTermAttributesValue)
        ON EACH [n.name, n.submission_value]
        """)
    # Wait for indexes to be online
    db.cypher_query("CALL db.awaitIndexes(300)")


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data for full-text search tests"""
    db_name = "ct-codelist-fulltext-search.api"
    inject_and_clear_db(db_name)
    inject_base_data(inject_unit_subset=False)

    # Create full-text indexes
    create_fulltext_indexes()

    catalogue = "SDTM CT"

    # Create an ordinal codelist with specific submission value for testing
    global codelist_ordinal
    codelist_ordinal = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="Severity Scale",
        sponsor_preferred_name="Severity Scale",
        submission_value="SEVERITY",
        library_name="Sponsor",
        approve=True,
        extensible=True,
        is_ordinal=True,
    )

    # Create a non-ordinal codelist
    global codelist_non_ordinal
    codelist_non_ordinal = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="Test Category",
        sponsor_preferred_name="Test Category",
        submission_value="TESTCAT",
        library_name="Sponsor",
        approve=True,
        extensible=True,
        is_ordinal=False,
    )

    # Create a codelist with special characters to test case insensitivity
    global codelist_with_special_chars
    codelist_with_special_chars = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="MySpecialCodelist",
        sponsor_preferred_name="MySpecialCodelist",
        submission_value="MYSPECIAL",
        library_name="Sponsor",
        approve=True,
        extensible=True,
        is_ordinal=False,
    )

    # Create terms for term-based search testing
    global term_alpha
    term_alpha = TestUtils.create_ct_term(
        codelist_uid=codelist_ordinal.codelist_uid,
        sponsor_preferred_name="Alpha Value",
        submission_value="ALPHA",
        order=1,
        library_name="Sponsor",
        approve=True,
        ordinal=1.0,
    )

    global term_beta
    term_beta = TestUtils.create_ct_term(
        codelist_uid=codelist_ordinal.codelist_uid,
        sponsor_preferred_name="Beta Value",
        submission_value="BETA",
        order=2,
        library_name="Sponsor",
        approve=True,
        ordinal=2.0,
    )

    global term_gamma
    term_gamma = TestUtils.create_ct_term(
        codelist_uid=codelist_non_ordinal.codelist_uid,
        sponsor_preferred_name="Gamma Result",
        submission_value="GAMMA",
        order=1,
        library_name="Sponsor",
        approve=True,
    )

    yield


# ============================================================================
# Tests for /codelists/full-text-search (search by codelist properties)
# ============================================================================


def test_fulltext_search_basic(api_client):
    """Test basic full-text search returns matching codelists"""
    response = api_client.get(
        f"{URL}/full-text-search",
        params={"search_string": "SEVERITY"},
    )
    assert_response_status_code(response, 200)

    items = response.json()["items"]
    assert len(items) >= 1

    # Check that the ordinal codelist is returned
    uids = [item["uid"] for item in items]
    assert codelist_ordinal.codelist_uid in uids

    # Verify the response structure
    for item in items:
        assert "uid" in item
        assert "sponsor_preferred_name" in item
        assert "submission_value" in item
        assert "library_name" in item


def test_fulltext_search_case_insensitive(api_client):
    """Test that full-text search is case insensitive"""
    # Search with lowercase
    response_lower = api_client.get(
        f"{URL}/full-text-search",
        params={"search_string": "severity"},
    )
    assert_response_status_code(response_lower, 200)

    # Search with uppercase
    response_upper = api_client.get(
        f"{URL}/full-text-search",
        params={"search_string": "SEVERITY"},
    )
    assert_response_status_code(response_upper, 200)

    # Search with mixed case
    response_mixed = api_client.get(
        f"{URL}/full-text-search",
        params={"search_string": "Severity"},
    )
    assert_response_status_code(response_mixed, 200)

    # All should return the same codelist
    uids_lower = {item["uid"] for item in response_lower.json()["items"]}
    uids_upper = {item["uid"] for item in response_upper.json()["items"]}
    uids_mixed = {item["uid"] for item in response_mixed.json()["items"]}

    assert codelist_ordinal.codelist_uid in uids_lower
    assert codelist_ordinal.codelist_uid in uids_upper
    assert codelist_ordinal.codelist_uid in uids_mixed


def test_fulltext_search_fuzziness(api_client):
    """Test that full-text search supports fuzzy matching (typo tolerance)"""
    # Search with a slight typo (missing letter)
    response = api_client.get(
        f"{URL}/full-text-search",
        params={"search_string": "Sevrity Scale"},  # Missing 'E'
    )
    assert_response_status_code(response, 200)

    # Should still find the codelist due to fuzziness
    uids = [item["uid"] for item in response.json()["items"]]
    assert codelist_ordinal.codelist_uid in uids

    # But searching with too many differences should NOT match
    response_too_far = api_client.get(
        f"{URL}/full-text-search",
        params={
            "search_string": "SVRT"
        },  # Too different from "SEVERITY" or "Severity Scale"
    )
    assert_response_status_code(response_too_far, 200)

    uids_too_far = [item["uid"] for item in response_too_far.json()["items"]]
    assert codelist_ordinal.codelist_uid not in uids_too_far


def test_fulltext_search_partial_match(api_client):
    """Test that full-text search supports partial matching (wildcard)"""
    # Search with partial string (default behavior uses wildcards)
    response = api_client.get(
        f"{URL}/full-text-search",
        params={"search_string": "SEVER"},
    )
    assert_response_status_code(response, 200)

    uids = [item["uid"] for item in response.json()["items"]]
    assert codelist_ordinal.codelist_uid in uids


def test_fulltext_search_only_ordinal(api_client):
    """Test filtering for only ordinal codelists"""
    # Search without filter - should return both ordinal and non-ordinal
    response_all = api_client.get(
        f"{URL}/full-text-search",
        params={"search_string": "TEST"},
    )
    assert_response_status_code(response_all, 200)
    uids_all = [item["uid"] for item in response_all.json()["items"]]
    assert codelist_non_ordinal.codelist_uid in uids_all

    # Search with only_ordinal_codelists=True
    response_ordinal = api_client.get(
        f"{URL}/full-text-search",
        params={
            "search_string": "TEST",
            "only_ordinal_codelists": True,
        },
    )
    assert_response_status_code(response_ordinal, 200)

    uids_ordinal = [item["uid"] for item in response_ordinal.json()["items"]]

    # Should not include non-ordinal codelist
    assert codelist_non_ordinal.codelist_uid not in uids_ordinal


def test_fulltext_search_match_whole_words(api_client):
    """Test match_whole_words parameter for exact phrase matching"""
    # Search without whole word matching (default) - partial match works
    response_partial = api_client.get(
        f"{URL}/full-text-search",
        params={
            "search_string": "SEVER",
            "match_whole_words": False,
        },
    )
    assert_response_status_code(response_partial, 200)
    uids_partial = [item["uid"] for item in response_partial.json()["items"]]
    assert codelist_ordinal.codelist_uid in uids_partial

    # Search with whole word matching - but pass partial word
    response_whole_partial = api_client.get(
        f"{URL}/full-text-search",
        params={
            "search_string": "SEVER",
            "match_whole_words": True,
        },
    )
    assert_response_status_code(response_whole_partial, 200)
    uids_whole_partial = [
        item["uid"] for item in response_whole_partial.json()["items"]
    ]
    assert codelist_ordinal.codelist_uid not in uids_whole_partial

    # Search with whole word matching - exact match required
    response_whole = api_client.get(
        f"{URL}/full-text-search",
        params={
            "search_string": "SEVERITY",
            "match_whole_words": True,
        },
    )
    assert_response_status_code(response_whole, 200)
    uids_whole = [item["uid"] for item in response_whole.json()["items"]]
    assert codelist_ordinal.codelist_uid in uids_whole


def test_fulltext_search_pagination(api_client):
    """Test pagination parameters"""
    response = api_client.get(
        f"{URL}/full-text-search",
        params={
            "search_string": "TEST",
            "page_number": 1,
            "page_size": 1,
        },
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert result["page"] == 1
    assert result["size"] == 1
    assert len(result["items"]) <= 1


def test_fulltext_search_no_results(api_client):
    """Test search with no matching results"""
    response = api_client.get(
        f"{URL}/full-text-search",
        params={"search_string": "NONEXISTENTVALUE12345"},
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert len(result["items"]) == 0


def test_fulltext_search_by_sponsor_preferred_name(api_client):
    """Test searching by sponsor_preferred_name field"""
    response = api_client.get(
        f"{URL}/full-text-search",
        params={"search_string": "Category"},  # Part of "Test Category"
    )
    assert_response_status_code(response, 200)

    uids = [item["uid"] for item in response.json()["items"]]
    assert codelist_non_ordinal.codelist_uid in uids


# ============================================================================
# Tests for /codelists/full-text-search-by-term (search codelists via terms)
# ============================================================================


def test_fulltext_search_by_term_basic(api_client):
    """Test basic term-based search returns codelists containing matching terms"""
    response = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={"search_string": "ALPHA"},
    )
    assert_response_status_code(response, 200)

    items = response.json()["items"]
    assert len(items) >= 1

    # Should return the codelist containing the ALPHA term
    uids = [item["uid"] for item in items]
    assert codelist_ordinal.codelist_uid in uids


def test_fulltext_search_by_term_case_insensitive(api_client):
    """Test that term search is case insensitive"""
    response_lower = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={"search_string": "alpha"},
    )
    response_upper = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={"search_string": "ALPHA"},
    )

    assert_response_status_code(response_lower, 200)
    assert_response_status_code(response_upper, 200)

    uids_lower = {item["uid"] for item in response_lower.json()["items"]}
    uids_upper = {item["uid"] for item in response_upper.json()["items"]}

    assert codelist_ordinal.codelist_uid in uids_lower
    assert codelist_ordinal.codelist_uid in uids_upper


def test_fulltext_search_by_term_fuzziness(api_client):
    """Test fuzzy matching for term search"""
    # Search with typo
    response = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={"search_string": "Alpa Value"},  # Missing 'H'
    )
    assert_response_status_code(response, 200)

    uids = [item["uid"] for item in response.json()["items"]]
    assert codelist_ordinal.codelist_uid in uids

    # But searching with too many differences should NOT match
    response_too_far = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={"search_string": "APHV"},  # Too different from "ALPHA"
    )
    assert_response_status_code(response_too_far, 200)

    uids_too_far = [item["uid"] for item in response_too_far.json()["items"]]
    assert codelist_ordinal.codelist_uid not in uids_too_far


def test_fulltext_search_by_term_only_ordinal(api_client):
    """Test filtering for only ordinal codelists in term search"""
    # GAMMA term is in non-ordinal codelist
    response = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={
            "search_string": "GAMMA",
            "only_ordinal_codelists": True,
        },
    )
    assert_response_status_code(response, 200)

    items = response.json()["items"]
    uids = [item["uid"] for item in items]

    # GAMMA's codelist (non-ordinal) should NOT be included
    assert codelist_non_ordinal.codelist_uid not in uids


def test_fulltext_search_by_term_match_whole_words(api_client):
    """Test match_whole_words for term search"""
    # Partial match without whole words
    response_partial = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={
            "search_string": "ALP",
            "match_whole_words": False,
        },
    )
    assert_response_status_code(response_partial, 200)

    uids_partial = [item["uid"] for item in response_partial.json()["items"]]
    assert codelist_ordinal.codelist_uid in uids_partial

    # Search with whole word matching - but pass partial word
    response_whole_partial = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={
            "search_string": "Alph",
            "match_whole_words": True,
        },
    )
    assert_response_status_code(response_whole_partial, 200)

    uids_whole_partial = [
        item["uid"] for item in response_whole_partial.json()["items"]
    ]
    assert codelist_ordinal.codelist_uid not in uids_whole_partial

    # Whole word match
    response_whole = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={
            "search_string": "ALPHA",
            "match_whole_words": True,
        },
    )
    assert_response_status_code(response_whole, 200)

    uids_whole = [item["uid"] for item in response_whole.json()["items"]]
    assert codelist_ordinal.codelist_uid in uids_whole


def test_fulltext_search_by_term_multiple_terms_same_codelist(api_client):
    """Test that searching for a term returns the codelist only once"""
    # Search for "Value" which appears in multiple terms of the same codelist
    response = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={"search_string": "Value"},
    )
    assert_response_status_code(response, 200)

    items = response.json()["items"]
    uids = [item["uid"] for item in items]

    # Codelist should appear only once, not multiple times
    assert uids.count(codelist_ordinal.codelist_uid) == 1


def test_fulltext_search_by_term_pagination(api_client):
    """Test pagination for term-based search"""
    response = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={
            "search_string": "Value",
            "page_number": 1,
            "page_size": 1,
        },
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert result["page"] == 1
    assert result["size"] == 1
    assert len(result["items"]) <= 1


def test_fulltext_search_by_term_sponsor_preferred_name(api_client):
    """Test searching by term's sponsor_preferred_name"""
    # "Result" is part of "Gamma Result" term name
    response = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={"search_string": "Result"},
    )
    assert_response_status_code(response, 200)

    uids = [item["uid"] for item in response.json()["items"]]
    assert codelist_non_ordinal.codelist_uid in uids


def test_fulltext_search_by_term_no_results(api_client):
    """Test term search with no matching results"""
    response = api_client.get(
        f"{URL}/full-text-search-by-term",
        params={"search_string": "NONEXISTENTTERM99999"},
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert len(result["items"]) == 0


def test_fulltext_search_special_lucene_characters(api_client):
    """Test that special Lucene characters are properly escaped and don't cause errors"""
    # Test various Lucene special characters that would cause syntax errors if not escaped
    special_chars = [
        "[",  # Range query syntax
        "]",  # Range query syntax
        "{",  # Range query syntax
        "}",  # Range query syntax
        "(",  # Grouping syntax
        ")",  # Grouping syntax
        "+",  # Required term
        "-",  # Prohibited term
        "!",  # Prohibited term
        ":",  # Field separator
        "~",  # Fuzzy search
        "^",  # Boost operator
        '"',  # Phrase query
        "*",  # Wildcard
        "?",  # Single char wildcard
        "\\",  # Escape character
    ]

    for char in special_chars:
        response = api_client.get(
            f"{URL}/full-text-search",
            params={"search_string": char},
        )
        # Should not cause a 500 error - should return 200 even if no results
        assert_response_status_code(response, 200)

        # Also test with the character in a search string
        response = api_client.get(
            f"{URL}/full-text-search",
            params={"search_string": f"TEST{char}VALUE"},
        )
        assert_response_status_code(response, 200)


def test_fulltext_search_by_term_special_lucene_characters(api_client):
    """Test that special Lucene characters are properly escaped in term search"""
    # Test various Lucene special characters in term search
    special_chars = [
        "[",
        "]",
        "{",
        "}",
        "(",
        ")",
        "+",
        "-",
        "!",
        ":",
        "~",
        "^",
        '"',
        "*",
        "?",
        "\\",
    ]

    for char in special_chars:
        response = api_client.get(
            f"{URL}/full-text-search-by-term",
            params={"search_string": char},
        )
        # Should not cause a 500 error - should return 200 even if no results
        assert_response_status_code(response, 200)

        # Also test with the character in a search string
        response = api_client.get(
            f"{URL}/full-text-search-by-term",
            params={"search_string": f"ALPHA{char}VALUE"},
        )
        assert_response_status_code(response, 200)
