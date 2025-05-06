# pylint: disable=unused-argument,redefined-outer-name

import logging
from copy import copy

import pytest

from clinical_mdr_api.models.study_selections.study import (
    Study,
    StudySoaPreferencesInput,
)
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.tests.integration.domain_repositories.test_study_definition_repository import (
    unlink_study_soa_properties,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import (
    assert_json_response,
    assert_response_status_code,
)

log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def dummy_study(request, base_data, tst_project) -> Study:
    """Creates a dummy Study for testing, with the intention to be reused over test parameters iterations"""

    study = TestUtils.create_study(project_number=tst_project.project_number)

    log.info("%s: created dummy Study: %s", request.fixturename, study.uid)

    # Study title has to be set before locking
    TestUtils.set_study_title(study.uid)

    # Study standatd version has to be set before locking
    TestUtils.set_study_standard_version(study_uid=study.uid)

    return study


@pytest.mark.parametrize(
    "soa_preferences_update",
    (
        {"show_epochs": None, "show_milestones": None},
        {"show_epochs": True, "show_milestones": None},
        {"show_epochs": None, "show_milestones": False},
        {"show_epochs": False, "show_milestones": True},
        {"show_epochs": False, "show_milestones": False},
        {"show_epochs": True, "show_milestones": True},
        {"show_epochs": None, "show_milestones": None, "baseline_as_time_zero": None},
        {"show_epochs": None, "show_milestones": None, "baseline_as_time_zero": True},
        {"show_epochs": None, "show_milestones": None, "baseline_as_time_zero": False},
        {"show_epochs": True, "show_milestones": None, "baseline_as_time_zero": False},
        {"show_epochs": True, "show_milestones": None, "baseline_as_time_zero": True},
        {"show_epochs": True, "show_milestones": None, "baseline_as_time_zero": None},
        {"show_epochs": None, "show_milestones": False, "baseline_as_time_zero": None},
        {"show_epochs": None, "show_milestones": False, "baseline_as_time_zero": True},
        {"show_epochs": None, "show_milestones": False, "baseline_as_time_zero": False},
        {"show_epochs": False, "show_milestones": True, "baseline_as_time_zero": True},
        {"show_epochs": False, "show_milestones": True, "baseline_as_time_zero": False},
        {"show_epochs": False, "show_milestones": True, "baseline_as_time_zero": None},
        {
            "show_epochs": False,
            "show_milestones": False,
            "baseline_as_time_zero": False,
        },
        {"show_epochs": False, "show_milestones": False, "baseline_as_time_zero": True},
        {"show_epochs": False, "show_milestones": False, "baseline_as_time_zero": None},
        {"show_epochs": True, "show_milestones": True, "baseline_as_time_zero": True},
        {"show_epochs": True, "show_milestones": True, "baseline_as_time_zero": False},
        {"show_epochs": True, "show_milestones": True, "baseline_as_time_zero": None},
    ),
)
def test_get_soa_preferences(
    base_data, tst_project, api_client, soa_preferences_update: dict[str, bool]
):
    """Verify getting SoA Preferences before update (after Study creation) and after update"""

    study = TestUtils.create_study(project_number=tst_project.project_number)

    # WHEN Study is recently created
    # THEN Study SoA preferences show_epochs is on
    # THEN Study SoA preferences show_milestones is off
    # THEN Study SoA preferences baseline_as_time_zero is on
    response = api_client.get(f"/studies/{study.uid}/soa-preferences")
    assert_response_status_code(response, 200)
    assert_json_response(response)
    data = response.json()
    assert data, "empty JSON data"
    assert data["study_uid"] == study.uid
    assert data["show_epochs"] is True
    assert data["show_milestones"] is False
    assert data["baseline_as_time_zero"] is True

    unlink_study_soa_properties(study.uid)

    # WHEN existing Study has no Study SoA Preferences StudyFields
    # THEN Study SoA preferences show_epochs is on
    # THEN Study SoA preferences show_milestones is off
    # THEN Study SoA preferences baseline_as_time_zero is off
    response = api_client.get(f"/studies/{study.uid}/soa-preferences")
    assert_response_status_code(response, 200)
    assert_json_response(response)
    data = response.json()
    assert data, "empty JSON data"
    assert data["study_uid"] == study.uid
    assert data["show_epochs"] is True
    assert data["show_milestones"] is False
    assert data["baseline_as_time_zero"] is False

    service = StudyService()
    service.post_study_soa_preferences(
        study_uid=study.uid,
        soa_preferences=StudySoaPreferencesInput(
            **{k: v for k, v in soa_preferences_update.items() if v is not None}
        ),
    )

    response = api_client.get(f"/studies/{study.uid}/soa-preferences")
    assert_response_status_code(response, 200)
    assert_json_response(response)
    data = response.json()
    assert data, "empty JSON data"

    defaults = StudySoaPreferencesInput().model_dump()

    assert data["study_uid"] == study.uid
    for key in ("show_epochs", "show_milestones"):
        if soa_preferences_update[key] is not None:
            expected = soa_preferences_update[key]
        else:
            expected = defaults[key]
        assert data[key] == expected


@pytest.mark.parametrize(
    ("soa_preferences_update", "soa_preferences_expected"),
    (
        (  # 0
            {},
            {
                "show_epochs": True,
                "show_milestones": False,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 1
            {"show_epochs": True},
            {
                "show_epochs": True,
                "show_milestones": False,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 2
            {"baseline_as_time_zero": True},
            {
                "show_epochs": True,
                "show_milestones": False,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 3
            {"show_milestones": True},
            {
                "show_epochs": True,
                "show_milestones": True,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 4
            {"show_epochs": False},
            {
                "show_epochs": False,
                "show_milestones": False,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 5
            {"baseline_as_time_zero": False},
            {
                "show_epochs": True,
                "show_milestones": False,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 6
            {"show_epochs": False, "show_milestones": True},
            {
                "show_epochs": False,
                "show_milestones": True,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 7
            {"show_epochs": False, "show_milestones": False},
            {
                "show_epochs": False,
                "show_milestones": False,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 8
            {"show_epochs": True, "show_milestones": True},
            {
                "show_epochs": True,
                "show_milestones": True,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 9
            {"show_milestones": True, "baseline_as_time_zero": False},
            {
                "show_epochs": True,
                "show_milestones": True,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 10
            {
                "show_epochs": True,
                "show_milestones": False,
                "baseline_as_time_zero": False,
            },
            {
                "show_epochs": True,
                "show_milestones": False,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 11
            {"show_epochs": False, "baseline_as_time_zero": False},
            {
                "show_epochs": False,
                "show_milestones": False,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 12
            {
                "show_epochs": False,
                "show_milestones": False,
                "baseline_as_time_zero": False,
            },
            {
                "show_epochs": False,
                "show_milestones": False,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 13
            {
                "show_epochs": True,
                "show_milestones": True,
                "baseline_as_time_zero": True,
            },
            {
                "show_epochs": True,
                "show_milestones": True,
                "baseline_as_time_zero": True,
            },
        ),
    ),
)
def test_patch_soa_preferences(
    dummy_study,
    api_client,
    soa_preferences_update: dict[str, bool],
    soa_preferences_expected: dict[str, bool],
):
    """Verifies partial and complete updates of SoA Preferences"""

    # Remove previous SoA preferences
    unlink_study_soa_properties(dummy_study.uid)

    # Update SoA preferences
    response = api_client.patch(
        f"/studies/{dummy_study.uid}/soa-preferences", json=soa_preferences_update
    )
    assert_response_status_code(response, 200)
    assert_json_response(response)
    data = response.json()
    assert data, "empty JSON data"

    # Check payload, should be a full SoA preferences
    assert data["study_uid"] == dummy_study.uid
    for key in ("show_epochs", "show_milestones"):
        assert data[key] == soa_preferences_expected[key]

    # Response payload to PATCH and later GET should equal
    response = api_client.get(f"/studies/{dummy_study.uid}/soa-preferences")
    assert_response_status_code(response, 200)
    assert_json_response(response)
    data2 = response.json()
    assert data2 == data, "Response payload of PATCH doesn't match with GET"


@pytest.mark.parametrize(
    ("soa_preferences_update",),
    (
        ({"show_epochs": None},),
        ({"show_epochs": "foo"},),
        ({"show_milestones": None},),
        ({"baseline_as_time_zero": 42},),
        ({"show_milestones": 4.2},),
        ({"baseline_as_time_zero": -3.4},),
        ({"show_epochs": -33},),
        ({"show_epochs": None, "show_milestones": None},),
        (
            {
                "show_epochs": None,
                "show_milestones": None,
                "baseline_as_time_zero": None,
            },
        ),
    ),
)
def test_patch_soa_preferences_invalid_input(
    dummy_study,
    api_client,
    soa_preferences_update: dict[str, bool],
):
    """Verify that invalid SoA Preferences input gets rejected"""

    response = api_client.patch(
        f"/studies/{dummy_study.uid}/soa-preferences", json=soa_preferences_update
    )
    assert_response_status_code(response, 422)
    assert_json_response(response)


@pytest.mark.parametrize(
    ("soa_preferences_initial", "soa_preferences_update"),
    (
        (  # 0
            {},
            {"show_epochs": True, "show_milestones": True},
        ),
        (  # 1
            {},
            {
                "show_epochs": True,
                "show_milestones": True,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 2
            {"show_epochs": True},
            {"show_epochs": True, "show_milestones": True},
        ),
        (  # 3
            {"show_epochs": False},
            {
                "baseline_as_time_zero": True,
                "show_epochs": True,
                "show_milestones": True,
            },
        ),
        (  # 4
            {"baseline_as_time_zero": False},
            {
                "baseline_as_time_zero": True,
                "show_epochs": True,
                "show_milestones": True,
            },
        ),
        (  # 5
            {"baseline_as_time_zero": False},
            {"show_epochs": True, "show_milestones": True},
        ),
        (  # 6
            {"show_milestones": False},
            {
                "baseline_as_time_zero": False,
                "show_epochs": True,
                "show_milestones": False,
            },
        ),
        (  # 7
            {
                "show_epochs": False,
                "show_milestones": True,
                "baseline_as_time_zero": True,
            },
            {"show_milestones": True, "show_epochs": False},
        ),
        (  # 8
            {
                "show_milestones": False,
                "show_epochs": True,
                "baseline_as_time_zero": True,
            },
            {
                "show_epochs": True,
                "show_milestones": False,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 9
            {
                "show_milestones": False,
                "show_epochs": True,
                "baseline_as_time_zero": True,
            },
            {
                "show_epochs": True,
                "show_milestones": False,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 10
            {
                "show_epochs": False,
                "show_milestones": False,
                "baseline_as_time_zero": False,
            },
            {
                "show_epochs": False,
                "show_milestones": False,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 11
            {
                "show_epochs": True,
                "show_milestones": True,
                "baseline_as_time_zero": True,
            },
            {
                "show_epochs": True,
                "show_milestones": True,
                "baseline_as_time_zero": True,
            },
        ),
    ),
)
def test_soa_preferences_versioning(
    dummy_study,
    api_client,
    soa_preferences_initial: dict[str, bool],
    soa_preferences_update: dict[str, bool],
):
    """Verify that SoA preferences for older Study version are locked and retrievable by study_value_version"""

    # Set SoA preferences
    response0 = api_client.patch(
        f"/studies/{dummy_study.uid}/soa-preferences", json=soa_preferences_initial
    )
    assert_response_status_code(response0, 200)

    # Lock the study
    response1 = api_client.post(
        f"/studies/{dummy_study.uid}/locks",
        json={"change_description": "testing"},
    )
    assert response1.status_code == 201
    assert_json_response(response1)
    data = response1.json()
    prev_version = data["current_metadata"]["version_metadata"]["version_number"]

    # Ensure that preferences cannot be updated on a locked study
    response2 = api_client.patch(
        f"/studies/{dummy_study.uid}/soa-preferences", json=soa_preferences_update
    )
    assert_response_status_code(response2, 400)
    data = response2.json()
    assert data["type"] == "BusinessLogicException"
    assert "is locked" in data["message"]

    # Unlock the study
    unlock_response = api_client.delete(
        f"/studies/{dummy_study.uid}/locks",
    )
    assert unlock_response.status_code == 200
    assert_json_response(unlock_response)

    # Update SoA preferences
    response2 = api_client.patch(
        f"/studies/{dummy_study.uid}/soa-preferences", json=soa_preferences_update
    )
    assert_response_status_code(response2, 200)

    # Verify latest SoA preferences
    response3 = api_client.get(f"/studies/{dummy_study.uid}/soa-preferences")
    assert_response_status_code(response3, 200)
    assert_json_response(response3)
    data = response3.json()
    soa_preferences_expected = copy(soa_preferences_initial)
    soa_preferences_expected.update(soa_preferences_update)
    assert data.items() >= soa_preferences_expected.items()

    # Verify SoA preferences of previous Study study_value_version
    response4 = api_client.get(
        f"/studies/{dummy_study.uid}/soa-preferences",
        params={"study_value_version": prev_version},
    )
    assert_response_status_code(response4, 200)
    assert_json_response(response4)
    data = response4.json()
    assert data.items() >= soa_preferences_initial.items()
