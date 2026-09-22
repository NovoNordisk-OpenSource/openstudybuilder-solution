# pylint: disable=redefined-outer-name,unused-argument

import logging

from clinical_mdr_api.models.study_selections.study import StudySoaPreferencesInput
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)


def test_study_soa_preferences(base_data, tst_project):
    service = StudyService()

    study = TestUtils.create_study(project_number=tst_project.project_number)

    preferences_input = StudySoaPreferencesInput(
        show_epochs=True, show_milestones=False
    )
    assert preferences_input.show_epochs is True
    assert preferences_input.show_milestones is False
    assert preferences_input.baseline_as_time_zero is False

    soa_preferences = service.patch_study_soa_preferences(
        study.uid, StudySoaPreferencesInput(show_milestones=True)
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is True
    assert soa_preferences.show_milestones is True
    assert preferences_input.baseline_as_time_zero is False

    soa_preferences = service.patch_study_soa_preferences(
        study.uid,
        StudySoaPreferencesInput(show_epochs=False, baseline_as_time_zero=True),
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is False
    assert soa_preferences.show_milestones is True
    assert soa_preferences.baseline_as_time_zero is True

    soa_preferences = service.patch_study_soa_preferences(
        study.uid,
        StudySoaPreferencesInput(show_epochs=False, show_milestones=False),
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is False
    assert soa_preferences.show_milestones is False
    assert soa_preferences.baseline_as_time_zero is True

    soa_preferences = service.patch_study_soa_preferences(
        study.uid,
        StudySoaPreferencesInput(show_milestones=True, baseline_as_time_zero=False),
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is False
    assert soa_preferences.show_milestones is True
    assert soa_preferences.baseline_as_time_zero is False

    soa_preferences = service.get_study_soa_preferences(study.uid)
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is False
    assert soa_preferences.show_milestones is True
    assert soa_preferences.baseline_as_time_zero is False


def test_patch_study_soa_preferences(base_data, tst_project):
    service = StudyService()

    study = TestUtils.create_study(project_number=tst_project.project_number)

    soa_preferences = service.patch_study_soa_preferences(
        study.uid, StudySoaPreferencesInput(show_epochs=False)
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is False
    assert soa_preferences.show_milestones is False
    assert soa_preferences.baseline_as_time_zero is True

    soa_preferences = service.patch_study_soa_preferences(
        study.uid, StudySoaPreferencesInput(show_milestones=True)
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is False
    assert soa_preferences.show_milestones is True
    assert soa_preferences.baseline_as_time_zero is True

    soa_preferences = service.patch_study_soa_preferences(
        study.uid, StudySoaPreferencesInput(baseline_as_time_zero=False)
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is False
    assert soa_preferences.show_milestones is True
    assert soa_preferences.baseline_as_time_zero is False

    soa_preferences = service.patch_study_soa_preferences(
        study.uid, StudySoaPreferencesInput(show_epochs=True)
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is True
    assert soa_preferences.show_milestones is True
    assert soa_preferences.baseline_as_time_zero is False

    soa_preferences = service.patch_study_soa_preferences(
        study.uid,
        StudySoaPreferencesInput(
            show_milestones=True, show_epochs=False, baseline_as_time_zero=False
        ),
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is False
    assert soa_preferences.show_milestones is True
    assert soa_preferences.baseline_as_time_zero is False

    study = TestUtils.create_study(project_number=tst_project.project_number)

    soa_preferences = service.patch_study_soa_preferences(
        study.uid, StudySoaPreferencesInput(show_milestones=False)
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is True
    assert soa_preferences.show_milestones is False
    assert soa_preferences.baseline_as_time_zero is True

    study = TestUtils.create_study(project_number=tst_project.project_number)

    soa_preferences = service.patch_study_soa_preferences(
        study.uid,
        StudySoaPreferencesInput(
            show_epochs=True, show_milestones=True, baseline_as_time_zero=True
        ),
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is True
    assert soa_preferences.show_milestones is True
    assert soa_preferences.baseline_as_time_zero is True

    study = TestUtils.create_study(project_number=tst_project.project_number)

    soa_preferences = service.patch_study_soa_preferences(
        study.uid,
        StudySoaPreferencesInput(
            show_epochs=False, show_milestones=False, baseline_as_time_zero=False
        ),
    )
    assert soa_preferences.study_uid == study.uid
    assert soa_preferences.show_epochs is False
    assert soa_preferences.show_milestones is False
    assert soa_preferences.baseline_as_time_zero is False
