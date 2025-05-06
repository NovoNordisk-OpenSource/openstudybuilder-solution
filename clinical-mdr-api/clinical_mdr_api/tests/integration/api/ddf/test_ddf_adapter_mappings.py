"""
Tests for DDF adapter mappings
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from starlette.testclient import TestClient
from usdm_model import StudyArm, StudyElement, StudyEpoch

from clinical_mdr_api.main import app
from clinical_mdr_api.models.study_selections.study import (
    RegistryIdentifiersJsonModel,
    StudyIdentificationMetadataJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
)
from clinical_mdr_api.services.ddf.usdm_mapper import USDMMapper
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_arm_selection import (
    StudyArmSelectionService,
)
from clinical_mdr_api.services.studies.study_design_cell import StudyDesignCellService
from clinical_mdr_api.services.studies.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.services.studies.study_endpoint_selection import (
    StudyEndpointSelectionService,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "ddfadapter.tests.unit"
    inject_and_clear_db(db_name)
    inject_base_data()

    yield


@pytest.fixture(scope="module")
def ddf_mapper(tst_study):
    study_uid = tst_study.uid
    mapper = USDMMapper(
        get_osb_study_design_cells=StudyDesignCellService().get_all_design_cells,
        get_osb_study_arms=StudyArmSelectionService().get_all_selection,
        get_osb_study_epochs=StudyEpochService().get_all_epochs,
        get_osb_study_elements=StudyElementSelectionService().get_all_selection,
        get_osb_study_endpoints=StudyEndpointSelectionService().get_all_selection,
        get_osb_study_visits=StudyVisitService(study_uid).get_all_visits,
        get_osb_study_activities=StudyActivitySelectionService().get_all_selection,
        get_osb_activity_schedules=StudyActivityScheduleService().get_all_schedules,
    )
    return mapper


def test_ddf_study_arms(ddf_mapper, tst_study, study_arms):
    ddf_arms = ddf_mapper._get_study_arms(tst_study)
    for ddf_arm, sb_arm in zip(ddf_arms, study_arms):
        assert ddf_arm.description == sb_arm.description
        assert ddf_arm.type.code == sb_arm.arm_type.term_uid


def test_ddf_study_cells(ddf_mapper, tst_study, study_design_cells):
    ddf_study_cells = ddf_mapper._get_study_cells(tst_study)
    for ddf_study_cell, sb_study_design_cell in zip(
        ddf_study_cells, study_design_cells
    ):
        assert ddf_study_cell.armId == ddf_mapper._id_manager.get_id(
            StudyArm.__name__, sb_study_design_cell.study_arm_uid
        )
        assert ddf_study_cell.epochId == ddf_mapper._id_manager.get_id(
            StudyEpoch.__name__, sb_study_design_cell.study_epoch_uid
        )
        assert ddf_study_cell.elementIds == [
            ddf_mapper._id_manager.get_id(
                StudyElement.__name__, sb_study_design_cell.study_element_uid
            )
        ]


def test_ddf_study_description(ddf_mapper, tst_study):
    ddf_study_description = ddf_mapper._get_study_description(tst_study)
    assert (
        ddf_study_description
        == tst_study.current_metadata.study_description.study_title
    )


def test_ddf_study_activities(ddf_mapper, tst_study, study_activities):
    ddf_study_activities = ddf_mapper._get_study_activities(tst_study)
    assert ddf_study_activities is not None
    assert len(ddf_study_activities) > 0


def test_study_elements(ddf_mapper, tst_study, study_elements):
    ddf_study_elements = ddf_mapper._get_study_elements(tst_study)
    assert ddf_study_elements is not None
    assert len(ddf_study_elements) > 0


def test_study_epochs(ddf_mapper, tst_study, study_epochs):
    ddf_study_epochs = ddf_mapper._get_study_epochs(tst_study)
    assert ddf_study_epochs is not None
    assert len(ddf_study_epochs) > 0


def test_study_visits(ddf_mapper, tst_study, study_visits):
    ddf_study_encounters = ddf_mapper._get_study_encounters(tst_study)
    assert ddf_study_encounters is not None
    assert len(ddf_study_encounters) > 0


def test_study_identifier(ddf_mapper, tst_study):
    ri_metadata = RegistryIdentifiersJsonModel()
    ri_metadata.ct_gov_id = "ct_gov_has_value"
    ri_metadata.eudract_id = "eudract_id_has_value"
    identification_metadata = StudyIdentificationMetadataJsonModel(
        registry_identifiers=ri_metadata
    )
    current_metadata = StudyMetadataJsonModel(
        identification_metadata=identification_metadata
    )
    study_patch_request = StudyPatchRequestJsonModel(current_metadata=current_metadata)
    study_service = StudyService()
    patched_study = study_service.patch(
        uid=tst_study.uid,
        dry=False,
        study_patch_request=study_patch_request,
    )

    ddf_study_identifier = ddf_mapper._get_study_identifier(patched_study)
    assert ddf_study_identifier is not None
