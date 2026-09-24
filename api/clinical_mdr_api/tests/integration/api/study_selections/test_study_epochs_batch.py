"""
Tests for study epoch batch preview and batch POST/PATCH endpoints.
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

SUBTYPE_1 = "EpochSubType_0001"
SUBTYPE_2 = "EpochSubType_0002"
SUBTYPE_3 = "EpochSubType_0003"
BASIC_SUBTYPE = "Basic_uid"
EPOCH_CT_1 = "Epoch_0001"


@pytest.fixture(scope="module")
def api_client():
    yield TestClient(app)


@pytest.fixture(scope="module")
def epoch_batch_test_data():
    db_name = "studyepochbatchapi"
    inject_and_clear_db(db_name)
    _, test_data_dict = inject_base_data()
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    create_study_epoch_codelists_ret_cat_and_lib(use_test_utils=True)
    yield test_data_dict


def _create_mcp_study(acronym: str):
    study = TestUtils.create_study(acronym=acronym)
    TestUtils.set_study_standard_version(study_uid=study.uid)
    return study


def _epoch_create_payload(
    study_uid: str, subtype_uid: str, **kwargs: Any
) -> dict[str, Any]:
    payload: dict[str, Any] = {"study_uid": study_uid, "epoch_subtype": subtype_uid}
    payload.update(kwargs)
    return payload


def _post_batch_preview(api_client, study_uid: str, payload: list[dict[str, Any]]):
    return api_client.post(
        f"/studies/{study_uid}/study-epochs/batch/preview", json=payload
    )


def _post_batch(api_client, study_uid: str, payload: list[dict[str, Any]]):
    return api_client.post(f"/studies/{study_uid}/study-epochs/batch", json=payload)


def _preview_response_to_batch_post(
    preview_body: dict[str, Any],
) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for item in preview_body["items"]:
        assert item["response_code"] == 200
        content = item["content"]
        operations.append(
            {
                "method": "POST",
                "content": {
                    "study_uid": content["study_uid"],
                    "epoch_subtype": content["epoch_subtype_ctterm"]["term_uid"],
                    "epoch": content["epoch"],
                    "description": content.get("description"),
                    "order": content.get("order"),
                    "duration": content.get("duration"),
                    "color_hash": content.get("color_hash"),
                    "start_rule": content.get("start_rule"),
                    "end_rule": content.get("end_rule"),
                    "duration_unit": content.get("duration_unit"),
                },
            }
        )
    return operations


def _normalize_affected_existing(
    affected: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return sorted(
        [
            {
                "uid": item["uid"],
                "epoch_subtype": item["epoch_subtype"],
                "current_epoch_name": item["current_epoch_name"],
                "proposed_epoch_name": item["proposed_epoch_name"],
                "current_epoch": item["current_epoch"],
                "proposed_epoch": item["proposed_epoch"],
            }
            for item in affected
        ],
        key=lambda item: item["uid"],
    )


def test_batch_preview_three_subtypes_empty_affected_existing(
    api_client, epoch_batch_test_data
):
    study = _create_mcp_study("MCPEpochBatch001")
    response = _post_batch_preview(
        api_client,
        study.uid,
        [
            _epoch_create_payload(study.uid, SUBTYPE_1),
            _epoch_create_payload(study.uid, SUBTYPE_2),
            _epoch_create_payload(study.uid, SUBTYPE_3),
        ],
    )
    assert_response_status_code(response, 200)
    body = response.json()
    assert len(body["items"]) == 3
    assert body["affected_existing"] == []
    assert all(item["response_code"] == 200 for item in body["items"])
    assert body["items"][0]["content"]["uid"] == "preview"


def test_batch_preview_with_epoch_sent(api_client, epoch_batch_test_data):
    study = _create_mcp_study("MCPEpochBatch002")
    response = _post_batch_preview(
        api_client,
        study.uid,
        [_epoch_create_payload(study.uid, SUBTYPE_1, epoch=EPOCH_CT_1)],
    )
    assert_response_status_code(response, 200)
    body = response.json()
    assert body["items"][0]["content"]["epoch"] == EPOCH_CT_1


def test_batch_preview_two_same_subtype_correct_ordinals_no_affected(
    api_client, epoch_batch_test_data
):
    study = _create_mcp_study("MCPEpochBatch003")
    response = _post_batch_preview(
        api_client,
        study.uid,
        [
            _epoch_create_payload(study.uid, SUBTYPE_1),
            _epoch_create_payload(study.uid, SUBTYPE_1),
        ],
    )
    assert_response_status_code(response, 200)
    body = response.json()
    assert body["affected_existing"] == []
    names = [item["content"]["epoch_name"] for item in body["items"]]
    assert names[0] == "Epoch Subtype"
    assert names[1] == "Epoch Subtype 2"


def test_batch_preview_affected_existing_renames_sole_existing(
    api_client, epoch_batch_test_data
):
    study = _create_mcp_study("MCPEpochBatch004")
    existing = create_study_epoch(SUBTYPE_1, study_uid=study.uid)
    response = _post_batch_preview(
        api_client,
        study.uid,
        [
            _epoch_create_payload(study.uid, SUBTYPE_1),
            _epoch_create_payload(study.uid, SUBTYPE_1),
        ],
    )
    assert_response_status_code(response, 200)
    body = response.json()
    assert len(body["affected_existing"]) == 1
    affected = body["affected_existing"][0]
    assert affected["uid"] == existing.uid
    assert affected["current_epoch_name"] == existing.epoch_name
    assert affected["proposed_epoch_name"] == "Epoch Subtype 1"


def test_batch_preview_affected_existing_deduplicated(
    api_client, epoch_batch_test_data
):
    study = _create_mcp_study("MCPEpochBatch005")
    existing = create_study_epoch(SUBTYPE_1, study_uid=study.uid)
    response = _post_batch_preview(
        api_client,
        study.uid,
        [
            _epoch_create_payload(study.uid, SUBTYPE_1),
            _epoch_create_payload(study.uid, SUBTYPE_1),
            _epoch_create_payload(study.uid, SUBTYPE_1),
        ],
    )
    assert_response_status_code(response, 200)
    body = response.json()
    affected_uids = [item["uid"] for item in body["affected_existing"]]
    assert affected_uids.count(existing.uid) == 1


def test_batch_post_three_epochs_without_preview(api_client, epoch_batch_test_data):
    study = _create_mcp_study("MCPEpochBatch006")
    response = _post_batch(
        api_client,
        study.uid,
        [
            {"method": "POST", "content": _epoch_create_payload(study.uid, SUBTYPE_1)},
            {"method": "POST", "content": _epoch_create_payload(study.uid, SUBTYPE_2)},
            {"method": "POST", "content": _epoch_create_payload(study.uid, SUBTYPE_3)},
        ],
    )
    assert_response_status_code(response, 207)
    body = response.json()
    assert len(body["items"]) == 3
    assert all(item["response_code"] == 201 for item in body["items"])
    assert body["affected_existing"] == []


def test_batch_post_with_epoch_sent(api_client, epoch_batch_test_data):
    study = _create_mcp_study("MCPEpochBatch007")
    response = _post_batch(
        api_client,
        study.uid,
        [
            {
                "method": "POST",
                "content": _epoch_create_payload(
                    study.uid, SUBTYPE_1, epoch=EPOCH_CT_1
                ),
            }
        ],
    )
    assert_response_status_code(response, 207)
    assert response.json()["items"][0]["content"]["epoch"] == EPOCH_CT_1


def test_batch_post_affected_existing_on_commit(api_client, epoch_batch_test_data):
    study = _create_mcp_study("MCPEpochBatch008")
    existing = create_study_epoch(SUBTYPE_1, study_uid=study.uid)
    response = _post_batch(
        api_client,
        study.uid,
        [
            {"method": "POST", "content": _epoch_create_payload(study.uid, SUBTYPE_1)},
        ],
    )
    assert_response_status_code(response, 207)
    body = response.json()
    assert len(body["affected_existing"]) == 1
    assert body["affected_existing"][0]["uid"] == existing.uid
    assert body["affected_existing"][0]["proposed_epoch_name"] == "Epoch Subtype 1"


def test_batch_post_affected_existing_matches_preview_forecast(
    api_client, epoch_batch_test_data
):
    study = _create_mcp_study("MCPEpochBatch015")
    existing = create_study_epoch(SUBTYPE_1, study_uid=study.uid)

    preview_response = _post_batch_preview(
        api_client,
        study.uid,
        [
            _epoch_create_payload(
                study.uid, SUBTYPE_1, description="MCP forecast add 1"
            ),
            _epoch_create_payload(
                study.uid, SUBTYPE_1, description="MCP forecast add 2"
            ),
        ],
    )
    assert_response_status_code(preview_response, 200)
    preview_body = preview_response.json()
    forecast = _normalize_affected_existing(preview_body["affected_existing"])
    assert len(forecast) == 1
    assert forecast[0]["uid"] == existing.uid
    assert forecast[0]["current_epoch_name"] == existing.epoch_name
    assert forecast[0]["proposed_epoch_name"] == "Epoch Subtype 1"

    post_response = _post_batch(
        api_client,
        study.uid,
        _preview_response_to_batch_post(preview_body),
    )
    assert_response_status_code(post_response, 207)
    post_body = post_response.json()
    actual = _normalize_affected_existing(post_body["affected_existing"])

    assert actual == forecast

    get_response = api_client.get(f"/studies/{study.uid}/study-epochs/{existing.uid}")
    assert_response_status_code(get_response, 200)
    assert get_response.json()["epoch_name"] == forecast[0]["proposed_epoch_name"]
    assert get_response.json()["epoch"] == forecast[0]["proposed_epoch"]


def test_batch_patch_edit(api_client, epoch_batch_test_data):
    study = _create_mcp_study("MCPEpochBatch009")
    existing = create_study_epoch(SUBTYPE_1, study_uid=study.uid)
    response = _post_batch(
        api_client,
        study.uid,
        [
            {
                "method": "PATCH",
                "content": {
                    "study_uid": study.uid,
                    "study_epoch_uid": existing.uid,
                    "description": "MCP batch patch description",
                    "change_description": "batch patch test",
                },
            }
        ],
    )
    assert_response_status_code(response, 207)
    body = response.json()
    assert body["items"][0]["response_code"] == 200
    assert body["items"][0]["content"]["description"] == "MCP batch patch description"


def test_reject_second_basic_epoch_batch_preview(api_client, epoch_batch_test_data):
    study = _create_mcp_study("MCPEpochBatch010")
    create_study_epoch(BASIC_SUBTYPE, study_uid=study.uid)
    response = _post_batch_preview(
        api_client,
        study.uid,
        [_epoch_create_payload(study.uid, BASIC_SUBTYPE)],
    )
    assert_response_status_code(response, 200)
    assert response.json()["items"][0]["response_code"] == 400


def test_reject_second_basic_epoch_batch_post(api_client, epoch_batch_test_data):
    study = _create_mcp_study("MCPEpochBatch011")
    create_study_epoch(BASIC_SUBTYPE, study_uid=study.uid)
    response = _post_batch(
        api_client,
        study.uid,
        [
            {
                "method": "POST",
                "content": _epoch_create_payload(study.uid, BASIC_SUBTYPE),
            }
        ],
    )
    assert_response_status_code(response, 400)


def test_invalid_subtype_error_per_item(api_client, epoch_batch_test_data):
    study = _create_mcp_study("MCPEpochBatch012")
    response = _post_batch_preview(
        api_client,
        study.uid,
        [_epoch_create_payload(study.uid, "InvalidEpochSubTypeUID")],
    )
    assert_response_status_code(response, 200)
    assert response.json()["items"][0]["response_code"] == 400


def test_locked_study_batch_preview_forbidden(api_client, epoch_batch_test_data):
    study = _create_mcp_study("MCPEpochBatch013")
    create_study_epoch(SUBTYPE_1, study_uid=study.uid)
    patch_response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "study_description": {"study_title": "MCP lock title"},
            }
        },
    )
    assert_response_status_code(patch_response, 200)
    lock_response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={
            "change_description": "lock for batch test",
            "reason_for_change_uid": epoch_batch_test_data["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(lock_response, 201)
    response = _post_batch_preview(
        api_client,
        study.uid,
        [_epoch_create_payload(study.uid, SUBTYPE_2)],
    )
    assert_response_status_code(response, 400)
    assert "locked" in response.json()["message"].lower()


def test_mixed_post_and_patch_batch(api_client, epoch_batch_test_data):
    study = _create_mcp_study("MCPEpochBatch014")
    existing = create_study_epoch(SUBTYPE_1, study_uid=study.uid)
    response = _post_batch(
        api_client,
        study.uid,
        [
            {"method": "POST", "content": _epoch_create_payload(study.uid, SUBTYPE_2)},
            {
                "method": "PATCH",
                "content": {
                    "study_uid": study.uid,
                    "study_epoch_uid": existing.uid,
                    "description": "mixed batch update",
                    "change_description": "mixed batch",
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    body = response.json()
    assert len(body["items"]) == 2
    assert body["items"][0]["response_code"] == 201
    assert body["items"][1]["response_code"] == 200
