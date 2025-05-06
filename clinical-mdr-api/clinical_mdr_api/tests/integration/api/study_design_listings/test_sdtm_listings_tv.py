"""
Tests for /listings/studies/all/adam/ endpoints
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
from clinical_mdr_api.models.listings.listings_sdtm import StudyVisitListing
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_library_data,
    create_some_visits,
    generate_study_root,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import CDISC_LIBRARY_NAME, SDTM_CT_CATALOGUE_NAME

study_uid: str

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    global study_uid
    study_uid = "study_root"
    inject_and_clear_db("SDTMTVListingTest.api")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    create_library_data()
    generate_study_root()
    create_some_visits()
    TestUtils.create_study_fields_configuration()
    # Creating codelists, library and catalogue for study standard version
    TestUtils.create_library(name=CDISC_LIBRARY_NAME, is_editable=True)
    TestUtils.create_ct_catalogue(
        library=CDISC_LIBRARY_NAME, catalogue_name=SDTM_CT_CATALOGUE_NAME
    )
    TestUtils.create_ct_codelists_using_cypher()
    TestUtils.set_study_standard_version(study_uid=study_uid)
    fix_study_preferred_time_unit(study_uid=study_uid)


def test_tv_listing(api_client):
    response = api_client.get(
        "/listings/studies/study_root/sdtm/tv",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None

    expected_output = [
        StudyVisitListing(
            STUDYID="SOME_ID-0",
            DOMAIN="TV",
            VISITNUM=100,
            VISIT="VISIT 1",
            VISITDY=1,
            ARMCD=None,
            ARM=None,
            TVSTRL="START_RULE",
            TVENRL="END_RULE",
        ).model_dump(),
        StudyVisitListing(
            STUDYID="SOME_ID-0",
            DOMAIN="TV",
            VISITNUM=200,
            VISIT="VISIT 2",
            VISITDY=11,
            ARMCD=None,
            ARM=None,
            TVSTRL="START_RULE",
            TVENRL="END_RULE",
        ).model_dump(),
        StudyVisitListing(
            STUDYID="SOME_ID-0",
            DOMAIN="TV",
            VISITNUM=300,
            VISIT="VISIT 3",
            VISITDY=13,
            ARMCD=None,
            ARM=None,
            TVSTRL="START_RULE",
            TVENRL="END_RULE",
        ).model_dump(),
        StudyVisitListing(
            STUDYID="SOME_ID-0",
            DOMAIN="TV",
            VISITNUM=400,
            VISIT="VISIT 4",
            VISITDY=31,
            ARMCD=None,
            ARM=None,
            TVSTRL="START_RULE",
            TVENRL="END_RULE",
        ).model_dump(),
        StudyVisitListing(
            STUDYID="SOME_ID-0",
            DOMAIN="TV",
            VISITNUM=410,
            VISIT="VISIT 4",
            VISITDY=62,
            ARMCD=None,
            ARM=None,
            TVSTRL="START_RULE",
            TVENRL="END_RULE",
        ).model_dump(),
        StudyVisitListing(
            STUDYID="SOME_ID-0",
            DOMAIN="TV",
            VISITNUM=500,
            VISIT="VISIT 5",
            VISITDY=36,
            ARMCD=None,
            ARM=None,
            TVSTRL="START_RULE",
            TVENRL="END_RULE",
        ).model_dump(),
    ]
    assert res == expected_output


def test_tv_listing_versioning(api_client):
    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study_uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study_uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        "/listings/studies/study_root/sdtm/tv",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None
    tv_before_unlock = res

    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study_uid}/locks")
    assert_response_status_code(response, 200)

    # get all visits
    response = api_client.get(
        f"/studies/{study_uid}/study-visits/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res

    # edit study visit
    response = api_client.patch(
        f"/studies/{study_uid}/study-visits/{old_res[0]['uid']}",
        json={
            "show_visit": False,
            "time_unit_uid": "UnitDefinition_000002",
            "time_value": 0,
            "visit_contact_mode_uid": "VisitContactMode_0001",
            "visit_type_uid": "VisitType_0002",
            "time_reference_uid": "VisitSubType_0002",
            "is_global_anchor_visit": False,
            "visit_class": "SINGLE_VISIT",
            "study_epoch_uid": "StudyEpoch_000001",
            "uid": old_res[0]["uid"],
            "study_uid": study_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_type_uid"] == "VisitType_0002"

    # edit study visit
    response = api_client.delete(
        f"/studies/{study_uid}/study-visits/{old_res[1]['uid']}",
    )
    assert_response_status_code(response, 204)

    # get all study visits of a specific study version
    response = api_client.get(
        f"/listings/studies/{study_uid}/sdtm/tv?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"] == tv_before_unlock

    response = api_client.get(
        "/listings/studies/study_root/sdtm/tv",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert len(res) == 5
