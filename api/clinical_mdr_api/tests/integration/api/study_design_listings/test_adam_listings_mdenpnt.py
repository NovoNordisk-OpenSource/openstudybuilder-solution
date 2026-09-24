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
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

log = logging.getLogger(__name__)
study: Study
objective_uid: str
test_data_dict = {}
reason_for_lock_term_uid: str
reason_for_unlock_term_uid: str


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
    _, test_data = inject_base_data()
    global reason_for_lock_term_uid
    reason_for_lock_term_uid = test_data["reason_for_lock_terms"][0].term_uid
    global reason_for_unlock_term_uid
    reason_for_unlock_term_uid = test_data["reason_for_unlock_terms"][0].term_uid
    global study
    study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=study.uid)

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

    _catalogue_name, library_name = get_catalogue_name_library_name()
    catalogue_name = "SDTM CT"

    objective_level_codelist = create_codelist(
        "Objective Level",
        "CTCodelist_ObjectiveLevel",
        catalogue_name,
        library_name,
        submission_value=settings.study_objective_level_cl_submval,
    )
    objective_level_term = create_ct_term(
        "Objective Level 1",
        "ObjectiveLevel_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": objective_level_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Objective level 1 submval",
            }
        ],
    )
    test_data_dict["objective_level_term"] = objective_level_term

    # Create a endpoint level codelist
    endpoint_level_codelist = create_codelist(
        "Endpoint Level",
        "CTCodelist_EndpointLevel",
        catalogue_name,
        library_name,
        submission_value=settings.study_endpoint_level_cl_submval,
    )
    test_data_dict["endpoint_type_codelist"] = endpoint_level_codelist
    endpoint_level_term = create_ct_term(
        "Endpoint Level 1",
        "EndpointLevel_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": endpoint_level_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Endpoint level 1 submval",
            }
        ],
    )
    test_data_dict["endpoint_level_term"] = endpoint_level_term
    endpoint_level_term_2 = create_ct_term(
        "Endpoint Level 2",
        "EndpointLevel_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": endpoint_level_codelist.codelist_uid,
                "order": 2,
                "submission_value": "Endpoint level 2 submval",
            }
        ],
    )
    test_data_dict["endpoint_level_term_2"] = endpoint_level_term_2
    # Create a endpoint sublevel codelist
    endpoint_sublevel_codelist = create_codelist(
        "Endpoint Sublevel",
        "CTCodelist_EndpointSublevel",
        catalogue_name,
        library_name,
        submission_value=settings.study_endpoint_sublevel_cl_submval,
    )
    test_data_dict["endpoint_sublevel_codelist"] = endpoint_sublevel_codelist
    endpoint_sublevel_term = create_ct_term(
        "Endpoint Sublevel 1",
        "EndpointSublevel_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": endpoint_sublevel_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Endpoint sublevel 1 submval",
            }
        ],
    )
    test_data_dict["endpoint_sublevel_term"] = endpoint_sublevel_term
    yield test_data_dict


def test_adam_listing_mdendpnt(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-objectives",
        json={
            "objective_uid": "Objective_000001",
            "objective_level_uid": test_data_dict["objective_level_term"].uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    global objective_uid
    objective_uid = res["study_objective_uid"]

    # create en endpoint 1
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints",
        json={"endpoint_uid": "Endpoint_000001", "study_objective_uid": objective_uid},
    )
    assert_response_status_code(response, 201)

    # create endpoint 2
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints",
        json={
            "endpoint_level_uid": test_data_dict["endpoint_level_term"].uid,
            "endpoint_sublevel_uid": test_data_dict["endpoint_sublevel_term"].uid,
            "endpoint_uid": "Endpoint_000001",
            "endpoint_units": {"separator": "string", "units": ["unit 1", "unit 2"]},
            "timeframe_uid": "Timeframe_000001",
            "study_objective_uid": objective_uid,
        },
    )
    assert_response_status_code(response, 201)

    # get all endpoints
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        "/listings/studies/Study_000002/adam/mdendpnt/",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    res_objectives = response.json()["items"]
    assert res is not None

    expected_output = StudyEndpntAdamListing(
        STUDYID_OBJ="Study_000002",
        OBJTVLVL="Objective Level 1",
        OBJTV="objective_1",
        OBJTVPT="objective_1",
        ENDPNTLVL="Endpoint Level 1",
        ENDPNTSL="Endpoint Sublevel 1",
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
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": reason_for_lock_term_uid,
        },
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
    response = api_client.post(
        f"/studies/{study.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )
    assert_response_status_code(response, 201)
    # edit study endpoint
    response = api_client.patch(
        f"/studies/{study.uid}/study-endpoints/StudyEndpoint_000001",
        json={
            "endpoint_uid": "Endpoint_000001",
            "endpoint_level_uid": test_data_dict["endpoint_level_term_2"].uid,
        },
    )
    res = response.json()
    assert (
        res["endpoint_level"]["term_uid"] == test_data_dict["endpoint_level_term_2"].uid
    )
    assert_response_status_code(response, 200)

    # get all study mdendpts of a specific study version
    response = api_client.get(
        f"/listings/studies/{study.uid}/adam/mdendpnt",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"][1]["ENDPNTLVL"] == "Endpoint Level 2"

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
    assert "Objective Level 1" in res

    # get study mdendpt headers
    response = api_client.get(
        f"/listings/studies/{study.uid}/adam/mdendpnt/headers?field_name=OBJTVLVL&study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == md_endpnt_headers_before_unlock
