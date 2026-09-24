# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

from typing import Any

import pytest
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    create_study_visit_codelists,
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import (
    assert_response_status_code,
    parse_json_response,
)
from consumer_api.tests.utils import set_db


class TestData:
    def __init__(self):
        self.study = TestUtils.create_study()

        self.epochs = []
        for i in range(3):
            self.epochs.append(
                TestUtils.create_study_epoch(
                    study_uid=self.study.uid, epoch_subtype="EpochSubType_0001"
                )
            )

        visit_params = generate_default_input_data_for_visit()
        visit_params.pop("time_value", None)

        self.visits = []
        for i in range(9):
            self.visits.append(
                TestUtils.create_study_visit(  # pylint: disable=repeated-keyword
                    study_uid=self.study.uid,
                    study_epoch_uid=self.epochs[int(i / 3)].uid,
                    time_value=i * 7,
                    **visit_params,
                )
            )


@pytest.fixture(scope="module")
def test_database() -> dict[str, Any]:
    db_name = "study-soa-split"
    set_db(db_name)
    _, test_data_dict = inject_base_data()
    create_study_visit_codelists(create_unit_definitions=False, use_test_utils=True)
    return test_data_dict


def test_study_soa_splits(api_client: TestClient, test_database):
    test_data = TestData()
    reason_for_lock_term_uid = test_database["reason_for_lock_terms"][0].term_uid
    reason_for_unlock_term_uid = test_database["reason_for_unlock_terms"][0].term_uid

    # Returns 404 if study does not exist
    response = api_client.get("/studies/Study_000000/soa-splits")
    assert_response_status_code(response, 404)

    # Returns 404 if study value does not exist
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": "0"},
    )
    assert_response_status_code(response, 404)

    # Returns 404 if study and study value does not exist
    response = api_client.get(
        "/studies/Study_000000/soa-splits", params={"study_value_version": "0"}
    )
    assert_response_status_code(response, 404)

    # Initially no SOA splits, returns an empty list
    response = api_client.get(f"/studies/{test_data.study.uid}/soa-splits")
    returned = parse_json_response(response, assert_status=200)
    assert returned == []

    # Add a uid to SoA splits
    response = api_client.put(
        f"/studies/{test_data.study.uid}/soa-splits",
        json={"uid": test_data.visits[5].uid},
    )
    returned = parse_json_response(response, assert_status=200)
    expected = [{"uid": test_data.visits[5].uid, "study_uid": test_data.study.uid}]
    assert returned == expected

    # Get SoA splits
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
    )
    returned = parse_json_response(response, assert_status=200)
    assert returned == expected

    # Add another uid to SoA splits
    response = api_client.put(
        f"/studies/{test_data.study.uid}/soa-splits",
        json={"uid": test_data.visits[3].uid},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    expected = [
        {"uid": test_data.visits[3].uid, "study_uid": test_data.study.uid},
        {"uid": test_data.visits[5].uid, "study_uid": test_data.study.uid},
    ]
    assert returned == expected

    # Add a duplicate uid to SoA splits - should fail
    response = api_client.put(
        f"/studies/{test_data.study.uid}/soa-splits",
        json={"uid": test_data.visits[3].uid},
    )
    assert_response_status_code(response, 409)

    # Add another uid to SoA splits
    response = api_client.put(
        f"/studies/{test_data.study.uid}/soa-splits",
        json={"uid": test_data.visits[1].uid},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    expected = [
        {"uid": test_data.visits[1].uid, "study_uid": test_data.study.uid},
        {"uid": test_data.visits[3].uid, "study_uid": test_data.study.uid},
        {"uid": test_data.visits[5].uid, "study_uid": test_data.study.uid},
    ]
    assert returned == expected

    # Add a non-existing uid to SoA splits - should fail
    response = api_client.put(
        f"/studies/{test_data.study.uid}/soa-splits",
        json={"uid": "StudyVisits_012345"},
    )
    assert_response_status_code(response, 404)

    # Get SoA splits
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == expected

    # Delete an uid from SoA splits
    response = api_client.delete(
        f"/studies/{test_data.study.uid}/soa-splits/{test_data.visits[3].uid}",
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    expected = [
        {"uid": test_data.visits[1].uid, "study_uid": test_data.study.uid},
        {"uid": test_data.visits[5].uid, "study_uid": test_data.study.uid},
    ]
    assert returned == expected

    # Get SoA splits
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == expected

    # Lock the study
    v1_version = TestUtils.lock_study(
        test_data.study.uid, reason_for_lock_term_uid=reason_for_lock_term_uid
    )
    v1_expected = expected

    # Get SoA splits for specific version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": v1_version},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v1_expected

    # Get SoA splits for latest version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v1_expected

    # Try to add another uid to SoA splits to locked study - should fail
    response = api_client.put(
        f"/studies/{test_data.study.uid}/soa-splits",
        json={"uid": test_data.visits[0].uid},
    )
    assert_response_status_code(response, 400)

    # Try to delete an uid from SoA splits of a locked study - should fail
    response = api_client.delete(
        f"/studies/{test_data.study.uid}/soa-splits/{test_data.visits[1].uid}",
    )
    assert_response_status_code(response, 400)

    # Unlock the study
    TestUtils.unlock_study(
        test_data.study.uid, reason_for_unlock_term_uid=reason_for_unlock_term_uid
    )

    # Get SoA splits for specific version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": v1_version},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v1_expected

    # Get SoA splits for latest version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v1_expected

    # Delete an uid from SoA splits
    response = api_client.delete(
        f"/studies/{test_data.study.uid}/soa-splits/{test_data.visits[1].uid}",
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    expected = [{"uid": test_data.visits[5].uid, "study_uid": test_data.study.uid}]
    assert returned == expected

    # Get SoA splits for previous version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": v1_version},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v1_expected

    # Lock and unlock the study again
    v2_version = TestUtils.lock_and_unlock_study(
        test_data.study.uid,
        reason_for_lock_term_uid=reason_for_lock_term_uid,
        reason_for_unlock_term_uid=reason_for_unlock_term_uid,
    )
    v2_expected = expected

    # Get SoA splits for v1 version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": v1_version},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v1_expected

    # Get SoA splits for latest version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == expected

    # Get SoA splits for v2 version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": v2_version},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v2_expected

    # Add another uid to SoA splits
    response = api_client.put(
        f"/studies/{test_data.study.uid}/soa-splits",
        json={"uid": test_data.visits[4].uid},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    expected = [
        {"uid": test_data.visits[4].uid, "study_uid": test_data.study.uid},
        {"uid": test_data.visits[5].uid, "study_uid": test_data.study.uid},
    ]
    assert returned == expected

    # Get SoA splits for v1 version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": v1_version},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v1_expected

    # Get SoA splits for latest version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == expected

    # Get SoA splits for v2 version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": v2_version},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v2_expected

    # Delete all SoA splits
    response = api_client.delete(
        f"/studies/{test_data.study.uid}/soa-splits/{test_data.visits[5].uid}",
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    expected = [{"uid": test_data.visits[4].uid, "study_uid": test_data.study.uid}]
    assert returned == expected
    response = api_client.delete(
        f"/studies/{test_data.study.uid}/soa-splits",
    )
    assert_response_status_code(response, 204)

    # Get SoA splits for latest version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
    )
    returned = parse_json_response(response, assert_status=200)
    assert returned == []

    # Get SoA splits for v2 version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": v2_version},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v2_expected

    # Get SoA splits for v1 version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": v1_version},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == v1_expected


def test_study_locked_with_no_soa_splits(api_client: TestClient, test_database):
    test_data = TestData()
    reason_for_lock_term_uid = test_database["reason_for_lock_terms"][0].term_uid
    reason_for_unlock_term_uid = test_database["reason_for_unlock_terms"][0].term_uid

    # Initially no SOA splits
    response = api_client.get(f"/studies/{test_data.study.uid}/soa-splits")
    returned = parse_json_response(response, assert_status=200)
    assert returned == []

    # Try to delete an uid from non-existing SoA splits
    response = api_client.delete(
        f"/studies/{test_data.study.uid}/soa-splits/{test_data.visits[3].uid}",
    )
    assert_response_status_code(response, 404)

    # Lock & unlock a Study version
    v1_version = TestUtils.lock_and_unlock_study(
        test_data.study.uid,
        reason_for_lock_term_uid=reason_for_lock_term_uid,
        reason_for_unlock_term_uid=reason_for_unlock_term_uid,
    )

    # Add a uid to SoA splits
    response = api_client.put(
        f"/studies/{test_data.study.uid}/soa-splits",
        json={"uid": test_data.visits[4].uid},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    expected = [{"uid": test_data.visits[4].uid, "study_uid": test_data.study.uid}]
    assert returned == expected

    # Add another uid to SoA splits
    response = api_client.put(
        f"/studies/{test_data.study.uid}/soa-splits",
        json={"uid": test_data.visits[6].uid},
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    expected = [
        {"uid": test_data.visits[4].uid, "study_uid": test_data.study.uid},
        {"uid": test_data.visits[6].uid, "study_uid": test_data.study.uid},
    ]
    assert returned == expected

    # Get SoA splits for v1 version
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
        params={"study_value_version": v1_version},
    )
    returned = parse_json_response(response)
    assert returned == []

    # Get SoA splits
    response = api_client.get(
        f"/studies/{test_data.study.uid}/soa-splits",
    )
    returned = _sort_by_uid(parse_json_response(response, assert_status=200))
    assert returned == expected


def _sort_by_uid(value: list[dict[str, Any]]):
    assert isinstance(value, list)
    for x in value:
        assert isinstance(x, dict)
    return sorted(value, key=lambda x: x.get("uid"))
