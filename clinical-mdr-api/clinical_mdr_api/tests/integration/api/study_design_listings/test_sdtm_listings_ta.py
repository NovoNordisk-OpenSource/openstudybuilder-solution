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
from clinical_mdr_api.models.listings.listings_sdtm import StudyArmListing
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
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
    inject_and_clear_db("SDTMTAListingTest.api")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    study = generate_study_root()
    study_uid = study.uid
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
        create_study_element(element_type_term.uid, study_uid),
        create_study_element(element_type_term_2.uid, study_uid),
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
    edit_study_epoch(epoch_uid=study_epoch2.uid)
    TestUtils.create_study_fields_configuration()


def test_ta_listing(api_client):
    response = api_client.get(
        "/listings/studies/study_root/sdtm/ta",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None

    expected_output = [
        # 1
        StudyArmListing(
            ARM="Arm_Name_1",
            ARMCD="Arm_code_1",
            DOMAIN="TA",
            ELEMENT="Element_Name_1",
            EPOCH="Epoch Subtype 2",
            ETCD="2",
            STUDYID="SOME_ID-0",
            TABRANCH=None,
            TAETORD="2",
            TATRANS="Transition_Rule_1",
        ).model_dump(),
        # 2
        StudyArmListing(
            ARM="Arm_Name_2",
            ARMCD="Arm_code_2-Branch_Arm_code_1",
            DOMAIN="TA",
            ELEMENT="Element_Name_1",
            EPOCH="Epoch Subtype 1",
            ETCD="1",
            STUDYID="SOME_ID-0",
            TABRANCH="Branch_Arm_Name_1_edit",
            TAETORD="1",
            TATRANS="Transition_Rule_1",
        ).model_dump(),
        # 3
        StudyArmListing(
            ARM="Arm_Name_2",
            ARMCD="Arm_code_2-Branch_Arm_code_1",
            DOMAIN="TA",
            ELEMENT="Element_Name_1",
            EPOCH="Epoch Subtype 2",
            ETCD="1",
            STUDYID="SOME_ID-0",
            TABRANCH="Branch_Arm_Name_1_edit",
            TAETORD="2",
            TATRANS="Transition_Rule_1",
        ).model_dump(),
        # 4
        StudyArmListing(
            ARM="Arm_Name_3",
            ARMCD="Arm_code_3",
            DOMAIN="TA",
            ELEMENT="Element_Name_1",
            EPOCH="Epoch Subtype 2",
            ETCD="1",
            STUDYID="SOME_ID-0",
            TABRANCH=None,
            TAETORD="2",
            TATRANS="Transition_Rule_1",
        ).model_dump(),
    ]
    assert res == expected_output
