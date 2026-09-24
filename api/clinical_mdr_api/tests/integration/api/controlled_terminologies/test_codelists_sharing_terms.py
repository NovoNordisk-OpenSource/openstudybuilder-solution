"""
Tests for sponsor ct package
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

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
from clinical_mdr_api.tests.integration.utils.utils import (
    CDISC_LIBRARY_NAME,
    CT_CATALOGUE_NAME,
    SPONSOR_LIBRARY_NAME,
    TestUtils,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

CDASH_CATALOGUE_NAME = "CDASH CT"

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
# Legacy variables for existing tests
sponsor_codelist_a: CTCodelist
sponsor_codelist_b: CTCodelist
sponsor_term_a: CTTerm
sponsor_term_b: CTTerm
sponsor_term_c: CTTerm

# CDISC test data
cdisc_codelist_1: CTCodelist
cdisc_codelist_2: CTCodelist
cdisc_term_in_one: CTTerm
cdisc_term_in_both: CTTerm

# Sponsor test data
sponsor_codelist_unpaired_1: CTCodelist
sponsor_codelist_unpaired_2: CTCodelist
# Cross-catalogue test data
sponsor_codelist_cdash: CTCodelist
sponsor_term_for_cross_catalogue: CTTerm
sponsor_codelist_paired_cd: CTCodelist
sponsor_codelist_paired_name: CTCodelist
sponsor_term_in_unpaired_1: CTTerm
sponsor_term_in_paired_name: CTTerm
sponsor_term_in_paired_code: CTTerm

URL = "/ct/codelists"


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "ct-codelists-sharing-terms.api"
    inject_and_clear_db(db_name)
    inject_base_data(inject_unit_subset=False)

    catalogue = CT_CATALOGUE_NAME
    sponsor_library = SPONSOR_LIBRARY_NAME
    cdisc_library = CDISC_LIBRARY_NAME

    # Legacy test data for existing tests
    global sponsor_codelist_a
    sponsor_codelist_a = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="Codelist A",
        library_name=sponsor_library,
        approve=True,
        extensible=True,
    )
    global sponsor_codelist_b
    sponsor_codelist_b = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="Codelist B",
        library_name=sponsor_library,
        approve=True,
        extensible=True,
    )
    global sponsor_term_a
    sponsor_term_a = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_a.codelist_uid,
        sponsor_preferred_name="Term A",
        submission_value="A",
        library_name=sponsor_library,
        approve=True,
    )
    global sponsor_term_b
    sponsor_term_b = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_b.codelist_uid,
        sponsor_preferred_name="Term B",
        submission_value="B",
        library_name=sponsor_library,
        approve=True,
    )
    global sponsor_term_c
    sponsor_term_c = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_a.codelist_uid,
        sponsor_preferred_name="Term C",
        submission_value="C",
        library_name=sponsor_library,
        approve=True,
    )

    # CDISC test data
    global cdisc_codelist_1
    cdisc_codelist_1 = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="CDISC Codelist 1",
        library_name=cdisc_library,
        approve=True,
        extensible=True,
    )
    global cdisc_codelist_2
    cdisc_codelist_2 = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="CDISC Codelist 2",
        library_name=cdisc_library,
        approve=True,
        extensible=True,
    )

    # CDISC Term in one codelist
    global cdisc_term_in_one
    cdisc_term_in_one = TestUtils.create_ct_term(
        codelist_uid=cdisc_codelist_1.codelist_uid,
        sponsor_preferred_name="CDISC Term Single",
        submission_value="CDISC_SINGLE",
        library_name=cdisc_library,
        approve=True,
    )

    # CDISC Term in both codelists with different submission values
    global cdisc_term_in_both
    cdisc_term_in_both = TestUtils.create_ct_term(
        codelist_uid=cdisc_codelist_1.codelist_uid,
        sponsor_preferred_name="CDISC Term Both",
        submission_value="CDISC_BOTH_1",
        library_name=cdisc_library,
        approve=True,
    )
    # Add term to second CT codelist with a different submission value
    # Use Cypher because the API will reject such an action
    db.cypher_query(
        """
        MATCH (t:CTTermRoot {uid:$term_uid})
        MATCH (cl:CTCodelistRoot {uid:$codelist_uid})
        CREATE (cct:CTCodelistTerm {submission_value:$submission_value})
        CREATE (t)<-[:HAS_TERM_ROOT]-(cct)<-[:HAS_TERM]-(cl)
    """,
        {
            "term_uid": cdisc_term_in_both.term_uid,
            "codelist_uid": cdisc_codelist_2.codelist_uid,
            "submission_value": "CDISC_BOTH_2",
        },
    )

    # Sponsor test data
    # Unpaired sponsor codelists
    global sponsor_codelist_unpaired_1
    sponsor_codelist_unpaired_1 = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="Sponsor Unpaired 1",
        library_name=sponsor_library,
        approve=True,
        extensible=True,
    )
    global sponsor_codelist_unpaired_2
    sponsor_codelist_unpaired_2 = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="Sponsor Unpaired 2",
        library_name=sponsor_library,
        approve=True,
        extensible=True,
    )

    # Paired sponsor codelists
    global sponsor_codelist_paired_cd
    sponsor_codelist_paired_cd = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="Sponsor Paired_cd",
        library_name=sponsor_library,
        approve=True,
        extensible=True,
    )
    global sponsor_codelist_paired_name
    sponsor_codelist_paired_name = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="Sponsor Paired",
        library_name=sponsor_library,
        approve=True,
        extensible=True,
        paired_codes_codelist_uid=sponsor_codelist_paired_cd.codelist_uid,
    )

    # Sponsor term in the first unpaired codelist
    global sponsor_term_in_unpaired_1
    sponsor_term_in_unpaired_1 = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_unpaired_1.codelist_uid,
        sponsor_preferred_name="Sponsor Term Unpaired 1",
        submission_value="SPONSOR_UNPAIRED_1",
        library_name=sponsor_library,
        approve=True,
    )

    # Sponsor term in the name codelist of name-code pair
    global sponsor_term_in_paired_name
    sponsor_term_in_paired_name = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_paired_name.codelist_uid,
        sponsor_preferred_name="Sponsor Term Paired name",
        submission_value="SPONSOR_PAIRED",
        library_name=sponsor_library,
        approve=True,
    )
    # Sponsor term in the code codelist of name-code pair
    global sponsor_term_in_paired_code
    sponsor_term_in_paired_code = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_paired_cd.codelist_uid,
        sponsor_preferred_name="Sponsor Term Paired code 2",
        submission_value="SPONSOR_PAIRED_2",
        library_name=sponsor_library,
        approve=True,
    )

    # Cross-catalogue test data
    TestUtils.create_ct_catalogue(
        library=sponsor_library,
        catalogue_name=CDASH_CATALOGUE_NAME,
    )
    global sponsor_codelist_cdash
    sponsor_codelist_cdash = TestUtils.create_ct_codelist(
        catalogue_name=CDASH_CATALOGUE_NAME,
        name="Sponsor CDASH Codelist",
        library_name=sponsor_library,
        approve=True,
        extensible=True,
    )
    global sponsor_term_for_cross_catalogue
    sponsor_term_for_cross_catalogue = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_unpaired_1.codelist_uid,
        sponsor_preferred_name="Sponsor Term Cross Catalogue",
        submission_value="SDTM_SUBVAL",
        library_name=sponsor_library,
        approve=True,
    )

    TestUtils.edit_library_editable(cdisc_library, is_editable=False)

    yield


def test_duplicated_submission_value(api_client):
    # Test that adding a term with the same submission value
    # as another one in the codelist returns a 409 conflict error
    sponsor_term_a_duplicate = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_b.codelist_uid,
        sponsor_preferred_name="Term A - Duplicate",
        submission_value="A",
        library_name="Sponsor",
        approve=True,
    )
    response = api_client.post(
        f"{URL}/{sponsor_codelist_a.codelist_uid}/terms",
        json={
            "term_uid": sponsor_term_a_duplicate.term_uid,
            "order": 2,
            "submission_value": "A",
        },
    )
    assert_response_status_code(response, 409)
    response_json = response.json()
    assert "already has a Term with submission value 'A'" in response_json["message"]


def test_existing_submission_value(api_client):
    # Test that it is possible to add an existing term to a second codelist
    # with a submission value that already exists in another codelist.
    response = api_client.post(
        f"{URL}/{sponsor_codelist_b.codelist_uid}/terms",
        json={"term_uid": sponsor_term_c.term_uid, "order": 2, "submission_value": "C"},
    )
    assert_response_status_code(response, 201)


def test_reuse_previous_submission_value(api_client):
    # Test that it is possible to remove a term from a codelist
    # and then reuse the same submission value for a new term in the same codelist
    term1 = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_a.codelist_uid,
        sponsor_preferred_name="Term to remove",
        submission_value="REMOVED",
        library_name="Sponsor",
        approve=True,
    )
    response = api_client.delete(
        f"{URL}/{sponsor_codelist_a.codelist_uid}/terms/{term1.term_uid}"
    )
    assert_response_status_code(response, 200)

    term2 = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_a.codelist_uid,
        sponsor_preferred_name="New term to add",
        submission_value="REMOVED",
        library_name="Sponsor",
        approve=True,
    )

    assert term2 is not None


def test_cdisc_terms_submission_value_rules(api_client):
    invalid_submission_value = "NEW_SUBVAL"
    # Add CDISC term to a codelist with new submission value ❌
    response = api_client.post(
        f"{URL}/{sponsor_codelist_unpaired_1.codelist_uid}/terms",
        json={
            "term_uid": cdisc_term_in_one.term_uid,
            "order": 2,
            "submission_value": invalid_submission_value,
        },
    )
    assert_response_status_code(response, 400)
    response_json = response.json()
    assert (
        f"Term with UID '{cdisc_term_in_one.term_uid}' belongs to a non-editable library. Cannot add a new submission value '{invalid_submission_value}'. All possible submission values are already defined."  # pylint: disable=line-too-long
        in response_json["message"]
    )

    # Add CDISC term to a codelist with same submission value ✅
    response = api_client.post(
        f"{URL}/{sponsor_codelist_unpaired_1.codelist_uid}/terms",
        json={
            "term_uid": cdisc_term_in_one.term_uid,
            "order": 2,
            "submission_value": cdisc_term_in_one.codelists[0].submission_value,
        },
    )
    assert_response_status_code(response, 201)

    # Same but for a term which has 2 submission values
    # Add CDISC term to a codelist with new submission value ❌
    response = api_client.post(
        f"{URL}/{sponsor_codelist_unpaired_1.codelist_uid}/terms",
        json={
            "term_uid": cdisc_term_in_both.term_uid,
            "order": 2,
            "submission_value": invalid_submission_value,
        },
    )
    assert_response_status_code(response, 400)
    response_json = response.json()
    assert (
        f"Term with UID '{cdisc_term_in_both.term_uid}' belongs to a non-editable library. Cannot add a new submission value '{invalid_submission_value}'. All possible submission values are already defined."  # pylint: disable=line-too-long
        in response_json["message"]
    )

    # Add CDISC term to a codelist with one of its 2 pre-existing submission values ✅
    response = api_client.post(
        f"{URL}/{sponsor_codelist_unpaired_1.codelist_uid}/terms",
        json={
            "term_uid": cdisc_term_in_both.term_uid,
            "order": 2,
            "submission_value": "CDISC_BOTH_2",
        },
    )
    assert_response_status_code(response, 201)


def test_sponsor_terms_submission_value_rules(api_client):
    # Add Sponsor term not yet in a codelist, to a codelist
    # New submission value is accepted ✅
    response = api_client.post(
        "/ct/terms",
        json={
            "catalogue_names": ["SDTM CT"],
            "codelists": [
                {
                    "codelist_uid": sponsor_codelist_unpaired_1.codelist_uid,
                    "order": 2,
                    "submission_value": "RANDOM_XXX_3000",
                }
            ],
            "definition": "new term",
            "sponsor_preferred_name": "new term",
            "sponsor_preferred_name_sentence_case": "new term",
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 201)

    invalid_submission_value = "NEW_SUBVAL"

    # Add Sponsor term to a codelist with new submission value ❌
    response = api_client.post(
        f"{URL}/{sponsor_codelist_unpaired_2.codelist_uid}/terms",
        json={
            "term_uid": sponsor_term_in_unpaired_1.term_uid,
            "order": 2,
            "submission_value": invalid_submission_value,
        },
    )
    assert_response_status_code(response, 400)
    response_json = response.json()
    assert (
        # pylint: disable=line-too-long
        f"Term with UID '{sponsor_term_in_unpaired_1.term_uid}' is already part of a codelist with submission value '{sponsor_term_in_unpaired_1.codelists[0].submission_value}'. Cannot add a new submission value '{invalid_submission_value}', except for a paired codelist or a different catalogue. Please reuse the existing submission value."
        in response_json["message"]
    )

    # Add Sponsor term to a codelist with same submission value ✅
    response = api_client.post(
        f"{URL}/{sponsor_codelist_unpaired_2.codelist_uid}/terms",
        json={
            "term_uid": sponsor_term_in_unpaired_1.term_uid,
            "order": 2,
            "submission_value": sponsor_term_in_unpaired_1.codelists[
                0
            ].submission_value,
        },
    )
    assert_response_status_code(response, 201)


def test_sponsor_terms_submission_value_rules_paired_codelists(api_client):
    name_submission_value = sponsor_term_in_paired_name.codelists[0].submission_value
    code_submission_value = f"{name_submission_value}_CD"
    # Add a term from a paired codelist with a new submission value
    # But not to the paired codelist ❌
    response = api_client.post(
        f"{URL}/{sponsor_codelist_unpaired_1.codelist_uid}/terms",
        json={
            "term_uid": sponsor_term_in_paired_name.term_uid,
            "order": 2,
            "submission_value": code_submission_value,
        },
    )
    assert_response_status_code(response, 400)
    response_json = response.json()
    assert (
        # pylint: disable=line-too-long
        f"Term with UID '{sponsor_term_in_paired_name.term_uid}' is already part of a codelist with submission value '{name_submission_value}'. Cannot add a new submission value '{code_submission_value}', except for a paired codelist or a different catalogue. Please reuse the existing submission value."
        in response_json["message"]
    )

    # Add to the paired codelist ✅
    response = api_client.post(
        f"{URL}/{sponsor_codelist_paired_cd.codelist_uid}/terms",
        json={
            "term_uid": sponsor_term_in_paired_name.term_uid,
            "order": 2,
            "submission_value": code_submission_value,
        },
    )
    assert_response_status_code(response, 201)

    # Test the other direction (add to code codelist, then name)
    code_submission_value = sponsor_term_in_paired_code.codelists[0].submission_value
    name_submission_value = f"{name_submission_value}_NAME"
    # Add a term from a paired codelist with a new submission value
    # But not to the paired codelist ❌
    response = api_client.post(
        f"{URL}/{sponsor_codelist_unpaired_1.codelist_uid}/terms",
        json={
            "term_uid": sponsor_term_in_paired_code.term_uid,
            "order": 2,
            "submission_value": name_submission_value,
        },
    )
    assert_response_status_code(response, 400)
    response_json = response.json()
    assert (
        # pylint: disable=line-too-long
        f"Term with UID '{sponsor_term_in_paired_code.term_uid}' is already part of a codelist with submission value '{code_submission_value}'. Cannot add a new submission value '{name_submission_value}', except for a paired codelist or a different catalogue. Please reuse the existing submission value."
        in response_json["message"]
    )

    # Add to the paired codelist ✅
    response = api_client.post(
        f"{URL}/{sponsor_codelist_paired_name.codelist_uid}/terms",
        json={
            "term_uid": sponsor_term_in_paired_code.term_uid,
            "order": 2,
            "submission_value": name_submission_value,
        },
    )
    assert_response_status_code(response, 201)


def test_sponsor_terms_submission_value_rules_different_catalogue(api_client):
    # Term already has submission value "SDTM_SUBVAL" in an SDTM CT codelist

    # Adding to another SDTM CT codelist with a different submission value ❌
    response = api_client.post(
        f"{URL}/{sponsor_codelist_unpaired_2.codelist_uid}/terms",
        json={
            "term_uid": sponsor_term_for_cross_catalogue.term_uid,
            "order": 2,
            "submission_value": "CDASH_SUBVAL",
        },
    )
    assert_response_status_code(response, 400)
    response_json = response.json()
    assert (
        # pylint: disable=line-too-long
        f"Term with UID '{sponsor_term_for_cross_catalogue.term_uid}' is already part of a codelist with submission value 'SDTM_SUBVAL'. Cannot add a new submission value 'CDASH_SUBVAL', except for a paired codelist or a different catalogue. Please reuse the existing submission value."
        in response_json["message"]
    )

    # Adding to a CDASH CT codelist with a different submission value ✅
    response = api_client.post(
        f"{URL}/{sponsor_codelist_cdash.codelist_uid}/terms",
        json={
            "term_uid": sponsor_term_for_cross_catalogue.term_uid,
            "order": 2,
            "submission_value": "CDASH_SUBVAL",
        },
    )
    assert_response_status_code(response, 201)

    # Adding to the same CDASH CT codelist again with the SAME submission value ✅
    # (i.e. the CDASH subval is now also a known subval for this term)
    new_term = TestUtils.create_ct_term(
        codelist_uid=sponsor_codelist_unpaired_1.codelist_uid,
        sponsor_preferred_name="Another Sponsor Term Cross Catalogue",
        submission_value="SDTM_SUBVAL_2",
        library_name=SPONSOR_LIBRARY_NAME,
        approve=True,
    )
    response = api_client.post(
        f"{URL}/{sponsor_codelist_cdash.codelist_uid}/terms",
        json={
            "term_uid": new_term.term_uid,
            "order": 3,
            "submission_value": "CDASH_SUBVAL_2",
        },
    )
    assert_response_status_code(response, 201)
