"""
Tests for /studies/{study_uid}/study-branch-arms endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from typing import Any
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.domains.enums import StudyDesignClassEnum
from clinical_mdr_api.main import app
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_selection import StudySelectionArm
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
test_data_dict: dict[str, Any]
study_arm: StudySelectionArm
branch_arm_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    client = TestClient(app)
    yield client


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studybrancharmapi"
    inject_and_clear_db(db_name)

    global study, test_data_dict
    study, test_data_dict = inject_base_data()

    global study_arm
    study_arm = TestUtils.create_study_arm(
        study_uid=study.uid,
        name="test_arm",
        short_name="test_arm",
    )
    yield


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(api_client)


def test_branch_arm_modify_actions_on_locked_study(api_client):
    global branch_arm_uid
    response = api_client.post(
        f"/studies/{study.uid}/study-branch-arms",
        json={
            "name": "BranchArm_Name_1",
            "short_name": "BranchArm_Short_Name_1",
            "code": "BranchArm_code_1",
            "description": "desc...",
            "randomization_group": "Randomization_Group_1",
            "number_of_subjects": 1,
            "arm_uid": study_arm.arm_uid,
        },
    )
    assert_response_status_code(response, 201)

    # get all arms
    response = api_client.get(
        f"/studies/{study.uid}/study-branch-arm/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res
    branch_arm_uid = res[0]["branch_arm_uid"]

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
        f"/studies/{study.uid}/study-branch-arms",
        json={
            "name": "BranchArm_Name_2",
            "short_name": "BranchArm_Short_Name_2",
            "code": "BranchArm_code_2",
            "description": "desc...",
            "randomization_group": "Randomization_Group_2",
            "number_of_subjects": 1,
            "arm_uid": study_arm.arm_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # edit arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-branch-arms/{branch_arm_uid}",
        json={
            "name": "New_Branch_Arm_Name_1",
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-branch-arm/audit-trail/",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert old_res == res

    # test cannot delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-branch-arms/{branch_arm_uid}"
    )
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


def test_study_branch_arm_study_versions(api_client):
    before_unlock_arms = api_client.get(f"/studies/{study.uid}/study-arms").json()
    before_unlock_branch_arms = api_client.get(
        f"/studies/{study.uid}/study-branch-arms"
    ).json()["items"]
    # Unlock -- Study remain unlocked
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

    # edit arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-arms/{study_arm.arm_uid}",
        json={
            "name": "New_Arm_Name_2",
        },
    )
    assert_response_status_code(response, 200)

    # edit branch arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-branch-arms/{branch_arm_uid}",
        json={
            "name": "New_Branch_Arm_Name_1",
        },
    )
    assert_response_status_code(response, 200)

    # get all
    for i, _ in enumerate(before_unlock_arms["items"]):
        before_unlock_arms["items"][i]["study_version"] = mock.ANY
    assert (
        before_unlock_arms
        == api_client.get(
            f"/studies/{study.uid}/study-arms?study_value_version=1"
        ).json()
    )
    for i, _ in enumerate(before_unlock_branch_arms):
        before_unlock_branch_arms[i]["study_version"] = mock.ANY
    assert (
        before_unlock_branch_arms
        == api_client.get(
            f"/studies/{study.uid}/study-branch-arms?study_value_version=1"
        ).json()["items"]
    )


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
def test_get_study_branch_arms_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-branch-arms"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_batch_operations(api_client):
    test_study = TestUtils.create_study()
    study_arm = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        name="test_arm",
        short_name="test_arm",
    )
    branch_arm_name_1 = "Unique branch arm name1"
    branch_arm_name_2 = "Unique branch arm name2"
    response = api_client.post(
        f"/studies/{test_study.uid}/study-branch-arms/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "name": branch_arm_name_1,
                    "short_name": "BranchArm_Short_Name_1",
                    "code": "BranchArm_code_1",
                    "description": "desc...",
                    "randomization_group": "Randomization_Group_1",
                    "number_of_subjects": 1,
                    "arm_uid": study_arm.arm_uid,
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": branch_arm_name_2,
                    "short_name": "BranchArm_Short_Name_2",
                    "code": "BranchArm_code_2",
                    "description": "desc...",
                    "randomization_group": "Randomization_Group_2",
                    "number_of_subjects": 1,
                    "arm_uid": study_arm.arm_uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)

    res = response.json()
    assert res[0]["response_code"] == 201
    assert res[0]["content"]["name"] == branch_arm_name_1
    assert res[1]["response_code"] == 201
    assert res[1]["content"]["name"] == branch_arm_name_2
    study_branch_arm_1_uid = res[0]["content"]["branch_arm_uid"]
    study_branch_arm_2_uid = res[1]["content"]["branch_arm_uid"]

    response = api_client.get(f"/studies/{test_study.uid}/study-branch-arms")
    assert_response_status_code(response, 200)
    study_branch_arms = response.json()["items"]

    assert len(study_branch_arms) == 2
    assert study_branch_arms[0]["name"] == branch_arm_name_1
    assert study_branch_arms[1]["name"] == branch_arm_name_2

    response = api_client.post(
        f"/studies/{test_study.uid}/study-branch-arms/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "branch_arm_uid": study_branch_arm_1_uid,
                    "name": branch_arm_name_2,
                },
            },
        ],
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"Value '{branch_arm_name_2}' in field Branch Arm Name is not unique for the study."
    )

    response = api_client.post(
        f"/studies/{test_study.uid}/study-branch-arms/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "branch_arm_uid": study_branch_arm_1_uid,
                    "name": branch_arm_name_2,
                },
            },
            {
                "method": "PATCH",
                "content": {
                    "branch_arm_uid": study_branch_arm_2_uid,
                    "name": branch_arm_name_1,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 200
    assert res[0]["content"]["name"] == branch_arm_name_2
    assert res[1]["response_code"] == 200
    assert res[1]["content"]["name"] == branch_arm_name_1

    response = api_client.post(
        f"/studies/{test_study.uid}/study-branch-arms/batch",
        json=[
            {
                "method": "DELETE",
                "content": {
                    "branch_arm_uid": study_branch_arm_1_uid,
                },
            },
            {
                "method": "DELETE",
                "content": {
                    "branch_arm_uid": study_branch_arm_2_uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 204
    assert res[1]["response_code"] == 204

    response = api_client.get(f"/studies/{test_study.uid}/study-branch-arms")
    assert_response_status_code(response, 200)
    study_branch_arms = response.json()["items"]
    assert len(study_branch_arms) == 0


def test_derived_number_of_subjects_property(api_client):
    test_study = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{test_study.uid}/study-design-classes",
        json={
            "value": StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value
        },
    )
    assert_response_status_code(response, 201)

    study_arm = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        name="test_arm",
        short_name="test_arm",
        number_of_subjects=100,
    )
    study_cohort_1 = TestUtils.create_study_cohort(
        study_uid=test_study.uid,
        name="cohort name 1",
        short_name="cohort name 1",
        arm_uids=[study_arm.arm_uid],
        number_of_subjects=30,
    )
    study_cohort_2 = TestUtils.create_study_cohort(
        study_uid=test_study.uid,
        name="cohort name 2",
        short_name="cohort name 2",
        arm_uids=[study_arm.arm_uid],
        number_of_subjects=70,
    )
    response = api_client.post(
        f"/studies/{test_study.uid}/study-branch-arms/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "name": "Unique branch arm name1",
                    "short_name": "BranchArm_Short_Name_1",
                    "code": "BranchArm_code_1",
                    "description": "desc...",
                    "randomization_group": "Randomization_Group_1",
                    "number_of_subjects": 5,
                    "arm_uid": study_arm.arm_uid,
                    "study_cohort_uid": study_cohort_1.cohort_uid,
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": "Unique branch arm name2",
                    "short_name": "BranchArm_Short_Name_2",
                    "code": "BranchArm_code_2",
                    "description": "desc...",
                    "randomization_group": "Randomization_Group_2",
                    "number_of_subjects": 5,
                    "arm_uid": study_arm.arm_uid,
                    "study_cohort_uid": study_cohort_1.cohort_uid,
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": "Unique branch arm name3",
                    "short_name": "BranchArm_Short_Name_3",
                    "code": "BranchArm_code_3",
                    "description": "desc...",
                    "randomization_group": "Randomization_Group_3",
                    "number_of_subjects": 5,
                    "arm_uid": study_arm.arm_uid,
                    "study_cohort_uid": study_cohort_2.cohort_uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)

    response = api_client.get(f"/studies/{test_study.uid}/study-arms")
    assert_response_status_code(response, 200)
    study_arms = response.json()["items"]
    assert len(study_arms) == 1
    assert study_arms[0]["number_of_subjects"] == 15

    response = api_client.get(f"/studies/{test_study.uid}/study-cohorts")
    assert_response_status_code(response, 200)
    study_cohorts = response.json()["items"]
    assert len(study_cohorts) == 2
    assert study_cohorts[0]["number_of_subjects"] == 10
    assert study_cohorts[1]["number_of_subjects"] == 5

    response = api_client.get(f"/studies/{test_study.uid}/study-branch-arms")
    assert_response_status_code(response, 200)
    study_branch_arms = response.json()["items"]
    assert len(study_branch_arms) > 1
    last_study_branch_arm = study_branch_arms[-1]

    response = api_client.patch(
        f"/studies/{test_study.uid}/study-branch-arms/{last_study_branch_arm['branch_arm_uid']}",
        json={"number_of_subjects": 20},
    )
    assert_response_status_code(response, 200)
    response = api_client.get(
        f"/studies/{test_study.uid}/study-branch-arms/{last_study_branch_arm['branch_arm_uid']}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["number_of_subjects"] == 20

    response = api_client.get(f"/studies/{test_study.uid}/study-arms")
    assert_response_status_code(response, 200)
    study_arms = response.json()["items"]
    assert len(study_arms) == 1
    assert study_arms[0]["number_of_subjects"] == 30

    response = api_client.get(f"/studies/{test_study.uid}/study-cohorts")
    assert_response_status_code(response, 200)
    study_cohorts = response.json()["items"]
    assert len(study_cohorts) == 2
    assert study_cohorts[0]["number_of_subjects"] == 10
    assert study_cohorts[1]["number_of_subjects"] == 20

    # Edit StudyDesignClass to check if number_of_subject properties has changed
    response = api_client.put(
        f"/studies/{test_study.uid}/study-design-classes",
        json={"value": StudyDesignClassEnum.MANUAL.value},
    )
    assert_response_status_code(response, 200)
    # Verify StudyBranchArms are removed when switching from Cohort stepper to Study with arms only
    response = api_client.get(f"/studies/{test_study.uid}/study-branch-arms")
    assert_response_status_code(response, 200)
    study_branch_arms = response.json()["items"]
    assert len(study_branch_arms) == 0
    # Verify StudyCohorts are removed when switching from Cohort stepper to Study with arms only
    response = api_client.get(f"/studies/{test_study.uid}/study-cohorts")
    assert_response_status_code(response, 200)
    study_cohorts = response.json()["items"]
    assert len(study_cohorts) == 0

    response = api_client.get(f"/studies/{test_study.uid}/study-arms")
    assert_response_status_code(response, 200)
    study_arms = response.json()["items"]
    assert len(study_arms) == 1
    assert study_arms[0]["number_of_subjects"] == 100

    orphaned_cohort = TestUtils.create_study_cohort(
        study_uid=test_study.uid,
        name="orphaned cohort",
        short_name="orphaned cohort",
    )

    # Create simple StudyBranchArm and edit StudyDesignClass back to cohort stepper to see whether StudyBranchArm is removed
    TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="_",
        short_name="_",
        code="_",
        randomization_group="_",
        number_of_subjects=5,
        study_arm_uid=study_arm.arm_uid,
    )
    response = api_client.put(
        f"/studies/{test_study.uid}/study-design-classes",
        json={
            "value": StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.get(f"/studies/{test_study.uid}/study-arms")
    assert_response_status_code(response, 200)
    study_arms = response.json()["items"]
    assert len(study_arms) == 1
    assert study_arms[0]["number_of_subjects"] == 0

    response = api_client.get(f"/studies/{test_study.uid}/study-cohorts")
    assert_response_status_code(response, 200)
    study_cohorts = response.json()["items"]
    assert len(study_cohorts) == 1
    assert study_cohorts[0]["number_of_subjects"] == 0
    assert study_cohorts[0]["name"] == orphaned_cohort.name

    # Verify StudyBranchArms are removed when switching from Study with arms only to Cohort stepper
    response = api_client.get(f"/studies/{test_study.uid}/study-branch-arms")
    assert_response_status_code(response, 200)
    study_branch_arms = response.json()["items"]
    assert len(study_branch_arms) == 0


def test_study_arms_branches_and_cohorts_endpoint(api_client):
    test_study = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{test_study.uid}/study-design-classes",
        json={
            "value": StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-arms-branches-and-cohorts"
    )
    assert_response_status_code(response, 200)
    study_arms_branches_and_cohorts = response.json()
    assert len(study_arms_branches_and_cohorts) == 0

    study_arm = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        name="test_arm",
        short_name="test_arm",
    )

    study_cohort_1 = TestUtils.create_study_cohort(
        study_uid=test_study.uid,
        name="cohort name 1",
        short_name="cohort name 1",
        arm_uids=[study_arm.arm_uid],
    )

    study_cohort_2 = TestUtils.create_study_cohort(
        study_uid=test_study.uid,
        name="cohort name 2",
        short_name="cohort name 2",
        arm_uids=[study_arm.arm_uid],
    )

    study_branch_arm_1 = TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="Unique branch arm name1",
        short_name="BranchArm_Short_Name_1",
        code="BranchArm_code_1",
        randomization_group="Randomization_Group_1",
        number_of_subjects=5,
        study_arm_uid=study_arm.arm_uid,
        study_cohort_uid=study_cohort_1.cohort_uid,
    )
    study_branch_arm_2 = TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="Unique branch arm name2",
        short_name="BranchArm_Short_Name_2",
        code="BranchArm_code_2",
        randomization_group="Randomization_Group_2",
        number_of_subjects=5,
        study_arm_uid=study_arm.arm_uid,
        study_cohort_uid=study_cohort_1.cohort_uid,
    )
    study_branch_arm_3 = TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="Unique branch arm name3",
        short_name="BranchArm_Short_Name_3",
        code="BranchArm_code_3",
        randomization_group="Randomization_Group_3",
        number_of_subjects=5,
        study_arm_uid=study_arm.arm_uid,
        study_cohort_uid=study_cohort_2.cohort_uid,
    )

    response = api_client.patch(
        f"/studies/{test_study.uid}/study-branch-arms/{study_branch_arm_3.branch_arm_uid}",
        json={"number_of_subjects": 20},
    )
    assert_response_status_code(response, 200)
    study_branch_arm_3 = response.json()

    response = api_client.get(
        f"/studies/{test_study.uid}/study-arms/{study_arm.arm_uid}"
    )
    assert_response_status_code(response, 200)
    study_arm = response.json()
    response = api_client.get(
        f"/studies/{test_study.uid}/study-cohorts/{study_cohort_1.cohort_uid}"
    )
    assert_response_status_code(response, 200)
    study_cohort_1 = response.json()
    response = api_client.get(
        f"/studies/{test_study.uid}/study-cohorts/{study_cohort_2.cohort_uid}"
    )
    assert_response_status_code(response, 200)
    study_cohort_2 = response.json()

    response = api_client.get(
        f"/studies/{test_study.uid}/study-arms-branches-and-cohorts"
    )
    assert_response_status_code(response, 200)
    study_arms_branches_and_cohorts = response.json()

    assert len(study_arms_branches_and_cohorts) == 1
    assert study_arms_branches_and_cohorts[0]["uid"] == study_arm["arm_uid"]
    assert study_arms_branches_and_cohorts[0]["name"] == study_arm["name"]
    assert study_arms_branches_and_cohorts[0]["short_name"] == study_arm["short_name"]
    assert (
        study_arms_branches_and_cohorts[0]["number_of_subjects"]
        == study_arm["number_of_subjects"]
    )

    assert len(study_arms_branches_and_cohorts[0]["study_cohorts"]) == 2
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][0]["uid"]
        == study_cohort_1["cohort_uid"]
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][0]["name"]
        == study_cohort_1["name"]
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][0]["short_name"]
        == study_cohort_1["short_name"]
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][0]["number_of_subjects"]
        == study_cohort_1["number_of_subjects"]
    )
    assert (
        len(study_arms_branches_and_cohorts[0]["study_cohorts"][0]["study_branch_arms"])
        == 2
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][0]["study_branch_arms"][0][
            "uid"
        ]
        == study_branch_arm_1.branch_arm_uid
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][0]["study_branch_arms"][0][
            "number_of_subjects"
        ]
        == study_branch_arm_1.number_of_subjects
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][0]["study_branch_arms"][1][
            "uid"
        ]
        == study_branch_arm_2.branch_arm_uid
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][0]["study_branch_arms"][1][
            "number_of_subjects"
        ]
        == study_branch_arm_2.number_of_subjects
    )

    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][1]["uid"]
        == study_cohort_2["cohort_uid"]
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][1]["name"]
        == study_cohort_2["name"]
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][1]["short_name"]
        == study_cohort_2["short_name"]
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][1]["number_of_subjects"]
        == study_cohort_2["number_of_subjects"]
    )
    assert (
        len(study_arms_branches_and_cohorts[0]["study_cohorts"][1]["study_branch_arms"])
        == 1
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][1]["study_branch_arms"][0][
            "uid"
        ]
        == study_branch_arm_3["branch_arm_uid"]
    )
    assert (
        study_arms_branches_and_cohorts[0]["study_cohorts"][1]["study_branch_arms"][0][
            "number_of_subjects"
        ]
        == study_branch_arm_3["number_of_subjects"]
    )


def test_deleted_branch_arms_not_returned_in_study_arms_endpoints(api_client):
    test_study = TestUtils.create_study()

    # update study title so the study can be locked
    response = api_client.patch(
        f"/studies/{test_study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    study_arm = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        name="Arm with deletions",
        short_name="Arm with deletions short",
    )
    branch_arm_keep = TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="Branch arm to keep",
        short_name="Branch arm to keep short",
        code="keep",
        study_arm_uid=study_arm.arm_uid,
    )
    branch_arm_delete = TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="Branch arm to delete",
        short_name="Branch arm to delete short",
        code="delete",
        study_arm_uid=study_arm.arm_uid,
    )

    # Lock the study — this creates a versioned StudyValue (version "1") whose
    # HAS_STUDY_BRANCH_ARM relationships still point to both branch arms.
    response = api_client.post(
        f"/studies/{test_study.uid}/locks",
        json={
            "change_description": "Lock for delete test",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # Unlock so the study is editable again
    response = api_client.post(
        f"/studies/{test_study.uid}/unlocks",
        json={
            "change_description": "Unlock for delete test",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # Delete one branch arm — this disconnects it from the *latest* StudyValue only;
    # the locked StudyValue (version "1") still has HAS_STUDY_BRANCH_ARM to it.
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-branch-arms/{branch_arm_delete.branch_arm_uid}"
    )
    assert_response_status_code(response, 204)

    # GET /study-arms?study_value_version=1 — the versioned StudyValue still has
    # HAS_STUDY_BRANCH_ARM to the deleted node, so the Delete label guard is the only
    # thing preventing it from appearing. This would fail without the fix.
    response = api_client.get(
        f"/studies/{test_study.uid}/study-arms?study_value_version=1"
    )
    assert_response_status_code(response, 200)
    arms = response.json()["items"]
    assert len(arms) == 1
    connected = arms[0]["arm_connected_branch_arms"]
    assert connected is not None
    connected_uids = [b["branch_arm_uid"] for b in connected]
    assert branch_arm_keep.branch_arm_uid in connected_uids
    assert branch_arm_delete.branch_arm_uid not in connected_uids

    # GET /study-arms/{arm_uid}?study_value_version=1 — same check on the single-arm endpoint
    response = api_client.get(
        f"/studies/{test_study.uid}/study-arms/{study_arm.arm_uid}?study_value_version=1"
    )
    assert_response_status_code(response, 200)
    arm = response.json()
    connected = arm["arm_connected_branch_arms"]
    assert connected is not None
    connected_uids = [b["branch_arm_uid"] for b in connected]
    assert branch_arm_keep.branch_arm_uid in connected_uids
    assert branch_arm_delete.branch_arm_uid not in connected_uids


def test_study_branch_arm_is_not_updated_when_same_payload_is_sent(api_client):
    test_study = TestUtils.create_study()

    study_arm = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        name="Arm 1 name",
        short_name="Arm 1 short name",
        description="Arm 1 description",
    )

    study_cohort = TestUtils.create_study_cohort(
        study_uid=test_study.uid,
        name="cohort name 1",
        short_name="cohort name 1",
        arm_uids=[study_arm.arm_uid],
    )
    study_branch_arm = TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="Unique branch arm name",
        short_name="BranchArm_Short_Name",
        code="BranchArm_code",
        randomization_group="Randomization_Group",
        number_of_subjects=5,
        study_arm_uid=study_arm.arm_uid,
        study_cohort_uid=study_cohort.cohort_uid,
    )
    # edit branch arm
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-branch-arms/{study_branch_arm.branch_arm_uid}",
        json={
            "name": "Unique branch arm name",
            "short_name": "BranchArm_Short_Name",
            "code": "BranchArm_code",
            "randomization_group": "Randomization_Group",
            "number_of_subjects": 5,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["name"] == "Unique branch arm name"
    assert res["short_name"] == "BranchArm_Short_Name"

    # get branch arm audit trail
    response = api_client.get(
        f"/studies/{test_study.uid}/study-branch-arms/{study_branch_arm.branch_arm_uid}/audit-trail",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 1
