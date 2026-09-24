"""
Tests for /studies/{study_uid}/study-endpoints endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from datetime import datetime, timezone
from typing import Any
from unittest import mock

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
from clinical_mdr_api.domains.enums import ValidationMode
from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies import ct_term
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.api.study_selections.utils import (
    ct_term_retrieval_at_date_test_common,
)
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
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

log = logging.getLogger(__name__)
study: Study
endpoint_uid: str
study_objective_uid1: str
initial_ct_term_study_standard_test: ct_term.CTTerm
objective_level_term: ct_term.CTTerm
objective_level_term2: ct_term.CTTerm
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyendpointapi"
    inject_and_clear_db(db_name)

    global study, test_data_dict
    study, test_data_dict = inject_base_data()

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

    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)

    ct_term_start_date = datetime(2020, 3, 25, tzinfo=timezone.utc)

    objlevel_codelist = create_codelist(
        settings.study_objective_level_name,
        settings.study_objective_level_name,
        catalogue_name,
        library_name,
        submission_value="OBJTLEVL",
    )

    global objective_level_term
    obj_term1_name = settings.study_objective_level_name + " term"
    objective_level_term = TestUtils.create_ct_term(
        codelist_uid=objlevel_codelist.codelist_uid,
        submission_value=obj_term1_name,
        sponsor_preferred_name=obj_term1_name,
        order=2,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
    )
    global objective_level_term2
    obj_term2_name = settings.study_objective_level_name + " term2"
    objective_level_term2 = TestUtils.create_ct_term(
        codelist_uid=objlevel_codelist.codelist_uid,
        submission_value=obj_term2_name,
        sponsor_preferred_name=obj_term2_name,
        order=3,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
    )

    ct_term_codelist_name = settings.study_endpoint_level_name
    create_codelist(
        ct_term_codelist_name, ct_term_codelist_name, catalogue_name, library_name
    )

    endpoint_level_codelist = create_codelist(
        "Endpoint Level",
        "CTCodelist_EndpointLevel",
        catalogue_name,
        library_name,
        submission_value=settings.study_endpoint_level_cl_submval,
    )
    global initial_ct_term_study_standard_test
    initial_ct_term_study_standard_test = TestUtils.create_ct_term(
        codelist_uid=endpoint_level_codelist.codelist_uid,
        submission_value="Endpoint level 1 submval",
        sponsor_preferred_name="Endpoint Level 1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
        term_uid="EndpointLevel_0001",
    )
    create_ct_term(
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
    # Create a endpoint sublevel codelist
    endpoint_sublevel_codelist = create_codelist(
        "Endpoint Sublevel",
        "CTCodelist_EndpointSublevel",
        catalogue_name,
        library_name,
        submission_value=settings.study_endpoint_sublevel_cl_submval,
    )
    create_ct_term(
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
    cdisc_package_name = "SDTM CT 2020-03-27"
    TestUtils.create_ct_package(
        catalogue=catalogue_name,
        name=cdisc_package_name,
        approve_elements=False,
        effective_date=datetime(2020, 3, 27, tzinfo=timezone.utc),
    )
    # patch the date of the latest HAS_VERSION FINAL relationship so it can be detected by the selected study_standard_Version
    params = {
        "uid": initial_ct_term_study_standard_test.term_uid,
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    # adjust term end date of the 0.1 draft
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Draft' 
                    SET has_version.end_date = $date
                """,
        params=params,
    )
    # adjust term start_date of the 1.0 final
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )
    # adjust cl start and end date of the 0.1 draft
    params["uid"] = endpoint_level_codelist.codelist_uid
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTCodelistNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )
    # adjust term start_date of the 1.0 final
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_ATTRIBUTES_ROOT]-(ct_attrs:CTCodelistAttributesRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_attrs)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )

    yield


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(
        api_client, mode=ValidationMode.WARNING
    )  # needs to be warning for now as it's leaving broken data


def test_study_endpoint_modify_actions_on_locked_study(api_client):
    global endpoint_uid
    global study_objective_uid1

    response = api_client.post(
        f"/studies/{study.uid}/study-objectives",
        json={
            "objective_uid": "Objective_000001",
            "objective_level_uid": objective_level_term.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["objective_level"]["term_uid"] == objective_level_term.term_uid
    study_objective_uid1 = res["study_objective_uid"]

    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints",
        json={
            "endpoint_uid": "Endpoint_000001",
            "study_objective_uid": study_objective_uid1,
            "endpoint_level_uid": "EndpointLevel_0001",
        },
    )
    res = response.json()
    assert res["endpoint_level"]["term_uid"] == "EndpointLevel_0001"
    assert_response_status_code(response, 201)

    # get all endpoints
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res
    endpoint_uid = res[0]["study_endpoint_uid"]

    # get specific endpoint of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["endpoint_level"]["term_uid"] == "EndpointLevel_0001"

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
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints",
        json={
            "timeframe_uid": "Timeframe_000001",
            "study_objective_uid": study_objective_uid1,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # edit endpoint
    response = api_client.patch(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
        json={"new_order": 2},
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    for i, _ in enumerate(old_res):
        old_res[i]["study_objective"]["study_version"] = mock.ANY
    assert old_res == res

    # test cannot delete
    response = api_client.delete(f"/studies/{study.uid}/study-endpoints/{endpoint_uid}")
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


def test_study_endpoint_with_study_objective_relationship(api_client):
    # get specific study endpoint
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["endpoint_level"]["term_uid"] == "EndpointLevel_0001"
    assert res["study_objective"]["study_objective_uid"] == study_objective_uid1
    before_unlock = res
    before_unlock_objectives = api_client.get(
        f"/studies/{study.uid}/study-objectives"
    ).json()

    # get study endpoint headers
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/headers?field_name=endpoint_level.term_uid",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == ["EndpointLevel_0001"]

    # Unlock
    response = api_client.post(
        f"/studies/{study.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # edit study endpoint
    response = api_client.patch(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
        json={
            "endpoint_uid": "Endpoint_000001",
            "endpoint_level_uid": "EndpointLevel_0002",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["endpoint_level"]["term_uid"] == "EndpointLevel_0002"

    # edit study objective
    response = api_client.patch(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid1}",
        json={
            "objective_uid": "Objective_000002",
            "objective_level_uid": objective_level_term2.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["objective_level"]["term_uid"] == objective_level_term2.term_uid

    # get all study endpoints of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock["study_version"] = mock.ANY
    before_unlock["study_objective"]["study_version"] = mock.ANY
    assert res["items"][0] == before_unlock

    # get all
    for i, _ in enumerate(before_unlock_objectives["items"]):
        before_unlock_objectives["items"][i]["study_version"] = mock.ANY
    assert (
        before_unlock_objectives
        == api_client.get(
            f"/studies/{study.uid}/study-objectives?study_value_version=1"
        ).json()
    )

    # get specific study endpoint of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == before_unlock

    # get study endpoint headers of specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/headers?field_name=endpoint_level.term_uid&study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == ["EndpointLevel_0001"]

    # get all study endpoints
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"][0]["endpoint_level"]["term_uid"] == "EndpointLevel_0002"

    # get specific study endpoint
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["endpoint_level"]["term_uid"] == "EndpointLevel_0002"


def test_study_value_version_validation(api_client):
    # get all study endpoints of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints?study_value_version=a",
    )
    assert_response_status_code(response, 400)

    # get study study endpoint headers
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/headers?field_name=endpoint_level.term_uid",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == ["EndpointLevel_0002"]


@pytest.mark.parametrize(
    "export_format",
    [
        pytest.param("text/csv"),
        pytest.param("text/xml"),
        pytest.param(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    ],
)
def test_get_study_endpoints_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-endpoints"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_update_endpoint_library_items_of_relationship_to_value_nodes(api_client):
    """
    Test that the StudyEndpoint selection remains connected to the specific Value node even if the Value node is not latest anymore.

    StudyEndpoint is connected to value nodes:
    - EndpointTemplate
    """
    # get specific study endpoint
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    library_template_endpoint_uid = res["endpoint"]["template"]["uid"]
    initial_endpoint_name = res["endpoint"]["name"]

    text_value_2_name = "2ndname"
    # change endpoint name and approve the version
    api_client.post(
        f"/endpoint-templates/{library_template_endpoint_uid}/versions",
        json={
            "change_description": "test change",
            "name": text_value_2_name,
            "guidance_text": "don't know",
        },
    )
    api_client.post(
        f"/endpoint-templates/{library_template_endpoint_uid}/approvals?cascade=true"
    )

    # check that the Library item has been changed
    response = api_client.get(f"/endpoint-templates/{library_template_endpoint_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == text_value_2_name

    # check that the StudySelection StudyEndpoint hasn't been updated
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["endpoint"]["name"] == initial_endpoint_name

    # check that the StudySelection can approve the current version
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}/accept-version",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["accepted_version"] is True
    assert res["endpoint"]["template"]["name"] == initial_endpoint_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    counting_before_sync = len(res)

    # check that the StudySelection's objective can be updated to the LATEST
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}/sync-latest-endpoint-version",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["endpoint"]["template"]["name"] == text_value_2_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res) == counting_before_sync + 1


def test_update_timeframe_library_items_of_relationship_to_value_nodes(api_client):
    """
    Test that the StudyEndpoint selection remains connected to the specific Value node even if the Value node is not latest anymore.

    StudyEndpoint is connected to value nodes:
    - TimeframeTemplate
    """

    # timeframes
    response = api_client.patch(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
        json={
            "timeframe_uid": "Timeframe_000001",
            "study_objective_uid": study_objective_uid1,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    library_template_timeframe_uid = res["timeframe"]["template"]["uid"]
    initial_timeframe_name = res["timeframe"]["template"]["name"]

    text_value_2_name = "2ndname"
    # change endpoint name and approve the version
    api_client.post(
        f"/timeframe-templates/{library_template_timeframe_uid}/versions",
        json={"change_description": "test change", "name": text_value_2_name},
    )
    # change endpoint name and approve the version
    api_client.patch(
        f"/timeframe-templates/{library_template_timeframe_uid}",
        json={
            "name": text_value_2_name,
            "library": {"name": "Sponsor", "is_editable": True},
            "change_description": "Work in Progress",
        },
    )
    api_client.post(
        f"/timeframe-templates/{library_template_timeframe_uid}/approvals?cascade=true"
    )
    # check that the Library item has been changed
    response = api_client.get(f"/timeframe-templates/{library_template_timeframe_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == text_value_2_name

    # check that the StudySelection StudyEndpoint hasn't been updated
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["timeframe"]["name"] == initial_timeframe_name

    # check that the StudySelection can approve the current version
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}/accept-version",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["accepted_version"] is True
    assert res["timeframe"]["template"]["name"] == initial_timeframe_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    counting_before_sync = len(res)

    # check that the StudySelection's objective can be updated to the LATEST
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}/sync-latest-timeframe-version",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["timeframe"]["template"]["name"] == text_value_2_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res) == counting_before_sync + 1


def test_study_endpoint_version_selecting_ct_package(api_client):
    """change the name of a CTTerm, and verify that the study selection is still set to the old name of the CTTerm when the Sponsor Standard version is set"""
    study_selection_breadcrumb = "study-endpoints"
    study_selection_ctterm_uid_input_key = "endpoint_level_uid"
    study_selection_ctterm_keys = "endpoint_level"
    study_selection_ctterm_uid_key = "term_uid"
    study_for_ctterm_versioning = TestUtils.create_study()

    response = api_client.post(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}",
        json={
            "endpoint_uid": "Endpoint_000001",
            study_selection_ctterm_uid_input_key: "EndpointLevel_0001",
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    study_selection_uid_study_standard_test = res["study_endpoint_uid"]
    assert res["order"] == 1
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_uid_key]
        == "EndpointLevel_0001"
    )

    # edit ctterm
    new_ctterm_name = "new ctterm name"
    ctterm_uid = initial_ct_term_study_standard_test.term_uid
    # change ctterm name and approve the version
    response = api_client.post(
        f"/ct/terms/{ctterm_uid}/names/versions",
    )
    assert_response_status_code(response, 201)
    api_client.patch(
        f"/ct/terms/{ctterm_uid}/names",
        json={
            "sponsor_preferred_name": new_ctterm_name,
            "sponsor_preferred_name_sentence_case": new_ctterm_name,
            "change_description": "string",
        },
    )
    response = api_client.post(f"/ct/terms/{ctterm_uid}/names/approvals")
    assert_response_status_code(response, 201)

    # get study selection with ctterm latest
    response = api_client.patch(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
        json={
            study_selection_ctterm_uid_input_key: ctterm_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_uid_key] == ctterm_uid
    )
    assert res[study_selection_ctterm_keys]["term_name"] == new_ctterm_name

    # get ct_packages
    response = api_client.get(
        "/ct/packages",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    ct_package_uid = res[0]["uid"]

    # create study standard version
    response = api_client.post(
        f"/studies/{study_for_ctterm_versioning.uid}/study-standard-versions",
        json={
            "ct_package_uid": ct_package_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["ct_package"]["uid"] == ct_package_uid

    # get study selection with previous ctterm
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_uid_key] == ctterm_uid
    )
    assert (
        res[study_selection_ctterm_keys]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # patch the study selection so it will be seen on the audit trail the change of ctterm versions, because the selection of study standard version
    response = api_client.patch(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
        json={
            "name": "New_Endpoint_Name_1",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_keys]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # get versions of objective
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0][study_selection_ctterm_keys]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert res[1][study_selection_ctterm_keys]["term_name"] == new_ctterm_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0][study_selection_ctterm_keys]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert res[1][study_selection_ctterm_keys]["term_name"] == new_ctterm_name


def test_study_endpoint_ct_term_retrieval_at_date(api_client):
    """
    Test that any CT Term name fetched in the context of a study selection either:
    * Matches the date of the Study Standard version when available
    * Or the latest final version is returned
    The study selection return model includes a queried_effective_data property to verify this
    """

    study_for_queried_effective_date = TestUtils.create_study()
    study_selection_breadcrumb = "study-endpoints"
    study_selection_ctterm_keys = "endpoint_level"
    study_selection_ctterm_uid_input_key = "endpoint_level_uid"

    # Create selection
    response = api_client.post(
        f"/studies/{study_for_queried_effective_date.uid}/{study_selection_breadcrumb}",
        json={
            "endpoint_uid": "Endpoint_000001",
            study_selection_ctterm_uid_input_key: "EndpointLevel_0001",
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res[study_selection_ctterm_keys]["queried_effective_date"] is None
    assert res[study_selection_ctterm_keys]["date_conflict"] is False
    study_selection_uid_study_standard_test = res["study_endpoint_uid"]

    ct_term_retrieval_at_date_test_common(
        api_client,
        study_selection_breadcrumb=study_selection_breadcrumb,
        study_selection_ctterm_uid_input_key=study_selection_ctterm_uid_input_key,
        study_selection_ctterm_keys=study_selection_ctterm_keys,
        study_for_queried_effective_date=study_for_queried_effective_date,
        initial_ct_term_study_standard_test=initial_ct_term_study_standard_test,
        study_selection_uid_study_standard_test=study_selection_uid_study_standard_test,
    )
