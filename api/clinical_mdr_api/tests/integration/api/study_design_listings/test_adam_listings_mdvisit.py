"""
Tests for /listings/studies/all/adam/ endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=invalid-name

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from unittest import mock

import pytest
from neomodel import db

from clinical_mdr_api.models.listings.listings_adam import StudyVisitAdamListing
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    create_reason_for_lock_unlock_terms,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    get_unit_uid_by_name,
)
from clinical_mdr_api.tests.integration.utils.factory_epoch import create_study_epoch
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_library_data,
    create_some_visits,
    generate_study_root,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

study_uid: str
reason_for_lock_term_uid: str
reason_for_unlock_term_uid: str

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    global study_uid, reason_for_lock_term_uid, reason_for_unlock_term_uid
    study_uid = "study_root"
    inject_and_clear_db("ADAMMDVISITListingTest")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    create_library_data()
    generate_study_root()
    create_some_visits()
    # Creating library and catalogue for study standard version
    TestUtils.create_library(name=settings.cdisc_library_name, is_editable=True)
    TestUtils.create_ct_catalogue(
        library=settings.cdisc_library_name,
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    TestUtils.create_ct_codelists_using_cypher()
    TestUtils.set_study_standard_version(study_uid=study_uid)
    fix_study_preferred_time_unit(study_uid)
    lock_unlock_data = create_reason_for_lock_unlock_terms()
    reason_for_lock_term_uid = lock_unlock_data["reason_for_lock_terms"][0].term_uid
    reason_for_unlock_term_uid = lock_unlock_data["reason_for_unlock_terms"][0].term_uid


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
        AVISIT="Visit 1 (day 1)",
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
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": reason_for_lock_term_uid,
        },
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
    response = api_client.post(
        f"/studies/{study_uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )
    assert_response_status_code(response, 201)

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
            "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
            "visit_type": {"term_uid": "VisitType_0002"},
            "time_reference": {"term_uid": "VisitSubType_0002"},
            "is_global_anchor_visit": False,
            "visit_class": "SINGLE_VISIT",
            "study_epoch_uid": "StudyEpoch_000001",
            "uid": old_res[0]["uid"],
            "study_uid": study_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_type"]["term_uid"] == "VisitType_0002"

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


def test_adam_with_protocol_soa_html_with_time_units(api_client):
    study_for_export = TestUtils.create_study()
    visit_to_create = generate_default_input_data_for_visit().copy()
    visit_to_create.update({"time_value": 10})
    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_export.uid
    )
    TestUtils.create_study_visit(
        study_uid=study_for_export.uid,
        study_epoch_uid=study_epoch.uid,
        **visit_to_create,
    )
    response = api_client.get(
        f"/listings/studies/{study_for_export.uid}/adam/mdvisit/",
    )
    assert response.status_code == 200
    res = response.json()["items"]
    assert res is not None

    expected_output = StudyVisitAdamListing(
        STUDYID="",
        VISTPCD="Visit Type2",
        AVISITN=100,
        AVISIT="Visit 1 (week 11)",
        AVISIT1N=71,
        VISLABEL="V1",
        AVISIT1="Day 71",
        AVISIT2="Week 11",
        AVISIT2N="11",
    )
    # pylint: disable=invalid-name
    expected_output.STUDYID = mock.ANY
    assert res[0] == expected_output.model_dump()
    day_uid = get_unit_uid_by_name("day")
    response = api_client.patch(
        f"/studies/{study_for_export.uid}/time-units?for_protocol_soa=true",
        json={"unit_definition_uid": day_uid},
    )
    res = response.json()
    assert response.status_code == 200
    assert res["time_unit_name"] == "day"

    response = api_client.get(
        f"/listings/studies/{study_for_export.uid}/adam/mdvisit/",
    )
    assert response.status_code == 200
    res = response.json()["items"]
    assert res is not None
    expected_output = StudyVisitAdamListing(
        STUDYID="",
        VISTPCD="Visit Type2",
        AVISITN=100,
        AVISIT="Visit 1 (day 71)",
        AVISIT1N=71,
        VISLABEL="V1",
        AVISIT1="Day 71",
        AVISIT2="Week 11",
        AVISIT2N="11",
    )
    expected_output.STUDYID = mock.ANY  # pylint: disable=invalid-name
    assert res[0] == expected_output.model_dump()
