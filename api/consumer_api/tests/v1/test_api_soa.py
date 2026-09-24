# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
from copy import deepcopy
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    get_unit_uid_by_name,
)
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    create_study_visit_codelists,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db

BASE_URL = "/v1"


@pytest.fixture(scope="module")
def soa_setup() -> dict[str, Any]:
    db_name = "consumer-api-v1-soa"
    set_db(db_name)

    study, test_data_dict = inject_base_data()
    create_study_visit_codelists(create_unit_definitions=False, use_test_utils=True)

    flowchart_group_codelist = TestUtils.create_ct_codelist(
        name="Flowchart Group",
        submission_value="FLWCRTGRP",
        extensible=True,
        approve=True,
    )
    soa_group_term = TestUtils.create_ct_term(
        codelist_uid=flowchart_group_codelist.codelist_uid,
        submission_value="EFFICACY",
        sponsor_preferred_name="Efficacy",
    )

    activity_group_1 = TestUtils.create_activity_group("Activity group 1")
    activity_subgroup_1 = TestUtils.create_activity_subgroup("Activity subgroup 1")
    activity_group_2 = TestUtils.create_activity_group("Activity group 2")
    activity_subgroup_2 = TestUtils.create_activity_subgroup("Activity subgroup 2")

    activity = TestUtils.create_activity(
        name="Activity 1",
        activity_groups=[activity_group_1.uid],
        activity_subgroups=[activity_subgroup_1.uid],
        approve=True,
    )
    activity_2 = TestUtils.create_activity(
        name="Activity 2",
        activity_groups=[activity_group_2.uid],
        activity_subgroups=[activity_subgroup_2.uid],
        approve=True,
    )

    return {
        "study_uid": study.uid,
        "reason_for_lock_term_uid": test_data_dict["reason_for_lock_terms"][0].term_uid,
        "day_unit_uid": get_unit_uid_by_name("day"),
        "epoch_subtype_uid": "EpochSubType_0001",
        "visit_type_uid": "VisitType_0003",
        "visit_contact_mode_uid": "VisitContactMode_0001",
        "visit_time_reference_uid": "VisitSubType_0005",
        "soa_group_uid": soa_group_term.term_uid,
        "activity_uid": activity.uid,
        "activity_uid_2": activity_2.uid,
        "valid_activity_group_uid": activity_group_1.uid,
        "valid_activity_subgroup_uid": activity_subgroup_1.uid,
        "invalid_activity_group_uid": activity_group_2.uid,
        "invalid_activity_subgroup_uid": activity_subgroup_2.uid,
        "valid_activity_group_uid_2": activity_group_2.uid,
        "valid_activity_subgroup_uid_2": activity_subgroup_2.uid,
    }


@pytest.fixture(scope="module")
def api_client(soa_setup):
    yield TestClient(app)


def _build_soa_payload(
    soa_setup: dict[str, Any],
    *,
    epoch_subtype_uid: str | None = None,
    visit_type_uid: str | None = None,
    visit_contact_mode_uid: str | None = None,
    visit_time_reference_uid: str | None = None,
    visit_window_unit_uid: str | None = None,
    visit_timing_unit_uid: str | None = None,
    visit_epoch_reference_id: str | None = None,
    activity_uid: str | None = None,
    soa_group_uid: str | None = None,
    activity_group_uid: str | None = None,
    activity_subgroup_uid: str | None = None,
    activity_visit_reference_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "epochs": [
            {
                "reference_id": "epoch_001",
                "subtype": epoch_subtype_uid or soa_setup["epoch_subtype_uid"],
                "order": 1,
            },
            {
                "reference_id": "epoch_002",
                "subtype": epoch_subtype_uid or soa_setup["epoch_subtype_uid"],
                "order": 2,
            },
        ],
        "visits": [
            {
                "reference_id": "visit_001",
                "epoch_reference_id": visit_epoch_reference_id or "epoch_001",
                "type": visit_type_uid or soa_setup["visit_type_uid"],
                "name": "V1",
                "short_name": "V1",
                "number": 1,
                "class": "MANUALLY_DEFINED_VISIT",
                "subclass": "SINGLE_VISIT",
                "contact_mode": visit_contact_mode_uid
                or soa_setup["visit_contact_mode_uid"],
                "is_global_anchor_visit": True,
                "window": {
                    "before": 0,
                    "after": 0,
                    "unit_uid": visit_window_unit_uid or soa_setup["day_unit_uid"],
                },
                "timing": {
                    "timing_reference_uid": visit_time_reference_uid
                    or soa_setup["visit_time_reference_uid"],
                    "value": 0,
                    "unit_uid": visit_timing_unit_uid or soa_setup["day_unit_uid"],
                },
            },
            {
                "reference_id": "visit_002",
                "epoch_reference_id": "epoch_002",
                "type": visit_type_uid or soa_setup["visit_type_uid"],
                "name": "V2",
                "short_name": "V2",
                "number": 2,
                "class": "MANUALLY_DEFINED_VISIT",
                "subclass": "SINGLE_VISIT",
                "contact_mode": visit_contact_mode_uid
                or soa_setup["visit_contact_mode_uid"],
                "is_global_anchor_visit": False,
                "window": {
                    "before": 1,
                    "after": 1,
                    "unit_uid": visit_window_unit_uid or soa_setup["day_unit_uid"],
                },
                "timing": {
                    "timing_reference_uid": visit_time_reference_uid
                    or soa_setup["visit_time_reference_uid"],
                    "value": 7,
                    "unit_uid": visit_timing_unit_uid or soa_setup["day_unit_uid"],
                },
            },
        ],
        "activities": [
            {
                "reference_id": "activity_001",
                "visit_reference_ids": activity_visit_reference_ids or ["visit_001"],
                "activity_uid": activity_uid or soa_setup["activity_uid"],
                "soa_group_uid": soa_group_uid or soa_setup["soa_group_uid"],
                "activity_group_uid": activity_group_uid
                or soa_setup["valid_activity_group_uid"],
                "activity_subgroup_uid": activity_subgroup_uid
                or soa_setup["valid_activity_subgroup_uid"],
            },
            {
                "reference_id": "activity_002",
                "visit_reference_ids": activity_visit_reference_ids or ["visit_002"],
                "activity_uid": activity_uid or soa_setup["activity_uid_2"],
                "soa_group_uid": soa_group_uid or soa_setup["soa_group_uid"],
                "activity_group_uid": activity_group_uid
                or soa_setup["valid_activity_group_uid_2"],
                "activity_subgroup_uid": activity_subgroup_uid
                or soa_setup["valid_activity_subgroup_uid_2"],
            },
        ],
    }


def test_create_soa(api_client, soa_setup):
    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=_build_soa_payload(soa_setup),
    )
    assert_response_status_code(response, 201)

    response_data = response.json()
    assert set(response_data.keys()) == {"epochs", "visits", "activities"}
    assert response_data["epochs"]["epoch_001"]
    assert response_data["epochs"]["epoch_002"]
    assert response_data["visits"]["visit_001"]
    assert response_data["visits"]["visit_002"]
    assert response_data["activities"]["activity_001"]
    assert response_data["activities"]["activity_002"]


def test_create_soa_rejects_invalid_activity_uid(api_client, soa_setup):
    payload = _build_soa_payload(soa_setup, activity_uid="Activity_DOES_NOT_EXIST")

    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=payload,
    )
    assert_response_status_code(response, 400)
    assert "invalid activity_uid" in response.json()["message"]


def test_create_soa_rejects_invalid_activity_grouping(api_client, soa_setup):
    payload = _build_soa_payload(
        soa_setup,
        activity_group_uid=soa_setup["invalid_activity_group_uid"],
        activity_subgroup_uid=soa_setup["valid_activity_subgroup_uid"],
    )

    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=payload,
    )
    assert_response_status_code(response, 400)
    assert "invalid combination of activity_group_uid" in response.json()["message"]


@pytest.mark.parametrize(
    "payload_overrides,message_fragment",
    [
        (("epoch_subtype_uid", "NotAnEpochSubtype"), "invalid subtype"),
        (("visit_type_uid", "NotAVisitType"), "invalid type"),
        (
            ("visit_contact_mode_uid", "NotAContactMode"),
            "invalid contact_mode",
        ),
        (
            ("visit_time_reference_uid", "NotATimeReference"),
            "invalid timing.timing_reference_uid",
        ),
        (("visit_window_unit_uid", "NotAUnit"), "invalid window.unit_uid"),
        (("visit_timing_unit_uid", "NotAUnit"), "invalid timing.unit_uid"),
        (("soa_group_uid", "NotASoaGroup"), "invalid soa_group_uid"),
        (("activity_uid", "NotAnActivity"), "invalid activity_uid"),
    ],
)
def test_create_soa_rejects_invalid_uids(
    api_client,
    soa_setup,
    payload_overrides,
    message_fragment,
):
    override_field, override_value = payload_overrides
    payload = _build_soa_payload(soa_setup, **{override_field: override_value})

    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=payload,
    )
    assert_response_status_code(response, 400)
    assert message_fragment in response.json()["message"]


def test_create_soa_rejects_invalid_cross_references(api_client, soa_setup):
    invalid_visit_payload = _build_soa_payload(
        soa_setup,
        visit_epoch_reference_id="epoch_DOES_NOT_EXIST",
    )
    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=invalid_visit_payload,
    )
    assert_response_status_code(response, 400)
    assert "invalid epoch reference ID" in response.json()["message"]

    invalid_activity_payload = _build_soa_payload(
        soa_setup,
        activity_visit_reference_ids=["visit_DOES_NOT_EXIST"],
    )
    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=invalid_activity_payload,
    )
    assert_response_status_code(response, 400)
    assert "invalid visit reference ID" in response.json()["message"]


def test_create_soa_rejects_duplicate_epoch_reference_ids(api_client, soa_setup):
    payload = _build_soa_payload(soa_setup)
    duplicate_epoch = deepcopy(payload["epochs"][0])
    duplicate_epoch["order"] = 2
    payload["epochs"].append(duplicate_epoch)

    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=payload,
    )
    assert_response_status_code(response, 400)
    assert "All epoch reference IDs must be unique." in response.json()["message"]


def test_create_soa_rejects_duplicate_epoch_orders(api_client, soa_setup):
    payload = _build_soa_payload(soa_setup)
    duplicate_order_epoch = deepcopy(payload["epochs"][0])
    duplicate_order_epoch["reference_id"] = "epoch_003"
    duplicate_order_epoch["order"] = 2
    payload["epochs"].append(duplicate_order_epoch)

    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=payload,
    )
    assert_response_status_code(response, 400)
    assert "All epoch orders must be unique." in response.json()["message"]


def test_create_soa_rejects_duplicate_visit_reference_ids(api_client, soa_setup):
    payload = _build_soa_payload(soa_setup)
    duplicate_visit = deepcopy(payload["visits"][0])
    duplicate_visit["number"] = 2
    duplicate_visit["name"] = "V2"
    duplicate_visit["short_name"] = "V2"
    payload["visits"].append(duplicate_visit)

    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=payload,
    )
    assert_response_status_code(response, 400)
    assert "All visit reference IDs must be unique." in response.json()["message"]


def test_create_soa_rejects_colliding_unique_visit_numbers(api_client, soa_setup):
    # Two visits whose `number` collide on `number * 10` (e.g. 10 and 100
    # both derive/specify a unique_visit_number of 100). Without unique_number
    # supplied this must fail in pre-validation, not deep inside
    # StudyVisitService.
    payload = _build_soa_payload(soa_setup)
    payload["visits"][0]["number"] = 10
    payload["visits"][1]["unique_number"] = 100

    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=payload,
    )
    assert_response_status_code(response, 400)
    assert "unique_visit_number" in response.json()["message"]


def test_create_soa_accepts_explicit_unique_visit_numbers(api_client, soa_setup):
    # Same colliding `number` values, but the caller supplies explicit,
    # distinct unique_number values to resolve the collision.
    payload = _build_soa_payload(soa_setup)
    payload["visits"][0]["number"] = 10
    payload["visits"][0]["unique_number"] = 100
    payload["visits"][1]["number"] = 100
    payload["visits"][1]["unique_number"] = 1000

    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=payload,
    )
    assert_response_status_code(response, 201)


def test_create_soa_rejects_duplicate_activity_reference_ids(api_client, soa_setup):
    payload = _build_soa_payload(soa_setup)
    duplicate_activity = deepcopy(payload["activities"][0])
    payload["activities"].append(duplicate_activity)

    response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=payload,
    )
    assert_response_status_code(response, 400)
    assert "All activity reference IDs must be unique." in response.json()["message"]


def test_create_soa_replaces_existing_entities(api_client, soa_setup):
    first_payload = _build_soa_payload(soa_setup)
    first_response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=first_payload,
    )
    assert_response_status_code(first_response, 201)
    first_data = first_response.json()

    second_payload = deepcopy(first_payload)
    second_payload["epochs"][0]["reference_id"] = "epoch_101"
    second_payload["epochs"][1]["reference_id"] = "epoch_102"
    second_payload["visits"][0]["reference_id"] = "visit_101"
    second_payload["visits"][0]["epoch_reference_id"] = "epoch_101"
    second_payload["visits"][1]["reference_id"] = "visit_102"
    second_payload["visits"][1]["epoch_reference_id"] = "epoch_102"
    second_payload["activities"][0]["reference_id"] = "activity_101"
    second_payload["activities"][0]["visit_reference_ids"] = ["visit_101"]
    second_payload["activities"][1]["reference_id"] = "activity_102"
    second_payload["activities"][1]["visit_reference_ids"] = ["visit_102"]

    second_response = api_client.post(
        f"{BASE_URL}/studies/{soa_setup['study_uid']}/soa",
        json=second_payload,
    )
    assert_response_status_code(second_response, 201)
    second_data = second_response.json()

    first_epoch_uids = set(first_data["epochs"].values())
    first_visit_uids = set(first_data["visits"].values())
    first_activity_uids = set(first_data["activities"].values())

    second_epoch_uids = set(second_data["epochs"].values())
    second_visit_uids = set(second_data["visits"].values())
    second_activity_uids = set(second_data["activities"].values())

    assert not first_epoch_uids.intersection(second_epoch_uids)
    assert not first_visit_uids.intersection(second_visit_uids)
    assert not first_activity_uids.intersection(second_activity_uids)

    all_epochs = StudyEpochService.get_all_epochs(
        study_uid=soa_setup["study_uid"], page_size=0
    )
    assert len(all_epochs.items) == 2
    assert {epoch.uid for epoch in all_epochs.items} == second_epoch_uids

    all_visits = StudyVisitService.get_all_visits(
        study_uid=soa_setup["study_uid"], page_size=0, lite=True
    )
    assert len(all_visits.items) == 2
    assert {visit.uid for visit in all_visits.items} == second_visit_uids

    all_activities = StudyActivitySelectionService().get_all_selection(
        study_uid=soa_setup["study_uid"], page_size=0
    )
    assert len(all_activities.items) == 2
    assert {
        activity.study_activity_uid for activity in all_activities.items
    } == second_activity_uids


def test_create_soa_rolls_back_on_mid_flight_failure(api_client, soa_setup):
    # Use a dedicated study so we can observe rollback in isolation
    # of the other module-scoped tests.
    study = TestUtils.create_study()
    payload_overrides = {
        "epochs": [
            {
                "reference_id": "epoch_rb_001",
                "subtype": soa_setup["epoch_subtype_uid"],
                "order": 1,
            },
        ],
        "visits": [
            {
                "reference_id": "visit_rb_001",
                "epoch_reference_id": "epoch_rb_001",
                "type": soa_setup["visit_type_uid"],
                "name": "VR1",
                "short_name": "VR1",
                "number": 1,
                "class": "MANUALLY_DEFINED_VISIT",
                "subclass": "SINGLE_VISIT",
                "contact_mode": soa_setup["visit_contact_mode_uid"],
                "is_global_anchor_visit": True,
                "window": {
                    "before": 0,
                    "after": 0,
                    "unit_uid": soa_setup["day_unit_uid"],
                },
                "timing": {
                    "timing_reference_uid": soa_setup["visit_time_reference_uid"],
                    "value": 0,
                    "unit_uid": soa_setup["day_unit_uid"],
                },
            },
        ],
        "activities": [
            {
                "reference_id": "activity_rb_001",
                "visit_reference_ids": ["visit_rb_001"],
                "activity_uid": soa_setup["activity_uid"],
                "soa_group_uid": soa_setup["soa_group_uid"],
                "activity_group_uid": soa_setup["valid_activity_group_uid"],
                "activity_subgroup_uid": soa_setup["valid_activity_subgroup_uid"],
            },
        ],
    }

    # Seed the study with a known-good SoA.
    seed_response = api_client.post(
        f"{BASE_URL}/studies/{study.uid}/soa",
        json=payload_overrides,
    )
    assert_response_status_code(seed_response, 201)
    seed_data = seed_response.json()

    seed_epoch_uids = set(seed_data["epochs"].values())
    seed_visit_uids = set(seed_data["visits"].values())
    seed_activity_uids = set(seed_data["activities"].values())

    # Craft a payload that passes our pre-validation but fails inside
    # the create phase: two visits sharing the same visit number
    # (and thus the same derived unique_visit_number) will be rejected
    # by StudyVisitService.create.
    bad_payload = deepcopy(payload_overrides)
    bad_visit = deepcopy(bad_payload["visits"][0])
    bad_visit["reference_id"] = "visit_rb_002"
    bad_visit["name"] = "VR2"
    bad_visit["short_name"] = "VR2"
    bad_visit["is_global_anchor_visit"] = False
    bad_payload["visits"].append(bad_visit)

    response = api_client.post(
        f"{BASE_URL}/studies/{study.uid}/soa",
        json=bad_payload,
    )
    # The request must fail. The exact status depends on which downstream
    # exception is raised, but it must NOT be 201.
    assert response.status_code != 201, response.json()

    # The original SoA must remain intact: same UIDs, same counts.
    remaining_epochs = StudyEpochService.get_all_epochs(
        study_uid=study.uid, page_size=0
    )
    assert {epoch.uid for epoch in remaining_epochs.items} == seed_epoch_uids

    remaining_visits = StudyVisitService.get_all_visits(
        study_uid=study.uid, page_size=0, lite=True
    )
    assert {visit.uid for visit in remaining_visits.items} == seed_visit_uids

    remaining_activities = StudyActivitySelectionService().get_all_selection(
        study_uid=study.uid, page_size=0
    )
    assert {
        activity.study_activity_uid for activity in remaining_activities.items
    } == seed_activity_uids


def test_create_soa_rejects_anchor_visit_with_nonzero_timing(api_client, soa_setup):
    # Use a dedicated study so the failure of this destructive POST
    # does not perturb other module-scoped tests.
    study = TestUtils.create_study()

    # Anchor-eligibility rule (StudyVisitService): a global anchor visit
    # must take place at day 0 (or be an Information Visit). Setting
    # timing.value to a non-zero value with is_global_anchor_visit=True
    # must propagate as a 400 from the underlying visit service.
    payload = {
        "epochs": [
            {
                "reference_id": "epoch_anchor_001",
                "subtype": soa_setup["epoch_subtype_uid"],
                "order": 1,
            },
        ],
        "visits": [
            {
                "reference_id": "visit_anchor_001",
                "epoch_reference_id": "epoch_anchor_001",
                "type": soa_setup["visit_type_uid"],
                "name": "VA1",
                "short_name": "VA1",
                "number": 1,
                "class": "MANUALLY_DEFINED_VISIT",
                "subclass": "SINGLE_VISIT",
                "contact_mode": soa_setup["visit_contact_mode_uid"],
                "is_global_anchor_visit": True,
                "window": {
                    "before": 0,
                    "after": 0,
                    "unit_uid": soa_setup["day_unit_uid"],
                },
                "timing": {
                    "timing_reference_uid": soa_setup["visit_time_reference_uid"],
                    "value": 7,
                    "unit_uid": soa_setup["day_unit_uid"],
                },
            },
        ],
        "activities": [],
    }

    response = api_client.post(
        f"{BASE_URL}/studies/{study.uid}/soa",
        json=payload,
    )
    assert_response_status_code(response, 400)
    # The service wraps downstream failures with a 'Failed to create visit'
    # message and the visit's reference_id, plus the original anchor-visit error.
    message = response.json()["message"]
    assert "visit_anchor_001" in message
    assert "global anchor visit" in message.lower()


def test_create_soa_rejects_nonexistent_study(api_client, soa_setup):
    response = api_client.post(
        f"{BASE_URL}/studies/Study_DOES_NOT_EXIST/soa",
        json=_build_soa_payload(soa_setup),
    )
    assert_response_status_code(response, 404)


def test_create_soa_rejects_locked_study(api_client, soa_setup):
    # Create a dedicated study so locking it doesn't affect other tests
    locked_study = TestUtils.create_study()
    TestUtils.lock_study(
        locked_study.uid,
        reason_for_lock_term_uid=soa_setup["reason_for_lock_term_uid"],
    )

    response = api_client.post(
        f"{BASE_URL}/studies/{locked_study.uid}/soa",
        json=_build_soa_payload(soa_setup),
    )
    assert_response_status_code(response, 400)
    assert "LOCKED" in response.json()["message"]
