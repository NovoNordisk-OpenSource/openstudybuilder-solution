# pylint: disable=redefined-outer-name,unused-argument

"""
Integration tests for StudyService methods.
These tests verify service-level behavior including business logic and exception handling.
"""

import logging

import pytest
from neomodel import db

from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common.exceptions import NotFoundException

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def study_service():
    """Fixture providing a StudyService instance."""
    return StudyService()


def test_get_study_id__with_valid_study__returns_study_id(
    base_data, tst_project, study_service
):
    """
    Test that get_study_id returns the correct study ID for a valid study.

    SCENARIO: Retrieve study ID for an existing study with valid prefix and number
    GIVEN: A study exists with study_id_prefix and study_number
    WHEN: get_study_id is called with the study UID
    THEN: The study ID is returned in format "prefix-number"
    """
    # GIVEN
    study_number = TestUtils.random_str(4)
    study = TestUtils.create_study(
        number=study_number, project_number=tst_project.project_number
    )

    # WHEN
    study_id = study_service.get_study_id(study.uid)

    # THEN
    expected_id = f"{tst_project.project_number}-{study_number}"
    assert study_id == expected_id


def test_get_study_id__with_locked_version__returns_study_id(
    base_data, tst_project, study_service
):
    """
    Test that get_study_id returns the correct study ID for a locked study version.

    SCENARIO: Retrieve study ID for a specific locked version of a study
    GIVEN: A study exists with a locked version
    WHEN: get_study_id is called with the study UID and version number
    THEN: The study ID for that locked study version is returned
    """
    # GIVEN
    study_number = TestUtils.random_str(4)
    study = TestUtils.create_study(
        number=study_number, project_number=tst_project.project_number
    )

    # Lock a version
    latest_study_version = TestUtils.lock_and_unlock_study(
        study.uid,
        reason_for_lock_term_uid=base_data["reason_for_lock_terms"][0].term_uid,
        reason_for_unlock_term_uid=base_data["reason_for_unlock_terms"][0].term_uid,
    )

    # WHEN
    study_id = study_service.get_study_id(
        study.uid, study_value_version=latest_study_version
    )

    # THEN
    expected_id = f"{tst_project.project_number}-{study_number}"
    assert study_id == expected_id


def test_get_study_id__with_released_version__returns_study_id(
    base_data, tst_project, study_service
):
    """
    Test that get_study_id returns the correct study ID for a released study version.

    SCENARIO: Retrieve study ID for a specific released version of a study
    GIVEN: A study exists with a locked version
    WHEN: get_study_id is called with the study UID and version number
    THEN: The study ID for that released study version is returned
    """
    # GIVEN
    study_number = TestUtils.random_str(4)
    study = TestUtils.create_study(
        number=study_number, project_number=tst_project.project_number
    )

    # Release study
    released_study_version = TestUtils.release_study(
        study.uid,
        reason_for_release_term_uid=base_data["reason_for_lock_terms"][0].term_uid,
    )

    # WHEN
    study_id = study_service.get_study_id(
        study.uid, study_value_version=released_study_version
    )

    # THEN
    expected_id = f"{tst_project.project_number}-{study_number}"
    assert study_id == expected_id


def test_get_study_id__with_nonexistent_uid__raises_not_found_exception(
    base_data, study_service
):
    """
    Test that get_study_id raises NotFoundException when study doesn't exist.

    SCENARIO: Attempt to retrieve study ID for a non-existent study
    GIVEN: No study exists with the specified UID
    WHEN: get_study_id is called with a non-existent UID
    THEN: NotFoundException is raised with appropriate error message
    """
    # GIVEN
    non_existent_uid = "non-existent-12345"

    # WHEN / THEN
    with pytest.raises(NotFoundException) as exc_info:
        study_service.get_study_id(non_existent_uid)

    assert "Study" in str(exc_info.value)
    assert non_existent_uid in str(exc_info.value)
    assert "was not found" in str(exc_info.value)


def test_get_study_id__with_nonexistent_version__raises_not_found_exception(
    base_data, tst_project, study_service
):
    """
    Test that get_study_id raises NotFoundException when version doesn't exist.

    SCENARIO: Attempt to retrieve study ID for a non-existent version
    GIVEN: A study exists but the specified version does not
    WHEN: get_study_id is called with an invalid version number
    THEN: NotFoundException is raised with appropriate error message
    """
    # GIVEN
    study_number = TestUtils.random_str(4)
    study = TestUtils.create_study(
        number=study_number, project_number=tst_project.project_number
    )
    non_existent_version = "999.999"

    # WHEN / THEN
    with pytest.raises(NotFoundException) as exc_info:
        study_service.get_study_id(study.uid, study_value_version=non_existent_version)

    assert study.uid in str(exc_info.value)
    assert non_existent_version in str(exc_info.value)
    assert "was not found" in str(exc_info.value)


def test_get_study_id__with_missing_study_id_prefix__raises_not_found_exception(
    base_data, tst_project, study_service
):
    """
    Test that get_study_id raises NotFoundException when study_id_prefix is missing.

    SCENARIO: Attempt to retrieve study ID when prefix is not defined
    GIVEN: A study exists but study_id_prefix is NULL
    WHEN: get_study_id is called
    THEN: NotFoundException is raised indicating prefix is not defined
    """
    # GIVEN
    study_number = TestUtils.random_str(4)
    study = TestUtils.create_study(
        number=study_number, project_number=tst_project.project_number
    )

    # Manually set study_id_prefix to NULL in database
    db.cypher_query(
        """
        MATCH (sr:StudyRoot {uid: $uid})-[:LATEST]->(sv:StudyValue)
        SET sv.study_id_prefix = NULL
        """,
        {"uid": study.uid},
    )

    # WHEN / THEN
    with pytest.raises(NotFoundException) as exc_info:
        study_service.get_study_id(study.uid)

    assert study.uid in str(exc_info.value)
    assert "study_id_prefix" in str(exc_info.value)
    assert "not defined" in str(exc_info.value)


def test_get_study_id__with_missing_study_number__raises_not_found_exception(
    base_data, tst_project, study_service
):
    """
    Test that get_study_id raises NotFoundException when study_number is missing.

    SCENARIO: Attempt to retrieve study ID when number is not defined
    GIVEN: A study exists but study_number is NULL
    WHEN: get_study_id is called
    THEN: NotFoundException is raised indicating number is not defined
    """
    # GIVEN
    study_number = TestUtils.random_str(4)
    study = TestUtils.create_study(
        number=study_number, project_number=tst_project.project_number
    )

    # Remove study_number
    study = TestUtils.patch_study(study.uid, study_number=None)

    # WHEN / THEN
    with pytest.raises(NotFoundException) as exc_info:
        study_service.get_study_id(study.uid)

    assert study.uid in str(exc_info.value)
    assert "study_number" in str(exc_info.value)
    assert "not defined" in str(exc_info.value)


def test_get_study_id__after_release__returns_study_id(
    base_data, tst_project, study_service
):
    """
    Test that get_study_id works correctly for released studies.

    SCENARIO: Retrieve study ID for a released study
    GIVEN: A study has been released
    WHEN: get_study_id is called with the study UID
    THEN: The study ID is returned correctly
    """
    # GIVEN
    study_number = TestUtils.random_str(4)
    study = TestUtils.create_study(
        number=study_number, project_number=tst_project.project_number
    )
    TestUtils.release_study(
        study.uid,
        reason_for_release_term_uid=base_data["reason_for_lock_terms"][0].term_uid,
    )

    # WHEN
    study_id = study_service.get_study_id(study.uid)

    # THEN
    expected_id = f"{tst_project.project_number}-{study_number}"
    assert study_id == expected_id


def test_get_study_id__for_subpart__returns_study_id(
    base_data, tst_project, study_service
):
    """
    Test that get_study_id returns correct ID for study subpart.

    SCENARIO: Retrieve study ID for a study subpart
    GIVEN: A study subpart exists with study_id_prefix and study_number
    WHEN: get_study_id is called with the subpart UID
    THEN: The study ID is returned correctly (parent study prefix and number)
    """
    # GIVEN
    study_number = TestUtils.random_str(4)
    parent_study = TestUtils.create_study(
        number=study_number, project_number=tst_project.project_number
    )

    subpart_study = TestUtils.create_study(
        subpart_acronym="SUB1",
        study_parent_part_uid=parent_study.uid,
        project_number=tst_project.project_number,
    )

    # WHEN
    study_id = study_service.get_study_id(subpart_study.uid)

    # THEN
    expected_id = f"{tst_project.project_number}-{study_number}-SUB1"
    assert study_id == expected_id


def test_get_study_id__with_deleted_study__raises_not_found_exception(
    base_data, tst_project, study_service
):
    """
    Test that get_study_id raises NotFoundException for deleted studies.

    SCENARIO: Attempt to retrieve study ID for a deleted study
    GIVEN: A study has been marked as deleted
    WHEN: get_study_id is called with the deleted study UID
    THEN: NotFoundException is raised
    """
    # GIVEN
    study_number = TestUtils.random_str(4)
    study = TestUtils.create_study(
        number=study_number, project_number=tst_project.project_number
    )

    # Mark the study as deleted
    TestUtils.delete_study(study.uid)

    # WHEN / THEN
    with pytest.raises(NotFoundException) as exc_info:
        study_service.get_study_id(study.uid)

    assert study.uid in str(exc_info.value)
    assert "was not found" in str(exc_info.value)
