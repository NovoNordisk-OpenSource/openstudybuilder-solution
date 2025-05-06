"""
Tests for /studies/{study_uid}/study-design-cells endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import copy
import logging
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api import main
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignCell,
    StudySelectionArm,
    StudySelectionBranchArm,
)

# from clinical_mdr_api.routers.studies.study import PROJECT_NUMBER
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_branch_arm,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import PROJECT_NUMBER, TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
study_arm: StudySelectionArm
study_arm2: StudySelectionArm
study_branch_arm: StudySelectionBranchArm
element_type_term: CTTerm
epoch_uid: str
study_design_cell_uid: StudyDesignCell
study_element_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(main.app)


@pytest.fixture(scope="module")
def test_data():
    # reload(study_epoch_domain_module)
    # reload(study_epoch_service_module)
    """Initialize test data"""
    db_name = "studydesigncellapi"
    inject_and_clear_db(db_name)
    inject_base_data()
    global study_arm
    global study_arm2
    global study_branch_arm
    global study
    study = TestUtils.create_study()
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    TestUtils.set_study_standard_version(study_uid=study.uid)

    catalogue_name, library_name = get_catalogue_name_library_name()
    # Create a study arm
    arm_type_codelist = create_codelist(
        "Arm Type", "CTCodelist_ArmType", catalogue_name, library_name
    )
    arm_type_term = create_ct_term(
        arm_type_codelist.codelist_uid,
        "Arm Type",
        "ArmType_0001",
        1,
        catalogue_name,
        library_name,
    )
    study_arm = create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_1",
        short_name="Arm_Short_Name_1",
        code="Arm_code_1",
        description="desc...",
        colour_code="colour...",
        randomization_group="Randomization_Group_1",
        number_of_subjects=1,
        arm_type_uid=arm_type_term.uid,
    )
    study_arm2 = create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_2",
        short_name="Arm_Short_Name_2",
        code="Arm_code_2",
        description="desc...",
        colour_code="colour...",
        randomization_group="Randomization_Group_2",
        number_of_subjects=1,
        arm_type_uid=arm_type_term.uid,
    )
    study_branch_arm = create_study_branch_arm(
        study_uid=study.uid,
        name="BranchArm_1",
        short_name="BranchArm_1",
        code="1",
        description="before locked",
        colour_code="colour...",
        randomization_group="randomization_group",
        number_of_subjects="1",
        arm_uid=study_arm2.arm_uid,
    )
    create_study_epoch_codelists_ret_cat_and_lib()
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study.uid)
    global epoch_uid
    epoch_uid = study_epoch.uid
    element_type_codelist = create_codelist(
        "Element Type", "CTCodelist_ElementType", catalogue_name, library_name
    )
    global element_type_term
    element_type_term = create_ct_term(
        element_type_codelist.codelist_uid,
        "Element Type",
        "ElementType_0001",
        1,
        catalogue_name,
        library_name,
    )
    yield


def test_design_cell_modify_actions_on_locked_study(api_client):
    global study_element_uid
    response = api_client.post(
        f"/studies/{study.uid}/study-elements",
        json={
            "name": "Element_Name_1",
            "short_name": "Element_Short_Name_1",
            "element_subtype_uid": element_type_term.uid,
        },
    )
    res = response.json()
    study_element_uid = res["element_uid"]
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/studies/{study.uid}/study-design-cells",
        json={
            "study_arm_uid": study_arm.arm_uid,
            "study_epoch_uid": epoch_uid,
            "study_element_uid": study_element_uid,
            "transition_rule": "Transition_Rule_1",
        },
    )
    assert_response_status_code(response, 201)

    # get all design-cell
    response = api_client.get(
        f"/studies/{study.uid}/study-design-cells/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res
    design_cell_uid = res[0]["study_design_cell_uid"]

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

    response = api_client.post(
        f"/studies/{study.uid}/study-design-cells",
        json={
            "study_arm_uid": study_arm2.arm_uid,
            "study_epoch_uid": epoch_uid,
            "study_element_uid": study_element_uid,
            "transition_rule": "Transition_Rule_1",
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # edit epoch
    response = api_client.post(
        f"/studies/{study.uid}/study-design-cells/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "study_design_cell_uid": design_cell_uid,
                    "study_arm_uid": study_arm2.arm_uid,
                    "study_epoch_uid": epoch_uid,
                    "study_element_uid": study_element_uid,
                    "transition_rule": "Transition_Rule_1",
                },
            }
        ],
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-design-cells/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert old_res == res

    # test cannot delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-design-cells/{design_cell_uid}"
    )
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


# pylint: disable=too-many-statements
def test_study_design_cell_with_study_epoch_relationship(api_client):
    """
    HAVING:
        Arm
        Arm2
        BranchArm
        Element
        Epoch
        StudyDesignCell
    THEN:
        UNLOCK
                create 2nd studydesigncell
        GET checkpoints
            save all study selection's objects
        LOCK
        UNLOCK
        edit arm
        edit arm2
        edit brancharm
        edit element
        edit epoch
        edit epoch2
        delete studyDesignCell1

        compare checkpoints
            check arm, arm2, brancharms, element, epochs, designcells, designcells_by_arm, design_cells_by_epoch, design_cells_by_branch_arm
    """

    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert_response_status_code(response, 200)

    # preparing all objects before locking
    api_client.post(
        f"/studies/{study.uid}/study-design-cells",
        json={
            "study_branch_arm_uid": study_branch_arm.branch_arm_uid,
            "study_epoch_uid": epoch_uid,
            "study_element_uid": study_element_uid,
            "transition_rule": "Transition_Rule_1",
        },
    )

    # get all design-cell
    response = api_client.get(
        f"/studies/{study.uid}/study-design-cells",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock = res

    # get all
    before_unlock_arms = api_client.get(f"/studies/{study.uid}/study-arms").json()
    before_unlock_branch_arms = api_client.get(
        f"/studies/{study.uid}/study-branch-arms"
    ).json()
    before_unlock_elements = api_client.get(
        f"/studies/{study.uid}/study-elements"
    ).json()
    before_unlock_epochs = api_client.get(f"/studies/{study.uid}/study-epochs").json()
    before_unlock_design_cell_by_arm = api_client.get(
        f"/studies/{study.uid}/study-design-cells/arm/{study_arm.arm_uid}"
    ).json()
    before_unlock_design_cell_by_branch_arm = api_client.get(
        f"/studies/{study.uid}/study-design-cells/branch-arm/{study_branch_arm.branch_arm_uid}"
    ).json()
    before_unlock_design_cell_by_epoch = api_client.get(
        f"/studies/{study.uid}/study-design-cells/study-epochs/{epoch_uid}"
    ).json()

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)
    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert_response_status_code(response, 200)

    # edit arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-arms/{study_arm.arm_uid}",
        json={
            "name": "New_Arm_Name_1",
        },
    )
    assert_response_status_code(response, 200)

    # edit arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-arms/{study_arm2.arm_uid}",
        json={
            "name": "New_Arm_Name_2",
        },
    )
    assert_response_status_code(response, 200)

    # edit branch arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-branch-arms/{study_branch_arm.branch_arm_uid}",
        json={
            "name": "New_Branch_Arm_Name_1",
        },
    )
    assert_response_status_code(response, 200)

    # edit element
    response = api_client.patch(
        f"/studies/{study.uid}/study-elements/{study_element_uid}",
        json={
            "name": "New_Element_Name_1",
        },
    )
    assert_response_status_code(response, 200)

    # edit epoch
    response = api_client.patch(
        f"/studies/{study.uid}/study-epochs/{epoch_uid}",
        json={
            "study_uid": study.uid,
            "name": "New_epoch_Name_1",
            "change_description": "this is a changing test",
        },
    )
    assert_response_status_code(response, 200)

    # delete design cell
    response = api_client.delete(
        f"/studies/{study.uid}/study-design-cells/{before_unlock[0]['design_cell_uid']}"
    )
    assert_response_status_code(response, 204)

    # get all study design cells of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-design-cells?study_value_version=2",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    for i, _ in enumerate(before_unlock):
        before_unlock[i]["study_version"] = mock.ANY
    assert res == before_unlock

    # get all
    for i, _ in enumerate(before_unlock_arms["items"]):
        before_unlock_arms["items"][i]["study_version"] = mock.ANY
    assert (
        before_unlock_arms
        == api_client.get(
            f"/studies/{study.uid}/study-arms?study_value_version=2"
        ).json()
    )
    for i, _ in enumerate(before_unlock_branch_arms):
        before_unlock_branch_arms[i]["study_version"] = mock.ANY
    assert (
        before_unlock_branch_arms
        == api_client.get(
            f"/studies/{study.uid}/study-branch-arms?study_value_version=2"
        ).json()
    )
    for i, _ in enumerate(before_unlock_elements["items"]):
        before_unlock_elements["items"][i]["study_version"] = mock.ANY
    assert (
        before_unlock_elements
        == api_client.get(
            f"/studies/{study.uid}/study-elements?study_value_version=2"
        ).json()
    )
    for i, _ in enumerate(before_unlock_epochs["items"]):
        before_unlock_epochs["items"][i]["study_version"] = mock.ANY
    assert (
        before_unlock_epochs
        == api_client.get(
            f"/studies/{study.uid}/study-epochs?study_value_version=2"
        ).json()
    )
    for i, _ in enumerate(before_unlock_design_cell_by_arm):
        before_unlock_design_cell_by_arm[i]["study_version"] = mock.ANY
    assert (
        before_unlock_design_cell_by_arm
        == api_client.get(
            f"/studies/{study.uid}/study-design-cells/arm/{study_arm.arm_uid}?study_value_version=2"
        ).json()
    )
    for i, _ in enumerate(before_unlock_design_cell_by_branch_arm):
        before_unlock_design_cell_by_branch_arm[i]["study_version"] = mock.ANY
    assert (
        before_unlock_design_cell_by_branch_arm
        == api_client.get(
            f"/studies/{study.uid}/study-design-cells/branch-arm/{study_branch_arm.branch_arm_uid}?study_value_version=2"
        ).json()
    )
    for i, _ in enumerate(before_unlock_design_cell_by_epoch):
        before_unlock_design_cell_by_epoch[i]["study_version"] = mock.ANY
    assert (
        before_unlock_design_cell_by_epoch
        == api_client.get(
            f"/studies/{study.uid}/study-design-cells/study-epochs/{epoch_uid}?study_value_version=2"
        ).json()
    )

    study_cloned = api_client.post(
        f"/studies/{study.uid}/clone",
        json={
            "study_number": "6675",
            "study_acronym": "6675",
            "project_number": PROJECT_NUMBER,
            "description": "6675",
            "copy_study_arm": True,
            "copy_study_branch_arm": True,
            "copy_study_cohort": True,
            "copy_study_element": True,
            "copy_study_visit": True,
            "copy_study_epoch": True,
            "copy_study_footnote": True,
            "copy_study_design_matrix": True,
        },
    ).json()
    # get all
    cloned_arms = api_client.get(f"/studies/{study_cloned['uid']}/study-arms").json()
    cloned_arms_any = copy.deepcopy(cloned_arms)
    for i, _ in enumerate(cloned_arms_any["items"]):
        cloned_arms_any["items"][i]["study_version"] = mock.ANY
        cloned_arms_any["items"][i]["study_uid"] = mock.ANY
        cloned_arms_any["items"][i]["arm_uid"] = mock.ANY
        cloned_arms_any["items"][i]["arm_connected_branch_arms"] = mock.ANY
        cloned_arms_any["items"][i]["start_date"] = mock.ANY
        cloned_arms_any["items"][i]["arm_type"]["queried_effective_date"] = mock.ANY
    final_arms = api_client.get(f"/studies/{study.uid}/study-arms").json()
    for i, _ in enumerate(final_arms["items"]):
        final_arms["items"][i]["study_version"] = mock.ANY
        final_arms["items"][i]["study_uid"] = mock.ANY
        final_arms["items"][i]["arm_uid"] = mock.ANY
        final_arms["items"][i]["arm_connected_branch_arms"] = mock.ANY
        final_arms["items"][i]["start_date"] = mock.ANY
        final_arms["items"][i]["arm_type"]["queried_effective_date"] = mock.ANY
    assert cloned_arms_any == final_arms

    cloned_branch_arms = api_client.get(
        f"/studies/{study_cloned['uid']}/study-branch-arms"
    ).json()
    cloned_branch_arms_any = copy.deepcopy(cloned_branch_arms)
    for i, _ in enumerate(cloned_branch_arms_any):
        cloned_branch_arms_any[i]["study_version"] = mock.ANY
        cloned_branch_arms_any[i]["study_uid"] = mock.ANY
        cloned_branch_arms_any[i]["branch_arm_uid"] = mock.ANY
        cloned_branch_arms_any[i]["start_date"] = mock.ANY
        cloned_branch_arms_any[i]["arm_root"] = mock.ANY
    final_branch_arms = api_client.get(f"/studies/{study.uid}/study-branch-arms").json()
    for i, _ in enumerate(final_branch_arms):
        final_branch_arms[i]["study_version"] = mock.ANY
        final_branch_arms[i]["study_uid"] = mock.ANY
        final_branch_arms[i]["branch_arm_uid"] = mock.ANY
        final_branch_arms[i]["start_date"] = mock.ANY
        final_branch_arms[i]["arm_root"] = mock.ANY
    assert cloned_branch_arms_any == final_branch_arms

    cloned_elements = api_client.get(
        f"/studies/{study_cloned['uid']}/study-elements"
    ).json()
    assert len(cloned_elements["items"]) > 0
    cloned_epochs = api_client.get(
        f"/studies/{study_cloned['uid']}/study-epochs"
    ).json()
    assert len(cloned_epochs["items"]) > 0

    cloned_design_cell_by_branch_arm = api_client.get(
        f"/studies/{study_cloned['uid']}/study-design-cells/branch-arm/{cloned_branch_arms[0]['branch_arm_uid']}"
    ).json()
    cloned_design_cell_by_branch_arm_any = copy.deepcopy(
        cloned_design_cell_by_branch_arm
    )
    for i, _ in enumerate(cloned_design_cell_by_branch_arm_any):
        cloned_design_cell_by_branch_arm_any[i]["study_version"] = mock.ANY
        cloned_design_cell_by_branch_arm_any[i]["study_uid"] = mock.ANY
        cloned_design_cell_by_branch_arm_any[i]["design_cell_uid"] = mock.ANY
        cloned_design_cell_by_branch_arm_any[i]["study_branch_arm_uid"] = mock.ANY
        cloned_design_cell_by_branch_arm_any[i]["study_arm_uid"] = mock.ANY
        cloned_design_cell_by_branch_arm_any[i]["study_epoch_uid"] = mock.ANY
        cloned_design_cell_by_branch_arm_any[i]["study_element_uid"] = mock.ANY
        cloned_design_cell_by_branch_arm_any[i]["start_date"] = mock.ANY
    final_design_cell_by_branch_arm = api_client.get(
        f"/studies/{study.uid}/study-design-cells/branch-arm/{study_branch_arm.branch_arm_uid}"
    ).json()
    for i, _ in enumerate(final_design_cell_by_branch_arm):
        final_design_cell_by_branch_arm[i]["study_version"] = mock.ANY
        final_design_cell_by_branch_arm[i]["study_uid"] = mock.ANY
        final_design_cell_by_branch_arm[i]["design_cell_uid"] = mock.ANY
        final_design_cell_by_branch_arm[i]["study_branch_arm_uid"] = mock.ANY
        final_design_cell_by_branch_arm[i]["study_arm_uid"] = mock.ANY
        final_design_cell_by_branch_arm[i]["study_epoch_uid"] = mock.ANY
        final_design_cell_by_branch_arm[i]["study_element_uid"] = mock.ANY
        final_design_cell_by_branch_arm[i]["start_date"] = mock.ANY
    assert cloned_design_cell_by_branch_arm_any == final_design_cell_by_branch_arm

    response = api_client.post(
        f"/studies/{study.uid}/clone",
        json={
            "study_number": "6676",
            "study_acronym": "6676",
            "project_number": PROJECT_NUMBER,
            "description": "6676",
            "copy_study_arm": False,
            "copy_study_branch_arm": False,
            "copy_study_cohort": False,
            "copy_study_element": False,
            "copy_study_visit": False,
            "copy_study_epoch": False,
            "copy_study_footnote": False,
            "copy_study_design_matrix": False,
        },
    )
    response.json()
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "At least one item should be selected"

    response = api_client.post(
        f"/studies/{study.uid}/clone",
        json={
            "study_number": "6677",
            "study_acronym": "6677",
            "project_number": PROJECT_NUMBER,
            "description": "6677",
            "copy_study_arm": True,
            "copy_study_branch_arm": False,
            "copy_study_cohort": True,
            "copy_study_element": False,
            "copy_study_visit": False,
            "copy_study_epoch": False,
            "copy_study_footnote": False,
            "copy_study_design_matrix": False,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "Study Branch should be also included"
