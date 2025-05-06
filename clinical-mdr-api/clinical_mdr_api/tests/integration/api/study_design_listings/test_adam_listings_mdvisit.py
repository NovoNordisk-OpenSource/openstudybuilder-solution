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
from neomodel import db

from clinical_mdr_api.models.listings.listings_adam import StudyVisitAdamListing
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
def test_data():
    """Initialize test data"""
    global study_uid
    study_uid = "study_root"
    inject_and_clear_db("ADAMMDVISITListingTest")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    create_library_data()
    generate_study_root()
    create_some_visits()
    TestUtils.create_study_fields_configuration()
    # Creating library and catalogue for study standard version
    TestUtils.create_library(name=CDISC_LIBRARY_NAME, is_editable=True)
    TestUtils.create_ct_catalogue(
        library=CDISC_LIBRARY_NAME, catalogue_name=SDTM_CT_CATALOGUE_NAME
    )
    TestUtils.create_ct_codelists_using_cypher()
    TestUtils.set_study_standard_version(study_uid=study_uid)
    fix_study_preferred_time_unit(study_uid)


def test_adam_listing_mdvisit(api_client, test_data):
    response = api_client.get(
        "/listings/studies/study_root/adam/mdvisit/",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None
    res_visits = response.json()["items"]

    expected_output = StudyVisitAdamListing(
        STUDYID="SOME_ID-0",
        VISTPCD="BASELINE",
        AVISITN=100,
        AVISIT="VISIT 1",
        AVISIT1N=1,
        VISLABEL="V1",
        AVISIT1="Day 1",
        AVISIT2="Week 1",
        AVISIT2N="1",
    ).model_dump()
    assert res[0] == expected_output

    # headers endpoint testing
    field_name = "AVISIT"
    expected_result = []  # building expected result
    for res_visit in res_visits:
        value = res_visit[field_name]
        if value:
            expected_result.append(value)
    url = "/listings/studies/study_root/adam/mdvisit"
    response = api_client.get(f"{url}/headers?field_name={field_name}&page_size=100")
    res_headers = response.json()

    assert_response_status_code(response, 200)
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res_headers)
    if expected_result:
        assert len(res_headers) > 0
        assert len(set(expected_result)) == len(res_headers)
        assert all(item in res_headers for item in expected_result)
    else:
        assert len(res_headers) == 0


def test_adam_listing_mdvisit_versioning(api_client, test_data):
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
        f"/listings/studies/{study_uid}/adam/mdvisit/",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None
    md_visit_before_unlock = res

    # get study visit headers
    response = api_client.get(
        f"/listings/studies/{study_uid}/adam/mdvisit/headers?field_name=VISTPCD",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    md_visit_headers_before_unlock = res

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

    # get all study visits of a specific study version
    response = api_client.get(
        f"/listings/studies/{study_uid}/adam/mdvisit?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"] == md_visit_before_unlock
    assert res["items"][0]["VISTPCD"] == "BASELINE"

    # get study visit headers
    response = api_client.get(
        f"/listings/studies/{study_uid}/adam/mdvisit/headers?field_name=VISTPCD&study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == md_visit_headers_before_unlock
