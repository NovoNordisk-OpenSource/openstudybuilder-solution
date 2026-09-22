import re
import uuid
from datetime import date, datetime, timezone
from itertools import chain
from typing import Any, Callable

from neomodel import db
from usdm_info import __model_version__ as usdm_package_version
from usdm_model import Activity as USDMActivity
from usdm_model import Administration as USDMAdministration
from usdm_model import AliasCode as USDMAliasCode
from usdm_model import BiomedicalConcept as USDMBiomedicalConcept
from usdm_model import BiomedicalConceptProperty as USDMBiomedicalConceptProperty
from usdm_model import Code as USDMCode
from usdm_model import Duration as USDMDuration
from usdm_model import EligibilityCriterion as USDMEligibilityCriterion
from usdm_model import EligibilityCriterionItem as USDMEligibilityCriterionItem
from usdm_model import Encounter as USDMEncounter
from usdm_model import Endpoint as USDMEndpoint
from usdm_model import Indication as USDMIndication
from usdm_model import InterventionalStudyDesign as USDMInterventionalStudyDesign
from usdm_model import Objective as USDMObjective
from usdm_model import Organization as USDMOrganization
from usdm_model import Procedure as USDMProcedure
from usdm_model import Quantity as USDMQuantity
from usdm_model import Range as USDMRange
from usdm_model import ResponseCode as USDMResponseCode
from usdm_model import (
    ScheduledActivityInstance,
)
from usdm_model import ScheduleTimeline as USDMScheduleTimeline
from usdm_model import Study as USDMStudy
from usdm_model import (
    StudyArm,
)
from usdm_model import StudyCell as USDMStudyCell
from usdm_model import (
    StudyCohort,
)
from usdm_model import StudyDefinitionDocument as USDMStudyDefinitionDocument
from usdm_model import (
    StudyDefinitionDocumentVersion as USDMStudyDefinitionDocumentVersion,
)
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
from clinical_mdr_api.utils.api_version import get_api_version
from common.telemetry import trace_calls

DDF_ORGANIZATION_TYPE_STUDY_REGISTRY = "C93453"
DDF_ORGANIZATION_TYPE_REGULATORY_AGENCY = "C188863"
DDF_STUDY_ARM_DATA_ORIGIN_TYPE_GENERATED_WITHIN_STUDY = "C188866"
DDF_STUDY_POPULATION_DURATION_UNIT_DAYS = "C25301"
DDF_STUDY_POPULATION_DURATION_UNIT_WEEKS = "C29844"
DDF_STUDY_POPULATION_DURATION_UNIT_MONTHS = "C29846"
DDF_STUDY_POPULATION_DURATION_UNIT_YEARS = "C29848"
DDF_STUDY_POPULATION_ENROLLMENT_NUMBER_UNIT = "C44278"
DDF_STUDY_PROTOCOL_STATUS_DRAFT = "C85255"
DDF_STUDY_PROTOCOL_STATUS_FINAL = "C25508"
DDF_STUDY_POPULATION_SEX_BOTH = "C49636"
DDF_STUDY_POPULATION_SEX_FEMALE = "C16576"
DDF_STUDY_POPULATION_SEX_MALE = "C20197"
DDF_STUDY_OFFICIAL_TITLE = "C207616"
DDF_STUDY_ACRONYM = "C94108"
DDF_STUDY_BRIEF_TITLE = "C207615"
# DDF_STUDY_PUBLIC_TITLE ("C207617") and the USDM Scientific Title are not
# mapped: OSB's StudyDescription exposes only study_title and study_short_title,
# with no separate "public" or "scientific" title field. Add the mappings here
# when OSB source fields become available (ADO 873821).
# Eligibility-criterion category UIDs are also their CDISC NCI codes; listed
# here so the short-label map below stays readable.
DDF_ELIGIBILITY_CATEGORY_INCLUSION = "C25532"
DDF_ELIGIBILITY_CATEGORY_EXCLUSION = "C25370"
# Short labels for EligibilityCriterion.name / EligibilityCriterionItem.name
# (INC{n} / EXC{n}). Selections in unrecognised categories fall back to the
# raw OSB UID.
DDF_ELIGIBILITY_CATEGORY_SHORT_LABEL = {
    DDF_ELIGIBILITY_CATEGORY_INCLUSION: "INC",
    DDF_ELIGIBILITY_CATEGORY_EXCLUSION: "EXC",
}
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
    regex_match = re.search(r"(^C\d+)_?", term_uid)
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
    @trace_calls
    def __init__(
        self,
        get_osb_study_design_cells: Callable,
        get_osb_study_arms: Callable,
        get_osb_study_cohorts: Callable,
        get_osb_study_epochs: Callable,
        get_osb_study_elements: Callable,
        get_osb_study_endpoints: Callable,
        get_osb_study_visits: Callable,
        get_osb_study_activities: Callable,
        get_osb_activity_schedules: Callable,
        get_osb_study_criteria: Callable,
        get_osb_study_compound_dosings: Callable,
    ):
        self._get_osb_study_design_cells = get_osb_study_design_cells
        self._get_osb_study_arms = get_osb_study_arms
        self._get_osb_study_cohorts = get_osb_study_cohorts
        self._get_osb_study_epochs = get_osb_study_epochs
        self._get_osb_study_elements = get_osb_study_elements
        self._get_osb_study_endpoints = get_osb_study_endpoints
        self._get_osb_study_visits = get_osb_study_visits
        self._get_osb_study_activities = get_osb_study_activities
        self._get_osb_activity_schedules = get_osb_activity_schedules
        self._get_osb_study_criteria = get_osb_study_criteria
        self._get_osb_study_compound_dosings = get_osb_study_compound_dosings
        self._id_manager = IdManager()
        self._ct_package_effective_date: str = str(date.today())
        self._ct_terms_datetime: datetime | None = None
        self._bc_by_nci_id: dict[str, USDMBiomedicalConcept] = {}
        self._study_activity_bc_ids: dict[str, list[str]] = {}
        self._registid_labels: dict[str, str] = {}
        # Per-map() caches: dictionary term lookups repeat across indication /
        # intervention / registry paths within a single study export.
        self._dictionary_code_cache: dict[str, USDMCode] = {}
        self._dictionary_definition_cache: dict[str, str | None] = {}
        # Dose units repeat across compound dosings — cache the CTTermRoot lookup.
        self._unit_ct_term_cache: dict[str, str | None] = {}

    @staticmethod
    def _effective_date_to_str(effective_date) -> str:
        """Convert a Neo4j date value to a date-only string (YYYY-MM-DD)."""
        # Neo4j may return neo4j.time.Date or datetime — ensure date-only format
        return str(effective_date)[:10]

    @staticmethod
    def _effective_date_to_datetime(effective_date_str: str) -> datetime:
        """Convert effective date string (YYYY-MM-DD) to a timezone-aware datetime for version-aware CT term resolution."""
        d = date.fromisoformat(effective_date_str)
        return datetime(d.year, d.month, d.day, 23, 59, 59, 999999, tzinfo=timezone.utc)

    @staticmethod
    def _get_system_version() -> str | None:
        """Return the OpenStudyBuilder API version, or None if it cannot be read."""
        try:
            return get_api_version()
        except OSError:
            return None

    @staticmethod
    def _resolve_ct_package_effective_date(study_uid: str) -> str:
        """Resolve CT package effective date from study's selected CT package, falling back to latest CDISC CT package."""
        # Try study's own CT package first
        query = """
            MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)
                  -[:HAS_STUDY_STANDARD_VERSION]->(ssv:StudyStandardVersion)
                  -[:HAS_CT_PACKAGE]->(ct_pkg:CTPackage)
            RETURN ct_pkg.effective_date AS effective_date
            ORDER BY ct_pkg.effective_date DESC
            LIMIT 1
        """
        result, _ = db.cypher_query(query, {"study_uid": study_uid})
        if result and result[0][0] is not None:
            return USDMMapper._effective_date_to_str(result[0][0])

        # Fallback: latest CDISC CT package (from DDF CT or SDTM CT catalogues, excluding sponsor extensions)
        fallback_query = """
            MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]->(ct_pkg:CTPackage)
            WHERE cat.name IN ['DDF CT', 'SDTM CT'] AND NOT (ct_pkg)-[:EXTENDS_PACKAGE]->()
            RETURN ct_pkg.effective_date AS effective_date
            ORDER BY ct_pkg.effective_date DESC
            LIMIT 1
        """
        result, _ = db.cypher_query(fallback_query)
        if result and result[0][0] is not None:
            return USDMMapper._effective_date_to_str(result[0][0])

        # Ultimate fallback
        return str(date.today())

    @staticmethod
    def _load_registid_labels() -> dict[str, str]:
        """Load registry identifier term labels from the REGISTID sponsor codelist (CTCodelist_000038)."""
        query = """
            MATCH (cl:CTCodelistRoot {uid: 'CTCodelist_000038'})-[:HAS_TERM]->(clt:CTCodelistTerm)
                  -[:HAS_TERM_ROOT]->(tr:CTTermRoot)
            MATCH (tr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
            RETURN tr.uid AS term_uid, tnv.name AS term_name
        """
        result, _ = db.cypher_query(query)
        return {row[0]: row[1] for row in result}

    def get_void_usdm_code(self):
        return USDMCode(
            id=self._id_manager.get_id(USDMCode.__name__, "VOID_CODE"),
            code="",
            codeSystem="",
            codeSystemVersion="",
            decode="",
            instanceType="Code",
        )

    @trace_calls(args=[1], kwargs=["concept_id"])
    def get_ct_package_term_as_usdm_code(self, concept_id: str | None) -> USDMCode:
        if concept_id is None:
            return self.get_void_usdm_code()
        # OSB term_uids may carry a sponsor suffix ("C15228_OPENLABEL"); the
        # CTTermRoot uid is the bare C-code. Already-bare uids pass through.
        concept_id = extract_c_code_from_simple_term(concept_id) or concept_id
        # Version-aware term resolution: resolve term name at the study's CT package effective date.
        # Uses the ct_term_name_at_datetime pattern from common/queries.py — orders by dates_match DESC
        # so an exact version match is preferred, but falls back gracefully to the latest version.
        query = """
            MATCH (l:Library)-[:CONTAINS_TERM]->(cttr:CTTermRoot)
            WHERE cttr.uid = $concept_id
            MATCH (cttr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[version:HAS_VERSION]->(value:CTTermNameValue)
            WHERE version.status IN ['Final', 'Retired']
            WITH l, cttr, version, value,
                ($ct_terms_datetime IS NULL OR version.start_date <= $ct_terms_datetime
                    AND (version.end_date IS NULL OR version.end_date > $ct_terms_datetime)) AS dates_match
            ORDER BY dates_match DESC, version.start_date DESC
            LIMIT 1
            RETURN l, value
        """
        result, _ = db.cypher_query(
            query,
            {
                "concept_id": concept_id,
                "ct_terms_datetime": self._ct_terms_datetime,
            },
        )
        if len(result) == 0:
            return self.get_void_usdm_code()
        library = result[0][0]
        ct_term_name_value = result[0][1]
        code = USDMCode(
            id=self._id_manager.get_id(USDMCode.__name__, concept_id),
            code=concept_id,
            codeSystem=library["name"],
            codeSystemVersion=self._ct_package_effective_date,
            decode=ct_term_name_value["name"],
            instanceType="Code",
        )
        return code

    def _get_ct_term_uid_for_unit_definition(
        self, unit_definition_uid: str | None
    ) -> str | None:
        """Return the CTTermRoot uid (e.g. 'C28253') for a UnitDefinition uid, or None.

        OSB links UnitDefinitionValue to a CTTermContext via HAS_CT_UNIT, which in
        turn points to the CTTermRoot.  Units without CT linkage (e.g. UnitDefinition_000415)
        return None and the caller should fall back to the void code.
        """
        if unit_definition_uid is None:
            return None
        if unit_definition_uid in self._unit_ct_term_cache:
            return self._unit_ct_term_cache[unit_definition_uid]
        query = """
            MATCH (:UnitDefinitionRoot {uid: $uid})-[:LATEST]->(udv:UnitDefinitionValue)
                  -[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(ctr:CTTermRoot)
            RETURN ctr.uid AS term_uid
            LIMIT 1
        """
        result, _ = db.cypher_query(query, {"uid": unit_definition_uid})
        term_uid = result[0][0] if result and result[0][0] else None
        self._unit_ct_term_cache[unit_definition_uid] = term_uid
        return term_uid

    @trace_calls(args=[1], kwargs=["time_unit_name"])
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

    def get_ddf_study_population_enrollment_number_unit(self):
        return self.get_ct_package_term_as_usdm_code(
            DDF_STUDY_POPULATION_ENROLLMENT_NUMBER_UNIT
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

    @trace_calls
    def get_dictionary_term_as_usdm_code(self, term_uid: str) -> USDMCode:
        if term_uid is None:
            return self.get_void_usdm_code()
        if term_uid in self._dictionary_code_cache:
            return self._dictionary_code_cache[term_uid]
        query = """
            MATCH (l:Library)-[:CONTAINS_DICTIONARY_TERM]->(dtr:DictionaryTermRoot)-[:LATEST]->(dtv)
            WHERE dtr.uid = $term_uid
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
        # Prefer the dictionary's own concept identifier (e.g. SNOMED concept ID
        # like "44054006") over the OSB internal UID, so consumers of the USDM
        # export can resolve the code in the source dictionary. Fall back to
        # term_uid when the dictionary_id is missing.
        dictionary_id = ct_term_attributes_value.get("dictionary_id") or term_uid
        code = USDMCode(
            id=self._id_manager.get_id(USDMCode.__name__, term_uid),
            code=dictionary_id,
            codeSystem=library["name"],
            codeSystemVersion=self._ct_package_effective_date,
            decode=ct_term_attributes_value["name"],
            instanceType="Code",
        )
        self._dictionary_code_cache[term_uid] = code
        return code

    @trace_calls
    def get_dictionary_term_definition(self, term_uid: str) -> str | None:
        """Return the definition text for a DictionaryTerm, or None if absent."""
        if term_uid is None:
            return None
        if term_uid in self._dictionary_definition_cache:
            return self._dictionary_definition_cache[term_uid]
        query = """
            MATCH (dtr:DictionaryTermRoot)-[:LATEST]->(dtv)
            WHERE dtr.uid = $term_uid
            RETURN dtv.definition AS definition
        """
        result, _ = db.cypher_query(query, {"term_uid": term_uid})
        definition = result[0][0] if result else None
        self._dictionary_definition_cache[term_uid] = definition
        return definition

    @staticmethod
    def _get_study_rationale(study: OSBStudy) -> str:
        """StudyVersion.rationale — required str; OSB source is version_description
        (set on locked versions, None on drafts). Defaults to ""."""
        return (
            getattr(
                getattr(
                    getattr(study, "current_metadata", None), "version_metadata", None
                ),
                "version_description",
                None,
            )
            or ""
        )

    @trace_calls
    def map(self, study: OSBStudy) -> dict[str, Any]:
        self._ct_package_effective_date = self._resolve_ct_package_effective_date(
            study.uid
        )
        self._ct_terms_datetime = self._effective_date_to_datetime(
            self._ct_package_effective_date
        )
        self._registid_labels = self._load_registid_labels()
        # Reset per-study caches — codeSystemVersion is study-specific.
        self._dictionary_code_cache = {}
        self._dictionary_definition_cache = {}
        self._unit_ct_term_cache = {}

        usdm_study = USDMStudy(name=self._get_study_name(study), instanceType="Study")
        usdm_study.id = uuid.uuid4()
        usdm_study.label = self._get_study_label(study)

        # Set DDF study description
        usdm_study.description = self._get_study_description(study)

        # Set DDF study protocol document
        ddf_study_protocol_document = self._get_study_definition_document(study)
        usdm_study.documentedBy = [ddf_study_protocol_document]

        # Set DDF study titles in version
        ddf_study_titles = [
            USDMStudyTitle(
                id=self._id_manager.get_id(USDMStudyTitle.__name__),
                text=self._get_study_title(study),
                type=self.get_ct_package_term_as_usdm_code(DDF_STUDY_OFFICIAL_TITLE),
                instanceType="StudyTitle",
            )
        ]
        acronym_text = self._get_study_acronym(study)
        if acronym_text:
            ddf_study_titles.append(
                USDMStudyTitle(
                    id=self._id_manager.get_id(USDMStudyTitle.__name__),
                    text=acronym_text,
                    type=self.get_ct_package_term_as_usdm_code(DDF_STUDY_ACRONYM),
                    instanceType="StudyTitle",
                )
            )
        brief_title_text = self._get_study_brief_title(study)
        if brief_title_text:
            ddf_study_titles.append(
                USDMStudyTitle(
                    id=self._id_manager.get_id(USDMStudyTitle.__name__),
                    text=brief_title_text,
                    type=self.get_ct_package_term_as_usdm_code(DDF_STUDY_BRIEF_TITLE),
                    instanceType="StudyTitle",
                )
            )
        # Public Study Title (C207617) intentionally not emitted: OSB has no
        # source field for it yet (StudyDescription only carries study_title and
        # study_short_title).

        study_identifiers, organizations = (
            self._get_study_identifiers_and_organizations(study)
        )

        usdm_version = USDMStudyVersion(
            id=self._id_manager.get_id(USDMStudyVersion.__name__),
            titles=ddf_study_titles,
            studyIdentifiers=study_identifiers,
            organizations=organizations,
            versionIdentifier=self._get_study_version(study),
            rationale=self._get_study_rationale(study),
            # amendments: left empty — OSB does not model study amendments.
            # Not a mapper gap; populate once an OSB amendment domain exists.
            instanceType="StudyVersion",
            documentVersionIds=[s.id for s in usdm_study.documentedBy],
        )

        # Set study interventions
        usdm_version.studyInterventions = self._get_study_interventions(study)
        # Reset biomedical concept data (populated during _get_study_activities)
        self._bc_by_nci_id.clear()
        self._study_activity_bc_ids.clear()

        # Set DDF study design
        usdm_version.studyDesigns = self._get_study_designs(study)

        # Set eligibility criteria (lives on design + on version-level items)
        criteria, criterion_items = self._get_eligibility_criteria(study)
        if criteria:
            usdm_version.studyDesigns[0].eligibilityCriteria = criteria
            usdm_version.studyDesigns[0].population.criterionIds = [
                c.id for c in criteria
            ]
            usdm_version.eligibilityCriterionItems = criterion_items

        # Set biomedical concepts on study version
        usdm_version.biomedicalConcepts = list(self._bc_by_nci_id.values())

        # Inject interventions IDs into study design
        usdm_version.studyDesigns[0].studyInterventionIds = [
            intervention.id for intervention in usdm_version.studyInterventions
        ]

        # Set DDF study versions
        usdm_study.versions = [usdm_version]

        wrapped_study = {
            "study": usdm_study,
            "usdmVersion": usdm_package_version,
            "systemName": "OpenStudyBuilder",
            "systemVersion": self._get_system_version(),
        }

        return wrapped_study

    @trace_calls
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

    @trace_calls
    def _get_blinding_schema(self, study: OSBStudy):
        """Return the blinding schema as an AliasCode, or None when unset.

        OSB source: study.current_metadata.study_intervention.trial_blinding_schema_code
        USDM type: AliasCode (same pattern as studyPhase / _get_study_phase).
        blindingSchema is optional on InterventionalStudyDesign; None is returned
        when the OSB field is absent so the key is omitted from the output.
        """
        osb_current_metadata = getattr(study, "current_metadata", None)
        osb_study_intervention = getattr(
            osb_current_metadata, "study_intervention", None
        )
        osb_trial_blinding_schema_code = getattr(
            osb_study_intervention, "trial_blinding_schema_code", None
        )
        if osb_trial_blinding_schema_code is None:
            return None
        blinding_code = self.get_ct_package_term_as_usdm_code(
            osb_trial_blinding_schema_code.term_uid
        )
        return USDMAliasCode(
            id=self._id_manager.get_id(USDMAliasCode.__name__),
            standardCode=blinding_code,
            instanceType="AliasCode",
        )

    @trace_calls
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
                dataOriginType=self.get_ct_package_term_as_usdm_code(
                    DDF_STUDY_ARM_DATA_ORIGIN_TYPE_GENERATED_WITHIN_STUDY
                ),
            )
            for sa in osb_study_arms
        ]

    @trace_calls
    def _get_study_cohorts(self, study: OSBStudy):
        # Note: StudyCohort.code does not exist in usdm_model 0.67.0 — the field
        # is absent from StudyCohort.model_fields and is not emitted by any
        # DDF-RA corpus file. OSB's StudySelectionCohort.code (free text, e.g.
        # "HIC01") therefore has no USDM target and is intentionally unmapped.
        osb_study_cohorts = self._get_osb_study_cohorts(study_uid=study.uid).items
        return [
            StudyCohort(
                id=self._id_manager.get_id(StudyCohort.__name__, sc.cohort_uid),
                name=sc.name,
                label=sc.short_name,
                description=sc.description,
                # includesHealthySubjects: required bool on StudyCohort with no
                # per-cohort OSB source — StudySelectionCohort has no healthy-
                # subject attribute (only the study-level
                # study_population.healthy_subject_indicator, which is not
                # cohort-specific). Ships False as a structural default; source
                # it here when OSB adds a per-cohort attribute (ADO 873821).
                includesHealthySubjects=False,
                instanceType="StudyCohort",
            )
            for sc in osb_study_cohorts
        ]

    @trace_calls
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

    @trace_calls
    def _get_study_description(self, study: OSBStudy):
        study_description = getattr(
            getattr(study, "current_metadata", None), "study_description", None
        )
        return getattr(study_description, "study_title", None)

    @trace_calls
    def _get_study_designs(self, study: OSBStudy):
        # Create DDF study design using InterventionalStudyDesign subclass so that
        # model, subTypes, intentTypes, and blindingSchema — which only exist on
        # the subclass — can be populated.
        ddf_study_design = USDMInterventionalStudyDesign(
            id=self._id_manager.get_id(USDMInterventionalStudyDesign.__name__),
            name="Study Design  1",
            description="The main design for the study",
            arms=[],
            studyCells=[],
            rationale="",
            epochs=[],
            model=self._get_intervention_model(study),
            population=self._get_study_population(study),
            instanceType="InterventionalStudyDesign",
        )

        # Set DDF study type in version
        ddf_study_design.studyType = self._get_study_type(study)
        # Set study phase
        ddf_study_design.studyPhase = self._get_study_phase(study)

        # Set therapeutic areas
        ddf_study_design.therapeuticAreas = self._get_therapeutic_areas(study)

        # Set trial type codes (subTypes on InterventionalStudyDesign)
        ddf_study_design.subTypes = self._get_trial_type_codes(study)

        # Set trial intent type codes (intentTypes on InterventionalStudyDesign)
        ddf_study_design.intentTypes = self._get_trial_intent_types_codes(study)

        # Set blinding schema (blindingSchema on InterventionalStudyDesign)
        ddf_study_design.blindingSchema = self._get_blinding_schema(study)

        # estimands / analysisPopulations: left empty. Both need OSB domain
        # entities that do not exist yet (estimand selection, intercurrent-event
        # strategy per ICH E9(R1), analysis population). Not a mapper gap —
        # populate once OSB models them.

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

    @trace_calls
    def _load_biomedical_concept_data(self, study_uid: str):
        """Query activity instance NCI concept IDs with their properties and build BiomedicalConcept objects."""
        query = """
            MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)
                  -[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
            WHERE NOT (study_activity)-[:BEFORE]-()
            MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(sai:StudyActivityInstance)
                  <-[:HAS_STUDY_ACTIVITY_INSTANCE]-(sv)
            WHERE NOT (sai)-[:BEFORE]-() AND NOT (sai)-[:AFTER]->(:Delete:StudyAction)
            MATCH (sai)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(aiv:ActivityInstanceValue)
            WHERE aiv.nci_concept_id IS NOT NULL AND aiv.nci_concept_id <> ''
            OPTIONAL MATCH (aiv)-[:ACTIVITY_INSTANCE_CLASS]->(aic_root:ActivityInstanceClassRoot)
            OPTIONAL MATCH (aiv)-[:CONTAINS_ACTIVITY_ITEM]->(activity_item)
                <-[:HAS_ACTIVITY_ITEM]-(item_class_root:ActivityItemClassRoot)-[:LATEST]->(item_class_value:ActivityItemClassValue)
            OPTIONAL MATCH (aic_root)-[item_class_rel:HAS_ITEM_CLASS]->(item_class_root)
            WITH study_activity.uid AS study_activity_uid,
                 aiv.nci_concept_id AS nci_concept_id,
                 aiv.name AS name,
                 aiv.topic_code AS topic_code,
                 aiv.adam_param_code AS adam_param_code,
                 collect(DISTINCT CASE WHEN item_class_value IS NOT NULL THEN {
                     nci_concept_id: item_class_value.nci_concept_id,
                     name: coalesce(head([(item_class_root)-[:MAPS_VARIABLE_CLASS]->(vc:VariableClass) | vc.uid]), item_class_value.name),
                     data_type: head([(item_class_value)-[:HAS_DATA_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(dtv:CTTermNameValue) | dtv.name]),
                     mandatory: item_class_rel.mandatory,
                     response_codes: [(activity_item)-[:HAS_CT_TERM]->(tr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[ver:HAS_VERSION]->(tnv:CTTermNameValue) WHERE ver.status IN ['Final', 'Retired'] AND ($ct_terms_datetime IS NULL OR (ver.start_date <= $ct_terms_datetime AND (ver.end_date IS NULL OR ver.end_date > $ct_terms_datetime))) | {code: tr.uid, decode: tnv.name}]
                         + [(activity_item)-[:HAS_UNIT_DEFINITION]->(:UnitDefinitionRoot)-[:LATEST]->(udv:UnitDefinitionValue)-[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(utr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(uav:CTTermAttributesValue) | {code: uav.concept_id, decode: udv.name}]
                 } END) AS properties
            RETURN study_activity_uid, nci_concept_id, name, topic_code, adam_param_code, properties
        """
        result, _ = db.cypher_query(
            query,
            {"study_uid": study_uid, "ct_terms_datetime": self._ct_terms_datetime},
        )

        for (
            study_activity_uid,
            nci_concept_id,
            name,
            topic_code,
            adam_param_code,
            properties,
        ) in result:
            if nci_concept_id not in self._bc_by_nci_id:
                bc_properties = self._build_bc_properties(nci_concept_id, properties)
                reference = (
                    f"/mdr/specializations/sdtm/packages/{self._ct_package_effective_date}/datasetspecializations/{topic_code}"
                    if topic_code
                    else ""
                )
                bc_decode = adam_param_code or name or nci_concept_id
                bc_synonyms = (
                    [s for s in [adam_param_code, name] if s]
                    if adam_param_code and adam_param_code != name
                    else []
                )
                self._bc_by_nci_id[nci_concept_id] = USDMBiomedicalConcept(
                    id=self._id_manager.get_id(
                        USDMBiomedicalConcept.__name__, nci_concept_id
                    ),
                    name=name or nci_concept_id,
                    label=name or nci_concept_id,
                    synonyms=bc_synonyms,
                    reference=reference,
                    properties=bc_properties,
                    code=USDMAliasCode(
                        id=self._id_manager.get_id(
                            USDMAliasCode.__name__, f"BC_{nci_concept_id}"
                        ),
                        standardCode=USDMCode(
                            id=self._id_manager.get_id(
                                USDMCode.__name__, f"BC_{nci_concept_id}"
                            ),
                            code=nci_concept_id,
                            codeSystem="http://www.cdisc.org",
                            codeSystemVersion=self._ct_package_effective_date,
                            decode=bc_decode,
                            instanceType="Code",
                        ),
                        instanceType="AliasCode",
                    ),
                    instanceType="BiomedicalConcept",
                )

            bc_id = self._bc_by_nci_id[nci_concept_id].id
            if study_activity_uid not in self._study_activity_bc_ids:
                self._study_activity_bc_ids[study_activity_uid] = []
            if bc_id not in self._study_activity_bc_ids[study_activity_uid]:
                self._study_activity_bc_ids[study_activity_uid].append(bc_id)

    def _build_bc_properties(
        self, bc_nci_id: str, properties: list[dict[str, Any]]
    ) -> list[USDMBiomedicalConceptProperty]:
        """Build USDM BiomedicalConceptProperty objects from Cypher query results."""
        bc_properties = []
        for prop in properties:
            if prop is None:
                continue
            prop_nci_id = prop.get("nci_concept_id") or ""
            prop_name = prop.get("name") or prop_nci_id
            prop_key = f"{bc_nci_id}_{prop_nci_id}"

            response_codes = []
            for rc in prop.get("response_codes") or []:
                rc_code = rc.get("code", "")
                response_codes.append(
                    USDMResponseCode(
                        id=self._id_manager.get_id(
                            USDMResponseCode.__name__, f"RC_{prop_key}_{rc_code}"
                        ),
                        name=f"RC_{rc_code}",
                        label="",
                        isEnabled=True,
                        code=USDMCode(
                            id=self._id_manager.get_id(
                                USDMCode.__name__, f"RC_{prop_key}_{rc_code}"
                            ),
                            code=rc_code,
                            codeSystem="http://www.cdisc.org",
                            codeSystemVersion=self._ct_package_effective_date,
                            decode=rc.get("decode", ""),
                            instanceType="Code",
                        ),
                        instanceType="ResponseCode",
                    )
                )

            bc_properties.append(
                USDMBiomedicalConceptProperty(
                    id=self._id_manager.get_id(
                        USDMBiomedicalConceptProperty.__name__, prop_key
                    ),
                    name=prop_name,
                    label=prop_name,
                    isRequired=bool(prop.get("mandatory")),
                    isEnabled=True,
                    datatype=prop.get("data_type") or "",
                    responseCodes=response_codes,
                    code=USDMAliasCode(
                        id=self._id_manager.get_id(
                            USDMAliasCode.__name__, f"BCP_{prop_key}"
                        ),
                        standardCode=USDMCode(
                            id=self._id_manager.get_id(
                                USDMCode.__name__, f"BCP_{prop_key}"
                            ),
                            code=prop_nci_id,
                            codeSystem="http://www.cdisc.org",
                            codeSystemVersion=self._ct_package_effective_date,
                            decode=prop_name,
                            instanceType="Code",
                        ),
                        instanceType="AliasCode",
                    ),
                    instanceType="BiomedicalConceptProperty",
                )
            )
        return bc_properties

    @trace_calls
    def _get_study_activities(self, study: OSBStudy):
        self._load_biomedical_concept_data(study.uid)
        osb_study_activities = self._get_osb_study_activities(study.uid).items

        # Sort by composite SoA key so that nextId/previousId form a correct
        # linked list. The flat `order` field is NOT unique across the study —
        # activities in different SoA groups can share the same value. Guard
        # against None in any component (mirrors _get_study_epochs discipline:
        # only wire the chain when every activity has a full, sortable key).
        def _soa_sort_key(a):
            soa_order = (
                getattr(a.study_soa_group, "order", None) if a.study_soa_group else None
            )
            grp_order = (
                getattr(a.study_activity_group, "order", None)
                if a.study_activity_group
                else None
            )
            sub_order = (
                getattr(a.study_activity_subgroup, "order", None)
                if a.study_activity_subgroup
                else None
            )
            return (soa_order, grp_order, sub_order, a.order)

        all_orders_present = all(
            None not in _soa_sort_key(a) for a in osb_study_activities
        )
        if all_orders_present:
            osb_study_activities = sorted(osb_study_activities, key=_soa_sort_key)

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
                definedProcedures=(
                    [
                        USDMProcedure(
                            id=self._id_manager.get_id(
                                USDMProcedure.__name__, a.activity.uid
                            ),
                            name=a.activity.name,
                            # procedureType: no OSB source — no procedure-type
                            # attribute exists on Activity, ActivityForStudyActivity
                            # or ActivityInstance (ADO 254079)
                            procedureType="",
                            # studyInterventionId: left unset — OSB models no link
                            # between a study activity and a study intervention
                            # (ADO 254079)
                            # description: source activity.definition when present
                            description=(
                                a.activity.definition
                                if getattr(a.activity, "definition", None)
                                else None
                            ),
                            # code: resolve nci_concept_id via CT package when present;
                            # otherwise keep void code (required field)
                            code=(
                                self.get_ct_package_term_as_usdm_code(
                                    a.activity.nci_concept_id
                                )
                                if getattr(a.activity, "nci_concept_id", None)
                                else self.get_void_usdm_code()
                            ),
                        )
                    ]
                    if a.activity is not None and a.activity.name is not None
                    else []
                ),
                biomedicalConceptIds=self._study_activity_bc_ids.get(
                    a.study_activity_uid, []
                ),
                nextId=(
                    self._id_manager.get_id(
                        USDMActivity.__name__,
                        osb_study_activities[i + 1].study_activity_uid,
                    )
                    if all_orders_present and i + 1 < len(osb_study_activities)
                    else None
                ),
                previousId=(
                    self._id_manager.get_id(
                        USDMActivity.__name__,
                        osb_study_activities[i - 1].study_activity_uid,
                    )
                    if all_orders_present and i - 1 >= 0
                    else None
                ),
            )
            for i, a in enumerate(osb_study_activities)
        ]

    @trace_calls
    def _get_study_elements(self, study: OSBStudy):
        osb_study_elements = self._get_osb_study_elements(study.uid).items
        ddf_study_elements = []
        for osb_se in osb_study_elements:
            ddf_se_id = self._id_manager.get_id(
                USDMStudyElement.__name__, osb_se.element_uid
            )
            # Skip-rather-than-blank for optional transition rules
            transition_start_rule = (
                USDMTransitionRule(
                    id=self._id_manager.get_id(USDMTransitionRule.__name__),
                    name="Transition Start Rule",
                    text=osb_se.start_rule,
                )
                if osb_se.start_rule
                else None
            )
            transition_end_rule = (
                USDMTransitionRule(
                    id=self._id_manager.get_id(USDMTransitionRule.__name__),
                    name="Transition End Rule",
                    text=osb_se.end_rule,
                )
                if osb_se.end_rule
                else None
            )
            ddf_se = USDMStudyElement(
                id=ddf_se_id,
                name=osb_se.name if osb_se.name else " ",
                description=osb_se.description,
                label=osb_se.name,
                transitionStartRule=transition_start_rule,
                transitionEndRule=transition_end_rule,
                instanceType="StudyElement",
            )
            ddf_study_elements.append(ddf_se)
        return ddf_study_elements

    @trace_calls
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
                label=se.short_name,
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

    @trace_calls
    def _get_study_name(self, study: OSBStudy):
        osb_identification_metadata = getattr(
            getattr(study, "current_metadata", None), "identification_metadata", None
        )
        osb_study_id = getattr(osb_identification_metadata, "study_id", "")
        return osb_study_id

    # Registry identifier field names mapped to organization metadata.
    # Organization type codes (from DDF CT codelist C188724): C93453 = Study Registry, C188863 = Regulatory Agency
    # Labels are resolved at runtime from the REGISTID sponsor codelist (CTCodelist_000038) in the database.
    # org_name and id_scheme have no DB source and remain as configuration.
    REGISTRY_ORGANIZATIONS: dict[str, tuple[str, str | None, str, str, str]] = {
        # field_name: (org_name, registid_term_uid, id_scheme, org_type_code, fallback_label)
        "ct_gov_id": (
            "CT-GOV",
            "CTTerm_000212",
            "USGOV",
            DDF_ORGANIZATION_TYPE_STUDY_REGISTRY,
            "ClinicalTrials.gov ID",
        ),
        "eudract_id": (
            "EUDRACT",
            "CTTerm_000215",
            "EU",
            DDF_ORGANIZATION_TYPE_STUDY_REGISTRY,
            "EUDRACT ID",
        ),
        "eu_trial_number": (
            "EU-CT",
            "CTTerm_000218",
            "EU",
            DDF_ORGANIZATION_TYPE_STUDY_REGISTRY,
            "EU Trial Number",
        ),
        "universal_trial_number_utn": (
            "WHO-UTN",
            "CTTerm_000214",
            "UTN",
            DDF_ORGANIZATION_TYPE_STUDY_REGISTRY,
            "Universal Trial Number (UTN)",
        ),
        "japanese_trial_registry_id_japic": (
            "JAPIC",
            "CTTerm_000213",
            "JAPIC",
            DDF_ORGANIZATION_TYPE_STUDY_REGISTRY,
            "Japanese Trial Registry ID (JAPIC)",
        ),
        "japanese_trial_registry_number_jrct": (
            "JRCT",
            "CTTerm_000221",
            "JRCT",
            DDF_ORGANIZATION_TYPE_STUDY_REGISTRY,
            "Japanese Trial Registry Number (jRCT)",
        ),
        "investigational_new_drug_application_number_ind": (
            "FDA-IND",
            "CTTerm_000217",
            "USGOV",
            DDF_ORGANIZATION_TYPE_REGULATORY_AGENCY,
            "Investigational New Drug Application (IND) Number",
        ),
        "investigational_device_exemption_ide_number": (
            "FDA-IDE",
            "CTTerm_000224",
            "USGOV",
            DDF_ORGANIZATION_TYPE_REGULATORY_AGENCY,
            "Investigational Device Exemption (IDE) Number",
        ),
        "civ_id_sin_number": (
            "CIV-SIN",
            "CTTerm_000216",
            "EU",
            DDF_ORGANIZATION_TYPE_STUDY_REGISTRY,
            "CIV-ID/SIN Number",
        ),
        "national_clinical_trial_number": (
            "NCT-REG",
            "CTTerm_000220",
            "NATIONAL",
            DDF_ORGANIZATION_TYPE_STUDY_REGISTRY,
            "National Clinical Trial Number",
        ),
        "national_medical_products_administration_nmpa_number": (
            "NMPA",
            "CTTerm_000222",
            "NMPA",
            DDF_ORGANIZATION_TYPE_REGULATORY_AGENCY,
            "National Medical Products Administration (NMPA) Number",
        ),
        "eudamed_srn_number": (
            "EUDAMED",
            "CTTerm_000223",
            "EU",
            DDF_ORGANIZATION_TYPE_REGULATORY_AGENCY,
            "EUDAMED SRN Number",
        ),
        "eu_pas_number": (
            "EU-PAS",
            None,
            "EU",
            DDF_ORGANIZATION_TYPE_STUDY_REGISTRY,
            "EU PAS Register",
        ),
    }

    @trace_calls
    def _get_study_identifiers_and_organizations(self, study: OSBStudy):
        osb_identification_metadata = getattr(
            getattr(study, "current_metadata", None), "identification_metadata", None
        )
        osb_registry_identifiers = getattr(
            osb_identification_metadata, "registry_identifiers", []
        )

        study_identifiers = []
        organizations = []

        for field_name, (
            org_name,
            registid_term_uid,
            id_scheme,
            org_type_concept_id,
            fallback_label,
        ) in self.REGISTRY_ORGANIZATIONS.items():
            value = getattr(osb_registry_identifiers, field_name, None)
            if not value:
                continue

            # Resolve label from REGISTID codelist in DB, falling back to static label
            org_label = (
                self._registid_labels.get(registid_term_uid, fallback_label)
                if registid_term_uid
                else fallback_label
            )

            org_id = self._id_manager.get_id(USDMOrganization.__name__)
            organizations.append(
                USDMOrganization(
                    id=org_id,
                    name=org_name,
                    label=org_label,
                    type=self.get_ct_package_term_as_usdm_code(org_type_concept_id),
                    identifierScheme=id_scheme,
                    identifier=org_name,
                    instanceType="Organization",
                )
            )
            study_identifiers.append(
                USDMStudyIdentifier(
                    id=self._id_manager.get_id(USDMStudyIdentifier.__name__),
                    text=value,
                    scopeId=org_id,
                    instanceType="StudyIdentifier",
                )
            )

        return study_identifiers, organizations

    @trace_calls
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
            osb_disease_or_indication_term_uid = getattr(
                osb_disease_or_indication, "term_uid", None
            )
            if osb_disease_or_indication_name is not None:
                ddf_indication_codes = []
                ddf_indication_description = None
                if osb_disease_or_indication_term_uid is not None:
                    ddf_indication_codes.append(
                        self.get_dictionary_term_as_usdm_code(
                            osb_disease_or_indication_term_uid
                        )
                    )
                    ddf_indication_description = self.get_dictionary_term_definition(
                        osb_disease_or_indication_term_uid
                    )
                ddf_study_indication = USDMIndication(
                    id=self._id_manager.get_id(USDMIndication.__name__),
                    name=osb_disease_or_indication_name,
                    label=osb_disease_or_indication_name,
                    description=ddf_indication_description,
                    codes=ddf_indication_codes,
                    # isRareDisease is a required bool on usdm_model.Indication.
                    # OSB rare_disease_indicator may be None (unknown); "not rare"
                    # is the safe clinical default when the flag is unset.
                    isRareDisease=bool(osb_study_population_rare_disease_indicator),
                )
                ddf_study_indications.append(ddf_study_indication)
        return ddf_study_indications

    @trace_calls
    def _get_study_interventions(self, study: OSBStudy):
        osb_study_intervention = getattr(
            study.current_metadata, "study_intervention", None
        )
        usdm_study_intervention_codes = []

        if osb_study_intervention is not None:
            if osb_study_intervention.intervention_model_code is not None:
                intervention_model_code = self.get_ct_package_term_as_usdm_code(
                    osb_study_intervention.intervention_model_code.term_uid
                )
                usdm_study_intervention_codes.append(intervention_model_code)

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

        # Build one Administration per compound dosing.
        # Route, administrableProductId, and medicalDeviceId have no OSB source —
        # see §5 of ADO 254079 brief; left unset.
        osb_dosings = self._get_osb_study_compound_dosings(study_uid=study.uid).items
        usdm_administrations = []
        for dosing in osb_dosings:
            # duration — required on Administration.
            # Source: dosing.study_element.planned_duration (DurationJsonModel).
            planned_duration = getattr(dosing.study_element, "planned_duration", None)
            dur_value = getattr(planned_duration, "duration_value", None)
            dur_unit = getattr(
                getattr(planned_duration, "duration_unit_code", None), "name", None
            )
            if dur_value is not None and dur_unit is not None:
                try:
                    iso_text = get_ddf_timing_iso_duration_value(dur_value, dur_unit)
                    usdm_duration = USDMDuration(
                        id=self._id_manager.get_id(USDMDuration.__name__),
                        text=iso_text,
                        durationWillVary=False,
                        instanceType="Duration",
                    )
                except ValueError:
                    # Unsupported unit — emit Duration with no quantity
                    # (missing OSB source: planned_duration.duration_unit_code.name)
                    usdm_duration = USDMDuration(
                        id=self._id_manager.get_id(USDMDuration.__name__),
                        durationWillVary=False,
                        instanceType="Duration",
                    )
            else:
                # planned_duration absent — emit structural Duration with no quantity
                # (missing OSB source: study_element.planned_duration)
                usdm_duration = USDMDuration(
                    id=self._id_manager.get_id(USDMDuration.__name__),
                    durationWillVary=False,
                    instanceType="Duration",
                )

            # dose — source: dosing.dose_value (SimpleNumericValueWithUnit)
            usdm_dose = None
            if dosing.dose_value is not None:
                # Resolve unit via unit_definition_uid -> HAS_CT_UNIT -> CTTermRoot.
                # unit_label is a human label ("mg"), not a CTTermRoot uid, so it
                # cannot be passed directly to get_ct_package_term_as_usdm_code.
                dose_ct_term_uid = self._get_ct_term_uid_for_unit_definition(
                    dosing.dose_value.unit_definition_uid
                )
                dose_unit_code = self.get_ct_package_term_as_usdm_code(dose_ct_term_uid)
                usdm_dose = USDMQuantity(
                    id=self._id_manager.get_id(USDMQuantity.__name__),
                    value=dosing.dose_value.value,
                    unit=USDMAliasCode(
                        id=self._id_manager.get_id(USDMAliasCode.__name__),
                        standardCode=dose_unit_code,
                        instanceType="AliasCode",
                    ),
                    instanceType="Quantity",
                )

            # frequency — source: dosing.dose_frequency.term_uid
            usdm_frequency = None
            dose_frequency = dosing.dose_frequency
            if dose_frequency is not None:
                freq_code = self.get_ct_package_term_as_usdm_code(
                    dose_frequency.term_uid
                )
                usdm_frequency = USDMAliasCode(
                    id=self._id_manager.get_id(USDMAliasCode.__name__),
                    standardCode=freq_code,
                    instanceType="AliasCode",
                )

            admin_name = (
                getattr(getattr(dosing, "study_compound", None), "compound_uid", None)
                or getattr(dosing, "study_compound_dosing_uid", None)
                or "Administration"
            )
            usdm_administrations.append(
                USDMAdministration(
                    id=self._id_manager.get_id(
                        USDMAdministration.__name__,
                        dosing.study_compound_dosing_uid,
                    ),
                    name=admin_name,
                    duration=usdm_duration,
                    dose=usdm_dose,
                    frequency=usdm_frequency,
                    # route: no OSB source (ADO 254079 §5)
                    instanceType="Administration",
                )
            )

        return [
            USDMStudyIntervention(
                id=self._id_manager.get_id(USDMStudyIntervention.__name__),
                name="Study Intervention",
                description=(
                    osb_study_intervention.intervention_model_code.sponsor_preferred_name
                    if osb_study_intervention is not None
                    and osb_study_intervention.intervention_model_code is not None
                    else None
                ),
                codes=usdm_study_intervention_codes,
                role=self.get_void_usdm_code(),
                type=(
                    self.get_ct_package_term_as_usdm_code(
                        osb_study_intervention.intervention_type_code.term_uid
                    )
                    if osb_study_intervention is not None
                    and osb_study_intervention.intervention_type_code is not None
                    else self.get_void_usdm_code()
                ),
                administrations=usdm_administrations,
                instanceType="StudyIntervention",
            )
        ]

    @trace_calls
    def _get_study_label(self, study: OSBStudy):
        if study.current_metadata is not None:
            if study.current_metadata.study_description is not None:
                return study.current_metadata.study_description.study_short_title
        return None

    @trace_calls
    def _get_study_acronym(self, study: OSBStudy):
        """Return the study acronym from identification metadata, or None if unset."""
        if study.current_metadata is not None:
            if study.current_metadata.identification_metadata is not None:
                return study.current_metadata.identification_metadata.study_acronym
        return None

    @trace_calls
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

    @trace_calls
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

    @trace_calls
    def _get_eligibility_criteria(
        self, study: OSBStudy
    ) -> tuple[list[USDMEligibilityCriterion], list[USDMEligibilityCriterionItem]]:
        """Map OSB study selection criteria to USDM EligibilityCriterion +
        EligibilityCriterionItem.

        OSB criterion text comes from the linked Criteria instance after
        bracket resolution (criteria.name_plain), or — when only a template
        has been selected without an instance — from template.name_plain.
        This mirrors the criteria/template fallback used by
        ``study_flowchart`` for SoA footnotes. The OSB criteria_type term UID
        matches the CDISC NCI category code (Inclusion=C25532,
        Exclusion=C25370), so it feeds the existing CT-package-term helper
        directly. Selections with neither criterion nor template text and
        selections without a category are skipped rather than emitted blank.

        ``name`` follows the per-category INC{n} / EXC{n} short-label
        convention, with the sequence number being the per-category running
        count of emitted selections. ``identifier`` is the running global
        index across all emitted selections (1-based). Categories outside
        the known Inclusion/Exclusion pair fall back to the raw OSB
        study_criteria_uid for ``name`` so a misconfigured codelist doesn't
        silently mint ambiguous labels.
        """
        osb_criteria = self._get_osb_study_criteria(
            study_uid=study.uid, no_brackets=True
        ).items

        criteria: list[USDMEligibilityCriterion] = []
        criterion_items: list[USDMEligibilityCriterionItem] = []
        per_category_count: dict[str, int] = {}
        global_index = 0
        for selection in osb_criteria:
            criterion_text = (
                selection.criteria.name_plain
                if selection.criteria is not None
                else (
                    selection.template.name_plain
                    if selection.template is not None
                    else None
                )
            )
            if (
                not criterion_text
                or selection.criteria_type is None
                or not selection.criteria_type.term_uid
            ):
                continue

            global_index += 1
            category_uid = selection.criteria_type.term_uid
            short_label = DDF_ELIGIBILITY_CATEGORY_SHORT_LABEL.get(category_uid)
            if short_label is None:
                name = selection.study_criteria_uid
            else:
                per_category_count[category_uid] = (
                    per_category_count.get(category_uid, 0) + 1
                )
                name = f"{short_label}{per_category_count[category_uid]}"

            criterion_item = USDMEligibilityCriterionItem(
                id=self._id_manager.get_id(
                    USDMEligibilityCriterionItem.__name__,
                    selection.study_criteria_uid,
                ),
                name=name,
                text=criterion_text,
                instanceType="EligibilityCriterionItem",
            )
            criterion_items.append(criterion_item)

            criteria.append(
                USDMEligibilityCriterion(
                    id=self._id_manager.get_id(
                        USDMEligibilityCriterion.__name__,
                        selection.study_criteria_uid,
                    ),
                    name=name,
                    identifier=str(global_index),
                    category=self.get_ct_package_term_as_usdm_code(category_uid),
                    criterionItemId=criterion_item.id,
                    instanceType="EligibilityCriterion",
                )
            )
        return criteria, criterion_items

    @trace_calls
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
            planned_enrollment_number = USDMQuantity(
                id=self._id_manager.get_id(USDMQuantity.__name__),
                value=osb_study_population.number_of_expected_subjects,
                unit=USDMAliasCode(
                    id=self._id_manager.get_id(USDMAliasCode.__name__),
                    standardCode=(
                        self.get_ddf_study_population_enrollment_number_unit()
                        or self.get_void_usdm_code()
                    ),
                    instanceType="AliasCode",
                ),
                instanceType="Quantity",
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

        # Attach study cohorts on the population
        # (in this usdm_model version, `cohorts` lives on
        # StudyDesignPopulation rather than on StudyDesign)
        population.cohorts = self._get_study_cohorts(study)

        return population

    @trace_calls
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

    @trace_calls
    def _get_study_schedule_timelines(self, study):
        osb_study_activity_schedules = self._get_osb_activity_schedules(study.uid)
        osb_study_visits = self._get_osb_study_visits(study.uid).items

        # Build plannedDuration from study_intervention.planned_study_length when set.
        # OSB source: study.current_metadata.study_intervention.planned_study_length
        # (DurationJsonModel with duration_value / duration_unit_code.name).
        osb_planned_study_length = getattr(
            getattr(
                getattr(study, "current_metadata", None), "study_intervention", None
            ),
            "planned_study_length",
            None,
        )
        usdm_planned_duration = None
        if osb_planned_study_length is not None:
            psl_value = getattr(osb_planned_study_length, "duration_value", None)
            psl_unit = getattr(
                getattr(osb_planned_study_length, "duration_unit_code", None),
                "name",
                None,
            )
            if psl_value is not None and psl_unit is not None:
                try:
                    iso_text = get_ddf_timing_iso_duration_value(psl_value, psl_unit)
                    usdm_planned_duration = USDMDuration(
                        id=self._id_manager.get_id(USDMDuration.__name__),
                        text=iso_text,
                        durationWillVary=False,
                        instanceType="Duration",
                    )
                except ValueError:
                    # Unsupported unit — do not crash the export; leave duration unset
                    pass

        # Create main timeline
        usdm_timeline_id = self._id_manager.get_id(USDMScheduleTimeline.__name__)
        usdm_timeline = USDMScheduleTimeline(
            id=usdm_timeline_id,
            name="Main Timeline",
            mainTimeline=True,
            entryCondition="",  # TODO: no OSB source for entryCondition
            entryId="",
            instances=[],
            plannedDuration=usdm_planned_duration,
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
                label=(
                    osb_visit.study_epoch.sponsor_preferred_name
                    if osb_visit.study_epoch
                    else ""
                ),
                description=(
                    osb_visit.study_epoch.sponsor_preferred_name
                    if osb_visit.study_epoch
                    else ""
                ),
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
                windowLabel=(
                    f"{osb_visit.min_visit_window_value}..{osb_visit.max_visit_window_value} {osb_visit.visit_window_unit_name}"
                    if ddf_timing_window_available
                    else None
                ),
            )
            timeline_instances.append(curr_scheduled_instance)
            usdm_timings.append(ddf_timing)
        usdm_timeline.timings = usdm_timings
        usdm_timeline.instances = timeline_instances
        # Wire entryId to the first ScheduledActivityInstance now that
        # instances are populated. Guard the empty case — entryId is a
        # required str so leave "" when there are no instances.
        if timeline_instances:
            usdm_timeline.entryId = timeline_instances[0].id
        return [usdm_timeline]

    @trace_calls
    def _get_study_title(self, study: OSBStudy):
        osb_current_metadata = getattr(study, "current_metadata", None)
        study_title = getattr(
            getattr(osb_current_metadata, "study_description", None), "study_title", ""
        )
        if study_title is not None:
            return study_title
        return "Study title not available"

    @trace_calls
    def _get_study_brief_title(self, study: OSBStudy) -> str | None:
        osb_current_metadata = getattr(study, "current_metadata", None)
        return getattr(
            getattr(osb_current_metadata, "study_description", None),
            "study_short_title",
            None,
        )

    @trace_calls
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

    @trace_calls
    def _get_study_version(self, study: OSBStudy):
        osb_current_metadata = getattr(study, "current_metadata", None)
        if not osb_current_metadata:
            # Structural default: versionIdentifier is a required str on
            # usdm_model.StudyVersion v4 — None/skip is not legal. Emit "" when
            # OSB metadata is missing rather than fabricating a value.
            return ""

        if osb_version_metadata := getattr(
            osb_current_metadata, "version_metadata", None
        ):

            rs = osb_version_metadata.study_status
            if osb_version_metadata.version_number:
                rs += f" v{osb_version_metadata.version_number}"

            return rs

        # Structural default: see comment on the early-return branch above.
        return ""

    @trace_calls
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
                type=self.get_ct_package_term_as_usdm_code(sv.visit_type.term_uid),
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
                    self.get_ct_package_term_as_usdm_code(
                        sv.visit_contact_mode.term_uid
                    )
                ],
                # environmentalSettings: left empty — no OSB care-setting source.
                # StudyVisit exposes only visit_contact_mode (already mapped to
                # contactModes above); the DDF-RA yardstick populates this from a
                # separate care-setting term OSB does not model (ADO 254080).
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

    @trace_calls
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

    @trace_calls
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

    @trace_calls
    def _get_trial_type_codes(self, study: OSBStudy):
        osb_current_metadata = getattr(study, "current_metadata", None)
        osb_high_level_study_design = getattr(
            osb_current_metadata, "high_level_study_design", None
        )
        osb_trial_type_codes = getattr(
            osb_high_level_study_design, "trial_type_codes", None
        )
        if not osb_trial_type_codes:
            return []
        return [
            (
                self.get_ct_package_term_as_usdm_code(osb_trial_type_code.term_uid)
                if osb_trial_type_code.term_uid is not None
                else self.get_void_usdm_code()
            )
            for osb_trial_type_code in osb_trial_type_codes
            if osb_trial_type_code
        ]
