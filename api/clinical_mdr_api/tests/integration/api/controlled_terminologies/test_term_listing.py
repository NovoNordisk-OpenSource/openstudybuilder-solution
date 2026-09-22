"""
Tests for listing terms with filtering
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import json
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
codelist_a: CTCodelist
term_a: CTTerm
term_b: CTTerm
term_c: CTTerm
term_d: CTTerm

URL = "/ct/terms"


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "ct-term-listing.api"
    inject_and_clear_db(db_name)
    inject_base_data(inject_unit_subset=False)

    catalogue = "SDTM CT"
    global codelist_a
    codelist_a = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        codelist_uid="CtCodelistA",
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
        definition="Term A definition",
        submission_value="submvalA",
        order=6,
        library_name="Sponsor",
        approve=True,
    )
    global term_b
    term_b = TestUtils.create_ct_term(
        codelist_uid=codelist_a.codelist_uid,
        sponsor_preferred_name="Term B",
        definition="Term B definition",
        submission_value="submvalB",
        order=5,
        library_name="Sponsor",
        approve=True,
    )
    global term_c
    term_c = TestUtils.create_ct_term(
        codelist_uid=codelist_a.codelist_uid,
        sponsor_preferred_name="Term C",
        definition="Term C definition",
        submission_value="submvalC",
        order=4,
        library_name="Sponsor",
        approve=True,
    )
    global term_d
    term_d = TestUtils.create_ct_term(
        codelist_uid=codelist_a.codelist_uid,
        sponsor_preferred_name="Term D",
        definition="Term D definition",
        submission_value="D",
        order=3,
        library_name="Sponsor",
        approve=True,
    )
    # Remove term D from the codelist
    TestUtils.remove_term_from_codelist(term_d.term_uid, codelist_a.codelist_uid)

    yield


@pytest.mark.parametrize(
    "filters",
    [
        pytest.param(
            json.dumps({"codelists.codelist_submission_value": {"v": [None]}})
        ),
        pytest.param(json.dumps({"codelists.codelist_name": {"v": [None]}})),
        pytest.param(json.dumps({"codelists.codelist_uid": {"v": [None]}})),
        pytest.param(json.dumps({"codelists.codelist_concept_id": {"v": [None]}})),
        pytest.param(json.dumps({"codelists.submission_value": {"v": [None]}})),
    ],
)
def test_list_terms_not_in_any_codelist(api_client, filters):
    response = api_client.get(f"{URL}", params={"filters": filters})
    assert_response_status_code(response, 200)

    terms = response.json()["items"]
    assert len(terms) == 1
    assert terms[0]["term_uid"] == term_d.term_uid


@pytest.mark.parametrize(
    "filters",
    [
        pytest.param(
            json.dumps({"codelists.codelist_submission_value": {"v": ["CL_A"]}})
        ),
        pytest.param(json.dumps({"codelists.codelist_name": {"v": ["Codelist A"]}})),
        pytest.param(json.dumps({"codelists.codelist_uid": {"v": ["CtCodelistA"]}})),
    ],
)
def test_list_terms_in_a_codelist(api_client, filters):
    response = api_client.get(f"{URL}", params={"filters": filters})
    assert_response_status_code(response, 200)

    terms = response.json()["items"]
    assert len(terms) == 3
    term_uids = set(term["term_uid"] for term in terms)
    assert term_uids == {term_a.term_uid, term_b.term_uid, term_c.term_uid}


@pytest.mark.parametrize(
    "filters",
    [
        pytest.param(
            json.dumps({"codelists.submission_value": {"v": ["submvalB"], "op": "eq"}})
        ),
        pytest.param(
            json.dumps({"name.sponsor_preferred_name": {"v": ["Term B"], "op": "eq"}})
        ),
        pytest.param(
            json.dumps(
                {"attributes.definition": {"v": ["Term B definition"], "op": "eq"}}
            )
        ),
    ],
)
def test_get_single_term(api_client, filters):
    response = api_client.get(f"{URL}", params={"filters": filters})
    assert_response_status_code(response, 200)

    terms = response.json()["items"]
    print(json.dumps(terms, indent=2))
    assert len(terms) == 1
    assert terms[0]["term_uid"] == term_b.term_uid
