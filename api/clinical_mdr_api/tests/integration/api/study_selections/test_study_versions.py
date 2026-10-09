"""
Tests for /studies endpoints
"""

import json
import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.domains.enums import ValidationMode
from clinical_mdr_api.main import app
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study

test_data_dict: dict[str, Any]


def _assert_protocol_header_versions(
    api_client, study_uid, expected_version, has_final
):
    response = api_client.get(f"/studies/{study_uid}/protocol-header-versions")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["protocol_header_version"] == expected_version
    assert res["has_final_protocol_locked_version"] is has_final


def _assert_snapshot_history(api_client, study_uid, params, total, expected_items):
    response = api_client.get(
        f"/studies/{study_uid}/snapshot-history",
        params=params,
    )
    assert_response_status_code(response, 200)
    payload = response.json()
    assert payload["total"] == total
    items = payload["items"]
    assert len(items) == len(expected_items)
    for item, expected in zip(items, expected_items):
        assert item["modified_date"] is not None
        assert item["modified_by"] is not None
        for field, value in expected.items():
            assert item[field] == value


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyversionsapi"
    inject_and_clear_db(db_name)
    global test_data_dict
    _, test_data_dict = inject_base_data()


def test_get_snapshot_history(api_client):
    study_with_history = TestUtils.create_study()
    response = api_client.patch(
        f"/studies/{study_with_history.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    _assert_protocol_header_versions(
        api_client, study_with_history.uid, expected_version=None, has_final=False
    )
    _assert_snapshot_history(
        api_client,
        study_with_history.uid,
        params={"total_count": True},
        total=1,
        expected_items=[
            {
                "study_status": ["DRAFT"],
                "reason_for_lock_name": None,
                "reason_for_unlock_name": None,
                "metadata_version": None,
                "description": None,
                "other_reason_for_unlocking": None,
            }
        ],
    )

    reason_for_lock_cl = test_data_dict["reason_for_lock_cl"]
    reason_for_lock = test_data_dict["reason_for_lock_terms"][0]
    final_protocol_term = TestUtils.create_ct_term(
        codelist_uid=reason_for_lock_cl.codelist_uid,
        sponsor_preferred_name="Final Protocol",
        submission_value=settings.final_protocol_term_submval,
    )

    for payload, expected_message in [
        (
            {
                "protocol_header_major_version": 0,
                "protocol_header_minor_version": 0,
                "change_description": "Lock 1",
                "reason_for_change_uid": reason_for_lock.term_uid,
            },
            "Protocol header version can't be set to 0.0",
        ),
        (
            {
                "change_description": "Lock 1",
                "reason_for_change_uid": final_protocol_term.term_uid,
            },
            "For 'Final Protocol', major version must be a non-zero value and minor version must be 0",
        ),
        (
            {
                "protocol_header_major_version": 1,
                "protocol_header_minor_version": 5,
                "change_description": "Lock 1",
                "reason_for_change_uid": final_protocol_term.term_uid,
            },
            "For 'Final Protocol', major version must be a non-zero value and minor version must be 0",
        ),
        (
            {
                "protocol_header_major_version": 1,
                "protocol_header_minor_version": None,
                "change_description": "Lock 1",
                "reason_for_change_uid": final_protocol_term.term_uid,
            },
            "Both protocol_header_major_version and protocol_header_minor_version must be set together or both must be None",
        ),
    ]:
        response = api_client.post(
            f"/studies/{study_with_history.uid}/locks",
            json=payload,
        )
        assert_response_status_code(response, 400)
        assert response.json()["message"] == expected_message

    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": reason_for_lock.term_uid,
        },
    )
    assert_response_status_code(response, 201)

    _assert_protocol_header_versions(
        api_client, study_with_history.uid, expected_version=None, has_final=False
    )

    response = api_client.get(
        f"/studies/{study_with_history.uid}/study-standard-versions/"
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["automatically_created"] is True

    _assert_snapshot_history(
        api_client,
        study_with_history.uid,
        params={"total_count": True},
        total=1,
        expected_items=[
            {
                "study_status": ["LOCKED", "RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": None,
                "metadata_version": "1",
                "protocol_header_major_version": None,
                "protocol_header_minor_version": None,
                "description": "Lock 1",
                "other_reason_for_locking_releasing": None,
                "other_reason_for_unlocking": None,
            }
        ],
    )

    filters = json.dumps(
        {
            "current_metadata.identification_metadata.study_id": {
                "v": ["123-3"],
                "op": "co",
            },
            "current_metadata.identification_metadata.study_acronym": {
                "v": ["st-9349574170"],
                "op": "co",
            },
        }
    )
    response = api_client.get(
        "/studies", params={"page_size": 0, "filters": filters, "operator": "or"}
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "items" in res
    assert "total" in res
    assert "page" in res
    assert "size" in res

    reason_for_unlock = test_data_dict["reason_for_unlock_terms"][0]
    response = api_client.post(
        f"/studies/{study_with_history.uid}/unlocks",
        json={
            "other_reason_for_unlocking": "Unlock",
            "reason_for_change_uid": reason_for_unlock.term_uid,
        },
    )
    assert_response_status_code(response, 201)

    _assert_protocol_header_versions(
        api_client, study_with_history.uid, expected_version=None, has_final=False
    )

    response = api_client.get(
        f"/studies/{study_with_history.uid}/study-standard-versions/"
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res) == 0

    response = api_client.get(
        f"/studies/{study_with_history.uid}/study-standard-versions/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["automatically_created"] is True

    _assert_snapshot_history(
        api_client,
        study_with_history.uid,
        params={"total_count": True},
        total=2,
        expected_items=[
            {
                "study_status": ["DRAFT"],
                "reason_for_lock_name": None,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": None,
                "description": None,
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": None,
                "protocol_header_major_version": None,
                "protocol_header_minor_version": None,
            },
            {
                "study_status": ["LOCKED", "RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": None,
                "metadata_version": "1",
                "protocol_header_major_version": None,
                "protocol_header_minor_version": None,
                "description": "Lock 1",
                "other_reason_for_unlocking": None,
                "other_reason_for_locking_releasing": None,
            },
        ],
    )

    response = api_client.post(
        f"/studies/{study_with_history.uid}/release",
        json={
            "change_description": "Explicit release",
            "reason_for_change_uid": reason_for_lock.term_uid,
            "protocol_header_major_version": 0,
            "protocol_header_minor_version": 1,
        },
    )
    assert_response_status_code(response, 201)

    _assert_protocol_header_versions(
        api_client, study_with_history.uid, expected_version="0.1", has_final=False
    )
    _assert_snapshot_history(
        api_client,
        study_with_history.uid,
        params={"total_count": True},
        total=3,
        expected_items=[
            {
                "study_status": ["DRAFT"],
                "reason_for_lock_name": None,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": None,
                "protocol_header_major_version": None,
                "protocol_header_minor_version": None,
                "description": None,
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": None,
            },
            {
                "study_status": ["RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "1.1",
                "description": "Explicit release",
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": None,
                "protocol_header_major_version": 0,
                "protocol_header_minor_version": 1,
            },
            {
                "study_status": ["LOCKED", "RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": None,
                "metadata_version": "1",
                "protocol_header_major_version": None,
                "protocol_header_minor_version": None,
                "description": "Lock 1",
                "other_reason_for_unlocking": None,
                "other_reason_for_locking_releasing": None,
            },
        ],
    )

    response = api_client.post(
        f"/studies/{study_with_history.uid}/release",
        json={
            "change_description": "Explicit second release",
            "reason_for_change_uid": reason_for_lock.term_uid,
            "other_reason_for_locking_releasing": "Release other reason",
            "protocol_header_major_version": 0,
            "protocol_header_minor_version": 2,
        },
    )
    assert_response_status_code(response, 201)

    _assert_protocol_header_versions(
        api_client, study_with_history.uid, expected_version="0.2", has_final=False
    )
    _assert_snapshot_history(
        api_client,
        study_with_history.uid,
        params={"total_count": True},
        total=4,
        expected_items=[
            {
                "study_status": ["DRAFT"],
                "reason_for_lock_name": None,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": None,
                "protocol_header_major_version": None,
                "protocol_header_minor_version": None,
                "description": None,
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": None,
            },
            {
                "study_status": ["RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "1.2",
                "protocol_header_major_version": 0,
                "protocol_header_minor_version": 2,
                "description": "Explicit second release",
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": "Release other reason",
            },
            {
                "study_status": ["RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "1.1",
                "protocol_header_minor_version": 1,
                "protocol_header_major_version": 0,
                "description": "Explicit release",
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": None,
            },
            {
                "study_status": ["LOCKED", "RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": None,
                "metadata_version": "1",
                "protocol_header_major_version": None,
                "protocol_header_minor_version": None,
                "description": "Lock 1",
                "other_reason_for_unlocking": None,
                "other_reason_for_locking_releasing": None,
            },
        ],
    )

    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={
            "change_description": "Lock 2",
            "reason_for_change_uid": final_protocol_term.term_uid,
            "other_reason_for_locking_releasing": "Lock other reason",
            "protocol_header_major_version": 1,
            "protocol_header_minor_version": 0,
        },
    )
    assert_response_status_code(response, 201)

    _assert_protocol_header_versions(
        api_client, study_with_history.uid, expected_version="1.0", has_final=True
    )
    _assert_snapshot_history(
        api_client,
        study_with_history.uid,
        params={"total_count": True},
        total=4,
        expected_items=[
            {
                "study_status": ["LOCKED", "RELEASED"],
                "reason_for_lock_name": final_protocol_term.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "2",
                "protocol_header_major_version": 1,
                "protocol_header_minor_version": 0,
                "description": "Lock 2",
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": "Lock other reason",
            },
            {
                "study_status": ["RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "1.2",
                "protocol_header_major_version": 0,
                "protocol_header_minor_version": 2,
                "description": "Explicit second release",
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": "Release other reason",
            },
            {
                "study_status": ["RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "1.1",
                "protocol_header_major_version": 0,
                "protocol_header_minor_version": 1,
                "description": "Explicit release",
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": None,
            },
            {
                "study_status": ["LOCKED", "RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": None,
                "metadata_version": "1",
                "protocol_header_major_version": None,
                "protocol_header_minor_version": None,
                "description": "Lock 1",
                "other_reason_for_unlocking": None,
                "other_reason_for_locking_releasing": None,
            },
        ],
    )

    response = api_client.post(
        f"/studies/{study_with_history.uid}/unlocks",
        json={"reason_for_change_uid": reason_for_unlock.term_uid},
    )
    assert_response_status_code(response, 201)

    _assert_snapshot_history(
        api_client,
        study_with_history.uid,
        params={"total_count": True},
        total=5,
        expected_items=[
            {
                "study_status": ["DRAFT"],
                "reason_for_lock_name": None,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": None,
                "protocol_header_major_version": None,
                "protocol_header_minor_version": None,
                "description": None,
                "other_reason_for_unlocking": None,
                "other_reason_for_locking_releasing": None,
            },
            {
                "study_status": ["LOCKED", "RELEASED"],
                "reason_for_lock_name": final_protocol_term.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "2",
                "protocol_header_major_version": 1,
                "protocol_header_minor_version": 0,
                "description": "Lock 2",
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": "Lock other reason",
            },
            {
                "study_status": ["RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "1.2",
                "protocol_header_major_version": 0,
                "protocol_header_minor_version": 2,
                "description": "Explicit second release",
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": "Release other reason",
            },
            {
                "study_status": ["RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "1.1",
                "protocol_header_major_version": 0,
                "protocol_header_minor_version": 1,
                "description": "Explicit release",
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": None,
            },
            {
                "study_status": ["LOCKED", "RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": None,
                "metadata_version": "1",
                "protocol_header_major_version": None,
                "protocol_header_minor_version": None,
                "description": "Lock 1",
                "other_reason_for_unlocking": None,
                "other_reason_for_locking_releasing": None,
            },
        ],
    )

    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={
            "change_description": "Lock 3",
            "reason_for_change_uid": reason_for_lock.term_uid,
            "other_reason_for_locking_releasing": "Lock 3 other reason",
            "protocol_header_major_version": 2,
            "protocol_header_minor_version": 0,
        },
    )
    assert_response_status_code(response, 201)

    _assert_protocol_header_versions(
        api_client, study_with_history.uid, expected_version="2.0", has_final=True
    )
    _assert_snapshot_history(
        api_client,
        study_with_history.uid,
        params={"only_latest_major_protocol_version": True, "total_count": True},
        total=2,
        expected_items=[
            {
                "study_status": ["LOCKED", "RELEASED"],
                "reason_for_lock_name": reason_for_lock.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "3",
                "original_metadata_version": "3",
                "protocol_header_major_version": 2,
                "protocol_header_minor_version": 0,
                "description": "Lock 3",
                "other_reason_for_unlocking": None,
                "other_reason_for_locking_releasing": "Lock 3 other reason",
            },
            {
                "study_status": ["LOCKED", "RELEASED"],
                "reason_for_lock_name": final_protocol_term.sponsor_preferred_name,
                "reason_for_unlock_name": reason_for_unlock.sponsor_preferred_name,
                "metadata_version": "2",
                "original_metadata_version": "2",
                "protocol_header_major_version": 1,
                "protocol_header_minor_version": 0,
                "description": "Lock 2",
                "other_reason_for_unlocking": "Unlock",
                "other_reason_for_locking_releasing": "Lock other reason",
            },
        ],
    )

    response = api_client.post(
        f"/studies/{study_with_history.uid}/unlocks",
        json={"reason_for_change_uid": reason_for_unlock.term_uid},
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={
            "change_description": "Lock 4 same major version",
            "reason_for_change_uid": reason_for_lock.term_uid,
            "protocol_header_major_version": 2,
            "protocol_header_minor_version": 0,
        },
    )
    assert_response_status_code(response, 201)

    _assert_snapshot_history(
        api_client,
        study_with_history.uid,
        params={"only_latest_major_protocol_version": True, "total_count": True},
        total=2,
        expected_items=[
            {
                "metadata_version": "4",
                "original_metadata_version": "3",
                "protocol_header_major_version": 2,
                "protocol_header_minor_version": 0,
            },
            {
                "metadata_version": "2",
                "original_metadata_version": "2",
                "protocol_header_major_version": 1,
                "protocol_header_minor_version": 0,
            },
        ],
    )


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(
        api_client, mode=ValidationMode.STRICT
    )
