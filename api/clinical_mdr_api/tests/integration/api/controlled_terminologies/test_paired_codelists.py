"""
Tests for sponsor ct package
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

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
catalogue: str

URL = "/ct/codelists"
PAIRED_URL = "/ct/paired-codelists"


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "ct-paired-codelists.api"
    inject_and_clear_db(db_name)
    inject_base_data(inject_unit_subset=False)

    global catalogue
    catalogue = "SDTM CT"
    yield


def test_get_paired_codelist(api_client):
    codes_cl = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="prelinked codes codelist",
        library_name="Sponsor",
        approve=True,
    )
    names_cl = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="prelinked names codelist",
        library_name="Sponsor",
        approve=True,
        paired_codes_codelist_uid=codes_cl.codelist_uid,
    )

    # Check the codelist with names
    response = api_client.get(f"{URL}/{names_cl.codelist_uid}/paired")
    assert_response_status_code(response, 200)
    response_json = response.json()
    assert response_json["codes"]["codelist_uid"] == codes_cl.codelist_uid
    assert response_json["names"] is None

    response = api_client.get(
        URL,
        params={
            "filters": json.dumps(
                {"codelist_uid": {"v": [names_cl.codelist_uid], "op": "eq"}}
            )
        },
    )
    assert_response_status_code(response, 200)
    response_json = response.json()
    print(response_json)
    assert len(response_json["items"]) == 1
    assert response_json["items"][0]["paired_codelist"]["uid"] == codes_cl.codelist_uid
    assert response_json["items"][0]["paired_codelist"]["name"] is not None

    # Check the codelist with codes
    response = api_client.get(f"{URL}/{codes_cl.codelist_uid}/paired")
    assert_response_status_code(response, 200)
    response_json = response.json()
    assert response_json["names"]["codelist_uid"] == names_cl.codelist_uid
    assert response_json["codes"] is None

    response = api_client.get(
        URL,
        params={
            "filters": json.dumps(
                {"codelist_uid": {"v": [codes_cl.codelist_uid], "op": "eq"}}
            )
        },
    )
    assert_response_status_code(response, 200)
    response_json = response.json()
    print(response_json)
    assert len(response_json["items"]) == 1
    assert response_json["items"][0]["paired_codelist"]["uid"] == names_cl.codelist_uid
    assert response_json["items"][0]["paired_codelist"]["name"] is not None


def test_get_all_codelists_sort_and_filter_by_paired_codelist_name(api_client):
    """
    Regression test: sorting/filtering the codelists listing by `paired_codelist.name`
    (the "Paired with" column in the frontend table) used to raise an error because
    that key had no mapping to a Cypher alias.
    """
    codes_cl = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="sort filter codes codelist",
        library_name="Sponsor",
        approve=True,
    )
    names_cl = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="sort filter names codelist",
        library_name="Sponsor",
        approve=True,
        paired_codes_codelist_uid=codes_cl.codelist_uid,
    )

    response = api_client.get(
        URL,
        params={"sort_by": '{"paired_codelist.name": true}'},
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        URL,
        params={
            "filters": json.dumps(
                {
                    "paired_codelist.name": {
                        "v": [codes_cl.name],
                        "op": "eq",
                    }
                }
            )
        },
    )
    assert_response_status_code(response, 200)
    response_json = response.json()
    assert len(response_json["items"]) == 1
    assert response_json["items"][0]["codelist_uid"] == names_cl.codelist_uid
    assert response_json["items"][0]["paired_codelist"]["uid"] == codes_cl.codelist_uid


def test_post_paired_codelist(api_client):
    codes_cl = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="premade codes codelist",
        library_name="Sponsor",
        approve=True,
    )
    response = api_client.post(
        URL,
        json={
            "name": "posted names codelist",
            "definition": "This is a test codelist",
            "sponsor_preferred_name": "posted names codelist",
            "catalogue_names": [catalogue],
            "library_name": "Sponsor",
            "paired_codes_codelist_uid": codes_cl.codelist_uid,
            "submission_value": "DUMMYNAMES",
            "extensible": True,
            "is_ordinal": False,
            "template_parameter": False,
            "terms": [],
        },
    )
    assert_response_status_code(response, 201)
    names_cl = response.json()

    response = api_client.get(f"{URL}/{names_cl['codelist_uid']}/paired")
    assert_response_status_code(response, 200)
    response_json = response.json()
    assert response_json["codes"]["codelist_uid"] == codes_cl.codelist_uid
    assert response_json["names"] is None


def test_add_paired_codelist(api_client):
    codes_cl = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="unlinked codes codelist",
        library_name="Sponsor",
        approve=True,
    )
    names_cl = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="unlinked names codelist",
        library_name="Sponsor",
        approve=True,
    )

    response = api_client.patch(
        f"{URL}/{names_cl.codelist_uid}/paired",
        json={
            "paired_codes_codelist_uid": codes_cl.codelist_uid,
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"{URL}/{names_cl.codelist_uid}/paired")
    assert_response_status_code(response, 200)
    response_json = response.json()
    assert response_json["codes"]["codelist_uid"] == codes_cl.codelist_uid
    assert response_json["names"] is None

    response = api_client.get(f"{URL}/{codes_cl.codelist_uid}/paired")
    assert_response_status_code(response, 200)
    response_json = response.json()
    assert response_json["names"]["codelist_uid"] == names_cl.codelist_uid
    assert response_json["codes"] is None


def test_unlink_paired_codelists(api_client):
    codes_cl = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="to unlinked codes codelist",
        library_name="Sponsor",
        approve=True,
    )
    names_cl = TestUtils.create_ct_codelist(
        catalogue_name=catalogue,
        name="to unlinked names codelist",
        library_name="Sponsor",
        approve=True,
        paired_codes_codelist_uid=codes_cl.codelist_uid,
    )

    response = api_client.patch(
        f"{URL}/{names_cl.codelist_uid}/paired",
        json={
            "paired_codes_codelist_uid": None,
            "paired_names_codelist_uid": None,
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"{URL}/{names_cl.codelist_uid}/paired")
    assert_response_status_code(response, 200)
    response_json = response.json()
    assert response_json["codes"] is None
    assert response_json["names"] is None


def test_create_paired_codelists(api_client):
    response = api_client.post(
        PAIRED_URL,
        json={
            "catalogue_names": [catalogue],
            "name_information": {
                "name": "paired names codelist",
                "submission_value": "PAIRED_NAMES_SV",
                "nci_preferred_name": "Names NCI Preferred",
                "definition": "Names codelist definition",
                "sponsor_preferred_name": "Names Sponsor Preferred",
            },
            "code_information": {
                "name": "paired codes codelist",
                "submission_value": "PAIRED_CODES_SV",
                "nci_preferred_name": "Codes NCI Preferred",
                "definition": "Codes codelist definition",
                "sponsor_preferred_name": "Codes Sponsor Preferred",
            },
            "extensible": True,
            "is_ordinal": False,
            "template_parameter": False,
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()

    # Response should have both names and codes codelists
    assert res["names"] is not None
    assert res["codes"] is not None

    names_uid = res["names"]["codelist_uid"]
    codes_uid = res["codes"]["codelist_uid"]
    assert names_uid != codes_uid

    # Verify names codelist attributes
    names_attrs = res["names"]["attributes"]
    assert names_attrs["name"] == "paired names codelist"
    assert names_attrs["submission_value"] == "PAIRED_NAMES_SV"
    assert names_attrs["nci_preferred_name"] == "Names NCI Preferred"
    assert names_attrs["definition"] == "Names codelist definition"
    names_name = res["names"]["name"]
    assert names_name["name"] == "Names Sponsor Preferred"

    # Verify codes codelist attributes
    codes_attrs = res["codes"]["attributes"]
    assert codes_attrs["name"] == "paired codes codelist"
    assert codes_attrs["submission_value"] == "PAIRED_CODES_SV"
    assert codes_attrs["nci_preferred_name"] == "Codes NCI Preferred"
    assert codes_attrs["definition"] == "Codes codelist definition"
    codes_name = res["codes"]["name"]
    assert codes_name["name"] == "Codes Sponsor Preferred"

    # Verify pairing from the names codelist side
    response = api_client.get(f"{URL}/{names_uid}/paired")
    assert_response_status_code(response, 200)
    paired = response.json()
    assert paired["codes"]["codelist_uid"] == codes_uid
    assert paired["names"] is None

    # Verify pairing from the codes codelist side
    response = api_client.get(f"{URL}/{codes_uid}/paired")
    assert_response_status_code(response, 200)
    paired = response.json()
    assert paired["names"]["codelist_uid"] == names_uid
    assert paired["codes"] is None


def test_create_paired_codelists_minimal(api_client):
    """Test creating paired codelists with minimal optional fields."""
    response = api_client.post(
        PAIRED_URL,
        json={
            "catalogue_names": [catalogue],
            "name_information": {
                "name": "minimal names codelist",
                "submission_value": "MIN_NAMES_SV",
                "definition": "Minimal names definition",
                "sponsor_preferred_name": "Min Names Sponsor",
            },
            "code_information": {
                "name": "minimal codes codelist",
                "submission_value": "MIN_CODES_SV",
                "definition": "Minimal codes definition",
                "sponsor_preferred_name": "Min Codes Sponsor",
            },
            "extensible": False,
            "is_ordinal": False,
            "template_parameter": False,
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["names"] is not None
    assert res["codes"] is not None
    assert res["names"]["attributes"]["nci_preferred_name"] is None
    assert res["codes"]["attributes"]["nci_preferred_name"] is None
