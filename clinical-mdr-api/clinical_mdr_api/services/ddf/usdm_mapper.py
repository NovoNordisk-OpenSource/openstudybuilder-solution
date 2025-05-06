import re
import uuid
from datetime import date
from itertools import chain
from typing import Any, Callable

from neomodel import db
from usdm_info import __model_version__ as usdm_package_version
from usdm_model import Activity as USDMActivity
from usdm_model import AliasCode as USDMAliasCode
from usdm_model import Code as USDMCode
from usdm_model import Encounter as USDMEncounter
from usdm_model import Endpoint as USDMEndpoint
from usdm_model import Indication as USDMIndication
from usdm_model import Objective as USDMObjective
from usdm_model import Organization as USDMOrganization
from usdm_model import Procedure as USDMProcedure
from usdm_model import Quantity as USDMQuantity
from usdm_model import Range as USDMRange
from usdm_model import ScheduledActivityInstance
from usdm_model import ScheduleTimeline as USDMScheduleTimeline
from usdm_model import Study as USDMStudy
from usdm_model import StudyArm
from usdm_model import StudyCell as USDMStudyCell
from usdm_model import StudyDefinitionDocument as USDMStudyDefinitionDocument
from usdm_model import (
    StudyDefinitionDocumentVersion as USDMStudyDefinitionDocumentVersion,
)
from usdm_model import StudyDesign as USDMStudyDesign
from usdm_model import StudyDesignPopulation as USDMStudyDesignPopulation
from usdm_model import StudyElement as USDMStudyElement
from usdm_model import StudyEpoch as USDMStudyEpoch
from usdm_model import StudyIdentifier as USDMStudyIdentifier
from usdm_model import StudyIntervention as USDMStudyIntervention
from usdm_model import StudyTitle as USDMStudyTitle
from usdm_model import StudyVersion as USDMStudyVersion
from usdm_model import Timing as USDMTiming
from usdm_model import TransitionRule as USDMTransitionRule

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.models.study_selections.study import Study as OSBStudy
from clinical_mdr_api.services.ddf.usdm_utils import IdManager

DDF_CT_PACKAGE_EFFECTIVE_DATE = "2023-12-15"
DDF_STUDY_POPULATION_DURATION_UNIT_DAYS = "C25301"
DDF_STUDY_POPULATION_DURATION_UNIT_WEEKS = "C29844"
DDF_STUDY_POPULATION_DURATION_UNIT_MONTHS = "C29846"
DDF_STUDY_POPULATION_DURATION_UNIT_YEARS = "C29848"
DDF_STUDY_PROTOCOL_STATUS_DRAFT = "C85255"
DDF_STUDY_PROTOCOL_STATUS_FINAL = "C25508"
DDF_STUDY_POPULATION_SEX_BOTH = "C49636"
DDF_STUDY_POPULATION_SEX_FEMALE = "C16576"
DDF_STUDY_POPULATION_SEX_MALE = "C20197"
DDF_TIMING_TYPE_AFTER = "C201356"
DDF_TIMING_TYPE_BEFORE = "C201357"
DDF_TIMING_TYPE_FIXED = "C201358"
DDF_TIME_RELATIVE_TO_FROM_START_TO_START = "C201355"


def get_ddf_timing_iso_duration_value(time_value: int, time_unit_name: str) -> str:
    timing_value = "P"
    abs_time_value = abs(time_value)
    if time_unit_name in ["week", "weeks"]:
        timing_value = timing_value + f"{abs_time_value}W"
    elif time_unit_name in ["day", "days"]:
        timing_value = timing_value + f"{abs_time_value}D"
    elif time_unit_name in ["hour", "hours"]:
        timing_value = timing_value + f"T{abs_time_value}H"
    else:
        raise ValueError(f"Unsupported time unit {time_unit_name}")
    return timing_value


def extract_c_code_from_simple_term(term_uid: str) -> str | None:
    regex_match = re.search("(^C[0-9]+)_", term_uid)
    if regex_match:
        return regex_match.group(1)
    return None


def _update_ddf_encounter_scheduled_at(encounters, schedule_timelines):
    encounters_timing_info = []  # (scheduled_instance_id, encounter_id, timing_id)
    timings = list(chain.from_iterable(tl.timings for tl in schedule_timelines))
    for timeline in schedule_timelines:
        for scheduled_instance in timeline.instances:
            encounters_timing_info.append(
                (
                    scheduled_instance.id,
                    scheduled_instance.encounterId,
                    next(
                        (
                            t.id
                            for t in timings
                            if t.relativeFromScheduledInstanceId
                            == scheduled_instance.id
                        ),
                        None,
                    ),
                )
            )
    for e in encounters:
        e.scheduledAtId = next(
            (eti[2] for eti in encounters_timing_info if eti[1] == e.id), None
        )


class USDMMapper:
    def __init__(
        self,
        get_osb_study_design_cells: Callable,
        get_osb_study_arms: Callable,
        get_osb_study_epochs: Callable,
        get_osb_study_elements: Callable,
        get_osb_study_endpoints: Callable,
        get_osb_study_visits: Callable,
        get_osb_study_activities: Callable,
        get_osb_activity_schedules: Callable,
    ):
        self._get_osb_study_design_cells = get_osb_study_design_cells
        self._get_osb_study_arms = get_osb_study_arms
        self._get_osb_study_epochs = get_osb_study_epochs
        self._get_osb_study_elements = get_osb_study_elements
        self._get_osb_study_endpoints = get_osb_study_endpoints
        self._get_osb_study_visits = get_osb_study_visits
        self._get_osb_study_activities = get_osb_study_activities
        self._get_osb_activity_schedules = get_osb_activity_schedules
        self._id_manager = IdManager()

    def get_void_usdm_code(self):
        return USDMCode(
            id=self._id_manager.get_id(USDMCode.__name__, "VOID_CODE"),
            code="",
            codeSystem="",
            codeSystemVersion="",
            decode="",
            instanceType="Code",
        )

    def get_ct_package_term_as_usdm_code(self, concept_id: str | None) -> USDMCode:
        if concept_id is None:
            return self.get_void_usdm_code()
        query = """
            MATCH (l:Library)-[:CONTAINS_TERM]->(cttr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->()-[:LATEST]->(cttav)
            WHERE cttr.uid STARTS WITH $concept_id
            RETURN l, cttav
        """
        result, _ = db.cypher_query(
            query,
            {
                "concept_id": concept_id,
            },
        )
        if len(result) == 0:
            return self.get_void_usdm_code()
        library = result[0][0]
        ct_term_attributes_value = result[0][1]
        code = USDMCode(
            id=self._id_manager.get_id(USDMCode.__name__, concept_id),
            code=concept_id,
            codeSystem=library["name"],
            codeSystemVersion=str(date.today()),
            decode=ct_term_attributes_value["preferred_term"],
            instanceType="Code",
        )
        return code

    def get_ddf_study_population_duration_unit_from_name_as_code(
        self, time_unit_name: str
    ) -> USDMCode:
        lowered_time_unit_name = time_unit_name.lower()
        if lowered_time_unit_name in ["day", "days"]:
            return self.get_ddf_study_population_duration_unit_days()
        if lowered_time_unit_name in ["week", "weeks"]:
            return self.get_ddf_study_population_duration_unit_weeks()
        if lowered_time_unit_name in ["month", "months"]:
            return self.get_ddf_study_population_duration_unit_months()
        if lowered_time_unit_name in ["year", "years"]:
            return self.get_ddf_study_population_duration_unit_years()
        return self.get_void_usdm_code()

    def get_ddf_study_population_duration_unit_days(self):
        return self.get_ct_package_term_as_usdm_code(
            DDF_STUDY_POPULATION_DURATION_UNIT_DAYS
        )

    def get_ddf_study_population_duration_unit_weeks(self):
        return self.get_ct_package_term_as_usdm_code(
            DDF_STUDY_POPULATION_DURATION_UNIT_WEEKS
        )

    def get_ddf_study_population_duration_unit_months(self):
        return self.get_ct_package_term_as_usdm_code(
            DDF_STUDY_POPULATION_DURATION_UNIT_MONTHS
        )

    def get_ddf_study_population_duration_unit_years(self):
        return self.get_ct_package_term_as_usdm_code(
            DDF_STUDY_POPULATION_DURATION_UNIT_YEARS
        )

    def get_ddf_study_protocol_status_draft(self):
        return self.get_ct_package_term_as_usdm_code(DDF_STUDY_PROTOCOL_STATUS_DRAFT)

    def get_ddf_study_protocol_status_final(self):
        return self.get_ct_package_term_as_usdm_code(DDF_STUDY_PROTOCOL_STATUS_FINAL)

    def get_ddf_study_population_sex_both(self):
        return self.get_ct_package_term_as_usdm_code(DDF_STUDY_POPULATION_SEX_BOTH)

    def get_ddf_study_population_sex_female(self):
        return self.get_ct_package_term_as_usdm_code(DDF_STUDY_POPULATION_SEX_FEMALE)

    def get_ddf_study_population_sex_male(self):
        return self.get_ct_package_term_as_usdm_code(DDF_STUDY_POPULATION_SEX_MALE)

    def get_ddf_timing_type_code_after(self):
        return self.get_ct_package_term_as_usdm_code(DDF_TIMING_TYPE_AFTER)

    def get_ddf_timing_type_code_before(self):
        return self.get_ct_package_term_as_usdm_code(DDF_TIMING_TYPE_BEFORE)

    def get_ddf_timing_type_code_fixed(self):
        return self.get_ct_package_term_as_usdm_code(DDF_TIMING_TYPE_FIXED)

    def get_ddf_timing_relative_to_from(self):
        return self.get_ct_package_term_as_usdm_code(
            DDF_TIME_RELATIVE_TO_FROM_START_TO_START
        )

    def get_dictionary_term_as_usdm_code(self, term_uid: str) -> USDMCode:
        if term_uid is None:
            return self.get_void_usdm_code()
        query = """
            MATCH (l:Library)-[:CONTAINS_DICTIONARY_TERM]->(dtr:DictionaryTermRoot)-[:LATEST]->(dtv)
            WHERE dtr.uid STARTS WITH $term_uid
            RETURN l, dtv
        """
        result, _ = db.cypher_query(
            query,
            {
                "term_uid": term_uid,
            },
        )
        if len(result) == 0:
            return self.get_void_usdm_code()
        library = result[0][0]
        ct_term_attributes_value = result[0][1]
        code = USDMCode(
            id=self._id_manager.get_id(USDMCode.__name__, term_uid),
            code=term_uid,
            codeSystem=library["name"],
            codeSystemVersion=str(date.today()),
            decode=ct_term_attributes_value["name"],
            instanceType="Code",
        )
        return code

    def map(self, study: OSBStudy) -> dict[str, Any]:
        usdm_study = USDMStudy(name=self._get_study_name(study), instanceType="Study")
        usdm_study.id = uuid.uuid4()
        usdm_study.label = self._get_study_label(study)

        # Set DDF study description
        usdm_study.description = self._get_study_description(study)

        # Set DDF study protocol document
        ddf_study_protocol_document = self._get_study_definition_document(study)
        usdm_study.documentedBy = [ddf_study_protocol_document]

        # Set DDF study title in version
        ddf_study_title = USDMStudyTitle(
            id=self._id_manager.get_id(USDMStudyTitle.__name__),
            text=self._get_study_title(study),
            type=self.get_void_usdm_code(),
            instanceType="StudyTitle",
        )

        usdm_version = USDMStudyVersion(
            id=self._id_manager.get_id(USDMStudyVersion.__name__),
            titles=[ddf_study_title],
            studyIdentifiers=self._get_study_identifier(study),
            versionIdentifier="",
            rationale="",
            instanceType="StudyVersion",
        )

        # Set DDF study version identifier
        usdm_version.versionIdentifier = self._get_study_version(study)
        # Set study interventions
        usdm_version.studyInterventions = self._get_study_interventions(study)
        # Set DDF study design
        usdm_version.studyDesigns = self._get_study_designs(study)

        # Inject interventions IDs into study design
        usdm_version.studyDesigns[0].studyInterventionIds = [
            intervention.id for intervention in usdm_version.studyInterventions
        ]

        # Set DDF study versions
        usdm_study.versions = [usdm_version]

        wrapped_study = {
            "study": usdm_study,
            "usdmVersion": usdm_package_version,
            "systemName": None,
            "systemVersion": None,
        }

        return wrapped_study

    def _get_intervention_model(self, study: OSBStudy):
        osb_current_metadata = getattr(study, "current_metadata", None)
        osb_study_intervention = getattr(
            osb_current_metadata, "study_intervention", None
        )
        osb_study_intervention_model_code = getattr(
            osb_study_intervention, "intervention_model_code", None
        )
        if osb_study_intervention_model_code:
            return self.get_ct_package_term_as_usdm_code(
                extract_c_code_from_simple_term(
                    study.current_metadata.study_intervention.intervention_model_code.term_uid
                )
            )
        return self.get_void_usdm_code()

    def _get_study_arms(self, study: OSBStudy):
        osb_study_arms = self._get_osb_study_arms(study.uid).items
        return [
            StudyArm(
                id=self._id_manager.get_id(StudyArm.__name__, sa.arm_uid),
                name=sa.name,
                label=sa.name,
                description=sa.description,
                type=(
                    self.get_ct_package_term_as_usdm_code(sa.arm_type.term_uid)
                    if sa.arm_type
                    else self.get_void_usdm_code()
                ),
                dataOriginDescription="",
                dataOriginType=self.get_void_usdm_code(),
            )
            for sa in osb_study_arms
        ]

    def _get_study_cells(self, study: OSBStudy):
        osb_design_cells = self._get_osb_study_design_cells(study.uid)
        return [
            USDMStudyCell(
                id=self._id_manager.get_id(USDMStudyCell.__name__, dc.design_cell_uid),
                armId=self._id_manager.get_id(StudyArm.__name__, dc.study_arm_uid),
                epochId=self._id_manager.get_id(
                    USDMStudyEpoch.__name__, dc.study_epoch_uid
                ),
                elementIds=[
                    self._id_manager.get_id(
                        USDMStudyElement.__name__, dc.study_element_uid
                    )
                ],
            )
            for dc in osb_design_cells
            if dc.study_arm_uid is not None
            and dc.study_epoch_uid is not None
            and dc.study_element_uid is not None
        ]

    def _get_study_description(self, study: OSBStudy):
        study_description = getattr(
            getattr(study, "current_metadata", None), "study_description", None
        )
        return getattr(study_description, "study_title", None)

    def _get_study_designs(self, study: OSBStudy):
        # Create DDF study design and set intervention model
        ddf_study_design = USDMStudyDesign(
            id=self._id_manager.get_id(USDMStudyDesign.__name__),
            name="Study Design  1",
            description="The main design for the study",
            arms=[],
            studyCells=[],
            rationale="",
            epochs=[],
            # TODO: reactivate when intervention model is available in package as InterventionalStudyDesign attribute
            # model=self._get_intervention_model(study),
            population=self._get_study_population(study),
            instanceType="StudyDesign",
        )

        # Set DDF study type in version
        ddf_study_design.studyType = self._get_study_type(study)
        # Set study phase
        ddf_study_design.studyPhase = self._get_study_phase(study)

        # Set therapeutic areas
        ddf_study_design.therapeuticAreas = self._get_therapeutic_areas(study)

        # Set trial type codes
        # TODO: reactivate when subTypes is available in package as InterventionalStudyDesign attribute
        # ddf_study_design.subTypes = self._get_trial_type_codes(study)

        # Set trial intent type codes
        # TODO: reactivate when intentTypes is available in package as InterventionalStudyDesign attribute
        # ddf_study_design.intentTypes = self._get_trial_intent_types_codes(study)

        # Set study arms
        ddf_study_design.arms = self._get_study_arms(study)

        # Set study elements
        ddf_study_design.elements = self._get_study_elements(study)

        # Set study epochs
        ddf_study_design.epochs = self._get_study_epochs(study)

        # Set study cells
        ddf_study_design.studyCells = self._get_study_cells(study)

        # Set study indications
        ddf_study_design.indications = self._get_study_indications(study)

        # Set study objectives and endpoints
        ddf_study_design.objectives = self._get_study_objectives(study)

        # Set study visits/encounters
        ddf_study_design.encounters = self._get_study_encounters(study)

        # Set study activities
        ddf_study_design.activities = self._get_study_activities(study)

        # Set schedule timeline
        ddf_study_design.scheduleTimelines = self._get_study_schedule_timelines(study)

        _update_ddf_encounter_scheduled_at(
            ddf_study_design.encounters, ddf_study_design.scheduleTimelines
        )

        return [ddf_study_design]

    def _get_study_activities(self, study: OSBStudy):
        osb_study_activities = self._get_osb_study_activities(study.uid).items
        return [
            USDMActivity(
                id=self._id_manager.get_id(USDMActivity.__name__, a.study_activity_uid),
                name=(
                    a.study_activity_subgroup.activity_subgroup_name
                    if a.study_activity_subgroup
                    and getattr(
                        a.study_activity_subgroup, "activity_subgroup_name", None
                    )
                    else " "
                ),
                isConditional=False,  # TODO hardcoded
                definedProcedures=(
                    [
                        USDMProcedure(
                            id=self._id_manager.get_id(
                                USDMProcedure.__name__, a.activity.uid
                            ),
                            name=a.activity.name,
                            procedureType="",
                            code=self.get_void_usdm_code(),
                            isConditional=False,  # TODO hardcoded
                        )
                    ]
                    if a.activity is not None and a.activity.name is not None
                    else []
                ),
            )
            for a in osb_study_activities
        ]

    def _get_study_elements(self, study: OSBStudy):
        osb_study_elements = self._get_osb_study_elements(study.uid).items
        ddf_study_elements = []
        for osb_se in osb_study_elements:
            ddf_se_id = self._id_manager.get_id(
                USDMStudyElement.__name__, osb_se.element_uid
            )
            ddf_se = USDMStudyElement(
                id=ddf_se_id,
                name=ddf_se_id,
                description=osb_se.description,
                label=osb_se.name,
                instanceType="StudyElement",
            )
            ddf_study_elements.append(ddf_se)
        return ddf_study_elements

    def _get_study_epochs(self, study: OSBStudy):
        osb_study_epochs = self._get_osb_study_epochs(study.uid).items

        # Since order is not mandatory in StudyEpoch, add next and previous IDs only
        # if order is available for every epoch
        osb_study_epochs_order_numbers = [e.order for e in osb_study_epochs]
        add_next_and_previous_ids = False
        if all(n is not None for n in osb_study_epochs_order_numbers) and len(
            osb_study_epochs_order_numbers
        ) == len(osb_study_epochs):
            add_next_and_previous_ids = True
            osb_study_epochs.sort(key=lambda e: e.order, reverse=False)

        ddf_study_epochs = [
            USDMStudyEpoch(
                id=self._id_manager.get_id(USDMStudyEpoch.__name__, se.uid),
                name=se.epoch_name if se.epoch_name is not None else " ",
                label=se.epoch_name,
                description=se.description,
                type=(
                    self.get_ct_package_term_as_usdm_code(se.epoch_type_ctterm.term_uid)
                    if se.epoch_type_ctterm is not None
                    else self.get_void_usdm_code()
                ),
                nextId=(
                    self._id_manager.get_id(
                        USDMStudyEpoch.__name__, osb_study_epochs[i + 1].uid
                    )
                    if add_next_and_previous_ids and i + 1 < len(osb_study_epochs)
                    else None
                ),
                previousId=(
                    self._id_manager.get_id(
                        USDMStudyEpoch.__name__, osb_study_epochs[i - 1].uid
                    )
                    if add_next_and_previous_ids and i - 1 >= 0
                    else None
                ),
            )
            for i, se in enumerate(osb_study_epochs)
        ]
        return ddf_study_epochs

    def _get_study_name(self, study: OSBStudy):
        osb_identification_metadata = getattr(
            getattr(study, "current_metadata", None), "identification_metadata", None
        )
        osb_study_id = getattr(osb_identification_metadata, "study_id", "")
        return osb_study_id

    def _get_study_identifier(self, study: OSBStudy):
        osb_identification_metadata = getattr(
            getattr(study, "current_metadata", None), "identification_metadata", None
        )
        osb_study_id = getattr(osb_identification_metadata, "study_id", "")

        organization = USDMOrganization(
            id=self._id_manager.get_id(USDMOrganization.__name__),
            name="NOVO NORDISK",
            identifier="NOVO NORDISK",
            identifierScheme="OpenStudyBuilder",
            label="Novo Nordisk A/S is a Danish multinational pharmaceutical company headquartered in Bagsværd with "
            "production facilities in nine countries and affiliates or offices in five countries.",
            type=self.get_void_usdm_code(),
        )
        study_identifier = USDMStudyIdentifier(
            id=self._id_manager.get_id(USDMStudyIdentifier.__name__),
            scopeId=organization.id,
            text=osb_study_id,
        )
        return [study_identifier]

    def _get_study_indications(self, study: OSBStudy):
        osb_study_population = getattr(
            getattr(study, "current_metadata", None), "study_population", None
        )
        if osb_study_population is None:
            return []
        osb_study_population_disease_condition_or_indication_codes = getattr(
            osb_study_population, "disease_condition_or_indication_codes", []
        )
        osb_study_population_rare_disease_indicator = getattr(
            osb_study_population, "rare_disease_indicator", None
        )

        ddf_study_indications = []
        for (
            osb_disease_or_indication
        ) in osb_study_population_disease_condition_or_indication_codes:
            osb_disease_or_indication_name = getattr(
                osb_disease_or_indication, "name", None
            )
            if (
                osb_disease_or_indication_name is not None
                and osb_study_population_rare_disease_indicator is not None
            ):
                ddf_study_indication = USDMIndication(
                    id=self._id_manager.get_id(USDMIndication.__name__),
                    name=osb_disease_or_indication_name,
                    label=osb_disease_or_indication_name,
                    isRareDisease=osb_study_population_rare_disease_indicator,
                )
                ddf_study_indications.append(ddf_study_indication)
        return ddf_study_indications

    def _get_study_interventions(self, study: OSBStudy):
        osb_study_intervention = study.current_metadata.study_intervention
        usdm_study_intervention_codes = []

        if osb_study_intervention.intervention_model_code is not None:
            intervention_model_code = self.get_ct_package_term_as_usdm_code(
                osb_study_intervention.intervention_model_code.term_uid
            )
            usdm_study_intervention_codes.append(intervention_model_code)

        if osb_study_intervention.intervention_type_code is not None:
            intervention_type_code = self.get_ct_package_term_as_usdm_code(
                osb_study_intervention.intervention_type_code.term_uid
            )
            usdm_study_intervention_codes.append(intervention_type_code)

        if osb_study_intervention.control_type_code is not None:
            intervention_control_type_code = self.get_ct_package_term_as_usdm_code(
                osb_study_intervention.control_type_code.term_uid
            )
            usdm_study_intervention_codes.append(intervention_control_type_code)

        if osb_study_intervention.trial_blinding_schema_code is not None:
            intervention_trial_blinding_schema_code = (
                self.get_ct_package_term_as_usdm_code(
                    osb_study_intervention.trial_blinding_schema_code.term_uid
                )
            )
            usdm_study_intervention_codes.append(
                intervention_trial_blinding_schema_code
            )

        if (
            osb_study_intervention.trial_intent_types_codes is not None
            and len(osb_study_intervention.trial_intent_types_codes) > 0
        ):
            intervention_trial_intent_types_codes = [
                self.get_ct_package_term_as_usdm_code(type_code.term_uid)
                for type_code in osb_study_intervention.trial_intent_types_codes
                if type_code
            ]
            if len(intervention_trial_intent_types_codes) > 0:
                for c in intervention_trial_intent_types_codes:
                    if c is not None:
                        usdm_study_intervention_codes.append(c)

        if len(usdm_study_intervention_codes) == 0:
            usdm_study_intervention_codes = [self.get_void_usdm_code()]

        return [
            USDMStudyIntervention(
                id=self._id_manager.get_id(USDMStudyIntervention.__name__),
                name="Study Intervention",
                description=(
                    osb_study_intervention.intervention_model_code.sponsor_preferred_name
                    if osb_study_intervention.intervention_model_code is not None
                    else None
                ),
                codes=usdm_study_intervention_codes,
                role=self.get_void_usdm_code(),
                type=self.get_void_usdm_code(),
                productDesignation=self.get_void_usdm_code(),
            )
        ]

    def _get_study_label(self, study: OSBStudy):
        if study.current_metadata is not None:
            if study.current_metadata.study_description is not None:
                return study.current_metadata.study_description.study_short_title
        return None

    def _get_study_objectives(self, study: OSBStudy):
        osb_study_endpoints = self._get_osb_study_endpoints(
            study.uid, no_brackets=True
        ).items
        return [
            USDMObjective(
                id=self._id_manager.get_id(
                    USDMObjective.__name__, se.study_objective.objective.uid
                ),
                instanceType="Objective",
                label=se.study_objective.objective.name_plain,
                text=se.study_objective.objective.name_plain,
                level=(
                    self.get_ct_package_term_as_usdm_code(
                        se.study_objective.objective_level.term_uid
                    )
                    if se.study_objective.objective_level is not None
                    else self.get_void_usdm_code()
                ),
                name=self._id_manager.get_id(
                    USDMObjective.__name__, se.study_objective.objective.uid
                ),
                description=se.study_objective.objective.name,
                endpoints=(
                    [
                        USDMEndpoint(
                            id=self._id_manager.get_id(
                                USDMEndpoint.__name__, se.endpoint.uid
                            ),
                            name=self._id_manager.get_id(
                                USDMEndpoint.__name__, se.endpoint.uid
                            ),
                            description=se.endpoint.name,
                            instanceType="Endpoint",
                            text=(
                                se.endpoint.name_plain
                                if se.endpoint.name is not None
                                else ""
                            ),
                            purpose=(
                                se.endpoint.name_plain
                                if se.endpoint.name_plain is not None
                                else ""
                            ),
                            label=(
                                se.endpoint.name_plain
                                if se.endpoint.name_plain is not None
                                else ""
                            ),
                            level=(
                                self.get_ct_package_term_as_usdm_code(
                                    se.endpoint_level.term_uid
                                )
                                if se.endpoint_level is not None
                                else self.get_void_usdm_code()
                            ),
                        )
                    ]
                    if se.endpoint is not None
                    else []
                ),
            )
            for se in osb_study_endpoints
            if se.study_objective is not None
        ]

    def _get_study_phase(self, study: OSBStudy):
        osb_study_design = getattr(
            getattr(study, "current_metadata", None), "high_level_study_design", None
        )
        osb_trial_phase_code = getattr(osb_study_design, "trial_phase_code", None)
        if osb_trial_phase_code:
            study_phase_code = self.get_ct_package_term_as_usdm_code(
                extract_c_code_from_simple_term(osb_trial_phase_code.term_uid)
            )
        else:
            study_phase_code = self.get_void_usdm_code()
        study_phase = USDMAliasCode(
            id=self._id_manager.get_id(USDMAliasCode.__name__),
            standardCode=study_phase_code,
            instanceType="AliasCode",
        )
        return study_phase

    def _get_study_population(self, study: OSBStudy):
        osb_study_population = study.current_metadata.study_population
        planned_sex_usdm_code = None
        if osb_study_population.sex_of_participants_code is not None:
            sex_term_uid_upper = (
                osb_study_population.sex_of_participants_code.sponsor_preferred_name.upper()
            )
            match sex_term_uid_upper:
                case "BOTH":
                    planned_sex_usdm_code = self.get_ddf_study_population_sex_both()
                case "FEMALE":
                    planned_sex_usdm_code = self.get_ddf_study_population_sex_female()
                case "MALE":
                    planned_sex_usdm_code = self.get_ddf_study_population_sex_male()
        if planned_sex_usdm_code is None:
            planned_sex_usdm_code = self.get_void_usdm_code()

        planned_age = None
        if (
            osb_study_population.planned_minimum_age_of_subjects is not None
            and osb_study_population.planned_maximum_age_of_subjects is not None
        ):
            if (
                osb_study_population.planned_minimum_age_of_subjects.duration_value
                is not None
                and osb_study_population.planned_maximum_age_of_subjects.duration_value
                is not None
            ):
                planned_age = USDMRange(
                    id=self._id_manager.get_id(USDMRange.__name__),
                    minValue=USDMQuantity(
                        id=self._id_manager.get_id(USDMQuantity.__name__),
                        value=osb_study_population.planned_minimum_age_of_subjects.duration_value,
                        unit=USDMAliasCode(
                            id=self._id_manager.get_id(USDMAliasCode.__name__),
                            standardCode=(
                                self.get_ddf_study_population_duration_unit_from_name_as_code(
                                    osb_study_population.planned_minimum_age_of_subjects.duration_unit_code.name
                                )
                                if osb_study_population.planned_minimum_age_of_subjects.duration_unit_code.name
                                is not None
                                else self.get_void_usdm_code()
                            ),
                            instanceType="AliasCode",
                        ),
                        instanceType="Quantity",
                    ),
                    maxValue=USDMQuantity(
                        id=self._id_manager.get_id(USDMQuantity.__name__),
                        value=osb_study_population.planned_maximum_age_of_subjects.duration_value,
                        unit=USDMAliasCode(
                            id=self._id_manager.get_id(USDMAliasCode.__name__),
                            standardCode=(
                                self.get_ddf_study_population_duration_unit_from_name_as_code(
                                    osb_study_population.planned_maximum_age_of_subjects.duration_unit_code.name
                                )
                                if osb_study_population.planned_maximum_age_of_subjects.duration_unit_code.name
                                is not None
                                else self.get_void_usdm_code()
                            ),
                            instanceType="AliasCode",
                        ),
                        instanceType="Quantity",
                    ),
                    isApproximate=False,
                    instanceType="Range",
                )
        planned_enrollment_number = None
        if osb_study_population.number_of_expected_subjects is not None:
            planned_enrollment_number = USDMRange(
                id=self._id_manager.get_id(USDMRange.__name__),
                minValue=osb_study_population.number_of_expected_subjects,
                maxValue=osb_study_population.number_of_expected_subjects,
                unit=self.get_void_usdm_code(),
                isApproximate=False,
                instanceType="Range",
            )

        population = USDMStudyDesignPopulation(
            id=self._id_manager.get_id(USDMStudyDesignPopulation.__name__),
            name="Study Design Population",
            plannedSex=[planned_sex_usdm_code],
            plannedEnrollmentNumber=planned_enrollment_number,
            plannedAge=planned_age,
            includesHealthySubjects=(
                osb_study_population.healthy_subject_indicator
                if osb_study_population.healthy_subject_indicator is not None
                else False
            ),
        )

        # Add population description as a concatenation of attributes
        usdm_population_description_attrs = [
            "diagnosis_group_codes",
            "disease_condition_or_indication_codes",
            "healthy_subject_indicator",
            "number_of_expected_subjects",
            "pediatric_investigation_plan_indicator",
            "pediatric_postmarket_study_indicator",
            "pediatric_study_indicator",
            "planned_maximum_age_of_subjects",
            "planned_minimum_age_of_subjects",
            "rare_disease_indicator",
            "relapse_criteria",
            "sex_of_participants_code",
            "stable_disease_minimum_duration",
            "therapeutic_area_code",
        ]
        description = " | ".join(
            [
                a + ": " + str(getattr(osb_study_population, a, None))
                for a in usdm_population_description_attrs
            ]
        )
        population.description = description

        return population

    def _get_study_definition_document(self, study: OSBStudy):
        ddf_study_definition_document = USDMStudyDefinitionDocument(
            id=self._id_manager.get_id(USDMStudyDefinitionDocument.__name__),
            name="Study Definition Document",
            language=self.get_void_usdm_code(),
            type=self.get_void_usdm_code(),
            templateName="",
            instanceType="StudyDefinitionDocument",
        )

        osb_current_metadata = getattr(study, "current_metadata", None)
        osb_study_status = getattr(
            getattr(osb_current_metadata, "version_metadata", None),
            "study_status",
            None,
        )
        osb_version_number = getattr(
            getattr(osb_current_metadata, "version_metadata", None),
            "version_number",
            None,
        )

        if osb_study_status == StudyStatus.DRAFT.value:
            ddf_protocol_status = self.get_ddf_study_protocol_status_draft()
        elif osb_study_status == StudyStatus.LOCKED.value:
            ddf_protocol_status = self.get_ddf_study_protocol_status_final()
        else:
            # TODO raise exception if not draft or locked status
            ddf_protocol_status = self.get_void_usdm_code()

        ddf_study_definition_document_version = USDMStudyDefinitionDocumentVersion(
            id=self._id_manager.get_id(USDMStudyDefinitionDocumentVersion.__name__),
            instanceType="StudyDefinitionDocumentVersion",
            status=ddf_protocol_status,
            version="DRAFT" if osb_study_status == "DRAFT" else str(osb_version_number),
        )

        ddf_study_definition_document.versions = [ddf_study_definition_document_version]
        return ddf_study_definition_document

    def _get_study_schedule_timelines(self, study):
        osb_study_activity_schedules = self._get_osb_activity_schedules(study.uid)
        osb_study_visits = self._get_osb_study_visits(study.uid).items

        # Create main timeline
        usdm_timeline_id = self._id_manager.get_id(USDMScheduleTimeline.__name__)
        usdm_timeline = USDMScheduleTimeline(
            id=usdm_timeline_id,
            name="Main Timeline",
            mainTimeline=True,
            entryCondition="",
            entryId="",
            instances=[],
        )

        # Create scheduled instances
        timeline_instances = []
        usdm_timings = []
        osb_global_anchor_visit = next(
            (v for v in osb_study_visits if v.is_global_anchor_visit is True), None
        )

        fixed_reference_scheduled_instance_id = self._id_manager.get_id(
            ScheduledActivityInstance.__name__
        )
        for osb_visit in osb_study_visits:
            osb_schedules_for_osb_visit = [
                s
                for s in osb_study_activity_schedules
                if s.study_visit_uid == osb_visit.uid
            ]

            curr_scheduled_instance_id = (
                self._id_manager.get_id(ScheduledActivityInstance.__name__)
                if osb_visit != osb_global_anchor_visit
                else fixed_reference_scheduled_instance_id
            )
            curr_scheduled_instance = ScheduledActivityInstance(
                id=curr_scheduled_instance_id,
                name="Activity Instance",
                timelineId=usdm_timeline_id,
                instanceType="ScheduledActivityInstance",
                encounterId=self._id_manager.get_id(
                    USDMEncounter.__name__, osb_visit.uid
                ),
                activityIds=[
                    self._id_manager.get_id(
                        USDMActivity.__name__, osb_schedule.study_activity_uid
                    )
                    for osb_schedule in osb_schedules_for_osb_visit
                ],
                epochId=self._id_manager.get_id(
                    USDMStudyEpoch.__name__, osb_visit.study_epoch_uid
                ),
            )

            ddf_timing_code = None
            if osb_visit.time_value:
                if osb_visit.time_value < 0:
                    ddf_timing_code = self.get_ddf_timing_type_code_before()
                elif osb_visit.time_value > 0:
                    ddf_timing_code = self.get_ddf_timing_type_code_after()
                else:
                    ddf_timing_code = self.get_ddf_timing_type_code_fixed()

            if ddf_timing_code is None:
                # No timing concept term in db
                ddf_timing_code = self.get_void_usdm_code()

            ddf_timing_id = self._id_manager.get_id(USDMTiming.__name__)
            ddf_timing_window_available = all(
                [
                    osb_visit.min_visit_window_value is not None,
                    osb_visit.max_visit_window_value is not None,
                    osb_visit.min_visit_window_value != 0
                    or osb_visit.max_visit_window_value != 0,
                ]
            )
            ddf_timing = USDMTiming(
                id=ddf_timing_id,
                name=ddf_timing_id,
                label=osb_visit.study_epoch.sponsor_preferred_name,
                description=osb_visit.study_epoch.sponsor_preferred_name,
                type=ddf_timing_code,
                relativeToFrom=self.get_ddf_timing_relative_to_from()
                or self.get_void_usdm_code(),
                value=(
                    get_ddf_timing_iso_duration_value(
                        osb_visit.time_value, osb_visit.time_unit_name
                    )
                    if osb_visit.time_value is not None
                    else ""
                ),
                valueLabel=(
                    f"{str(abs(osb_visit.time_value))} {osb_visit.time_unit_name}"
                    if osb_visit.time_value is not None
                    else ""
                ),
                relativeFromScheduledInstanceId=curr_scheduled_instance_id,
                relativeToScheduledInstanceId=fixed_reference_scheduled_instance_id,
                windowLower=(
                    get_ddf_timing_iso_duration_value(
                        osb_visit.min_visit_window_value,
                        osb_visit.visit_window_unit_name,
                    )
                    if ddf_timing_window_available
                    else None
                ),
                windowUpper=(
                    get_ddf_timing_iso_duration_value(
                        osb_visit.max_visit_window_value,
                        osb_visit.visit_window_unit_name,
                    )
                    if ddf_timing_window_available
                    else None
                ),
                window=(
                    f"{osb_visit.min_visit_window_value}..{osb_visit.max_visit_window_value} {osb_visit.visit_window_unit_name}"
                    if ddf_timing_window_available
                    else None
                ),
            )
            timeline_instances.append(curr_scheduled_instance)
            usdm_timings.append(ddf_timing)
        usdm_timeline.timings = usdm_timings
        usdm_timeline.instances = timeline_instances
        return [usdm_timeline]

    def _get_study_title(self, study: OSBStudy):
        osb_current_metadata = getattr(study, "current_metadata", None)
        study_title = getattr(
            getattr(osb_current_metadata, "study_description", None), "study_title", ""
        )
        if study_title is not None:
            return study_title
        return "Study title not available"

    def _get_study_type(self, study: OSBStudy):
        osb_study_design = getattr(
            getattr(study, "current_metadata", None), "high_level_study_design", None
        )
        osb_study_type_code = getattr(osb_study_design, "study_type_code", None)
        if osb_study_type_code:
            return self.get_ct_package_term_as_usdm_code(
                extract_c_code_from_simple_term(osb_study_type_code.term_uid)
            )
        return self.get_void_usdm_code()

    def _get_study_version(self, study: OSBStudy):
        osb_current_metadata = getattr(study, "current_metadata", None)
        return str(
            getattr(
                getattr(osb_current_metadata, "version_metadata", None),
                "version_number",
                "",
            )
        )

    def _get_study_encounters(self, study: OSBStudy):
        osb_study_visits = self._get_osb_study_visits(study.uid).items
        ordered_osb_study_visits = sorted(
            osb_study_visits, key=lambda sv: sv.visit_number, reverse=False
        )
        ddf_encounters = [
            USDMEncounter(
                id=self._id_manager.get_id(USDMEncounter.__name__, sv.uid),
                name=sv.visit_short_name,
                label=sv.visit_name,
                description=sv.description,
                type=self.get_ct_package_term_as_usdm_code(sv.visit_type_uid),
                transitionStartRule=USDMTransitionRule(
                    id=self._id_manager.get_id(USDMTransitionRule.__name__),
                    name="Transition Start Rule",
                    text=sv.start_rule if sv.start_rule is not None else "",
                ),
                transitionEndRule=USDMTransitionRule(
                    id=self._id_manager.get_id(USDMTransitionRule.__name__),
                    name="Transition End Rule",
                    text=sv.end_rule if sv.end_rule is not None else "",
                ),
                contactModes=[
                    self.get_ct_package_term_as_usdm_code(sv.visit_contact_mode_uid)
                ],
                nextId=(
                    self._id_manager.get_id(
                        USDMEncounter.__name__, ordered_osb_study_visits[i + 1].uid
                    )
                    if i + 1 < len(ordered_osb_study_visits)
                    else None
                ),
                previousId=(
                    self._id_manager.get_id(
                        USDMEncounter.__name__, ordered_osb_study_visits[i - 1].uid
                    )
                    if i - 1 >= 0
                    else None
                ),
            )
            for i, sv in enumerate(ordered_osb_study_visits)
        ]

        return ddf_encounters

    def _get_therapeutic_areas(self, study):
        osb_current_metadata = getattr(study, "current_metadata", None)
        osb_study_population = getattr(osb_current_metadata, "study_population", None)
        if osb_study_population:
            return [
                self.get_dictionary_term_as_usdm_code(
                    osb_therapeutic_area_code.term_uid
                )
                for osb_therapeutic_area_code in study.current_metadata.study_population.therapeutic_area_codes
            ]
        return []

    def _get_trial_intent_types_codes(self, study):
        osb_current_metadata = getattr(study, "current_metadata", None)
        osb_study_intervention = getattr(
            osb_current_metadata, "study_intervention", None
        )
        if osb_study_intervention:
            return [
                (
                    self.get_ct_package_term_as_usdm_code(
                        osb_trial_intent_type_code.term_uid
                    )
                    if osb_trial_intent_type_code.term_uid is not None
                    else self.get_void_usdm_code()
                )
                for osb_trial_intent_type_code in study.current_metadata.study_intervention.trial_intent_types_codes
                if osb_trial_intent_type_code
            ]
        return []

    def _get_trial_type_codes(self, study: OSBStudy):
        return [
            (
                self.get_ct_package_term_as_usdm_code(osb_trial_type_code.term_uid)
                if osb_trial_type_code.term_uid is not None
                else self.get_void_usdm_code()
            )
            for osb_trial_type_code in study.current_metadata.high_level_study_design.trial_type_codes
            if osb_trial_type_code
        ]
