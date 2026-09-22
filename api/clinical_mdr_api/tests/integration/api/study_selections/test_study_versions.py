"""
Tests for /studies endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

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


# pylint: disable=too-many-statements
def test_get_snapshot_history(api_client):
    study_with_history = TestUtils.create_study()
    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study_with_history.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{study_with_history.uid}/protocol-header-versions"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["protocol_header_version"] is None
    assert res["has_final_protocol_locked_version"] is False

    # snapshot history before lock
    response = api_client.get(
        f"/studies/{study_with_history.uid}/snapshot-history",
        params={"total_count": True},
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["total"] == 1
    res = res["items"]
    assert len(res) == 1
    assert res[0]["study_status"] == ["DRAFT"]
    assert res[0]["reason_for_lock_name"] is None
    assert res[0]["reason_for_unlock_name"] is None
    assert res[0]["metadata_version"] is None
    assert res[0]["description"] is None
    assert res[0]["other_reason_for_unlocking"] is None
    assert res[0]["modified_date"] is not None
    assert res[0]["modified_by"] is not None

    reason_for_lock_cl = test_data_dict["reason_for_lock_cl"]
    reason_for_lock = test_data_dict["reason_for_lock_terms"][0]
    # Create 'Final Protocol' reason for lock term
    final_protocol_term = TestUtils.create_ct_term(
        codelist_uid=reason_for_lock_cl.codelist_uid,
        sponsor_preferred_name="Final Protocol",
        submission_value=settings.final_protocol_term_submval,
    )

    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={
            "protocol_header_major_version": 0,
            "protocol_header_minor_version": 0,
            "change_description": "Lock 1",
            "reason_for_change_uid": reason_for_lock.term_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "Protocol header version can't be set to 0.0"

    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": final_protocol_term.term_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == "For 'Final Protocol', major version must be a non-zero value and minor version must be 0"
    )

    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={
            "protocol_header_major_version": 1,
            "protocol_header_minor_version": 5,
            "change_description": "Lock 1",
            "reason_for_change_uid": final_protocol_term.term_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == "For 'Final Protocol', major version must be a non-zero value and minor version must be 0"
    )

    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={
            "protocol_header_major_version": 1,
            "protocol_header_minor_version": None,
            "change_description": "Lock 1",
            "reason_for_change_uid": final_protocol_term.term_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == "Both protocol_header_major_version and protocol_header_minor_version must be set together or both must be None"
    )

    # Lock
    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": reason_for_lock.term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{study_with_history.uid}/protocol-header-versions"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["protocol_header_version"] is None
    assert res["has_final_protocol_locked_version"] is False

    # get all standard versions
    response = api_client.get(
        f"/studies/{study_with_history.uid}/study-standard-versions/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["automatically_created"] is True

    # snapshot history after lock
    response = api_client.get(
        f"/studies/{study_with_history.uid}/snapshot-history",
        params={"total_count": True},
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["total"] == 1
    res = res["items"]
    assert len(res) == 1
    assert res[0]["study_status"] == ["LOCKED", "RELEASED"]
    assert res[0]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[0]["reason_for_unlock_name"] is None
    assert res[0]["metadata_version"] == "1"
    assert res[0]["protocol_header_major_version"] is None
    assert res[0]["protocol_header_minor_version"] is None
    assert res[0]["description"] == "Lock 1"
    assert res[0]["other_reason_for_locking_releasing"] is None
    assert res[0]["other_reason_for_unlocking"] is None
    assert res[0]["modified_date"] is not None
    assert res[0]["modified_by"] is not None

    # Test filtering studies by study_id and study_acronym with OR operator
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
    # Unlock
    response = api_client.post(
        f"/studies/{study_with_history.uid}/unlocks",
        json={
            "other_reason_for_unlocking": "Unlock",
            "reason_for_change_uid": reason_for_unlock.term_uid,
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.get(
        f"/studies/{study_with_history.uid}/protocol-header-versions"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["protocol_header_version"] is None
    assert res["has_final_protocol_locked_version"] is False

    # get all standard versions
    response = api_client.get(
        f"/studies/{study_with_history.uid}/study-standard-versions/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res) == 0

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study_with_history.uid}/study-standard-versions/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["automatically_created"] is True

    # snapshot history after unlock
    response = api_client.get(
        f"/studies/{study_with_history.uid}/snapshot-history",
        params={"total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 2
    res = res["items"]
    assert len(res) == 2
    assert res[0]["study_status"] == ["DRAFT"]
    assert res[0]["reason_for_lock_name"] is None
    assert res[0]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[0]["metadata_version"] is None
    assert res[0]["description"] is None
    assert res[0]["other_reason_for_unlocking"] == "Unlock"
    assert res[0]["other_reason_for_locking_releasing"] is None
    assert res[0]["protocol_header_major_version"] is None
    assert res[0]["protocol_header_minor_version"] is None
    assert res[0]["modified_date"] is not None
    assert res[0]["modified_by"] is not None
    assert res[1]["study_status"] == ["LOCKED", "RELEASED"]
    assert res[1]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[1]["reason_for_unlock_name"] is None
    assert res[1]["metadata_version"] == "1"
    assert res[1]["protocol_header_major_version"] is None
    assert res[1]["protocol_header_minor_version"] is None
    assert res[1]["description"] == "Lock 1"
    assert res[1]["other_reason_for_unlocking"] is None
    assert res[1]["other_reason_for_locking_releasing"] is None
    assert res[1]["modified_date"] is not None
    assert res[1]["modified_by"] is not None

    # Release
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
    response = api_client.get(
        f"/studies/{study_with_history.uid}/protocol-header-versions"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["protocol_header_version"] == "0.1"
    assert res["has_final_protocol_locked_version"] is False

    # snapshot history after release
    response = api_client.get(
        f"/studies/{study_with_history.uid}/snapshot-history",
        params={"total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 3
    res = res["items"]

    assert len(res) == 3
    assert res[0]["study_status"] == ["DRAFT"]
    assert res[0]["reason_for_lock_name"] is None
    assert res[0]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[0]["metadata_version"] is None
    assert res[0]["protocol_header_major_version"] is None
    assert res[0]["protocol_header_minor_version"] is None
    assert res[0]["description"] is None
    assert res[0]["other_reason_for_unlocking"] == "Unlock"
    assert res[0]["other_reason_for_locking_releasing"] is None
    assert res[0]["modified_date"] is not None
    assert res[0]["modified_by"] is not None
    assert res[1]["study_status"] == ["RELEASED"]
    assert res[1]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[1]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[1]["metadata_version"] == "1.1"
    assert res[1]["description"] == "Explicit release"
    assert res[1]["other_reason_for_unlocking"] == "Unlock"
    assert res[1]["other_reason_for_locking_releasing"] is None
    assert res[1]["protocol_header_major_version"] == 0
    assert res[1]["protocol_header_minor_version"] == 1
    assert res[1]["modified_date"] is not None
    assert res[1]["modified_by"] is not None
    assert res[2]["study_status"] == ["LOCKED", "RELEASED"]
    assert res[2]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[2]["reason_for_unlock_name"] is None
    assert res[2]["metadata_version"] == "1"
    assert res[2]["protocol_header_major_version"] is None
    assert res[2]["protocol_header_minor_version"] is None
    assert res[2]["description"] == "Lock 1"
    assert res[2]["other_reason_for_unlocking"] is None
    assert res[2]["other_reason_for_locking_releasing"] is None
    assert res[2]["modified_date"] is not None
    assert res[2]["modified_by"] is not None

    # 2nd Release
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
    response = api_client.get(
        f"/studies/{study_with_history.uid}/protocol-header-versions"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["protocol_header_version"] == "0.2"
    assert res["has_final_protocol_locked_version"] is False
    # snapshot history after second release
    response = api_client.get(
        f"/studies/{study_with_history.uid}/snapshot-history",
        params={"total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 4
    res = res["items"]
    assert len(res) == 4
    assert res[0]["study_status"] == ["DRAFT"]
    assert res[0]["reason_for_lock_name"] is None
    assert res[0]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[0]["metadata_version"] is None
    assert res[0]["protocol_header_major_version"] is None
    assert res[0]["protocol_header_minor_version"] is None
    assert res[0]["description"] is None
    assert res[0]["other_reason_for_unlocking"] == "Unlock"
    assert res[0]["other_reason_for_locking_releasing"] is None
    assert res[0]["modified_date"] is not None
    assert res[0]["modified_by"] is not None
    assert res[1]["study_status"] == ["RELEASED"]
    assert res[1]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[1]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[1]["metadata_version"] == "1.2"
    assert res[1]["protocol_header_major_version"] == 0
    assert res[1]["protocol_header_minor_version"] == 2
    assert res[1]["description"] == "Explicit second release"
    assert res[1]["other_reason_for_unlocking"] == "Unlock"
    assert res[1]["other_reason_for_locking_releasing"] == "Release other reason"
    assert res[1]["modified_date"] is not None
    assert res[1]["modified_by"] is not None
    assert res[2]["study_status"] == ["RELEASED"]
    assert res[2]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[2]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[2]["metadata_version"] == "1.1"
    assert res[2]["protocol_header_minor_version"] == 1
    assert res[2]["protocol_header_major_version"] == 0
    assert res[2]["description"] == "Explicit release"
    assert res[2]["other_reason_for_unlocking"] == "Unlock"
    assert res[2]["other_reason_for_locking_releasing"] is None
    assert res[2]["modified_date"] is not None
    assert res[2]["modified_by"] is not None
    assert res[3]["study_status"] == ["LOCKED", "RELEASED"]
    assert res[3]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[3]["reason_for_unlock_name"] is None
    assert res[3]["metadata_version"] == "1"
    assert res[3]["protocol_header_major_version"] is None
    assert res[3]["protocol_header_minor_version"] is None
    assert res[3]["description"] == "Lock 1"
    assert res[3]["other_reason_for_unlocking"] is None
    assert res[3]["other_reason_for_locking_releasing"] is None
    assert res[3]["modified_date"] is not None
    assert res[3]["modified_by"] is not None

    # Lock
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
    response = api_client.get(
        f"/studies/{study_with_history.uid}/protocol-header-versions"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["protocol_header_version"] == "1.0"
    assert res["has_final_protocol_locked_version"] is True

    # snapshot history after lock
    response = api_client.get(
        f"/studies/{study_with_history.uid}/snapshot-history",
        params={"total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 4
    res = res["items"]
    assert len(res) == 4
    assert res[0]["study_status"] == ["LOCKED", "RELEASED"]
    assert res[0]["reason_for_lock_name"] == final_protocol_term.sponsor_preferred_name
    assert res[0]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[0]["metadata_version"] == "2"
    assert res[0]["protocol_header_major_version"] == 1
    assert res[0]["protocol_header_minor_version"] == 0
    assert res[0]["description"] == "Lock 2"
    assert res[0]["other_reason_for_unlocking"] == "Unlock"
    assert res[0]["other_reason_for_locking_releasing"] == "Lock other reason"
    assert res[0]["modified_date"] is not None
    assert res[0]["modified_by"] is not None
    assert res[1]["study_status"] == ["RELEASED"]
    assert res[1]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[1]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[1]["metadata_version"] == "1.2"
    assert res[1]["protocol_header_major_version"] == 0
    assert res[1]["protocol_header_minor_version"] == 2
    assert res[1]["description"] == "Explicit second release"
    assert res[1]["other_reason_for_unlocking"] == "Unlock"
    assert res[1]["other_reason_for_locking_releasing"] == "Release other reason"
    assert res[1]["modified_date"] is not None
    assert res[1]["modified_by"] is not None
    assert res[2]["study_status"] == ["RELEASED"]
    assert res[2]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[2]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[2]["metadata_version"] == "1.1"
    assert res[2]["protocol_header_major_version"] == 0
    assert res[2]["protocol_header_minor_version"] == 1
    assert res[2]["description"] == "Explicit release"
    assert res[2]["other_reason_for_unlocking"] == "Unlock"
    assert res[2]["other_reason_for_locking_releasing"] is None
    assert res[2]["modified_date"] is not None
    assert res[2]["modified_by"] is not None
    assert res[3]["study_status"] == ["LOCKED", "RELEASED"]
    assert res[3]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[3]["reason_for_unlock_name"] is None
    assert res[3]["metadata_version"] == "1"
    assert res[3]["protocol_header_major_version"] is None
    assert res[3]["protocol_header_minor_version"] is None
    assert res[3]["description"] == "Lock 1"
    assert res[3]["other_reason_for_unlocking"] is None
    assert res[3]["other_reason_for_locking_releasing"] is None
    assert res[3]["modified_date"] is not None
    assert res[3]["modified_by"] is not None

    # Unlock
    response = api_client.post(
        f"/studies/{study_with_history.uid}/unlocks",
        json={
            "reason_for_change_uid": reason_for_unlock.term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # snapshot history after unlock
    response = api_client.get(
        f"/studies/{study_with_history.uid}/snapshot-history",
        params={"total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 5
    res = res["items"]
    assert len(res) == 5
    assert res[0]["study_status"] == ["DRAFT"]
    assert res[0]["reason_for_lock_name"] is None
    assert res[0]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[0]["metadata_version"] is None
    assert res[0]["protocol_header_major_version"] is None
    assert res[0]["protocol_header_minor_version"] is None
    assert res[0]["description"] is None
    assert res[0]["other_reason_for_unlocking"] is None
    assert res[0]["other_reason_for_locking_releasing"] is None
    assert res[0]["modified_date"] is not None
    assert res[0]["modified_by"] is not None
    assert res[1]["study_status"] == ["LOCKED", "RELEASED"]
    assert res[1]["reason_for_lock_name"] == final_protocol_term.sponsor_preferred_name
    assert res[1]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[1]["metadata_version"] == "2"
    assert res[1]["protocol_header_major_version"] == 1
    assert res[1]["protocol_header_minor_version"] == 0
    assert res[1]["description"] == "Lock 2"
    assert res[1]["other_reason_for_unlocking"] == "Unlock"
    assert res[1]["other_reason_for_locking_releasing"] == "Lock other reason"
    assert res[1]["modified_date"] is not None
    assert res[1]["modified_by"] is not None
    assert res[2]["study_status"] == ["RELEASED"]
    assert res[2]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[2]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[2]["metadata_version"] == "1.2"
    assert res[2]["protocol_header_major_version"] == 0
    assert res[2]["protocol_header_minor_version"] == 2
    assert res[2]["description"] == "Explicit second release"
    assert res[2]["other_reason_for_unlocking"] == "Unlock"
    assert res[2]["other_reason_for_locking_releasing"] == "Release other reason"
    assert res[2]["modified_date"] is not None
    assert res[2]["modified_by"] is not None
    assert res[3]["study_status"] == ["RELEASED"]
    assert res[3]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[3]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[3]["metadata_version"] == "1.1"
    assert res[3]["protocol_header_major_version"] == 0
    assert res[3]["protocol_header_minor_version"] == 1
    assert res[3]["description"] == "Explicit release"
    assert res[3]["other_reason_for_unlocking"] == "Unlock"
    assert res[3]["other_reason_for_locking_releasing"] is None
    assert res[3]["modified_date"] is not None
    assert res[3]["modified_by"] is not None
    assert res[4]["study_status"] == ["LOCKED", "RELEASED"]
    assert res[4]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[4]["reason_for_unlock_name"] is None
    assert res[4]["metadata_version"] == "1"
    assert res[4]["protocol_header_major_version"] is None
    assert res[4]["protocol_header_minor_version"] is None
    assert res[4]["description"] == "Lock 1"
    assert res[4]["other_reason_for_unlocking"] is None
    assert res[4]["other_reason_for_locking_releasing"] is None
    assert res[4]["modified_date"] is not None
    assert res[4]["modified_by"] is not None

    # Lock
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
    response = api_client.get(
        f"/studies/{study_with_history.uid}/protocol-header-versions"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["protocol_header_version"] == "2.0"
    assert res["has_final_protocol_locked_version"] is True

    # snapshot history excluding versions without protocol header version
    response = api_client.get(
        f"/studies/{study_with_history.uid}/snapshot-history",
        params={"only_latest_major_protocol_version": True, "total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 2
    res = res["items"]
    assert len(res) == 2
    assert res[0]["study_status"] == ["LOCKED", "RELEASED"]
    assert res[0]["reason_for_lock_name"] == reason_for_lock.sponsor_preferred_name
    assert res[0]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[0]["metadata_version"] == "3"
    assert res[0]["original_metadata_version"] == "3"
    assert res[0]["protocol_header_major_version"] == 2
    assert res[0]["protocol_header_minor_version"] == 0
    assert res[0]["description"] == "Lock 3"
    assert res[0]["other_reason_for_unlocking"] is None
    assert res[0]["other_reason_for_locking_releasing"] == "Lock 3 other reason"
    assert res[0]["modified_date"] is not None
    assert res[0]["modified_by"] is not None
    assert res[1]["study_status"] == ["LOCKED", "RELEASED"]
    assert res[1]["reason_for_lock_name"] == final_protocol_term.sponsor_preferred_name
    assert res[1]["reason_for_unlock_name"] == reason_for_unlock.sponsor_preferred_name
    assert res[1]["metadata_version"] == "2"
    assert res[1]["original_metadata_version"] == "2"
    assert res[1]["protocol_header_major_version"] == 1
    assert res[1]["protocol_header_minor_version"] == 0
    assert res[1]["description"] == "Lock 2"
    assert res[1]["other_reason_for_unlocking"] == "Unlock"
    assert res[1]["other_reason_for_locking_releasing"] == "Lock other reason"
    assert res[1]["modified_date"] is not None
    assert res[1]["modified_by"] is not None

    # Unlock and re-lock with same major protocol version to test original_metadata_version
    response = api_client.post(
        f"/studies/{study_with_history.uid}/unlocks",
        json={
            "reason_for_change_uid": reason_for_unlock.term_uid,
        },
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

    # Now phv 2.0 has two entries: metadata_version "4" (latest) and "3" (original)
    response = api_client.get(
        f"/studies/{study_with_history.uid}/snapshot-history",
        params={"only_latest_major_protocol_version": True, "total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 2
    res = res["items"]
    assert len(res) == 2
    assert res[0]["metadata_version"] == "4"
    assert res[0]["original_metadata_version"] == "3"
    assert res[0]["protocol_header_major_version"] == 2
    assert res[0]["protocol_header_minor_version"] == 0
    assert res[1]["metadata_version"] == "2"
    assert res[1]["original_metadata_version"] == "2"
    assert res[1]["protocol_header_major_version"] == 1
    assert res[1]["protocol_header_minor_version"] == 0


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
