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
from clinical_mdr_api.models.listings.listings_sdtm import StudySummaryListing
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_branch_arm,
    create_study_cohort,
    create_study_design_cell,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    edit_study_epoch,
    generate_study_root,
    get_catalogue_name_library_name,
    patch_study_branch_arm,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import CDISC_LIBRARY_NAME, SDTM_CT_CATALOGUE_NAME

study_uid: str

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def api_client(test_data: None):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    global study_uid
    study_uid = "study_root"
    inject_and_clear_db("SDTMTSListingTest.api")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    TestUtils.create_library(name="UCUM", is_editable=True)
    study = generate_study_root()
    # Create an epoch
    create_study_epoch_codelists_ret_cat_and_lib()
    catalogue_name, library_name = get_catalogue_name_library_name()
    study_epoch = create_study_epoch("EpochSubType_0001")
    study_epoch2 = create_study_epoch("EpochSubType_0001")
    # Create a study element
    element_type_codelist = create_codelist(
        "Element Type", "CTCodelist_ElementType", catalogue_name, library_name
    )
    element_type_term = create_ct_term(
        element_type_codelist.codelist_uid,
        "Element Type",
        "ElementType_0001",
        1,
        catalogue_name,
        library_name,
    )
    element_type_term_2 = create_ct_term(
        element_type_codelist.codelist_uid,
        "Element Type",
        "ElementType_0002",
        2,
        catalogue_name,
        library_name,
    )
    study_elements = [
        create_study_element(element_type_term.uid, study.uid),
        create_study_element(element_type_term_2.uid, study.uid),
    ]

    codelist = create_codelist(
        name="Arm Type",
        uid="CTCodelist_00004",
        catalogue=catalogue_name,
        library=library_name,
    )
    arm_type = create_ct_term(
        codelist=codelist.codelist_uid,
        name="Arm Type",
        uid="ArmType_0001",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
    )

    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_1",
        short_name="Arm_Short_Name_1",
        code="Arm_code_1",
        description="desc...",
        colour_code="colour...",
        randomization_group="Arm_randomizationGroup",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_2",
        short_name="Arm_Short_Name_2",
        code="Arm_code_2",
        description="desc...",
        colour_code="colour...",
        randomization_group="Arm_randomizationGroup2",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_3",
        short_name="Arm_Short_Name_3",
        code="Arm_code_3",
        description="desc...",
        colour_code="colour...",
        randomization_group="Arm_randomizationGroup3",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )

    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_9",
        short_name="Arm_Short_Name_9",
        code="Arm_code_9",
        description="desc...",
        colour_code="colour...",
        randomization_group="Arm_randomizationGroup9",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )

    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch.uid,
        study_arm_uid="StudyArm_000003",
        study_uid=study.uid,
    )
    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000003",
        study_uid=study.uid,
    )

    create_study_design_cell(
        study_element_uid=study_elements[1].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000001",
        study_uid=study.uid,
    )

    branch_arm = create_study_branch_arm(
        study_uid=study.uid,
        name="Branch_Arm_Name_1",
        short_name="Branch_Arm_Short_Name_1",
        code="Branch_Arm_code_1",
        description="desc...",
        colour_code="colour...",
        randomization_group="Branch_Arm_randomizationGroup",
        number_of_subjects=100,
        arm_uid="StudyArm_000003",
    )
    branch_arm = patch_study_branch_arm(
        branch_arm_uid=branch_arm.branch_arm_uid, study_uid=study.uid
    )

    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000005",
        study_uid=study.uid,
    )

    create_study_cohort(
        study_uid=study.uid,
        name="Cohort_Name_1",
        short_name="Cohort_Short_Name_1",
        code="Cohort_code_1",
        description="desc...",
        colour_code="desc...",
        number_of_subjects=100,
        arm_uids=["StudyArm_000001"],
    )
    # edit an epoch to track if the relationships have been updated
    edit_study_epoch(epoch_uid=study_epoch2.uid)

    codelist = create_codelist(
        name="Trial Summary Parameter Test Code",
        uid="C66738",
        catalogue=catalogue_name,
        library=library_name,
    )

    arm_type = create_ct_term(
        codelist=codelist.codelist_uid,
        name="C98771",
        uid="C98771_NARMS",
        code_submission_value="NARMS",
        name_submission_value="Planned Number of Arms",
        preferred_term="Planned Number of Arms",
        definition="The planned number of intervention groups.",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
    )

    codelist = create_codelist(
        name="Trial Summary Parameter Test Name",
        uid="C67152",
        catalogue=catalogue_name,
        library=library_name,
    )

    arm_type = create_ct_term(
        codelist=codelist.codelist_uid,
        name="C126063",
        uid="C126063_NCOHORT",
        code_submission_value="NCOHORT",
        name_submission_value="Number of Groups/Cohorts",
        preferred_term="Number of Groups or Cohorts",
        definition="The number of groups or cohorts that are part of the study.",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
    )
    TestUtils.create_study_fields_configuration()
    # Creating library and catalogue for study standard version
    TestUtils.create_library(name=CDISC_LIBRARY_NAME, is_editable=True)
    TestUtils.create_ct_catalogue(
        library=CDISC_LIBRARY_NAME, catalogue_name=SDTM_CT_CATALOGUE_NAME
    )
    TestUtils.create_ct_codelists_using_cypher()
    TestUtils.set_study_standard_version(study_uid=study.uid)
    fix_study_preferred_time_unit(study_uid=study.uid)


def test_ts_listing(api_client: TestClient):
    response = api_client.get(
        "/listings/studies/study_root/sdtm/ts",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None

    expected_output = [
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID="some_id-0",
            TSPARM="Planned Number of Arms",
            TSPARMCD="NARMS",
            TSVAL="3",
            TSVALCD="",
            TSVALNF="",
            TSVCDREF="",
            TSVCDVER="",
        ).model_dump(),
        # 1
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID="some_id-0",
            TSPARM="Number of Groups/Cohorts",
            TSPARMCD="NCOHORT",
            TSVAL="1",
            TSVALCD="",
            TSVALNF="",
            TSVCDREF="",
            TSVCDVER="",
        ).model_dump(),
    ]
    assert res == expected_output


def test_ts_listing_versioning(api_client: TestClient):
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
        "/listings/studies/study_root/sdtm/ts",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None
    ts_before_unlock = res

    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study_uid}/locks")
    assert_response_status_code(response, 200)

    # get all visits
    response = api_client.get(
        f"/studies/{study_uid}/study-arms/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res

    # edit study arm
    response = api_client.delete(
        f"/studies/{study_uid}/study-arms/{old_res[0]['arm_uid']}"
    )
    assert_response_status_code(response, 204)

    # get all study visits of a specific study version
    response = api_client.get(
        f"/listings/studies/{study_uid}/sdtm/ts?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"] == ts_before_unlock

    response = api_client.get(
        "/listings/studies/study_root/sdtm/ts",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res[0]["TSVAL"] == "2"
