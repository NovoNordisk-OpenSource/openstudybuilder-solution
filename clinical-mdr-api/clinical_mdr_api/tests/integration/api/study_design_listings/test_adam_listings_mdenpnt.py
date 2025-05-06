"""
Tests for /studies/{study_uid}/study-endpoints endpoints
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

from clinical_mdr_api.domain_repositories.models.syntax import (
    EndpointRoot,
    EndpointTemplateRoot,
    ObjectiveRoot,
    ObjectiveTemplateRoot,
    TimeframeRoot,
    TimeframeTemplateRoot,
)
from clinical_mdr_api.main import app
from clinical_mdr_api.models.listings.listings_adam import StudyEndpntAdamListing
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_ENDPOINT_CYPHER,
    STARTUP_STUDY_OBJECTIVE_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)
study: Study
objective_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "ADAMMDENDPNTListingTest"
    inject_and_clear_db(db_name)
    inject_base_data()
    global study
    study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=study.uid)
    TestUtils.create_study_fields_configuration()

    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_OBJECTIVE_CYPHER)
    db.cypher_query(STARTUP_STUDY_ENDPOINT_CYPHER)
    ObjectiveTemplateRoot.generate_node_uids_if_not_present()
    ObjectiveRoot.generate_node_uids_if_not_present()
    EndpointTemplateRoot.generate_node_uids_if_not_present()
    EndpointRoot.generate_node_uids_if_not_present()
    TimeframeTemplateRoot.generate_node_uids_if_not_present()
    TimeframeRoot.generate_node_uids_if_not_present()

    yield


def test_adam_listing_mdendpnt(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-objectives",
        json={
            "objective_uid": "Objective_000001",
            "objective_level_uid": "term_root_final",
        },
    )
    res = response.json()
    global objective_uid
    objective_uid = res["study_objective_uid"]
    assert_response_status_code(response, 201)

    # create en endpoint 1
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints",
        json={"endpoint_uid": "Endpoint_000001", "study_objective_uid": objective_uid},
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # create endpoint 2
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints",
        json={
            "endpoint_level_uid": "term_root_final",
            "endpoint_sublevel_uid": "term_root_final_non_edit",
            "endpoint_uid": "Endpoint_000001",
            "endpoint_units": {"separator": "string", "units": ["unit 1", "unit 2"]},
            "timeframe_uid": "Timeframe_000001",
            "study_objective_uid": objective_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # get all endpoints
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)

    response = api_client.get(
        "/listings/studies/Study_000002/adam/mdendpnt/",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    res_objectives = response.json()["items"]
    assert res is not None

    expected_output = StudyEndpntAdamListing(
        STUDYID="Study_000002",
        OBJTVLVL="term_value_name1",
        OBJTV="objective_1",
        OBJTVPT="objective_1",
        ENDPNTLVL="term_value_name1",
        ENDPNTSL="term_value_name3",
        ENDPNT="endpoint_1",
        ENDPNTPT="endpoint_1",
        UNITDEF=None,
        UNIT=None,
        TMFRM="timeframe_1",
        TMFRMPT="timeframe_1",
        RACT=[],
        RACTSGRP=[],
        RACTGRP=[],
        RACTINST=[],
    ).model_dump()
    assert res[0] == expected_output

    # headers endpoint testing
    field_name = "OBJTVLVL"
    expected_result = []  # building expected result
    for res_objective in res_objectives:
        value = res_objective[field_name]
        if value:
            expected_result.append(value)
    url = "/listings/studies/Study_000002/adam/mdendpnt"
    response = api_client.get(f"{url}/headers?field_name={field_name}&page_size=100")
    res_headers = response.json()

    assert_response_status_code(response, 200)
    log.info("Returned %s", res_headers)
    log.info("Expected result is %s", expected_result)
    if expected_result:
        assert len(res_headers) > 0
        assert len(set(expected_result)) == len(res_headers)
        assert all(item in res_headers for item in expected_result)
    else:
        assert len(res_headers) == 0


def test_adam_listing_mdendpnt_versioning(api_client):
    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/listings/studies/{study.uid}/adam/mdendpnt/",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None
    md_endpnt_before_unlock = res

    # get study endpoint headers
    response = api_client.get(
        f"/listings/studies/{study.uid}/adam/mdendpnt/headers?field_name=OBJTVLVL",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    md_endpnt_headers_before_unlock = res

    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert_response_status_code(response, 200)

    # edit study endpoint
    response = api_client.patch(
        f"/studies/{study.uid}/study-endpoints/StudyEndpoint_000001",
        json={
            "endpoint_uid": "Endpoint_000001",
            "endpoint_level_uid": "term_root_final5",
        },
    )
    res = response.json()
    assert res["endpoint_level"]["term_uid"] == "term_root_final5"
    assert_response_status_code(response, 200)

    # get all study mdendpts of a specific study version
    response = api_client.get(
        f"/listings/studies/{study.uid}/adam/mdendpnt",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"][1]["ENDPNTLVL"] == "term_value_name1"

    # get all mdendpts of a specific study version
    response = api_client.get(
        f"/listings/studies/{study.uid}/adam/mdendpnt?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"] == md_endpnt_before_unlock
    assert res["items"][1]["ENDPNTLVL"] is None

    # get mdendpt headers
    response = api_client.get(
        f"/listings/studies/{study.uid}/adam/mdendpnt/headers?field_name=OBJTVLVL",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert "term_value_name1" in res

    # get study mdendpt headers
    response = api_client.get(
        f"/listings/studies/{study.uid}/adam/mdendpnt/headers?field_name=OBJTVLVL&study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == md_endpnt_headers_before_unlock
