"""
Tests for /studies/{study_uid}/study-design-classes endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.domains.enums import StudyDesignClassEnum
from clinical_mdr_api.main import app
from clinical_mdr_api.models.projects.project import Project
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
project: Project
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studydesignclassapi"
    inject_and_clear_db(db_name)

    global study, test_data_dict
    study, test_data_dict = inject_base_data()

    clinical_programme = TestUtils.create_clinical_programme(name="Test CP")
    global project
    project = TestUtils.create_project(
        name="Test project",
        project_number="1234",
        description="Base project",
        clinical_programme_uid=clinical_programme.uid,
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


def test_study_design_class_get(api_client):
    datetime_before_study_design_class_creation = datetime.now(timezone.utc)
    response = api_client.get(
        f"/studies/{study.uid}/study-design-classes",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["value"] == StudyDesignClassEnum.MANUAL.value
    assert res["study_uid"] == study.uid
    assert (
        datetime.strptime(res["start_date"], settings.date_time_format)
        > datetime_before_study_design_class_creation
    )


def test_study_design_class_create(api_client):
    study_with_cohorts = (
        StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value
    )
    new_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{new_study.uid}/study-design-classes",
        json={"value": study_with_cohorts},
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["value"] == study_with_cohorts
    assert res["study_uid"] == new_study.uid

    response = api_client.post(
        f"/studies/{new_study.uid}/study-design-classes",
        json={
            "value": StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value
        },
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert (
        res["message"]
        == f"StudyDesignClass already exist for Study with UID '{new_study.uid}'"
    )

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{new_study.uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/studies/{new_study.uid}/study-design-classes",
        json={
            "value": StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{new_study.uid}' is locked."


def test_study_design_class_edit(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{new_study.uid}/study-design-classes",
        json={"value": StudyDesignClassEnum.MANUAL.value},
    )
    assert_response_status_code(response, 201)

    new_value = (
        StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value
    )
    response = api_client.put(
        f"/studies/{new_study.uid}/study-design-classes",
        json={"value": new_value},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["value"] == new_value
    assert res["study_uid"] == new_study.uid


def test_check_if_study_design_classes_edition_is_allowed(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-classes/editions-allowed",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res is True

    study_cohort = TestUtils.create_study_cohort(
        study_uid=new_study.uid, name="some cohort", short_name="some cohort"
    )

    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-classes/editions-allowed",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res is False

    response = api_client.delete(
        f"/studies/{new_study.uid}/study-cohorts/{study_cohort.cohort_uid}",
    )
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-classes/editions-allowed",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res is True
