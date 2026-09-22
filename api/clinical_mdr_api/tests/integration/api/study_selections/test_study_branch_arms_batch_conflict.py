"""
Tests for study branch arm batch POST conflict resolution and copy-from-study endpoint.
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import logging
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies import ct_term
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

study: Study
investigational_arm: ct_term.CTTerm
placebo_arm_type: ct_term.CTTerm


@pytest.fixture(scope="module")
def api_client():
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    db_name = "studybrancharmbatchconflictapi"
    inject_and_clear_db(db_name)

    global study, investigational_arm, placebo_arm_type
    study, _ = inject_base_data()

    _catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    catalogue_name = "SDTM CT"
    ct_term_codelist = create_codelist(
        "Arm Type",
        "CTCodelist_ArmType_BranchBatchConflict",
        catalogue_name,
        library_name,
        submission_value="ARMTTP",
    )

    investigational_arm = TestUtils.create_ct_term(
        codelist_uid=ct_term_codelist.codelist_uid,
        submission_value="Investigational Arm",
        sponsor_preferred_name="Investigational Arm",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=datetime(2020, 3, 25, tzinfo=timezone.utc),
        approve=True,
    )
    placebo_arm_type = TestUtils.create_ct_term(
        codelist_uid=ct_term_codelist.codelist_uid,
        submission_value="Placebo Arm",
        sponsor_preferred_name="Placebo Arm",
        order=2,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=datetime(2020, 3, 25, tzinfo=timezone.utc),
        approve=True,
    )

    for term in (investigational_arm, placebo_arm_type):
        db.cypher_query(
            """
            MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val)
            WHERE n.uid = $uid AND EXISTS((ct_name)-[:LATEST]-(val))
              AND has_version.status = 'Final'
            SET has_version.start_date = $date
            """,
            params={
                "uid": term.term_uid,
                "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
            },
        )

    db.cypher_query(
        """
        MATCH (n)-[:HAS_ATTRIBUTES_ROOT]-(attr:CTCodelistAttributesRoot)-[has_version:HAS_VERSION]-(val)
        WHERE n.uid = $uid AND EXISTS((attr)-[:LATEST]-(val))
          AND has_version.status = 'Final'
        SET has_version.start_date = $date
        """,
        params={
            "uid": ct_term_codelist.codelist_uid,
            "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
        },
    )


@pytest.fixture(scope="module")
def arm_types(test_data):
    yield {
        "investigational": investigational_arm,
        "placebo": placebo_arm_type,
    }


def _post_batch(api_client, study_uid: str, payload: list[dict[str, Any]]):
    return api_client.post(
        f"/studies/{study_uid}/study-branch-arms/batch", json=payload
    )


def test_batch_post_three_unique_branch_arms(api_client, arm_types):
    target_study = TestUtils.create_study()
    study_arm = TestUtils.create_study_arm(
        study_uid=target_study.uid,
        name="MCPBranchBatchArm",
        short_name="MCPBBA1",
        arm_type_uid=arm_types["investigational"].term_uid,
    )

    response = _post_batch(
        api_client,
        target_study.uid,
        [
            {
                "method": "POST",
                "content": {
                    "name": "MCPBranchBatch1",
                    "short_name": "MCPBB1",
                    "arm_uid": study_arm.arm_uid,
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": "MCPBranchBatch2",
                    "short_name": "MCPBB2",
                    "arm_uid": study_arm.arm_uid,
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": "MCPBranchBatch3",
                    "short_name": "MCPBB3",
                    "arm_uid": study_arm.arm_uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert len(res) == 3
    assert all(item["response_code"] == 201 for item in res)


def test_batch_post_skip_by_name(api_client, arm_types):
    target_study = TestUtils.create_study()
    study_arm = TestUtils.create_study_arm(
        study_uid=target_study.uid,
        name="MCPBranchSkipArm",
        short_name="MCPBSA1",
        arm_type_uid=arm_types["investigational"].term_uid,
    )
    TestUtils.create_study_branch_arm(
        study_uid=target_study.uid,
        name="MCPBranchSkipName",
        short_name="MCPBSN1",
        study_arm_uid=study_arm.arm_uid,
    )

    response = _post_batch(
        api_client,
        target_study.uid,
        [
            {
                "method": "POST",
                "content": {
                    "name": "MCPBranchSkipName",
                    "short_name": "MCPBSN2",
                    "arm_uid": study_arm.arm_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 200
    assert "creation skipped" in res[0]["notification"]
    assert res[0]["content"]["name"] == "MCPBranchSkipName"


def test_batch_post_skip_by_short_name(api_client, arm_types):
    target_study = TestUtils.create_study()
    study_arm = TestUtils.create_study_arm(
        study_uid=target_study.uid,
        name="MCPBranchSkipShortArm",
        short_name="MCPBSSA1",
        arm_type_uid=arm_types["investigational"].term_uid,
    )
    TestUtils.create_study_branch_arm(
        study_uid=target_study.uid,
        name="MCPBranchSkipShort1",
        short_name="MCPBSSH",
        study_arm_uid=study_arm.arm_uid,
    )

    response = _post_batch(
        api_client,
        target_study.uid,
        [
            {
                "method": "POST",
                "content": {
                    "name": "MCPBranchSkipShort2",
                    "short_name": "MCPBSSH",
                    "arm_uid": study_arm.arm_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 200
    assert "creation skipped" in res[0]["notification"]
    assert res[0]["content"]["short_name"] == "MCPBSSH"


def test_batch_mixed_patch_and_post(api_client, arm_types):
    target_study = TestUtils.create_study()
    study_arm = TestUtils.create_study_arm(
        study_uid=target_study.uid,
        name="MCPBranchMixedArm",
        short_name="MCPBMA1",
        arm_type_uid=arm_types["investigational"].term_uid,
    )
    existing_branch = TestUtils.create_study_branch_arm(
        study_uid=target_study.uid,
        name="MCPBranchMixedExisting",
        short_name="MCPBME1",
        study_arm_uid=study_arm.arm_uid,
    )
    api_client.patch(
        f"/studies/{target_study.uid}/study-branch-arms/{existing_branch.branch_arm_uid}",
        json={"description": "Original description"},
    )

    response = _post_batch(
        api_client,
        target_study.uid,
        [
            {
                "method": "PATCH",
                "content": {
                    "branch_arm_uid": existing_branch.branch_arm_uid,
                    "description": "Updated description",
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": "MCPBranchMixedNew",
                    "short_name": "MCPBMN1",
                    "arm_uid": study_arm.arm_uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert len(res) == 2
    assert res[0]["response_code"] == 200
    assert res[0]["content"]["description"] == "Updated description"
    assert res[1]["response_code"] == 201
    assert res[1]["content"]["name"] == "MCPBranchMixedNew"


def test_copy_from_study_creates_all_branch_arms(api_client, arm_types):
    source_study = TestUtils.create_study()
    target_study = TestUtils.create_study()
    arm_type_uid = arm_types["investigational"].term_uid
    source_arm = TestUtils.create_study_arm(
        study_uid=source_study.uid,
        name="MCPSourceParentArm",
        short_name="MCPSPA1",
        arm_type_uid=arm_type_uid,
    )
    target_arm = TestUtils.create_study_arm(
        study_uid=target_study.uid,
        name="MCPSourceParentArm",
        short_name="MCPTPA1",
        arm_type_uid=arm_type_uid,
    )
    TestUtils.create_study_branch_arm(
        study_uid=source_study.uid,
        name="MCPCopyBranch1",
        short_name="MCPCB1",
        study_arm_uid=source_arm.arm_uid,
    )
    TestUtils.create_study_branch_arm(
        study_uid=source_study.uid,
        name="MCPCopyBranch2",
        short_name="MCPCB2",
        study_arm_uid=source_arm.arm_uid,
    )

    response = api_client.post(
        f"/studies/{target_study.uid}/study-branch-arms/copy-from-study/{source_study.uid}"
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert len(res) == 2
    assert all(item["response_code"] == 201 for item in res)
    assert all(
        item["content"]["arm_root"]["arm_uid"] == target_arm.arm_uid for item in res
    )

    list_response = api_client.get(f"/studies/{target_study.uid}/study-branch-arms")
    assert_response_status_code(list_response, 200)
    names = [item["name"] for item in list_response.json()["items"]]
    assert "MCPCopyBranch1" in names
    assert "MCPCopyBranch2" in names


def test_copy_from_study_skips_conflicting_branch_arm_on_target(api_client, arm_types):
    source_study = TestUtils.create_study()
    target_study = TestUtils.create_study()
    arm_type_uid = arm_types["investigational"].term_uid
    source_arm = TestUtils.create_study_arm(
        study_uid=source_study.uid,
        name="MCPCopyConflictParent",
        short_name="MCPCCP1",
        arm_type_uid=arm_type_uid,
    )
    target_arm = TestUtils.create_study_arm(
        study_uid=target_study.uid,
        name="MCPCopyConflictParent",
        short_name="MCPCCPT1",
        arm_type_uid=arm_type_uid,
    )
    TestUtils.create_study_branch_arm(
        study_uid=source_study.uid,
        name="MCPCopyConflictBranch",
        short_name="MCPCCB1",
        study_arm_uid=source_arm.arm_uid,
    )
    TestUtils.create_study_branch_arm(
        study_uid=source_study.uid,
        name="MCPCopyUniqueBranch",
        short_name="MCPCUB1",
        study_arm_uid=source_arm.arm_uid,
    )
    TestUtils.create_study_branch_arm(
        study_uid=target_study.uid,
        name="MCPCopyConflictBranch",
        short_name="MCPCCBT1",
        study_arm_uid=target_arm.arm_uid,
    )

    response = api_client.post(
        f"/studies/{target_study.uid}/study-branch-arms/copy-from-study/{source_study.uid}"
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert len(res) == 2
    assert res[0]["response_code"] == 200
    assert "creation skipped" in res[0]["notification"]
    assert res[0]["content"]["name"] == "MCPCopyConflictBranch"
    assert res[1]["response_code"] == 201
    assert res[1]["content"]["name"] == "MCPCopyUniqueBranch"

    list_response = api_client.get(f"/studies/{target_study.uid}/study-branch-arms")
    assert_response_status_code(list_response, 200)
    assert len(list_response.json()["items"]) == 2


def test_copy_from_study_skips_when_parent_arm_type_differs(api_client, arm_types):
    source_study = TestUtils.create_study()
    target_study = TestUtils.create_study()
    source_arm = TestUtils.create_study_arm(
        study_uid=source_study.uid,
        name="MCPParentArmTypeDiff",
        short_name="MCPPATD1",
        arm_type_uid=arm_types["investigational"].term_uid,
    )
    TestUtils.create_study_arm(
        study_uid=target_study.uid,
        name="MCPParentArmTypeDiff",
        short_name="MCPPATDT1",
        arm_type_uid=arm_types["placebo"].term_uid,
    )
    TestUtils.create_study_branch_arm(
        study_uid=source_study.uid,
        name="MCPBranchTypeDiff",
        short_name="MCPBTD1",
        study_arm_uid=source_arm.arm_uid,
    )

    response = api_client.post(
        f"/studies/{target_study.uid}/study-branch-arms/copy-from-study/{source_study.uid}"
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert len(res) == 1
    assert res[0]["response_code"] == 200
    assert res[0]["content"] is None
    assert "matches parent arm name 'MCPParentArmTypeDiff'" in res[0]["notification"]
    assert "arm type 'Investigational Arm'" in res[0]["notification"]

    list_response = api_client.get(f"/studies/{target_study.uid}/study-branch-arms")
    assert_response_status_code(list_response, 200)
    assert len(list_response.json()["items"]) == 0


def test_copy_from_study_skips_when_no_parent_arm_on_target(api_client, arm_types):
    source_study = TestUtils.create_study()
    target_study = TestUtils.create_study()
    source_arm = TestUtils.create_study_arm(
        study_uid=source_study.uid,
        name="MCPMissingParentArm",
        short_name="MCPMPA1",
        arm_type_uid=arm_types["investigational"].term_uid,
    )
    TestUtils.create_study_branch_arm(
        study_uid=source_study.uid,
        name="MCPOrphanBranch",
        short_name="MCPORB1",
        study_arm_uid=source_arm.arm_uid,
    )

    response = api_client.post(
        f"/studies/{target_study.uid}/study-branch-arms/copy-from-study/{source_study.uid}"
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert len(res) == 1
    assert res[0]["response_code"] == 200
    assert res[0]["content"] is None
    assert "matches parent arm name 'MCPMissingParentArm'" in res[0]["notification"]
    assert "arm type 'Investigational Arm'" in res[0]["notification"]


def test_copy_from_study_target_not_found(api_client, arm_types):
    source_study = TestUtils.create_study()
    response = api_client.post(
        f"/studies/Study_DoesNotExist/study-branch-arms/copy-from-study/{source_study.uid}"
    )
    assert_response_status_code(response, 404)


def test_copy_from_study_rejects_same_study(api_client):
    target_study = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{target_study.uid}/study-branch-arms/copy-from-study/{target_study.uid}"
    )
    assert_response_status_code(response, 400)
    assert "must differ" in response.json()["message"]


def test_copy_from_study_not_found(api_client):
    target_study = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{target_study.uid}/study-branch-arms/copy-from-study/Study_DoesNotExist"
    )
    assert_response_status_code(response, 404)


def test_copy_from_study_empty_source(api_client):
    source_study = TestUtils.create_study()
    target_study = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{target_study.uid}/study-branch-arms/copy-from-study/{source_study.uid}"
    )
    assert_response_status_code(response, 207)
    assert response.json() == []
