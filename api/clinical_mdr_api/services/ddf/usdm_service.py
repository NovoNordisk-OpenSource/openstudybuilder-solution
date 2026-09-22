from typing import Any

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyComponentEnum,
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
from clinical_mdr_api.services.studies.study_cohort_selection import (
    StudyCohortSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)
from clinical_mdr_api.services.studies.study_criteria_selection import (
    StudyCriteriaSelectionService,
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
from common.telemetry import trace_calls


class USDMService:
    _usdm_mapper: USDMMapper

    @trace_calls
    def __init__(self):
        self._usdm_mapper = USDMMapper(
            get_osb_study_design_cells=StudyDesignCellService().get_all_design_cells,
            get_osb_study_arms=StudyArmSelectionService().get_all_selection,
            get_osb_study_cohorts=StudyCohortSelectionService().get_all_selection,
            get_osb_study_epochs=StudyEpochService.get_all_epochs,
            get_osb_study_elements=StudyElementSelectionService().get_all_selection,
            get_osb_study_endpoints=StudyEndpointSelectionService().get_all_selection,
            get_osb_study_visits=StudyVisitService.get_all_visits,
            get_osb_study_activities=StudyActivitySelectionService().get_all_selection,
            get_osb_activity_schedules=StudyActivityScheduleService().get_all_schedules,
            get_osb_study_criteria=StudyCriteriaSelectionService().get_all_selection,
            get_osb_study_compound_dosings=StudyCompoundDosingSelectionService().get_all_compound_dosings,
        )

    @trace_calls(args=[1], kwargs=["uid"])
    def get_by_uid(self, uid: str) -> dict[str, Any]:
        osb_study = StudyService().get_by_uid(
            uid,
            include_sections=[
                StudyComponentEnum.IDENTIFICATION_METADATA,
                StudyComponentEnum.REGISTRY_IDENTIFIERS,
                StudyComponentEnum.VERSION_METADATA,
                StudyComponentEnum.STUDY_DESCRIPTION,
                StudyComponentEnum.STUDY_DESIGN,
                StudyComponentEnum.STUDY_INTERVENTION,
                StudyComponentEnum.STUDY_POPULATION,
            ],
        )

        usdm_wrapped_study = self._usdm_mapper.map(osb_study)
        return usdm_wrapped_study
