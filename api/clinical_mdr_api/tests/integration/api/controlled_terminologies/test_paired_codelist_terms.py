"""
Tests for paired codelist terms endpoint
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
names_codelist: CTCodelist
codes_codelist: CTCodelist
unpaired_codelist: CTCodelist
term_a: CTTerm
term_b: CTTerm
term_c: CTTerm

CATALOGUE = "SDTM CT"
URL = "/ct/paired-codelists"


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data:
    - A names codelist paired with a codes codelist
    - 3 terms in the names codelist
    - Same 3 terms added to the codes codelist with different submission values
    - An unpaired codelist for the 400 error test
    """
    db_name = "ct-paired-codelist-terms.api"
    inject_and_clear_db(db_name)
    inject_base_data(inject_unit_subset=False)

    # Create the two codelists that will be paired
    global codes_codelist
    codes_codelist = TestUtils.create_ct_codelist(
        catalogue_name=CATALOGUE,
        name="Codes CL",
        sponsor_preferred_name="Codes CL",
        submission_value="CODES_CL",
        library_name="Sponsor",
        approve=True,
        extensible=True,
    )
    global names_codelist
    names_codelist = TestUtils.create_ct_codelist(
        catalogue_name=CATALOGUE,
        name="Names CL",
        sponsor_preferred_name="Names CL",
        submission_value="NAMES_CL",
        library_name="Sponsor",
        approve=True,
        extensible=True,
        paired_codes_codelist_uid=codes_codelist.codelist_uid,
    )

    # Create terms in the names codelist
    global term_a
    term_a = TestUtils.create_ct_term(
        codelist_uid=names_codelist.codelist_uid,
        sponsor_preferred_name="Term A",
        submission_value="NAME_A",
        order=1,
        library_name="Sponsor",
        approve=True,
    )
    global term_b
    term_b = TestUtils.create_ct_term(
        codelist_uid=names_codelist.codelist_uid,
        sponsor_preferred_name="Term B",
        submission_value="NAME_B",
        order=2,
        library_name="Sponsor",
        approve=True,
    )
    global term_c
    term_c = TestUtils.create_ct_term(
        codelist_uid=names_codelist.codelist_uid,
        sponsor_preferred_name="Term C",
        submission_value="NAME_C",
        order=3,
        library_name="Sponsor",
        approve=True,
    )

    # Add the same terms to the codes codelist with different submission values
    codelist_service = CTCodelistService()
    codelist_service.add_term(
        codelist_uid=codes_codelist.codelist_uid,
        term_uid=term_a.term_uid,
        order=1,
        submission_value="CODE_A",
    )
    codelist_service.add_term(
        codelist_uid=codes_codelist.codelist_uid,
        term_uid=term_b.term_uid,
        order=2,
        submission_value="CODE_B",
    )
    codelist_service.add_term(
        codelist_uid=codes_codelist.codelist_uid,
        term_uid=term_c.term_uid,
        order=3,
        submission_value="CODE_C",
    )

    # Create an unpaired codelist for the 400 error test
    global unpaired_codelist
    unpaired_codelist = TestUtils.create_ct_codelist(
        catalogue_name=CATALOGUE,
        sponsor_preferred_name="Unpaired CL",
        submission_value="UNPAIRED_CL",
        library_name="Sponsor",
        approve=True,
    )

    yield


def test_get_paired_terms_from_names_codelist(api_client):
    """Requesting paired terms using the names codelist UID should return
    all terms with both name and code submission values."""
    response = api_client.get(f"{URL}/{names_codelist.codelist_uid}/terms")
    assert_response_status_code(response, 200)

    res = response.json()
    terms = res["items"]
    assert len(terms) == 3

    # Default sort is by order ascending
    assert terms[0]["term_uid"] == term_a.term_uid
    assert terms[1]["term_uid"] == term_b.term_uid
    assert terms[2]["term_uid"] == term_c.term_uid

    assert terms[0]["name_submission_value"] == "NAME_A"
    assert terms[0]["code_submission_value"] == "CODE_A"
    assert terms[1]["name_submission_value"] == "NAME_B"
    assert terms[1]["code_submission_value"] == "CODE_B"
    assert terms[2]["name_submission_value"] == "NAME_C"
    assert terms[2]["code_submission_value"] == "CODE_C"

    assert terms[0]["sponsor_preferred_name"] == "Term A"
    assert terms[1]["sponsor_preferred_name"] == "Term B"
    assert terms[2]["sponsor_preferred_name"] == "Term C"


def test_get_paired_terms_from_codes_codelist(api_client):
    """Requesting paired terms using the codes codelist UID should return
    the same results as requesting from the names codelist."""
    response = api_client.get(f"{URL}/{codes_codelist.codelist_uid}/terms")
    assert_response_status_code(response, 200)

    terms = response.json()["items"]
    assert len(terms) == 3

    assert terms[0]["name_submission_value"] == "NAME_A"
    assert terms[0]["code_submission_value"] == "CODE_A"
    assert terms[1]["name_submission_value"] == "NAME_B"
    assert terms[1]["code_submission_value"] == "CODE_B"
    assert terms[2]["name_submission_value"] == "NAME_C"
    assert terms[2]["code_submission_value"] == "CODE_C"


def test_get_paired_terms_returns_400_for_unpaired_codelist(api_client):
    """Requesting paired terms for a codelist without a paired codelist
    should return a 400 error."""
    response = api_client.get(f"{URL}/{unpaired_codelist.codelist_uid}/terms")
    assert_response_status_code(response, 400)


def test_get_paired_terms_pagination(api_client):
    """Pagination should work correctly on the paired terms endpoint."""
    response = api_client.get(
        f"{URL}/{names_codelist.codelist_uid}/terms",
        params={"page_size": 2, "page_number": 1},
    )
    assert_response_status_code(response, 200)

    res = response.json()
    assert len(res["items"]) == 2
    assert res["items"][0]["term_uid"] == term_a.term_uid
    assert res["items"][1]["term_uid"] == term_b.term_uid

    response = api_client.get(
        f"{URL}/{names_codelist.codelist_uid}/terms",
        params={"page_size": 2, "page_number": 2},
    )
    assert_response_status_code(response, 200)

    res = response.json()
    assert len(res["items"]) == 1
    assert res["items"][0]["term_uid"] == term_c.term_uid


def test_get_paired_terms_total_count(api_client):
    """The total_count parameter should return the total number of items."""
    response = api_client.get(
        f"{URL}/{names_codelist.codelist_uid}/terms",
        params={"page_size": 2, "page_number": 1, "total_count": True},
    )
    assert_response_status_code(response, 200)

    res = response.json()
    assert len(res["items"]) == 2
    assert res["total"] == 3


def test_get_paired_terms_sort_by_name(api_client):
    """Sorting by sponsor_preferred_name descending should reverse the order."""
    response = api_client.get(
        f"{URL}/{names_codelist.codelist_uid}/terms",
        params={"sort_by": '{"sponsor_preferred_name": false}'},
    )
    assert_response_status_code(response, 200)

    terms = response.json()["items"]
    assert terms[0]["sponsor_preferred_name"] == "Term C"
    assert terms[1]["sponsor_preferred_name"] == "Term B"
    assert terms[2]["sponsor_preferred_name"] == "Term A"
