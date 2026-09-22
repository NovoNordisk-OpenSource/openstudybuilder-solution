"""
Tests for listing terms in a codelist
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
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
codelist_a: CTCodelist
term_a: CTTerm
term_b: CTTerm
term_c: CTTerm

URL = "/ct/codelists"


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "ct-codelist-term-listing.api"
    inject_and_clear_db(db_name)
    inject_base_data(inject_unit_subset=False)

    catalogue = "SDTM CT"
    global codelist_a
    codelist_a = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        sponsor_preferred_name="Codelist A",
        submission_value="CL_A",
        library_name="Sponsor",
        approve=True,
        extensible=True,
    )
    global term_a
    term_a = TestUtils.create_ct_term(
        codelist_uid=codelist_a.codelist_uid,
        sponsor_preferred_name="Term A",
        submission_value="A",
        order=6,
        library_name="Sponsor",
        approve=True,
    )
    global term_b
    term_b = TestUtils.create_ct_term(
        codelist_uid=codelist_a.codelist_uid,
        sponsor_preferred_name="Term B",
        submission_value="B",
        order=5,
        library_name="Sponsor",
        approve=True,
    )
    global term_c
    term_c = TestUtils.create_ct_term(
        codelist_uid=codelist_a.codelist_uid,
        sponsor_preferred_name="Term C",
        submission_value="C",
        order=4,
        library_name="Sponsor",
        approve=True,
    )
    yield


def assert_terms(terms):
    assert len(terms) == 3
    assert terms[0]["term_uid"] == term_c.term_uid
    assert terms[1]["term_uid"] == term_b.term_uid
    assert terms[2]["term_uid"] == term_a.term_uid
    assert terms[0]["sponsor_preferred_name"] == "Term C"
    assert terms[1]["sponsor_preferred_name"] == "Term B"
    assert terms[2]["sponsor_preferred_name"] == "Term A"
    assert terms[0]["submission_value"] == "C"
    assert terms[1]["submission_value"] == "B"
    assert terms[2]["submission_value"] == "A"
    assert terms[0]["order"] == 4
    assert terms[1]["order"] == 5
    assert terms[2]["order"] == 6


def test_list_terms(api_client):
    response = api_client.get(f"{URL}/{codelist_a.codelist_uid}/terms")
    assert_response_status_code(response, 200)

    terms = response.json()["items"]
    assert_terms(terms)


def test_list_terms_sort_by_name(api_client):
    response = api_client.get(
        f"{URL}/{codelist_a.codelist_uid}/terms",
        params={"sort_by": '{"sponsor_preferred_name": true}'},
    )
    assert_response_status_code(response, 200)

    terms = response.json()["items"]
    assert terms[0]["sponsor_preferred_name"] == "Term A"
    assert terms[1]["sponsor_preferred_name"] == "Term B"
    assert terms[2]["sponsor_preferred_name"] == "Term C"


def test_list_terms_for_cl_submval(api_client):
    response = api_client.get(
        f"{URL}/terms", params={"codelist_submission_value": "CL_A"}
    )
    assert_response_status_code(response, 200)

    terms = response.json()["items"]
    assert_terms(terms)


def test_list_terms_for_cl_name(api_client):
    response = api_client.get(f"{URL}/terms", params={"codelist_name": "Codelist A"})
    assert_response_status_code(response, 200)

    terms = response.json()["items"]
    assert_terms(terms)


def test_list_terms_for_cl_uid(api_client):
    response = api_client.get(
        f"{URL}/terms", params={"codelist_uid": codelist_a.codelist_uid}
    )
    assert_response_status_code(response, 200)

    terms = response.json()["items"]
    assert_terms(terms)
