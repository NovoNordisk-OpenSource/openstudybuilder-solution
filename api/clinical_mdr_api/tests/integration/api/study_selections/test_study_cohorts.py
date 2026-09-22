"""
Tests for /studies/{study_uid}/study-cohorts endpoints
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
study_arm: StudySelectionArm
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studycohortapi"
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


def test_cohort_modify_actions_on_locked_study(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-cohorts",
        json={
            "name": "Cohort_Name_1",
            "short_name": "Cohort_Short_Name_1",
            "code": "Cohort_code_1",
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # get all cohorts
    response = api_client.get(
        f"/studies/{study.uid}/study-cohort/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res
    cohort_uid = res[0]["cohort_uid"]

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
        f"/studies/{study.uid}/study-cohorts",
        json={
            "name": "Cohort_Name_2",
            "short_name": "Cohort_Short_Name_2",
            "code": "Cohort_code_2",
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."
    # edit cohort
    response = api_client.patch(
        f"/studies/{study.uid}/study-cohorts/{cohort_uid}",
        json={
            "name": "New_cohort_Name_1",
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-cohort/audit-trail/",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert old_res == res

    # test cannot delete
    response = api_client.delete(f"/studies/{study.uid}/study-cohorts/{cohort_uid}")
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


def test_study_cohort_study_value_version(api_client):
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
    res = response.json()
    branch_arm = res

    response = api_client.post(
        f"/studies/{study.uid}/study-cohorts",
        json={
            "name": "Cohort_Name_2",
            "short_name": "Cohort_Short_Name_2",
            "code": "Cohort_code_2",
            "arm_uids": [
                study_arm.arm_uid,
            ],
            "branch_arm_uids": [
                branch_arm["branch_arm_uid"],
            ],
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    cohort = res

    before_unlock_arms = api_client.get(f"/studies/{study.uid}/study-arms").json()
    before_unlock_branch_arms = api_client.get(
        f"/studies/{study.uid}/study-branch-arms"
    ).json()["items"]
    before_unlock_cohorts = api_client.get(f"/studies/{study.uid}/study-cohorts").json()

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
            "name": "New_Arm_Name_1",
        },
    )
    assert_response_status_code(response, 200)
    response.json()

    # edit branch arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-branch-arms/{branch_arm['branch_arm_uid']}",
        json={
            "name": "New_Branch_Arm_Name_1",
        },
    )
    assert_response_status_code(response, 200)
    response.json()

    # edit cohort
    response = api_client.patch(
        f"/studies/{study.uid}/study-cohorts/{cohort['cohort_uid']}",
        json={
            "name": "New_cohort_Name_2",
        },
    )
    assert_response_status_code(response, 200)
    response.json()

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
        ).json()["items"]
    )
    for i, _ in enumerate(before_unlock_cohorts["items"]):
        before_unlock_cohorts["items"][i]["study_version"] = mock.ANY
        if before_unlock_cohorts["items"][i]["branch_arm_roots"]:
            for ith_branch, _ in enumerate(
                before_unlock_cohorts["items"][i]["branch_arm_roots"]
            ):
                before_unlock_cohorts["items"][i]["branch_arm_roots"][ith_branch][
                    "study_version"
                ] = mock.ANY
    assert (
        before_unlock_cohorts
        == api_client.get(
            f"/studies/{study.uid}/study-cohorts?study_value_version=2"
        ).json()
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
def test_get_study_cohorts_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-cohorts"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_batch_operations(api_client):
    test_study = TestUtils.create_study()

    cohort_name_1 = "Cohort_Name_1"
    cohort_name_2 = "Cohort_Name_2"
    response = api_client.post(
        f"/studies/{test_study.uid}/study-cohorts/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "name": cohort_name_1,
                    "short_name": "Cohort_Short_Name_1",
                    "code": "Cohort_code_1",
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": cohort_name_2,
                    "short_name": "Cohort_Short_Name_2",
                    "code": "Cohort_code_2",
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 201
    assert res[0]["content"]["name"] == cohort_name_1
    assert res[1]["response_code"] == 201
    assert res[1]["content"]["name"] == cohort_name_2
    study_cohort_1_uid = res[0]["content"]["cohort_uid"]
    study_cohort_2_uid = res[1]["content"]["cohort_uid"]

    response = api_client.get(f"/studies/{test_study.uid}/study-cohorts")
    assert_response_status_code(response, 200)
    study_cohorts = response.json()["items"]

    assert len(study_cohorts) == 2
    assert study_cohorts[0]["name"] == cohort_name_1
    assert study_cohorts[1]["name"] == cohort_name_2

    response = api_client.post(
        f"/studies/{test_study.uid}/study-cohorts/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "cohort_uid": study_cohort_1_uid,
                    "name": cohort_name_2,
                    "short_name": "Cohort_Short_Name_1",
                    "code": "Cohort_code_1",
                },
            },
        ],
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"Value '{cohort_name_2}' in field Cohort Name is not unique for the study."
    )

    response = api_client.post(
        f"/studies/{test_study.uid}/study-cohorts/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "cohort_uid": study_cohort_1_uid,
                    "name": cohort_name_2,
                    "short_name": "Cohort_Short_Name_1",
                    "code": "Cohort_code_1",
                },
            },
            {
                "method": "PATCH",
                "content": {
                    "cohort_uid": study_cohort_2_uid,
                    "name": cohort_name_1,
                    "short_name": "Cohort_Short_Name_2",
                    "code": "Cohort_code_2",
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 200
    assert res[0]["content"]["name"] == cohort_name_2
    assert res[1]["response_code"] == 200
    assert res[1]["content"]["name"] == cohort_name_1


def test_study_arm_delete_cascade_deletes_study_branch_arms(api_client):
    test_study = TestUtils.create_study()

    study_arm = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        name="test_arm",
        short_name="test_arm",
    )

    study_cohort_1 = TestUtils.create_study_cohort(
        study_uid=test_study.uid, name="cohort name 1", short_name="cohort name 1"
    )

    study_cohort_2 = TestUtils.create_study_cohort(
        study_uid=test_study.uid, name="cohort name 2", short_name="cohort name 2"
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

    response = api_client.get(f"/studies/{test_study.uid}/study-branch-arms")
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 3

    # Delete first StudyCohort
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-cohorts/{study_cohort_1.cohort_uid}?delete_linked_branches=true"
    )
    assert_response_status_code(response, 204)

    # Verify the StudyCohort is deleted
    response = api_client.get(
        f"/studies/{test_study.uid}/study-cohorts/{study_cohort_1.cohort_uid}"
    )
    assert_response_status_code(response, 404)

    # Verify that StudyBranchArms are cascade deleted
    response = api_client.get(
        f"/studies/{test_study.uid}/study-branch-arms/{study_branch_arm_1.branch_arm_uid}"
    )
    assert_response_status_code(response, 404)
    response = api_client.get(
        f"/studies/{test_study.uid}/study-branch-arms/{study_branch_arm_2.branch_arm_uid}"
    )
    assert_response_status_code(response, 404)

    # Delete second StudyCohort
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-cohorts/{study_cohort_2.cohort_uid}"
    )
    assert_response_status_code(response, 204)

    # Verify the StudyCohort is deleted
    response = api_client.get(
        f"/studies/{test_study.uid}/study-cohorts/{study_cohort_2.cohort_uid}"
    )
    assert_response_status_code(response, 404)

    # Verify that StudyBranchArms were not cascade deleted
    response = api_client.get(
        f"/studies/{test_study.uid}/study-branch-arms/{study_branch_arm_3.branch_arm_uid}"
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"/studies/{test_study.uid}/study-branch-arms")
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 1

    response = api_client.get(f"/studies/{test_study.uid}/study-arms")
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 1


def test_study_cohort_is_not_updated_when_same_payload_is_sent(api_client):
    test_study = TestUtils.create_study()

    test_arm = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        name="Arm 1 name",
        short_name="Arm 1 short name",
        description="Arm 1 description",
    )

    study_cohort = TestUtils.create_study_cohort(
        study_uid=test_study.uid,
        name="cohort name 1",
        short_name="cohort name 1",
        arm_uids=[test_arm.arm_uid],
    )
    # edit cohort
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-cohorts/{study_cohort.cohort_uid}",
        json={
            "name": "cohort name 1",
            "short_name": "cohort name 1",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["name"] == "cohort name 1"
    assert res["short_name"] == "cohort name 1"

    # get study cohort audit trail
    response = api_client.get(
        f"/studies/{test_study.uid}/study-cohorts/{study_cohort.cohort_uid}/audit-trail",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 1


def test_study_cohort_loses_relationship_to_arm_when_branch_arm_gets_deleted_when_cohorts_are_created_by_cohort_stepper(
    api_client,
):
    test_study = TestUtils.create_study()

    # Create StudyDesignClass for CohortStepper
    response = api_client.post(
        f"/studies/{test_study.uid}/study-design-classes",
        json={
            "value": StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value
        },
    )
    assert_response_status_code(response, 201)

    study_arm_1 = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        name="Arm 1 name",
        short_name="Arm 1 short name",
        description="Arm 1 description",
    )
    study_arm_2 = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        name="Arm 2 name",
        short_name="Arm 2 short name",
        description="Arm 2 description",
    )
    study_cohort = TestUtils.create_study_cohort(
        study_uid=test_study.uid,
        name="cohort name 1",
        short_name="cohort name 1",
    )
    study_branch_arm_1 = TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="Branch arm name 1",
        short_name="Branch arm short name 1",
        code="Branch code 1",
        randomization_group="Randomization group 1",
        number_of_subjects=1,
        study_arm_uid=study_arm_1.arm_uid,
        study_cohort_uid=study_cohort.cohort_uid,
    )
    study_branch_arm_2 = TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="Branch arm name 2",
        short_name="Branch arm short name 2",
        code="Branch code 2",
        randomization_group="Randomization group 2",
        number_of_subjects=2,
        study_arm_uid=study_arm_2.arm_uid,
        study_cohort_uid=study_cohort.cohort_uid,
    )

    response = api_client.get(f"/studies/{test_study.uid}/study-cohorts")
    assert_response_status_code(response, 200)
    study_cohorts = response.json()["items"]
    assert len(study_cohorts) == 1

    # Check StudyArms in scope of StudyCohort response
    assert len(study_cohorts[0]["arm_roots"]) == 2
    assert study_cohorts[0]["arm_roots"][0]["arm_uid"] == study_arm_1.arm_uid
    assert study_cohorts[0]["arm_roots"][1]["arm_uid"] == study_arm_2.arm_uid

    # Check StudyBranchArms in scope of StudyCohort response
    assert len(study_cohorts[0]["branch_arm_roots"]) == 2
    assert (
        study_cohorts[0]["branch_arm_roots"][0]["branch_arm_uid"]
        == study_branch_arm_1.branch_arm_uid
    )
    assert (
        study_cohorts[0]["branch_arm_roots"][1]["branch_arm_uid"]
        == study_branch_arm_2.branch_arm_uid
    )

    # After deleting one StudyBranchArm, the StudyCohort response should return only one StudyArm object as the path to StudyArm leads through deleted StudyBranch
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-branch-arms/{study_branch_arm_1.branch_arm_uid}"
    )
    assert_response_status_code(response, 204)

    response = api_client.get(f"/studies/{test_study.uid}/study-cohorts")
    assert_response_status_code(response, 200)
    study_cohorts = response.json()["items"]
    assert len(study_cohorts) == 1

    # Check StudyArms in scope of StudyCohort response
    assert len(study_cohorts[0]["arm_roots"]) == 1
    assert study_cohorts[0]["arm_roots"][0]["arm_uid"] == study_arm_2.arm_uid

    # Check StudyBranchArms in scope of StudyCohort response
    assert len(study_cohorts[0]["branch_arm_roots"]) == 1
    assert (
        study_cohorts[0]["branch_arm_roots"][0]["branch_arm_uid"]
        == study_branch_arm_2.branch_arm_uid
    )
