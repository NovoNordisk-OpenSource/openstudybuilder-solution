"""
Tests for /studies/{study_uid}/study-source-variables endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.domains.enums import StudyDesignClassEnum, StudySourceVariableEnum
from clinical_mdr_api.main import app
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_selection import StudySourceVariable
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
study_source_variable: StudySourceVariable
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
    db_name = "studysourcevariable"
    inject_and_clear_db(db_name)

    global study, test_data_dict
    global test_data_dict
    study, test_data_dict = inject_base_data()
    global study_source_variable
    study_source_variable = TestUtils.create_study_source_variable(
        study_uid=study.uid,
        source_variable=StudySourceVariableEnum.COHORT,
        source_variable_description="description",
    )

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


def test_study_source_variable_get(api_client):
    response = api_client.get(
        f"/studies/{study.uid}/study-source-variables",
    )
    assert_response_status_code(response, 200)

    res = response.json()
    assert res["source_variable"] == StudySourceVariableEnum.COHORT.value
    assert res["source_variable_description"] == "description"
    assert res["study_uid"] == study.uid


def test_study_source_variable_create(api_client):
    study_with_cohorts = StudySourceVariableEnum.COHORT.value
    source_variable_description = "Description of source variable"
    new_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{new_study.uid}/study-source-variables",
        json={
            "source_variable": study_with_cohorts,
            "source_variable_description": source_variable_description,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["source_variable"] == study_with_cohorts
    assert res["source_variable_description"] == source_variable_description
    assert res["study_uid"] == new_study.uid

    response = api_client.post(
        f"/studies/{new_study.uid}/study-source-variables",
        json={"source_variable": StudySourceVariableEnum.SUBGROUP.value},
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert (
        res["message"]
        == f"StudySourceVariable already exist for Study with UID '{new_study.uid}'"
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
        f"/studies/{new_study.uid}/study-source-variables",
        json={
            "source_variable": StudySourceVariableEnum.COHORT.value,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{new_study.uid}' is locked."


def test_study_source_variable_edit(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{new_study.uid}/study-source-variables",
        json={
            "source_variable": StudySourceVariableEnum.COHORT.value,
        },
    )
    assert_response_status_code(response, 201)

    new_value = StudySourceVariableEnum.STRATUM.value
    new_description = "new description"
    response = api_client.put(
        f"/studies/{new_study.uid}/study-source-variables",
        json={
            "source_variable": new_value,
            "source_variable_description": new_description,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["source_variable"] == new_value
    assert res["source_variable_description"] == new_description
    assert res["study_uid"] == new_study.uid


def test_clear_study_source_variable_when_changing_design_class(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    source_variable = StudySourceVariableEnum.COHORT.value
    source_variable_description = "source variable description"
    response = api_client.post(
        f"/studies/{new_study.uid}/study-source-variables",
        json={
            "source_variable": source_variable,
            "source_variable_description": source_variable_description,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["source_variable"] == source_variable
    assert res["source_variable_description"] == source_variable_description

    response = api_client.post(
        f"/studies/{new_study.uid}/study-design-classes",
        json={
            "value": StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.put(
        f"/studies/{new_study.uid}/study-design-classes",
        json={"value": StudyDesignClassEnum.MANUAL.value},
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{new_study.uid}/study-source-variables",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["source_variable"] is None
    assert res["source_variable_description"] is None
