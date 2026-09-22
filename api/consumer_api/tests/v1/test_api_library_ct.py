# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
from urllib.parse import quote_plus

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db

BASE_URL = "/v1"


CODELIST_FIELDS_ALL = [
    "uid",
    "name",
    "submission_value",
    "sponsor_preferred_name",
    "nci_preferred_name",
    "definition",
    "is_extensible",
    "library_name",
    "name_status",
    "name_version",
    "attributes_status",
    "attributes_version",
]

CODELIST_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "submission_value",
    "sponsor_preferred_name",
    "library_name",
    "name_status",
    "name_version",
    "attributes_status",
    "attributes_version",
]

CODELIST_SUBMISSION_VALUE = "CT Codelist"


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data(api_client):
    """Initialize test data"""
    db_name = "consumer-api-v1-library-ct"
    set_db(db_name)
    inject_base_data()
    TestUtils.create_study_fields_ct_data()


def test_get_codelists(api_client):
    response = api_client.get(f"{BASE_URL}/library/ct/codelists")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)

    assert len(res["items"]) > 0

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, CODELIST_FIELDS_ALL, CODELIST_FIELDS_NOT_NULL
        )


def test_get_codelists_pagination(api_client):
    # Default page size
    response = api_client.get(f"{BASE_URL}/library/ct/codelists")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    total_items = len(res["items"])

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/library/ct/codelists?page_size=1")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 1

    # Page through all results
    all_fetched = []
    response = api_client.get(f"{BASE_URL}/library/ct/codelists?page_size=1")
    all_fetched.extend(response.json()["items"])

    while response.json()["items"]:
        response = api_client.get(response.json()["next"])
        all_fetched.extend(response.json()["items"])

    assert len(all_fetched) == total_items


def test_get_codelists_invalid_pagination_params(api_client):
    response = api_client.get(f"{BASE_URL}/library/ct/codelists?page_size=0")
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )


def test_get_codelists_default_status_filter(api_client):
    """Default query filters by name_status=Final and attributes_status=Final.
    Verify all returned items have the correct status values."""
    response = api_client.get(f"{BASE_URL}/library/ct/codelists")
    assert_response_status_code(response, 200)
    res = response.json()

    assert len(res["items"]) > 0
    for item in res["items"]:
        assert item["name_status"] == "Final"
        assert item["attributes_status"] == "Final"


def test_get_codelists_filter_name_status_draft(api_client):
    """Filtering by name_status=Draft returns 3 items (other test data codelists names are Final)."""
    response = api_client.get(f"{BASE_URL}/library/ct/codelists?name_status=Draft")
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 3


def test_get_codelists_filter_attributes_status_draft(api_client):
    """Filtering by attributes_status=Draft returns no items (all test data codelists attributes are Final)."""
    response = api_client.get(
        f"{BASE_URL}/library/ct/codelists?attributes_status=Draft"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 0


def test_get_codelists_filter_both_statuses_explicit(api_client):
    """Explicitly passing both status filters as Final returns same results as default."""
    response_default = api_client.get(f"{BASE_URL}/library/ct/codelists")
    response_explicit = api_client.get(
        f"{BASE_URL}/library/ct/codelists?name_status=Final&attributes_status=Final"
    )
    assert_response_status_code(response_default, 200)
    assert_response_status_code(response_explicit, 200)

    assert response_default.json()["items"] == response_explicit.json()["items"]


# ------- Codelist Term tests -------

CODELIST_TERM_FIELDS_ALL = [
    "term_uid",
    "codelist_uid",
    "order",
    "ordinal",
    "submission_value",
    "sponsor_preferred_name",
    "concept_id",
    "nci_preferred_name",
    "library_name",
    "name_status",
    "name_version",
    "attributes_status",
    "attributes_version",
]

CODELIST_TERM_FIELDS_NOT_NULL = [
    "term_uid",
    "codelist_uid",
    "submission_value",
    "sponsor_preferred_name",
    "library_name",
    "name_status",
    "name_version",
    "attributes_status",
    "attributes_version",
]

CODELIST_UID = "C66737"


def test_get_codelist_terms(api_client):
    """Test retrieving codelist terms for the "CT Codelist" (10 final terms in test data)."""
    response = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_submission_value={CODELIST_SUBMISSION_VALUE}"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)

    assert len(res["items"]) == 10

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, CODELIST_TERM_FIELDS_ALL, CODELIST_TERM_FIELDS_NOT_NULL
        )

    # Verify items are sorted by sponsor_preferred_name ascending
    names = [item["sponsor_preferred_name"] for item in res["items"]]
    assert names == sorted(names)


def test_get_codelist_terms_nonexistent_codelist(api_client):
    """Test retrieving terms for a codelist that does not exist returns empty list."""
    response = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_submission_value=NONEXISTENT"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) == 0


def test_get_codelist_terms_pagination(api_client):
    # 'CT Codelist' has 10 final terms — page through with page_size=4 to verify pagination and that codelist_submission_value is preserved in links
    response = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_submission_value={CODELIST_SUBMISSION_VALUE}&page_size=4"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 4

    # Verify codelist_submission_value is preserved in pagination links
    encoded_value = quote_plus(CODELIST_SUBMISSION_VALUE)
    for key in ["self", "prev", "next"]:
        assert f"codelist_submission_value={encoded_value}" in res[key]

    # Page through all results
    all_fetched = []
    all_fetched.extend(res["items"])

    while res["items"]:
        response = api_client.get(res["next"])
        res = response.json()
        all_fetched.extend(res["items"])

    assert len(all_fetched) == 10


def test_get_codelist_terms_no_filters(api_client):
    """Calling without any filter returns all terms (200)."""
    response = api_client.get(f"{BASE_URL}/library/ct/codelist-terms")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) > 0

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, CODELIST_TERM_FIELDS_ALL, CODELIST_TERM_FIELDS_NOT_NULL
        )


def test_get_codelist_terms_filter_by_codelist_uid(api_client):
    """Filtering by codelist_uid returns the same terms as filtering by codelist_submission_value for the same codelist."""
    response_by_uid = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_uid={CODELIST_UID}"
    )
    assert_response_status_code(response_by_uid, 200)
    res_by_uid = response_by_uid.json()

    response_by_submval = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_submission_value={CODELIST_SUBMISSION_VALUE}"
    )
    assert_response_status_code(response_by_submval, 200)
    res_by_submval = response_by_submval.json()

    assert len(res_by_uid["items"]) == len(res_by_submval["items"])
    assert {item["term_uid"] for item in res_by_uid["items"]} == {
        item["term_uid"] for item in res_by_submval["items"]
    }


def test_get_codelist_terms_filter_by_both_params(api_client):
    """Filtering by both codelist_uid and codelist_submission_value returns the same results as filtering by either alone."""
    response = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_uid={CODELIST_UID}&codelist_submission_value={CODELIST_SUBMISSION_VALUE}"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    response_by_uid = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_uid={CODELIST_UID}"
    )
    assert len(res["items"]) == len(response_by_uid.json()["items"])


def test_get_codelist_terms_filter_by_nonexistent_codelist_uid(api_client):
    """Filtering by a nonexistent codelist_uid returns empty list."""
    response = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_uid=NONEXISTENT"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) == 0


def test_get_codelist_terms_invalid_pagination_params(api_client):
    response = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_submission_value={CODELIST_SUBMISSION_VALUE}&page_size=0"
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )


def test_get_codelist_terms_default_status_filter(api_client):
    """Default query filters by name_status=Final and attributes_status=Final.
    All test data terms are Final. Verify status fields in response."""
    response = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_submission_value={CODELIST_SUBMISSION_VALUE}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 10

    for item in res["items"]:
        assert item["name_status"] == "Final"
        assert item["attributes_status"] == "Final"


def test_get_codelist_terms_filter_name_status_draft(api_client):
    """Filtering by name_status=Draft returns no items (all test data terms are Final)."""
    response = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_submission_value={CODELIST_SUBMISSION_VALUE}&name_status=Draft"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 0


def test_get_codelist_terms_filter_attributes_status_draft(api_client):
    """Filtering by attributes_status=Draft returns no items (all test data term attributes are Final)."""
    response = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_submission_value={CODELIST_SUBMISSION_VALUE}&attributes_status=Draft"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 0


def test_get_codelist_terms_filter_both_statuses_explicit(api_client):
    """Explicitly passing both status filters as Final returns same results as default."""
    response_default = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_submission_value={CODELIST_SUBMISSION_VALUE}"
    )
    response_explicit = api_client.get(
        f"{BASE_URL}/library/ct/codelist-terms?codelist_submission_value={CODELIST_SUBMISSION_VALUE}&name_status=Final&attributes_status=Final"
    )
    assert_response_status_code(response_default, 200)
    assert_response_status_code(response_explicit, 200)

    assert response_default.json()["items"] == response_explicit.json()["items"]


# ------- Unit Definition tests -------

UNIT_DEFINITION_FIELDS_ALL = [
    "uid",
    "name",
    "library_name",
    "status",
    "version",
    "subsets",
    "is_convertible_unit",
    "is_master_unit",
    "is_si_unit",
    "is_display_unit",
    "is_us_conventional_unit",
    "use_complex_unit_conversion",
    "use_molecular_weight",
    "ucum_unit_name",
    "unit_dimension",
    "legacy_code",
    "conversion_factor_to_master",
]

UNIT_DEFINITION_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "library_name",
    "status",
    "version",
    "subsets",
]

UNIT_SUBSET_FIELDS = [
    "term_uid",
    "term_name",
    "term_submission_value",
    "codelist_uid",
    "codelist_name",
    "codelist_submission_value",
]

UNIT_SUBSET = "Study Time"


def test_get_unit_definitions(api_client):
    """Test retrieving unit definitions for the 'Study Time' subset (3 approved units in test data)."""
    response = api_client.get(
        f"{BASE_URL}/library/unit-definitions?subset={quote_plus(UNIT_SUBSET)}"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)

    assert len(res["items"]) == 3

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, UNIT_DEFINITION_FIELDS_ALL, UNIT_DEFINITION_FIELDS_NOT_NULL
        )
        # Each returned unit definition should belong to the requested subset
        subset_names = [s["term_name"] for s in item["subsets"]]
        assert UNIT_SUBSET in subset_names
        for subset in item["subsets"]:
            assert set(subset.keys()) == set(UNIT_SUBSET_FIELDS)

    # Verify items are sorted by name ascending
    names = [item["name"] for item in res["items"]]
    assert names == sorted(names)


def test_get_unit_definitions_nonexistent_subset(api_client):
    """Test retrieving unit definitions for a subset that does not exist returns empty list."""
    response = api_client.get(f"{BASE_URL}/library/unit-definitions?subset=NONEXISTENT")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) == 0


def test_get_unit_definitions_pagination(api_client):
    # 'Study Time' subset has 3 units — page through with page_size=2 to verify pagination and that subset is preserved in links
    response = api_client.get(
        f"{BASE_URL}/library/unit-definitions?subset={quote_plus(UNIT_SUBSET)}&page_size=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 2

    # Verify subset is preserved in pagination links
    encoded_value = quote_plus(UNIT_SUBSET)
    for key in ["self", "prev", "next"]:
        assert f"subset={encoded_value}" in res[key]

    # Page through all results
    all_fetched = []
    all_fetched.extend(res["items"])

    while res["items"]:
        response = api_client.get(res["next"])
        res = response.json()
        all_fetched.extend(res["items"])

    assert len(all_fetched) == 3


def test_get_unit_definitions_without_subset(api_client):
    """Omitting subset returns all unit definitions (at least the 3 in 'Study Time')."""
    response = api_client.get(f"{BASE_URL}/library/unit-definitions")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) >= 3

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, UNIT_DEFINITION_FIELDS_ALL, UNIT_DEFINITION_FIELDS_NOT_NULL
        )
        assert isinstance(item["subsets"], list)
        for subset in item["subsets"]:
            assert set(subset.keys()) == set(UNIT_SUBSET_FIELDS)


def test_get_unit_definitions_invalid_pagination_params(api_client):
    response = api_client.get(
        f"{BASE_URL}/library/unit-definitions?subset={quote_plus(UNIT_SUBSET)}&page_size=0"
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )


def test_get_unit_definitions_default_status_filter(api_client):
    """Default query filters by status=Final. All test data unit definitions are Final.
    Verify status and version fields in response."""
    response = api_client.get(
        f"{BASE_URL}/library/unit-definitions?subset={quote_plus(UNIT_SUBSET)}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 3

    for item in res["items"]:
        assert item["status"] == "Final"


def test_get_unit_definitions_filter_status_draft(api_client):
    """Filtering by status=Draft returns no items (all test data unit definitions are Final)."""
    response = api_client.get(
        f"{BASE_URL}/library/unit-definitions?subset={quote_plus(UNIT_SUBSET)}&status=Draft"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 0


def test_get_unit_definitions_filter_status_explicit_final(api_client):
    """Explicitly passing status=Final returns same results as default."""
    response_default = api_client.get(
        f"{BASE_URL}/library/unit-definitions?subset={quote_plus(UNIT_SUBSET)}"
    )
    response_explicit = api_client.get(
        f"{BASE_URL}/library/unit-definitions?subset={quote_plus(UNIT_SUBSET)}&status=Final"
    )
    assert_response_status_code(response_default, 200)
    assert_response_status_code(response_explicit, 200)

    assert response_default.json()["items"] == response_explicit.json()["items"]
