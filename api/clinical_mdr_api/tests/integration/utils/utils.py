# pylint: disable=broad-except
# pylint: disable=too-many-arguments
# pylint: disable=too-many-public-methods
# pylint: disable=dangerous-default-value
import csv
import io
import logging
from datetime import date, datetime, timedelta, timezone
from random import randint
from typing import Any, Literal
from xml.etree import ElementTree

import openpyxl
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DataModelIGRoot,
    DataModelRoot,
    Dataset,
    DatasetClass,
    DatasetScenario,
    DatasetVariable,
    VariableClass,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    DEFAULT_CODELIST_TYPE,
)
from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.domains.enums import (
    LibraryItemStatus,
    StudyDesignClassEnum,
    StudySourceVariableEnum,
    ValidationMode,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.main import app
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
    ActivityInstanceClassInput,
)
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityInstanceClassRelInput,
    ActivityItemClass,
    ActivityItemClassCreateInput,
    NonStandardVariableInput,
)
from clinical_mdr_api.models.brands.brand import Brand, BrandCreateInput
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
    ClinicalProgrammeInput,
)
from clinical_mdr_api.models.comments.comments import (
    CommentReply,
    CommentReplyCreateInput,
    CommentThread,
    CommentThreadCreateInput,
)
from clinical_mdr_api.models.concepts.active_substance import (
    ActiveSubstance,
    ActiveSubstanceCreateInput,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    Activity,
    ActivityCreateInput,
    ActivityGrouping,
)
from clinical_mdr_api.models.concepts.activities.activity_group import (
    ActivityGroup,
    ActivityGroupCreateInput,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
    ActivityInstanceCreateInput,
    ActivityInstanceGrouping,
)
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
    ActivitySubGroupCreateInput,
)
from clinical_mdr_api.models.concepts.compound import Compound, CompoundCreateInput
from clinical_mdr_api.models.concepts.compound_alias import (
    CompoundAlias,
    CompoundAliasCreateInput,
)
from clinical_mdr_api.models.concepts.concept import (
    LagTime,
    LagTimePostInput,
    NumericValueWithUnit,
    NumericValueWithUnitPostInput,
    TextValue,
    TextValuePostInput,
)
from clinical_mdr_api.models.concepts.medicinal_product import (
    MedicinalProduct,
    MedicinalProductCreateInput,
)
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    PharmaceuticalProduct,
    PharmaceuticalProductCreateInput,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
    UnitDefinitionPostInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelist,
    CTCodelistCreateInput,
    CTCodelistTermInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_package import CTPackage
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTerm,
    CTTermCodelistInput,
    CTTermCreateInput,
    CTTermNameAndAttributes,
    CTTermUidInput,
    SimpleCTTermNameWithConflictFlag,
)
from clinical_mdr_api.models.data_completeness_tag import (
    DataCompletenessTag,
    DataCompletenessTagInput,
)
from clinical_mdr_api.models.data_suppliers.data_supplier import (
    DataSupplier,
    DataSupplierInput,
)
from clinical_mdr_api.models.dictionaries.dictionary_codelist import (
    DictionaryCodelist,
    DictionaryCodelistCreateInput,
)
from clinical_mdr_api.models.dictionaries.dictionary_term import (
    DictionaryTerm,
    DictionaryTermCreateInput,
)
from clinical_mdr_api.models.feature_flag import FeatureFlag, FeatureFlagInput
from clinical_mdr_api.models.notification import (
    Notification,
    NotificationPostInput,
    NotificationType,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmFormalExpressionModel,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.models.odms.condition import OdmCondition, OdmConditionPostInput
from clinical_mdr_api.models.odms.form import OdmForm, OdmFormPostInput
from clinical_mdr_api.models.odms.item import OdmItem, OdmItemCodelist, OdmItemPostInput
from clinical_mdr_api.models.odms.item_group import OdmItemGroup, OdmItemGroupPostInput
from clinical_mdr_api.models.odms.method import OdmMethod, OdmMethodPostInput
from clinical_mdr_api.models.odms.study_event import (
    OdmStudyEvent,
    OdmStudyEventPostInput,
)
from clinical_mdr_api.models.odms.vendor_attribute import (
    OdmVendorAttribute,
    OdmVendorAttributePostInput,
)
from clinical_mdr_api.models.odms.vendor_element import (
    OdmVendorElement,
    OdmVendorElementPostInput,
)
from clinical_mdr_api.models.odms.vendor_namespace import (
    OdmVendorNamespace,
    OdmVendorNamespacePostInput,
)
from clinical_mdr_api.models.projects.project import Project, ProjectCreateInput
from clinical_mdr_api.models.standard_data_models.data_model import DataModel
from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG
from clinical_mdr_api.models.standard_data_models.dataset import (
    Dataset as DatasetAPIModel,
)
from clinical_mdr_api.models.standard_data_models.dataset_class import (
    DatasetClass as DatasetClassAPIModel,
)
from clinical_mdr_api.models.standard_data_models.dataset_scenario import (
    DatasetScenario as DatasetScenarioAPIModel,
)
from clinical_mdr_api.models.standard_data_models.dataset_variable import (
    DatasetVariable as DatasetVariableAPIModel,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model import (
    SponsorModel as SponsorModelAPIModel,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model import (
    SponsorModelCreateInput,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset import (
    SponsorModelDataset as SponsorModelDatasetAPIModel,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset import (
    SponsorModelDatasetInput,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariable as SponsorModelDatasetVariableAPIModel,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariableInput,
)
from clinical_mdr_api.models.standard_data_models.variable_class import (
    VariableClass as VariableClassAPIModel,
)
from clinical_mdr_api.models.study_selections.study import (
    HighLevelStudyDesignJsonModel,
    Study,
    StudyCreateInput,
    StudyDescriptionJsonModel,
    StudyIdentificationMetadataJsonModel,
    StudyInterventionJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
    StudyPopulationJsonModel,
    StudyPreferredTimeUnit,
    StudySoaPreferences,
    StudySoaPreferencesInput,
    StudySubpartCreateInput,
)
from clinical_mdr_api.models.study_selections.study_disease_milestone import (
    StudyDiseaseMilestone,
    StudyDiseaseMilestoneCreateInput,
)
from clinical_mdr_api.models.study_selections.study_epoch import (
    StudyEpoch,
    StudyEpochCreateInput,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    EndpointUnitsInput,
    ReferencedItem,
    StudyActivitySchedule,
    StudyActivityScheduleCreateInput,
    StudyCompoundDosing,
    StudyCompoundDosingInput,
    StudyDesignCell,
    StudyDesignCellCreateInput,
    StudyDesignClass,
    StudyDesignClassInput,
    StudySelectionActivity,
    StudySelectionActivityCreateInput,
    StudySelectionActivityInput,
    StudySelectionActivityInstanceBatchInput,
    StudySelectionActivityInstanceCreateInput,
    StudySelectionActivityInstanceEditInput,
    StudySelectionArm,
    StudySelectionArmCreateInput,
    StudySelectionBranchArm,
    StudySelectionBranchArmCreateInput,
    StudySelectionCohort,
    StudySelectionCohortCreateInput,
    StudySelectionCompound,
    StudySelectionCompoundCreateInput,
    StudySelectionCriteria,
    StudySelectionCriteriaCreateInput,
    StudySelectionElement,
    StudySelectionElementCreateInput,
    StudySelectionEndpoint,
    StudySelectionEndpointCreateInput,
    StudySelectionObjective,
    StudySelectionObjectiveCreateInput,
    StudySourceVariable,
    StudySourceVariableInput,
)
from clinical_mdr_api.models.study_selections.study_soa_footnote import (
    StudySoAFootnote,
    StudySoAFootnoteCreateInput,
)
from clinical_mdr_api.models.study_selections.study_standard_version import (
    StudyStandardVersionEditInput,
    StudyStandardVersionInput,
)
from clinical_mdr_api.models.study_selections.study_visit import (
    StudyVisit,
    StudyVisitCreateInput,
)
from clinical_mdr_api.models.syntax_instances.activity_instruction import (
    ActivityInstruction,
    ActivityInstructionCreateInput,
)
from clinical_mdr_api.models.syntax_instances.criteria import (
    Criteria,
    CriteriaCreateInput,
)
from clinical_mdr_api.models.syntax_instances.endpoint import (
    Endpoint,
    EndpointCreateInput,
)
from clinical_mdr_api.models.syntax_instances.footnote import (
    Footnote,
    FootnoteCreateInput,
)
from clinical_mdr_api.models.syntax_instances.objective import (
    Objective,
    ObjectiveCreateInput,
)
from clinical_mdr_api.models.syntax_instances.timeframe import (
    Timeframe,
    TimeframeCreateInput,
)
from clinical_mdr_api.models.syntax_pre_instances.activity_instruction_pre_instance import (
    ActivityInstructionPreInstance,
    ActivityInstructionPreInstanceCreateInput,
)
from clinical_mdr_api.models.syntax_pre_instances.criteria_pre_instance import (
    CriteriaPreInstance,
    CriteriaPreInstanceCreateInput,
)
from clinical_mdr_api.models.syntax_pre_instances.endpoint_pre_instance import (
    EndpointPreInstance,
    EndpointPreInstanceCreateInput,
)
from clinical_mdr_api.models.syntax_pre_instances.footnote_pre_instance import (
    FootnotePreInstance,
    FootnotePreInstanceCreateInput,
)
from clinical_mdr_api.models.syntax_pre_instances.objective_pre_instance import (
    ObjectivePreInstance,
    ObjectivePreInstanceCreateInput,
)
from clinical_mdr_api.models.syntax_templates.activity_instruction_template import (
    ActivityInstructionTemplate,
    ActivityInstructionTemplateCreateInput,
)
from clinical_mdr_api.models.syntax_templates.criteria_template import (
    CriteriaTemplate,
    CriteriaTemplateCreateInput,
)
from clinical_mdr_api.models.syntax_templates.endpoint_template import (
    EndpointTemplate,
    EndpointTemplateCreateInput,
)
from clinical_mdr_api.models.syntax_templates.footnote_template import (
    FootnoteTemplate,
    FootnoteTemplateCreateInput,
)
from clinical_mdr_api.models.syntax_templates.objective_template import (
    ObjectiveTemplate,
    ObjectiveTemplateCreateInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.syntax_templates.timeframe_template import (
    TimeframeTemplate,
    TimeframeTemplateCreateInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassService,
)
from clinical_mdr_api.services.biomedical_concepts.activity_item_class import (
    ActivityItemClassService,
)
from clinical_mdr_api.services.brands.brand import BrandService
from clinical_mdr_api.services.clinical_programmes.clinical_programme import (
    ClinicalProgrammeService,
)
from clinical_mdr_api.services.comments.comments import CommentsService
from clinical_mdr_api.services.concepts.active_substances_service import (
    ActiveSubstanceService,
)
from clinical_mdr_api.services.concepts.activities.activity_group_service import (
    ActivityGroupService,
)
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceGroupingsService,
    ActivityInstanceService,
)
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
)
from clinical_mdr_api.services.concepts.activities.activity_sub_group_service import (
    ActivitySubGroupService,
)
from clinical_mdr_api.services.concepts.compound_alias_service import (
    CompoundAliasService,
)
from clinical_mdr_api.services.concepts.compound_service import CompoundService
from clinical_mdr_api.services.concepts.medicinal_products_service import (
    MedicinalProductService,
)
from clinical_mdr_api.services.concepts.pharmaceutical_products_service import (
    PharmaceuticalProductService,
)
from clinical_mdr_api.services.concepts.simple_concepts.lag_time import LagTimeService
from clinical_mdr_api.services.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitService,
)
from clinical_mdr_api.services.concepts.simple_concepts.text_value import (
    TextValueService,
)
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_package import (
    CTPackageService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term_name import (
    CTTermNameService,
)
from clinical_mdr_api.services.data_completeness_tags import DataCompletenessTagService
from clinical_mdr_api.services.data_suppliers.data_supplier import DataSupplierService
from clinical_mdr_api.services.dictionaries.dictionary_codelist_generic_service import (
    DictionaryCodelistGenericService as DictionaryCodelistService,
)
from clinical_mdr_api.services.dictionaries.dictionary_term_generic_service import (
    DictionaryTermGenericService as DictionaryTermService,
)
from clinical_mdr_api.services.feature_flags import FeatureFlagService
from clinical_mdr_api.services.libraries import libraries as library_service
from clinical_mdr_api.services.notifications import NotificationService
from clinical_mdr_api.services.odms.conditions import OdmConditionService
from clinical_mdr_api.services.odms.forms import OdmFormService
from clinical_mdr_api.services.odms.item_groups import OdmItemGroupService
from clinical_mdr_api.services.odms.items import OdmItemService
from clinical_mdr_api.services.odms.methods import OdmMethodService
from clinical_mdr_api.services.odms.study_events import OdmStudyEventService
from clinical_mdr_api.services.odms.vendor_attributes import OdmVendorAttributeService
from clinical_mdr_api.services.odms.vendor_elements import OdmVendorElementService
from clinical_mdr_api.services.odms.vendor_namespaces import OdmVendorNamespaceService
from clinical_mdr_api.services.projects.project import ProjectService
from clinical_mdr_api.services.standard_data_models.data_model import DataModelService
from clinical_mdr_api.services.standard_data_models.data_model_ig import (
    DataModelIGService,
)
from clinical_mdr_api.services.standard_data_models.dataset import DatasetService
from clinical_mdr_api.services.standard_data_models.dataset_class import (
    DatasetClassService,
)
from clinical_mdr_api.services.standard_data_models.dataset_scenario import (
    DatasetScenarioService,
)
from clinical_mdr_api.services.standard_data_models.dataset_variable import (
    DatasetVariableService,
)
from clinical_mdr_api.services.standard_data_models.sponsor_model import (
    SponsorModelService,
)
from clinical_mdr_api.services.standard_data_models.sponsor_model_dataset import (
    SponsorModelDatasetService,
)
from clinical_mdr_api.services.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariableService,
)
from clinical_mdr_api.services.standard_data_models.variable_class import (
    VariableClassService,
)
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_instance_selection import (
    StudyActivityInstanceSelectionService,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_arm_selection import (
    StudyArmSelectionService,
)
from clinical_mdr_api.services.studies.study_branch_arm_selection import (
    StudyBranchArmSelectionService,
)
from clinical_mdr_api.services.studies.study_cohort_selection import (
    StudyCohortSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_selection import (
    StudyCompoundSelectionService,
)
from clinical_mdr_api.services.studies.study_criteria_selection import (
    StudyCriteriaSelectionService,
)
from clinical_mdr_api.services.studies.study_design_cell import StudyDesignCellService
from clinical_mdr_api.services.studies.study_design_class import StudyDesignClassService
from clinical_mdr_api.services.studies.study_disease_milestone import (
    StudyDiseaseMilestoneService,
)
from clinical_mdr_api.services.studies.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.services.studies.study_endpoint_selection import (
    StudyEndpointSelectionService,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.services.studies.study_objective_selection import (
    StudyObjectiveSelectionService,
)
from clinical_mdr_api.services.studies.study_soa_footnote import StudySoAFootnoteService
from clinical_mdr_api.services.studies.study_source_variable import (
    StudySourceVariableService,
)
from clinical_mdr_api.services.studies.study_standard_version_selection import (
    StudyStandardVersionService,
)
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.services.syntax_instances.activity_instructions import (
    ActivityInstructionService,
)
from clinical_mdr_api.services.syntax_instances.criteria import CriteriaService
from clinical_mdr_api.services.syntax_instances.endpoints import EndpointService
from clinical_mdr_api.services.syntax_instances.footnotes import FootnoteService
from clinical_mdr_api.services.syntax_instances.objectives import ObjectiveService
from clinical_mdr_api.services.syntax_instances.timeframes import TimeframeService
from clinical_mdr_api.services.syntax_pre_instances.activity_instruction_pre_instances import (
    ActivityInstructionPreInstanceService,
)
from clinical_mdr_api.services.syntax_pre_instances.criteria_pre_instances import (
    CriteriaPreInstanceService,
)
from clinical_mdr_api.services.syntax_pre_instances.endpoint_pre_instances import (
    EndpointPreInstanceService,
)
from clinical_mdr_api.services.syntax_pre_instances.footnote_pre_instances import (
    FootnotePreInstanceService,
)
from clinical_mdr_api.services.syntax_pre_instances.objective_pre_instances import (
    ObjectivePreInstanceService,
)
from clinical_mdr_api.services.syntax_templates.activity_instruction_templates import (
    ActivityInstructionTemplateService,
)
from clinical_mdr_api.services.syntax_templates.criteria_templates import (
    CriteriaTemplateService,
)
from clinical_mdr_api.services.syntax_templates.endpoint_templates import (
    EndpointTemplateService,
)
from clinical_mdr_api.services.syntax_templates.footnote_templates import (
    FootnoteTemplateService,
)
from clinical_mdr_api.services.syntax_templates.objective_templates import (
    ObjectiveTemplateService,
)
from clinical_mdr_api.services.syntax_templates.timeframe_templates import (
    TimeframeTemplateService,
)
from clinical_mdr_api.tests.unit.domain.study_definition_aggregate.test_study_metadata import (
    initialize_ct_codelist_map,
    initialize_ct_data_map,
)
from clinical_mdr_api.tests.utils.checks import (
    assert_response_content_type,
    assert_response_status_code,
)
from clinical_mdr_api.utils.db_integrity_checks import execute_all_checks_for_study
from common.auth.dependencies import dummy_user_test_auth
from common.auth.user import clear_users_cache
from common.config import settings
from common.utils import VisitClass, VisitSubclass

log = logging.getLogger(__name__)


class CTCodelistConfig:
    default: str
    dosage_form: str
    delivery_device: str
    frequency: str
    dispenser: str
    roa: str
    adverse_events: str
    domain: str

    def __init__(self, **kwargs: str):
        for key, value in kwargs.items():
            setattr(self, key, value)


AUTHOR = "test"
STUDY_UID = "study_root"
PROJECT_NUMBER = "123"
SPONSOR_LIBRARY_NAME = settings.sponsor_library_name
CDISC_LIBRARY_NAME = settings.cdisc_library_name
CT_CATALOGUE_NAME = "SDTM CT"
CT_CODELIST_UIDS: CTCodelistConfig = CTCodelistConfig(
    default="C66737",
    dosage_form="C66726",
    delivery_device="CDEVICE123",
    frequency="C71113",
    dispenser="CDISP123",
    roa="C66729",
    adverse_events="C66734",
    domain="C66734",
)
CT_CODELIST_NAMES = CTCodelistConfig(
    default="CT Codelist",
    dosage_form="Pharmaceutical Dosage Form",
    delivery_device="Delivery Device",
    frequency="Frequency",
    dispenser="Compound Dispensed In",
    roa="Route of Administration",
    adverse_events="SDTM Domain Abbreviation",
    domain="SDTM Domain Abbreviation",
)
CT_CODELIST_SUBMVALS = CTCodelistConfig(
    default="CT Codelist",
    dosage_form=settings.dosage_form_cl_submval,
    delivery_device=settings.delivery_device_cl_submval,
    frequency=settings.dose_frequency_cl_submval,
    dispenser=settings.compound_dispensed_in_cl_submval,
    roa=settings.route_of_administration_cl_submval,
    adverse_events=settings.stdm_domain_cl_submval,
    domain=settings.stdm_domain_cl_submval,
)

CT_CODELIST_LIBRARY = "CDISC"
CT_CODELIST_LIBRARY_SPONSOR = "Sponsor"
CT_PACKAGE_NAME = f"SDTM CT {datetime.now().strftime('%Y-%m-%d')}"
DICTIONARY_CODELIST_NAME = "UCUM"
DICTIONARY_CODELIST_LIBRARY = "UCUM"


def _resolve_ct_term(
    nested: dict | CTTermUidInput | None,
    flat_uid: str | None,
) -> CTTermUidInput | None:
    """Resolve a CT term field from either a nested object or a flat UID string."""
    if nested is not None:
        if isinstance(nested, dict):
            return CTTermUidInput(**nested)
        return nested
    if flat_uid is not None:
        return CTTermUidInput(term_uid=flat_uid)
    return None


class TestUtils:
    """Class containing methods that create all kinds of entities, e.g. library compounds"""

    sequential_study_number: int = 0

    @classmethod
    def assert_response_shape_ok(
        cls,
        response_json: Any,
        expected_fields: list[str],
        expected_not_null_fields: list[str],
    ):
        assert set(list(response_json.keys())) == set(expected_fields)
        for key in expected_not_null_fields:
            assert response_json[key] is not None, f"Field '{key}' is None"

    @classmethod
    def assert_paginated_response_shape_ok(
        cls,
        response_json: Any,
        include_study_version: bool = True,
    ):
        expected_fields = {"self", "prev", "next", "items"}
        if include_study_version:
            expected_fields.add("study_version")

        assert response_json.keys() == expected_fields
        for field in expected_fields:
            assert response_json[field] is not None, f"Field '{field}' is None"

        if include_study_version:
            assert response_json["study_version"].keys() == {
                "version_status",
                "version_number",
                "version_started_at",
                "version_ended_at",
                "retrieved_at",
            }

            for field in response_json["study_version"]:
                if field not in ["version_ended_at", "version_number"]:
                    assert (
                        response_json["study_version"][field] is not None
                    ), f"Field '{field}' is None"

    @classmethod
    def assert_timestamp_is_in_utc_zone(cls, val: str):
        datetime_ts: datetime = datetime.strptime(val, settings.date_time_format)
        assert datetime_ts.tzinfo == timezone.utc

    @classmethod
    def assert_timestamp_is_newer_than(cls, val: str, seconds: int):
        datetime_ts: datetime = datetime.strptime(val, settings.date_time_format)
        assert abs(datetime.now(timezone.utc) - datetime_ts) < timedelta(
            seconds=seconds
        )

    @classmethod
    def assert_chronological_sequence(cls, val1: str, val2: str):
        """Asserts that val1 timestamp is chronologically older than val2 timestamp"""
        ts1: datetime = datetime.strptime(val1, settings.date_time_format)
        ts2: datetime = datetime.strptime(val2, settings.date_time_format)
        assert ts1 - ts2 < timedelta(seconds=0)

    @classmethod
    def assert_sort_order(
        cls, items: list[dict[Any, Any]], key: str, desc: bool = False
    ):
        """Asserts that the supplied list of dictionaries is sorted by `key` in expected order"""
        if "." in key:
            # If the key is a nested key, we need to extract it from each item
            key1, key2 = key.split(".")
            sorted_items = sorted(items, key=lambda x: x[key1][key2], reverse=desc)
        else:
            sorted_items = sorted(items, key=lambda x: x[key], reverse=desc)
        assert items == sorted_items

    @classmethod
    def get_datetime(cls, val: str) -> datetime:
        """Returns datetime object from supplied string value"""
        return datetime.strptime(val, settings.date_time_format)

    @classmethod
    def assert_valid_csv(cls, val: str):
        csv_file = io.StringIO(val)
        try:
            csv_reader = csv.reader(csv_file)
            for _row in csv_reader:
                pass  # Do nothing, just iterate through the rows
        except csv.Error:
            assert False, "Returned content is not a valid CSV file"

    @classmethod
    def assert_valid_xml(cls, val: str):
        # Attempt to parse the XML content using ElementTree
        try:
            _root = ElementTree.fromstring(val)
        except ElementTree.ParseError:
            assert False, "Content is not valid XML"

    @classmethod
    def assert_valid_excel(cls, content):
        excel_file = io.BytesIO(content)
        # Attempt to open the Excel file using openpyxl
        try:
            _workbook = openpyxl.load_workbook(excel_file)
        except openpyxl.utils.exceptions.InvalidFileException:
            assert False, "File doesn't contain valid Excel data"

    @classmethod
    def verify_exported_data_format(
        cls,
        api_client: TestClient,
        export_format: str,
        url: str,
        params: dict[Any, Any] | None = None,
    ):
        """Verifies that the specified endpoint returns valid csv/xml/Excel content"""
        headers = {"Accept": export_format}
        log.info("GET %s | %s", url, headers)
        response = api_client.get(url, headers=headers, params=params)

        assert_response_status_code(response, 200)
        assert_response_content_type(response, export_format)

        if export_format == "text/csv":
            TestUtils.assert_valid_csv(response.content.decode("utf-8"))
        if export_format == "text/xml":
            TestUtils.assert_valid_xml(response.content.decode("utf-8"))
        if (
            export_format
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ):
            TestUtils.assert_valid_excel(response.content)
        return response

    @classmethod
    def random_str(cls, length: int = 8, prefix: str = ""):
        """returns a random numerical string of `length` with optional string prefix (length excludes prefix)"""
        return prefix + str(randint(0, 10**length - 1)).zfill(length)

    @classmethod
    def random_if_none(cls, val, length: int = 10, prefix: str = ""):
        """Return supplied `val` if its value is not None.
        Otherwise, return random numerical string of `length` with optional string prefix (length excludes prefix)
        """
        return val if val else cls.random_str(length, prefix)

    @classmethod
    def create_dummy_user(cls, user_id: str = "unknown-user"):
        clear_users_cache()
        dummy_user_test_auth(user_id=user_id)

    # region Syntax Templates
    @classmethod
    def create_template_parameter(cls, name: str) -> None:
        db.cypher_query(f"CREATE (:TemplateParameter {{name:'{name}'}})")

    @classmethod
    def set_final_props(cls, final_variable):
        return f""" SET {final_variable} = {{
        change_description: "Approved version",
        start_date: datetime("2020-06-26T00:00:00"),
        status: "Final",
        author_id: "unknown-user",
        version: "1.0"
    }} """

    @classmethod
    def update_entity_status(
        cls, entity_uid: str, status: str, entity_type: str
    ) -> None:
        """Update the status of an entity using a direct Cypher query

        Args:
            entity_uid: The UID of the entity to update
            status: The new status (e.g., 'Draft', 'Final')
            entity_type: The type of entity (e.g., 'ActivityGroup', 'ActivitySubGroup')
        """
        # Determine the root node label based on entity type
        root_label = f"{entity_type}Root"
        # Find the latest relationship by matching on the root node and getting the latest version
        # where end_date is null (the active version)
        query = f"""
        MATCH (root:{root_label} {{uid: $uid}})-[rel:HAS_VERSION]->(val)
        WHERE rel.end_date IS NULL
        SET rel.status = $status
        RETURN rel
        """

        params = {"uid": entity_uid, "status": status}
        db.cypher_query(query=query, params=params)

    @classmethod
    def create_feature_flag(
        cls,
        section: Literal["admin", "library", "studies"] = "library",
        feature: str = "Feature name",
        name: str = "Feature Flag Name",
        enabled: bool = False,
        description: str | None = "Feature Flag Description",
    ) -> FeatureFlag:
        service: FeatureFlagService = FeatureFlagService()
        payload = FeatureFlagInput(
            section=section,
            feature=feature,
            name=name,
            enabled=enabled,
            description=description,
        )
        return service.create_feature_flag(payload)

    @classmethod
    def create_data_completeness_tag(
        cls,
        name: str = "Data Completeness Tag Name",
    ) -> DataCompletenessTag:
        service: DataCompletenessTagService = DataCompletenessTagService()
        payload = DataCompletenessTagInput(name=name)
        return service.create_data_completeness_tag(payload)

    @classmethod
    def create_notification(
        cls,
        title: str = "Notification Title",
        notification_type: NotificationType = NotificationType.INFORMATION,
        description: str | None = "Notification Description",
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        published: bool = False,
    ) -> Notification:
        service: NotificationService = NotificationService()
        payload = NotificationPostInput(
            title=title,
            notification_type=notification_type,
            description=description,
            started_at=started_at,
            ended_at=ended_at,
            published=published,
        )
        return service.create_notification(payload)

    @classmethod
    def create_text_value(
        cls,
        library_name: str = SPONSOR_LIBRARY_NAME,
        name: str | None = None,
        name_sentence_case: str | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        template_parameter: bool = True,
    ) -> TextValue:
        service: TextValueService = TextValueService()
        payload: TextValuePostInput = TextValuePostInput(
            name=cls.random_if_none(name, prefix="name-"),
            name_sentence_case=cls.random_if_none(
                name_sentence_case, prefix="name_sentence_case-"
            ),
            definition=cls.random_if_none(definition, prefix="def-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbr-"),
            library_name=library_name,
            template_parameter=template_parameter,
        )

        result: TextValue = service.create(payload)  # type: ignore[assignment]
        return result

    @classmethod
    def create_data_supplier(
        cls,
        name: str | None,
        supplier_type_uid: str,
        order: int = 999999,
        description: str | None = None,
        api_base_url: str | None = None,
        ui_base_url: str | None = None,
        origin_source_uid: str | None = None,
        origin_type_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
    ) -> DataSupplier:
        service: DataSupplierService = DataSupplierService()
        payload: DataSupplierInput = DataSupplierInput(
            name=cls.random_if_none(name, prefix="name-"),
            order=order,
            description=description,
            api_base_url=api_base_url,
            ui_base_url=ui_base_url,
            supplier_type_uid=supplier_type_uid,
            origin_source_uid=origin_source_uid,
            origin_type_uid=origin_type_uid,
            library_name=library_name,
        )

        return service.create_approve(payload)

    @classmethod
    def create_objective_template(
        cls,
        name: str | None = None,
        guidance_text: str | None = None,
        study_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        indication_uids: list[str] | None = None,
        is_confirmatory_testing: bool = False,
        category_uids: list[str] | None = None,
        approve: bool = True,
    ) -> ObjectiveTemplate:
        service: ObjectiveTemplateService = ObjectiveTemplateService()
        payload: ObjectiveTemplateCreateInput = ObjectiveTemplateCreateInput(
            name=cls.random_if_none(name, prefix="ot-"),
            guidance_text=guidance_text,
            study_uid=study_uid,
            library_name=library_name,
            indication_uids=indication_uids or [],
            is_confirmatory_testing=is_confirmatory_testing,
            category_uids=category_uids,
        )

        result: ObjectiveTemplate = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_endpoint_template(
        cls,
        name: str | None = None,
        guidance_text: str | None = None,
        study_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        indication_uids: list[str] | None = None,
        category_uids: list[str] | None = None,
        sub_category_uids: list[str] | None = None,
        approve: bool = True,
    ) -> EndpointTemplate:
        service: EndpointTemplateService = EndpointTemplateService()
        payload: EndpointTemplateCreateInput = EndpointTemplateCreateInput(
            name=cls.random_if_none(name, prefix="et-"),
            guidance_text=guidance_text,
            study_uid=study_uid,
            library_name=library_name,
            indication_uids=indication_uids or [],
            category_uids=category_uids,
            sub_category_uids=sub_category_uids,
        )

        result: EndpointTemplate = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_activity_instruction_template(
        cls,
        name: str | None = None,
        guidance_text: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        indication_uids: list[str] | None = None,
        activity_uids: list[str] | None = None,
        activity_group_uids: list[str] | None = None,
        activity_subgroup_uids: list[str] | None = None,
        approve: bool = True,
    ) -> ActivityInstructionTemplate:
        service: ActivityInstructionTemplateService = (
            ActivityInstructionTemplateService()
        )
        payload: ActivityInstructionTemplateCreateInput = (
            ActivityInstructionTemplateCreateInput(
                name=cls.random_if_none(name, prefix="ct-"),
                guidance_text=cls.random_if_none(guidance_text),
                library_name=library_name,
                indication_uids=indication_uids or [],
                activity_uids=activity_uids,
                activity_group_uids=activity_group_uids or [],
                activity_subgroup_uids=activity_subgroup_uids or [],
            )
        )

        result: ActivityInstructionTemplate = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_criteria_template(
        cls,
        *,
        name: str | None = None,
        guidance_text: str | None = None,
        study_uid: str | None = None,
        type_uid: str,
        library_name: str = SPONSOR_LIBRARY_NAME,
        indication_uids: list[str] | None = None,
        category_uids: list[str] | None = None,
        sub_category_uids: list[str] | None = None,
        approve: bool = True,
    ) -> CriteriaTemplate:
        service: CriteriaTemplateService = CriteriaTemplateService()
        payload: CriteriaTemplateCreateInput = CriteriaTemplateCreateInput(
            name=cls.random_if_none(name, prefix="ct-"),
            guidance_text=cls.random_if_none(guidance_text),
            study_uid=study_uid,
            library_name=library_name,
            type_uid=type_uid,
            indication_uids=indication_uids or [],
            category_uids=category_uids,
            sub_category_uids=sub_category_uids,
        )

        result: CriteriaTemplate = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_footnote_template(
        cls,
        *,
        name: str | None = None,
        study_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        type_uid: str,
        indication_uids: list[str] | None = None,
        activity_uids: list[str] | None = None,
        activity_group_uids: list[str] | None = None,
        activity_subgroup_uids: list[str] | None = None,
        approve: bool = True,
    ) -> FootnoteTemplate:
        service: FootnoteTemplateService = FootnoteTemplateService()
        payload: FootnoteTemplateCreateInput = FootnoteTemplateCreateInput(
            name=cls.random_if_none(name, prefix="ct-"),
            study_uid=study_uid,
            library_name=library_name,
            type_uid=type_uid,
            indication_uids=indication_uids or [],
            activity_uids=activity_uids,
            activity_group_uids=activity_group_uids,
            activity_subgroup_uids=activity_subgroup_uids,
        )

        result: FootnoteTemplate = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_timeframe_template(
        cls,
        name: str | None = None,
        guidance_text: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        approve: bool = True,
    ) -> TimeframeTemplate:
        service: TimeframeTemplateService = TimeframeTemplateService()
        payload: TimeframeTemplateCreateInput = TimeframeTemplateCreateInput(
            name=cls.random_if_none(name, prefix="tt-"),
            guidance_text=guidance_text,
            library_name=library_name,
        )

        result: TimeframeTemplate = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    # endregion

    # region Syntax Instances
    @classmethod
    def create_activity_instruction(
        cls,
        activity_instruction_template_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        approve: bool = True,
    ) -> ActivityInstruction:
        if not activity_instruction_template_uid:
            activity_instruction_template_uid = (
                cls.create_activity_instruction_template(
                    name="test name",
                    guidance_text="guidance text",
                    library_name="Sponsor",
                    indication_uids=[],
                    activity_uids=[],
                    activity_group_uids=[],
                    activity_subgroup_uids=[],
                ).uid
            )

        service: ActivityInstructionService = ActivityInstructionService()
        payload: ActivityInstructionCreateInput = ActivityInstructionCreateInput(
            activity_instruction_template_uid=activity_instruction_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms or [],
        )

        result: ActivityInstruction = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_footnote(
        cls,
        footnote_template_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        parameter_terms: list[TemplateParameterMultiSelectInput] = [],
        approve: bool = True,
    ) -> Footnote:
        if not footnote_template_uid:
            # find the footnote type codelist
            codelist_uid = db.cypher_query("""
                MATCH (clr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(:CTCodelistAttributesValue {submission_value: 'FTNTTP'})
                RETURN clr.uid
                """)[0][0][0]

            footnote_template_uid = cls.create_footnote_template(
                name="test name",
                study_uid=None,
                library_name="Sponsor",
                type_uid=cls.create_ct_term(
                    sponsor_preferred_name="INCLUSION FOOTNOTE",
                    codelist_uid=codelist_uid,
                ).term_uid,
                indication_uids=[],
                activity_uids=[],
                activity_group_uids=[],
                activity_subgroup_uids=[],
            ).uid

        service: FootnoteService = FootnoteService()
        payload: FootnoteCreateInput = FootnoteCreateInput(
            footnote_template_uid=footnote_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms,
        )

        result: Footnote = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_criteria(
        cls,
        criteria_template_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        approve: bool = True,
    ) -> Criteria:
        if not criteria_template_uid:
            criteria_template_uid = cls.create_criteria_template(
                name="test name",
                guidance_text="guidance text",
                study_uid=None,
                library_name="Sponsor",
                indication_uids=[],
                category_uids=[],
                sub_category_uids=[],
                type_uid=cls.create_ct_term(
                    sponsor_preferred_name="INCLUSION CRITERIA"
                ).term_uid,
            ).uid

        service: CriteriaService = CriteriaService()
        payload: CriteriaCreateInput = CriteriaCreateInput(
            criteria_template_uid=criteria_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms or [],
        )

        result: Criteria = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_endpoint(
        cls,
        endpoint_template_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        approve: bool = True,
    ) -> Endpoint:
        if not parameter_terms:
            parameter_terms = []

        if not endpoint_template_uid:
            endpoint_template_uid = cls.create_endpoint_template(
                name="test name",
                guidance_text="guidance text",
                study_uid=None,
                library_name="Sponsor",
                indication_uids=[],
                category_uids=[],
                sub_category_uids=[],
            ).uid

        service: EndpointService = EndpointService()
        payload: EndpointCreateInput = EndpointCreateInput(
            endpoint_template_uid=endpoint_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms,
        )

        result: Endpoint = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_objective(
        cls,
        objective_template_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        approve: bool = True,
    ) -> Objective:
        if not objective_template_uid:
            objective_template_uid = cls.create_objective_template(
                name="test name",
                guidance_text="guidance text",
                study_uid=None,
                library_name="Sponsor",
                indication_uids=[],
                category_uids=[],
            ).uid

        service: ObjectiveService = ObjectiveService()
        payload: ObjectiveCreateInput = ObjectiveCreateInput(
            objective_template_uid=objective_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms,
        )

        result: Objective = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_timeframe(
        cls,
        timeframe_template_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        approve: bool = True,
    ) -> Timeframe:
        if not timeframe_template_uid:
            timeframe_template_uid = cls.create_timeframe_template(
                name="test name",
                guidance_text="guidance text",
                library_name="Sponsor",
            ).uid

        service: TimeframeService = TimeframeService()
        payload: TimeframeCreateInput = TimeframeCreateInput(
            timeframe_template_uid=timeframe_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms,
        )

        result: Timeframe = service.create(payload)  # type: ignore[assignment]
        if approve:
            result = service.approve(result.uid)
        return result

    # endregion

    # region Syntax Pre-Instances

    @classmethod
    def create_activity_instruction_pre_instance(
        cls,
        template_uid: str | None = None,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        indication_uids: list[str] | None = None,
        activity_uids: list[str] | None = None,
        activity_group_uids: list[str] | None = None,
        activity_subgroup_uids: list[str] | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        approve: bool = True,
    ) -> ActivityInstructionPreInstance:
        if not template_uid:
            activity_group_uid = cls.create_activity_group(name="test").uid
            template_uid = cls.create_activity_instruction_template(
                name="name",
                guidance_text="guidance text",
                library_name="Sponsor",
                indication_uids=[],
                activity_uids=[],
                activity_group_uids=[activity_group_uid],
                activity_subgroup_uids=[cls.create_activity_subgroup(name="test").uid],
                approve=False,
            ).uid

        service: ActivityInstructionPreInstanceService = (
            ActivityInstructionPreInstanceService()
        )
        payload: ActivityInstructionPreInstanceCreateInput = (
            ActivityInstructionPreInstanceCreateInput(
                library_name=library_name,
                parameter_terms=parameter_terms,
                indication_uids=indication_uids or [],
                activity_uids=activity_uids or [],
                activity_group_uids=activity_group_uids or [],
                activity_subgroup_uids=activity_subgroup_uids or [],
            )
        )

        result: ActivityInstructionPreInstance = service.create(  # type: ignore[assignment]
            payload, template_uid=template_uid
        )

        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_endpoint_pre_instance(
        cls,
        template_uid: str | None = None,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        indication_uids: list[str] | None = None,
        category_uids: list[str] | None = None,
        sub_category_uids: list[str] | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        approve: bool = True,
    ) -> EndpointPreInstance:
        if not template_uid:
            template_uid = cls.create_endpoint_template(
                name="name",
                guidance_text="guidance text",
                study_uid=None,
                library_name="Sponsor",
                indication_uids=[],
                category_uids=[],
                sub_category_uids=[],
            ).uid

        service: EndpointPreInstanceService = EndpointPreInstanceService()
        payload: EndpointPreInstanceCreateInput = EndpointPreInstanceCreateInput(
            library_name=library_name,
            parameter_terms=parameter_terms,
            indication_uids=indication_uids or [],
            category_uids=category_uids or [],
            sub_category_uids=sub_category_uids or [],
        )

        result: EndpointPreInstance = service.create(payload, template_uid=template_uid)  # type: ignore[assignment]

        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_objective_pre_instance(
        cls,
        template_uid: str | None = None,
        is_confirmatory_testing: bool = False,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        indication_uids: list[str] | None = None,
        category_uids: list[str] | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        approve: bool = True,
    ) -> ObjectivePreInstance:
        if not template_uid:
            template_uid = cls.create_objective_template(
                name="name",
                guidance_text="guidance text",
                study_uid=None,
                library_name="Sponsor",
                indication_uids=[],
                category_uids=[],
            ).uid

        service: ObjectivePreInstanceService = ObjectivePreInstanceService()
        payload: ObjectivePreInstanceCreateInput = ObjectivePreInstanceCreateInput(
            library_name=library_name,
            is_confirmatory_testing=is_confirmatory_testing,
            parameter_terms=parameter_terms,
            indication_uids=indication_uids or [],
            category_uids=category_uids or [],
        )

        result: ObjectivePreInstance = service.create(  # type: ignore[assignment]
            payload, template_uid=template_uid
        )

        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_footnote_pre_instance(
        cls,
        template_uid: str | None = None,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        indication_uids: list[str] | None = None,
        activity_uids: list[str] | None = None,
        activity_group_uids: list[str] | None = None,
        activity_subgroup_uids: list[str] | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        approve: bool = True,
    ) -> FootnotePreInstance:
        if not template_uid:
            activity_group_uid = cls.create_activity_group(name="test").uid
            ct_term = cls.create_ct_term(sponsor_preferred_name="INCLUSION CRITERIA")
            template_uid = cls.create_footnote_template(
                name="name",
                study_uid=None,
                type_uid=ct_term.term_uid,
                library_name="Sponsor",
                indication_uids=[],
                activity_uids=[],
                activity_group_uids=[activity_group_uid],
                activity_subgroup_uids=[cls.create_activity_subgroup(name="test").uid],
            ).uid

        service: FootnotePreInstanceService = FootnotePreInstanceService()
        payload: FootnotePreInstanceCreateInput = FootnotePreInstanceCreateInput(
            library_name=library_name,
            parameter_terms=parameter_terms,
            indication_uids=indication_uids or [],
            activity_uids=activity_uids or [],
            activity_group_uids=activity_group_uids or [],
            activity_subgroup_uids=activity_subgroup_uids or [],
        )

        result: FootnotePreInstance = service.create(payload, template_uid=template_uid)  # type: ignore[assignment]

        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_criteria_pre_instance(
        cls,
        template_uid: str | None = None,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        indication_uids: list[str] | None = None,
        category_uids: list[str] | None = None,
        sub_category_uids: list[str] | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        approve: bool = True,
    ) -> CriteriaPreInstance:
        if not template_uid:
            ct_term = cls.create_ct_term(sponsor_preferred_name="INCLUSION CRITERIA")
            template_uid = cls.create_criteria_template(
                name="name",
                guidance_text="guidance text",
                study_uid=None,
                type_uid=ct_term.term_uid,
                library_name="Sponsor",
                indication_uids=[],
                category_uids=[],
            ).uid

        service: CriteriaPreInstanceService = CriteriaPreInstanceService()
        payload: CriteriaPreInstanceCreateInput = CriteriaPreInstanceCreateInput(
            library_name=library_name,
            parameter_terms=parameter_terms,
            indication_uids=indication_uids or [],
            category_uids=category_uids or [],
            sub_category_uids=sub_category_uids or [],
        )

        result: CriteriaPreInstance = service.create(payload, template_uid=template_uid)  # type: ignore[assignment]

        if approve:
            result = service.approve(result.uid)
        return result

    # endregion

    @classmethod
    def create_compound(
        cls,
        name=None,
        name_sentence_case=None,
        definition=None,
        abbreviation=None,
        library_name=SPONSOR_LIBRARY_NAME,
        external_id=None,
        approve: bool = False,
    ) -> Compound:
        service: CompoundService = CompoundService()
        payload: CompoundCreateInput = CompoundCreateInput(
            name=cls.random_if_none(name, prefix="name-"),
            name_sentence_case=cls.random_if_none(
                name_sentence_case, prefix="name_sentence_case-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbreviation-"),
            library_name=library_name,
            external_id=cls.random_if_none(external_id, prefix="prodex-id-"),
        )

        result: Compound = service.create(payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_compound_alias(
        cls,
        name=None,
        name_sentence_case=None,
        definition=None,
        abbreviation=None,
        library_name=SPONSOR_LIBRARY_NAME,
        is_preferred_synonym=None,
        compound_uid=None,
        approve: bool = False,
    ) -> CompoundAlias:
        service: CompoundAliasService = CompoundAliasService()
        payload: CompoundAliasCreateInput = CompoundAliasCreateInput(
            name=cls.random_if_none(name, prefix="name-"),
            name_sentence_case=cls.random_if_none(
                name_sentence_case, prefix="name_sentence_case-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbreviation-"),
            library_name=library_name,
            is_preferred_synonym=(
                is_preferred_synonym if is_preferred_synonym else False
            ),
            compound_uid=compound_uid if compound_uid else "None",
        )

        result: CompoundAlias = service.create(payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_active_substance(
        cls,
        external_id=None,
        analyte_number=None,
        short_number=None,
        long_number=None,
        inn=None,
        library_name=SPONSOR_LIBRARY_NAME,
        unii_term_uid=None,
        approve: bool = False,
    ) -> ActiveSubstance:
        service: ActiveSubstanceService = ActiveSubstanceService()
        payload: ActiveSubstanceCreateInput = ActiveSubstanceCreateInput(
            external_id=cls.random_if_none(external_id, prefix="prodex-id-"),
            analyte_number=cls.random_if_none(analyte_number, prefix="analyte-"),
            short_number=cls.random_if_none(short_number, prefix="short-number-"),
            long_number=cls.random_if_none(long_number, prefix="long-number-"),
            inn=cls.random_if_none(inn, prefix="inn-"),
            library_name=library_name,
            unii_term_uid=unii_term_uid if unii_term_uid else None,
        )

        result: ActiveSubstance = service.create(payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_pharmaceutical_product(
        cls,
        external_id=None,
        library_name=SPONSOR_LIBRARY_NAME,
        dosage_form_uids=None,
        route_of_administration_uids=None,
        formulations=None,
        approve: bool = False,
    ) -> PharmaceuticalProduct:
        service: PharmaceuticalProductService = PharmaceuticalProductService()
        payload: PharmaceuticalProductCreateInput = PharmaceuticalProductCreateInput(
            external_id=cls.random_if_none(external_id, prefix="prodex-id-"),
            library_name=library_name,
            dosage_form_uids=dosage_form_uids if dosage_form_uids else [],
            route_of_administration_uids=(
                route_of_administration_uids if route_of_administration_uids else []
            ),
            formulations=formulations if formulations else [],
        )

        result: PharmaceuticalProduct = service.create(payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_medicinal_product(
        cls,
        external_id=None,
        name=None,
        name_sentence_case=None,
        library_name=SPONSOR_LIBRARY_NAME,
        dose_value_uids=None,
        dose_frequency_uids=None,
        delivery_device_uid=None,
        dispenser_uid=None,
        pharmaceutical_product_uids=None,
        compound_uid=None,
        approve: bool = False,
    ) -> MedicinalProduct:
        service: MedicinalProductService = MedicinalProductService()
        payload: MedicinalProductCreateInput = MedicinalProductCreateInput(
            name=cls.random_if_none(name, prefix="name-"),
            name_sentence_case=cls.random_if_none(
                name_sentence_case, prefix="name_sentence_case-"
            ),
            external_id=cls.random_if_none(external_id, prefix="prodex-id-"),
            library_name=library_name,
            dose_value_uids=dose_value_uids if dose_value_uids else [],
            dose_frequency_uids=dose_frequency_uids if dose_frequency_uids else [],
            delivery_device_uid=delivery_device_uid,
            dispenser_uid=dispenser_uid,
            pharmaceutical_product_uids=(
                pharmaceutical_product_uids if pharmaceutical_product_uids else []
            ),
            compound_uid=compound_uid if compound_uid else "None",
        )

        result: MedicinalProduct = service.create(payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_activity_instance(
        cls,
        activity_instance_class_uid: str,
        name: str | None = None,
        name_sentence_case: str | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        nci_concept_name: str | None = None,
        nci_concept_id: str | None = None,
        topic_code: str | None = None,
        molecular_weight: float | None = None,
        is_research_lab: bool = False,
        adam_param_code: str | None = None,
        is_required_for_activity: bool = False,
        is_default_selected_for_activity: bool = False,
        is_data_sharing: bool = False,
        is_legacy_usage: bool = False,
        is_derived: bool = False,
        legacy_description: str | None = None,
        activities: list[Any] | None = None,
        activity_subgroups: list[Any] | None = None,
        activity_groups: list[Any] | None = None,
        activity_items: list[Any] | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        approve: bool = True,
        retire_after_approve: bool = False,
        preview=False,
    ) -> ActivityInstance:
        service: ActivityInstanceService = ActivityInstanceService()
        groupings = []
        if activities is None:
            activities = []
        if activity_subgroups is None:
            activity_subgroups = []
        if activity_groups is None:
            activity_groups = []
        for activity_uid, activity_subgroup_uid, activity_group_uid in zip(
            activities, activity_subgroups, activity_groups
        ):
            activity_grouping: ActivityInstanceGrouping = ActivityInstanceGrouping(
                activity_uid=activity_uid,
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
            )
            groupings.append(activity_grouping)

        activity_instance_input: ActivityInstanceCreateInput = (
            ActivityInstanceCreateInput(
                nci_concept_id=nci_concept_id,
                nci_concept_name=nci_concept_name,
                name=name,
                name_sentence_case=name_sentence_case,
                definition=definition,
                abbreviation=abbreviation,
                topic_code=topic_code,
                molecular_weight=molecular_weight,
                is_research_lab=is_research_lab,
                adam_param_code=adam_param_code,
                is_required_for_activity=is_required_for_activity,
                is_default_selected_for_activity=is_default_selected_for_activity,
                is_data_sharing=is_data_sharing,
                is_legacy_usage=is_legacy_usage,
                is_derived=is_derived,
                legacy_description=legacy_description,
                activity_groupings=groupings,
                activity_instance_class_uid=activity_instance_class_uid,
                activity_items=activity_items if activity_items else [],
                library_name=library_name,
            )
        )
        result: ActivityInstance = service.create(  # type: ignore[assignment]
            concept_input=activity_instance_input, preview=preview
        )
        if approve and not preview:
            groupings_service = ActivityInstanceGroupingsService()
            service.approve(result.uid)
            groupings_service.approve(result.uid)
            if retire_after_approve:
                service.inactivate_final(result.uid)
                groupings_service.inactivate_final(result.uid)
        return result

    @classmethod
    def create_activity_instance_class(
        cls,
        name: str,
        order: int | None = None,
        definition: str | None = None,
        is_domain_specific: bool = False,
        level: int | None = None,
        nci_concept_id: str | None = None,
        nci_concept_name: str | None = None,
        parent_uid: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        approve: bool = True,
    ) -> ActivityInstanceClass:
        service: ActivityInstanceClassService = ActivityInstanceClassService()
        activity_instance_class_input: ActivityInstanceClassInput = (
            ActivityInstanceClassInput(
                name=name,
                order=order,
                definition=definition,
                is_domain_specific=is_domain_specific,
                level=level,
                nci_concept_id=nci_concept_id,
                nci_concept_name=nci_concept_name,
                parent_uid=parent_uid,
                library_name=library_name,
            )
        )
        result: ActivityInstanceClass = service.create(
            item_input=activity_instance_class_input
        )
        if approve and result.uid is not None:
            service.approve(result.uid)
        return result

    @classmethod
    def create_activity_item_class(
        cls,
        name: str,
        order: int,
        role_uid: str,
        data_type_uid: str,
        activity_instance_classes: list[ActivityInstanceClassRelInput],
        definition: str | None = None,
        display_name: str | None = None,
        nci_concept_id: str | None = None,
        nci_concept_name: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        non_standard_variable: NonStandardVariableInput | None = None,
        valid_codelist_uids: list[str] | None = None,
        approve: bool = True,
    ) -> ActivityItemClass:
        service: ActivityItemClassService = ActivityItemClassService()
        activity_item_class_input: ActivityItemClassCreateInput = (
            ActivityItemClassCreateInput(
                name=name,
                definition=definition,
                display_name=display_name,
                nci_concept_id=nci_concept_id,
                nci_concept_name=nci_concept_name,
                order=order,
                role_uid=role_uid,
                data_type_uid=data_type_uid,
                activity_instance_classes=activity_instance_classes,
                library_name=library_name,
                non_standard_variable=non_standard_variable,
                valid_codelist_uids=valid_codelist_uids,
            )
        )
        result: ActivityItemClass = service.create(concept_input=activity_item_class_input)  # type: ignore[assignment]
        if approve and result.uid is not None:
            service.approve(result.uid)
        return result

    @classmethod
    def create_activity(
        cls,
        name: str,
        name_sentence_case: str | None = None,
        nci_concept_id: str | None = None,
        nci_concept_name: str | None = None,
        synonyms: list[str] | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        activity_subgroups: list[str] | None = None,
        activity_groups: list[str] | None = None,
        request_rationale: str | None = None,
        is_request_final: bool = False,
        is_data_collected: bool = True,
        is_multiple_selection_allowed: bool = True,
        library_name: str = SPONSOR_LIBRARY_NAME,
        approve: bool = True,
    ) -> Activity:
        service: ActivityService = ActivityService()
        groupings = []
        if not synonyms:
            synonyms = []
        if not activity_subgroups:
            activity_subgroups = []
        if not activity_groups:
            activity_groups = []
        for activity_subgroup_uid, activity_group_uid in zip(
            activity_subgroups, activity_groups
        ):
            activity_grouping: ActivityGrouping = ActivityGrouping(
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
            )
            groupings.append(activity_grouping)
        activity_create_input: ActivityCreateInput = ActivityCreateInput(
            nci_concept_id=nci_concept_id,
            nci_concept_name=nci_concept_name,
            synonyms=synonyms,
            name=name,
            name_sentence_case=name_sentence_case if name_sentence_case else name,
            definition=definition,
            abbreviation=abbreviation,
            activity_groupings=groupings,
            request_rationale=request_rationale,
            is_request_final=is_request_final,
            is_data_collected=is_data_collected,
            is_multiple_selection_allowed=is_multiple_selection_allowed,
            library_name=library_name,
        )
        result: Activity = service.create(concept_input=activity_create_input)  # type: ignore[assignment]
        if approve:
            return service.approve(result.uid)
        return result

    @classmethod
    def create_activity_subgroup(
        cls,
        name: str,
        name_sentence_case: str | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        nci_concept_id: str | None = None,
        nci_concept_name: str | None = None,
        approve: bool = True,
    ) -> ActivitySubGroup:
        service: ActivitySubGroupService = ActivitySubGroupService()
        activity_subgroup_create_input: ActivitySubGroupCreateInput = (
            ActivitySubGroupCreateInput(
                name=name,
                name_sentence_case=name_sentence_case if name_sentence_case else name,
                definition=definition,
                abbreviation=abbreviation,
                library_name=library_name,
                nci_concept_id=nci_concept_id,
                nci_concept_name=nci_concept_name,
            )
        )
        result: ActivitySubGroup = service.create(  # type: ignore[assignment]
            concept_input=activity_subgroup_create_input
        )
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_activity_group(
        cls,
        name: str,
        name_sentence_case: str | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        nci_concept_id: str | None = None,
        nci_concept_name: str | None = None,
        approve: bool = True,
    ) -> ActivityGroup:
        service: ActivityGroupService = ActivityGroupService()
        activity_group_create_input: ActivityGroupCreateInput = (
            ActivityGroupCreateInput(
                name=name,
                name_sentence_case=name_sentence_case if name_sentence_case else name,
                definition=definition,
                abbreviation=abbreviation,
                library_name=library_name,
                nci_concept_id=nci_concept_id,
                nci_concept_name=nci_concept_name,
            )
        )
        result: ActivityGroup = service.create(  # type: ignore[assignment]
            concept_input=activity_group_create_input
        )
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_study_activity(
        cls,
        study_uid: str,
        soa_group_term_uid: str,
        activity_uid: str,
        activity_subgroup_uid: str | None = None,
        activity_group_uid: str | None = None,
        activity_instance_uid: str | None = None,
    ) -> StudySelectionActivity:
        service: StudyActivitySelectionService = StudyActivitySelectionService()
        study_activity: StudySelectionActivity = service.make_selection(
            study_uid=study_uid,
            selection_create_input=StudySelectionActivityCreateInput(
                soa_group_term_uid=soa_group_term_uid,
                activity_uid=activity_uid,
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
                activity_instance_uid=activity_instance_uid,
            ),
        )
        return study_activity

    @staticmethod
    def patch_study_activity_instance(
        study_uid: str,
        study_activity_instance_uid: str,
        activity_instance_uid: str,
        study_activity_uid: str,
        show_activity_instance_in_protocol_flowchart: bool = False,
    ):
        return StudyActivityInstanceSelectionService().patch_selection(
            study_uid=study_uid,
            study_selection_uid=study_activity_instance_uid,
            selection_update_input=StudySelectionActivityInstanceEditInput(
                activity_instance_uid=activity_instance_uid,
                study_activity_uid=study_activity_uid,
                show_activity_instance_in_protocol_flowchart=show_activity_instance_in_protocol_flowchart,
            ),
        )

    @staticmethod
    def batch_select_study_activity_instances(
        study_uid: str,
        study_activity_uid: str,
        activity_instance_uids: list[str],
    ):
        return StudyActivityInstanceSelectionService().handle_batch_operations(
            study_uid=study_uid,
            operations=[
                StudySelectionActivityInstanceBatchInput(
                    method="POST",
                    content=StudySelectionActivityInstanceCreateInput(
                        study_activity_uid=study_activity_uid,
                        activity_instance_uid=activity_instance_uid,
                    ),
                )
                for activity_instance_uid in activity_instance_uids
            ],
        )

    @classmethod
    def delete_study(cls, study_uid: str):
        StudyService().soft_delete(uid=study_uid)

    @classmethod
    def create_study_activity_schedule(
        cls,
        study_uid: str,
        study_visit_uid: str,
        study_activity_uid: str,
    ) -> StudyActivitySchedule:
        service: StudyActivityScheduleService = StudyActivityScheduleService()
        study_activity_schedule: StudyActivityScheduleCreateInput = (
            StudyActivityScheduleCreateInput(
                study_activity_uid=study_activity_uid,
                study_visit_uid=study_visit_uid,
            )
        )
        schedule = service.create(
            study_uid=study_uid,
            schedule_input=study_activity_schedule,
        )
        return schedule

    @classmethod
    def patch_study_activity_schedule(
        cls,
        study_uid: str,
        study_selection_uid: str,
        show_activity_in_protocol_flowchart: bool = False,
        soa_group_term_uid: str | None = None,
    ) -> StudyActivitySchedule:
        service: StudyActivitySelectionService = StudyActivitySelectionService()
        update = StudySelectionActivityInput(
            show_activity_in_protocol_flowchart=show_activity_in_protocol_flowchart,
            soa_group_term_uid=soa_group_term_uid,
        )
        schedule = service.patch_selection(
            study_uid=study_uid,
            study_selection_uid=study_selection_uid,
            selection_update_input=update,
        )
        return schedule

    @classmethod
    def create_study_soa_footnote(
        cls,
        study_uid: str,
        referenced_items: list[ReferencedItem],
        footnote_uid: str | None = None,
        footnote_template_uid: str | None = None,
    ) -> StudySoAFootnote:
        if not any((footnote_uid, footnote_template_uid)):
            raise ValueError(
                "At least one of footnote_uid or footnote_template_uid must be provided"
            )
        service: StudySoAFootnoteService = StudySoAFootnoteService()
        study_soa_footnote_input: StudySoAFootnoteCreateInput = (
            StudySoAFootnoteCreateInput(
                footnote_uid=footnote_uid,
                footnote_template_uid=footnote_template_uid,
                referenced_items=referenced_items,
            )
        )
        soa_footnote = service.create(
            study_uid=study_uid,
            footnote_input=study_soa_footnote_input,
            create_footnote=False,
        )
        return soa_footnote

    @classmethod
    def create_study_visit(
        cls,
        study_uid: str,
        study_epoch_uid: str | None = None,
        # Flat UID params (for explicit callers)
        visit_type_uid: str | None = None,
        visit_contact_mode_uid: str | None = None,
        time_reference_uid: str | None = None,
        epoch_allocation_uid: str | None = None,
        # Nested CT term params (for **datadict unpacking)
        visit_type: dict | CTTermUidInput | None = None,
        visit_contact_mode: dict | CTTermUidInput | None = None,
        time_reference: dict | CTTermUidInput | None = None,
        epoch_allocation: dict | CTTermUidInput | None = None,
        # Common params
        show_visit: bool = True,
        visit_class: VisitClass = "SINGLE_VISIT",  # type: ignore[assignment]
        is_global_anchor_visit: bool = False,
        time_value: int | None = None,
        time_unit_uid: str | None = None,
        visit_sublabel_reference: str | None = None,
        min_visit_window_value: int | None = None,
        max_visit_window_value: int | None = None,
        visit_window_unit_uid: str | None = None,
        description: str | None = None,
        start_rule: str | None = None,
        end_rule: str | None = None,
        visit_subclass: VisitSubclass | None = None,
    ) -> StudyVisit:
        # Resolve CT term fields: prefer nested object, fall back to flat UID
        _visit_type = _resolve_ct_term(visit_type, visit_type_uid)
        _visit_contact_mode = _resolve_ct_term(
            visit_contact_mode, visit_contact_mode_uid
        )
        _time_reference = _resolve_ct_term(time_reference, time_reference_uid)
        _epoch_allocation = _resolve_ct_term(epoch_allocation, epoch_allocation_uid)

        service: StudyVisitService = StudyVisitService(study_uid=study_uid)
        study_visit_input: StudyVisitCreateInput = StudyVisitCreateInput(
            study_epoch_uid=study_epoch_uid,
            visit_type=_visit_type,  # type: ignore[arg-type]
            time_reference=_time_reference,
            time_value=time_value,
            time_unit_uid=time_unit_uid,
            visit_sublabel_reference=visit_sublabel_reference,
            show_visit=show_visit,
            min_visit_window_value=min_visit_window_value,
            max_visit_window_value=max_visit_window_value,
            visit_window_unit_uid=visit_window_unit_uid,
            description=description,
            start_rule=start_rule,
            end_rule=end_rule,
            visit_contact_mode=_visit_contact_mode,  # type: ignore[arg-type]
            epoch_allocation=_epoch_allocation,
            visit_class=visit_class,
            visit_subclass=visit_subclass,
            is_global_anchor_visit=is_global_anchor_visit,
        )
        study_visit = service.create(
            study_uid=study_uid,
            study_visit_input=study_visit_input,
        )
        return study_visit

    # region Study selection
    @classmethod
    def _complete_parameter_terms(
        cls, parameter_terms: list[TemplateParameterMultiSelectInput]
    ):
        for value in parameter_terms:
            if value.conjunction is None:
                value.conjunction = ""
        return parameter_terms

    @classmethod
    def create_study_objective(
        cls,
        study_uid: str,
        objective_template_uid: str,
        library_name: str = SPONSOR_LIBRARY_NAME,
        objective_level_uid: str | None = None,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
    ) -> StudySelectionObjective:
        if not parameter_terms:
            parameter_terms = []

        service: StudyObjectiveSelectionService = StudyObjectiveSelectionService()
        objective_create_input: StudySelectionObjectiveCreateInput = (
            StudySelectionObjectiveCreateInput(
                objective_level_uid=objective_level_uid,
                objective_data=ObjectiveCreateInput(
                    objective_template_uid=objective_template_uid,
                    library_name=library_name,
                    parameter_terms=cls._complete_parameter_terms(parameter_terms),
                ),
            )
        )

        result: StudySelectionObjective = service.make_selection_create_objective(
            study_uid=study_uid, selection_create_input=objective_create_input
        )
        return result

    @classmethod
    def create_study_endpoint(
        cls,
        study_uid: str,
        endpoint_template_uid: str,
        library_name: str = SPONSOR_LIBRARY_NAME,
        study_objective_uid: str | None = None,
        endpoint_level_uid: str | None = None,
        endpoint_sublevel_uid: str | None = None,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        endpoint_units: EndpointUnitsInput | None = None,
        timeframe_uid: str | None = None,
    ) -> StudySelectionEndpoint:
        service: StudyEndpointSelectionService = StudyEndpointSelectionService()
        if parameter_terms is None:
            parameter_terms = []
        endpoint_create_input: StudySelectionEndpointCreateInput = (
            StudySelectionEndpointCreateInput(
                study_objective_uid=study_objective_uid,
                endpoint_level_uid=endpoint_level_uid,
                endpoint_sublevel_uid=endpoint_sublevel_uid,
                endpoint_data=EndpointCreateInput(
                    endpoint_template_uid=endpoint_template_uid,
                    library_name=library_name,
                    parameter_terms=cls._complete_parameter_terms(parameter_terms),
                ),
                endpoint_units=endpoint_units,
                timeframe_uid=timeframe_uid,
            )
        )

        result: StudySelectionEndpoint = service.make_selection_create_endpoint(
            study_uid=study_uid, selection_create_input=endpoint_create_input
        )
        return result

    @classmethod
    def create_study_criteria(
        cls,
        study_uid: str,
        criteria_template_uid: str,
        library_name: str = SPONSOR_LIBRARY_NAME,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
    ) -> StudySelectionCriteria:
        service: StudyCriteriaSelectionService = StudyCriteriaSelectionService()
        if parameter_terms is None:
            parameter_terms = []
        criteria_create_input: StudySelectionCriteriaCreateInput = (
            StudySelectionCriteriaCreateInput(
                criteria_data=CriteriaCreateInput(
                    criteria_template_uid=criteria_template_uid,
                    library_name=library_name,
                    parameter_terms=cls._complete_parameter_terms(parameter_terms),
                )
            )
        )

        result: StudySelectionCriteria = service.make_selection_create_criteria(
            study_uid=study_uid, selection_create_input=criteria_create_input
        )
        return result

    @classmethod
    def create_study_objective_and_endpoint_with_ct_levels(
        cls,
        study_uid: str,
        objective_level_uid: str,
        endpoint_level_uid: str,
    ) -> tuple[StudySelectionObjective, StudySelectionEndpoint]:
        """
        Create study objective and linked endpoint with CT objective/endpoint levels via
        selection services (same path as product API). Call while the study is still open
        before locking so the selections are included in the released study value used
        by consumer papillons study-metadata.
        """
        objective_template = cls.create_objective_template(
            name="Consumer study-metadata objective template",
            guidance_text="Objective template for consumer study-metadata tests",
        )
        study_objective = cls.create_study_objective(
            study_uid=study_uid,
            objective_template_uid=objective_template.uid,
            library_name=objective_template.library.name,
            objective_level_uid=objective_level_uid,
        )
        cls.create_template_parameter(settings.study_endpoint_tp_name)
        endpoint_template = cls.create_endpoint_template(
            name="Consumer study-metadata endpoint template",
            guidance_text="Endpoint template for consumer study-metadata tests",
        )
        unit_definition = cls.create_unit_definition(
            name="consumer-study-metadata-endpoint-unit"
        )
        timeframe_template = cls.create_timeframe_template(
            name="Consumer study-metadata timeframe template",
            guidance_text="Timeframe for consumer study-metadata tests",
        )
        timeframe = cls.create_timeframe(timeframe_template_uid=timeframe_template.uid)
        study_endpoint = cls.create_study_endpoint(
            study_uid=study_uid,
            endpoint_template_uid=endpoint_template.uid,
            library_name=endpoint_template.library.name,
            study_objective_uid=study_objective.study_objective_uid,
            endpoint_level_uid=endpoint_level_uid,
            endpoint_units=EndpointUnitsInput(units=[unit_definition.uid]),
            timeframe_uid=timeframe.uid,
        )
        return study_objective, study_endpoint

    @classmethod
    def patch_study_core_ct_text_fields_via_api(
        cls,
        study_uid: str,
        *,
        study_type_term_uid: str | None = None,
        intervention_type_term_uid: str | None = None,
        sex_of_participants_term_uid: str | None = None,
    ) -> Study:
        """
        Patch study_type_code, intervention_type_code, and sex_of_participants_code via
        StudyService (same path as PATCH /studies). Use before locking so consumer
        study-metadata date-conflict tests see CT-backed fields on the released snapshot.

        Defaults use term UIDs from ``initialize_ct_data_map`` (created by
        ``create_study_ct_data_map``), each on the correct configured codelist.
        """
        st_uid = study_type_term_uid or initialize_ct_data_map["StudyType"][0][0]
        int_uid = (
            intervention_type_term_uid
            or initialize_ct_data_map["InterventionType"][0][0]
        )
        sex_uid = (
            sex_of_participants_term_uid
            or initialize_ct_data_map["SexOfParticipants"][0][0]
        )
        return StudyService().patch(
            uid=study_uid,
            dry=False,
            study_patch_request=StudyPatchRequestJsonModel(
                current_metadata=StudyMetadataJsonModel(
                    high_level_study_design=HighLevelStudyDesignJsonModel(
                        study_type_code=SimpleCTTermNameWithConflictFlag(
                            term_uid=st_uid
                        )
                    ),
                    study_intervention=StudyInterventionJsonModel(
                        intervention_type_code=SimpleCTTermNameWithConflictFlag(
                            term_uid=int_uid
                        )
                    ),
                    study_population=StudyPopulationJsonModel(
                        sex_of_participants_code=SimpleCTTermNameWithConflictFlag(
                            term_uid=sex_uid
                        )
                    ),
                )
            ),
        )

    @classmethod
    def create_study_compound(
        cls,
        study_uid: str,
        medicinal_product_uid=None,
        compound_alias_uid=None,
        type_of_treatment_uid=None,
        other_info=None,
        reason_for_missing_null_value_uid=None,
    ) -> StudySelectionCompound:
        service: StudyCompoundSelectionService = StudyCompoundSelectionService()
        payload: StudySelectionCompoundCreateInput = StudySelectionCompoundCreateInput(
            medicinal_product_uid=medicinal_product_uid,
            compound_alias_uid=compound_alias_uid,
            type_of_treatment_uid=type_of_treatment_uid,
            other_info=cls.random_if_none(other_info, prefix="other_info-"),
            reason_for_missing_null_value_uid=reason_for_missing_null_value_uid,
        )

        result: StudySelectionCompound = service.make_selection(
            study_uid=study_uid, selection_create_input=payload
        )
        return result

    @classmethod
    def create_study_compound_dosing(
        cls,
        study_uid: str,
        study_compound_uid=None,
        study_element_uid=None,
        dose_value_uid=None,
        dose_frequency_uid=None,
    ) -> StudyCompoundDosing:
        service: StudyCompoundDosingSelectionService = (
            StudyCompoundDosingSelectionService()
        )
        payload: StudyCompoundDosingInput = StudyCompoundDosingInput(
            study_compound_uid=study_compound_uid,
            study_element_uid=study_element_uid,
            dose_value_uid=dose_value_uid,
            dose_frequency_uid=dose_frequency_uid,
        )

        result: StudyCompoundDosing = service.make_selection(
            study_uid=study_uid, selection_create_input=payload
        )
        return result

    @classmethod
    def create_study_element(
        cls,
        study_uid: str,
        name=None,
        short_name=None,
        code=None,
        description=None,
        planned_duration=None,
        start_rule=None,
        end_rule=None,
        element_colour=None,
        element_subtype_uid=None,
    ) -> StudySelectionElement:
        service: StudyElementSelectionService = StudyElementSelectionService()
        payload: StudySelectionElementCreateInput = StudySelectionElementCreateInput(
            name=name,
            short_name=short_name,
            code=code,
            description=description,
            planned_duration=planned_duration,
            start_rule=start_rule,
            end_rule=end_rule,
            element_colour=element_colour,
            element_subtype_uid=element_subtype_uid,
        )

        result: StudySelectionElement = service.make_selection(
            study_uid=study_uid, selection_create_input=payload
        )
        return result

    # endregion

    @classmethod
    def create_unit_definition(
        cls,
        name=None,
        library_name=SPONSOR_LIBRARY_NAME,
        convertible_unit=False,
        display_unit=True,
        master_unit=False,
        si_unit=False,
        us_conventional_unit=False,
        use_complex_unit_conversion=False,
        ct_units=None,
        unit_subsets=None,
        ucum=None,
        unit_dimension=None,
        legacy_code=None,
        use_molecular_weight=False,
        conversion_factor_to_master=0.001,
        comment=None,
        order=None,
        definition=None,
        template_parameter=False,
        approve: bool = True,
    ) -> UnitDefinitionModel:
        service: UnitDefinitionService = UnitDefinitionService()

        payload: UnitDefinitionPostInput = UnitDefinitionPostInput(
            name=name,
            library_name=library_name,
            convertible_unit=convertible_unit,
            display_unit=display_unit,
            master_unit=master_unit,
            si_unit=si_unit,
            us_conventional_unit=us_conventional_unit,
            use_complex_unit_conversion=use_complex_unit_conversion,
            ct_units=ct_units if ct_units else [],
            unit_subsets=unit_subsets if unit_subsets else [],
            ucum=ucum,
            unit_dimension=unit_dimension,
            legacy_code=legacy_code,
            use_molecular_weight=use_molecular_weight,
            conversion_factor_to_master=conversion_factor_to_master,
            comment=comment,
            order=order,
            definition=definition,
            template_parameter=template_parameter,
        )

        result: UnitDefinitionModel = service.create(concept_input=payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_odm_study_event(
        cls,
        name=None,
        library_name=SPONSOR_LIBRARY_NAME,
        oid: str | None = None,
        effective_date: date | None = None,
        retired_date: date | None = None,
        description: str | None = None,
        display_in_tree: bool = True,
        approve: bool = True,
    ) -> OdmStudyEvent:

        service: OdmStudyEventService = OdmStudyEventService()

        payload: OdmStudyEventPostInput = OdmStudyEventPostInput(
            library_name=library_name,
            name=cls.random_if_none(name),
            oid=cls.random_if_none(oid),
            effective_date=effective_date,
            retired_date=retired_date,
            description=description,
            display_in_tree=display_in_tree,
        )

        result: OdmStudyEvent = service.create(odm_input=payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_odm_form(
        cls,
        name=None,
        library_name=SPONSOR_LIBRARY_NAME,
        oid=None,
        repeating="Yes",
        sdtm_version=None,
        translated_texts: list[OdmTranslatedTextModel] | None = None,
        aliases: list[OdmAliasModel] | None = None,
        approve: bool = True,
    ) -> OdmForm:
        if not translated_texts:
            translated_texts = []
        if not aliases:
            aliases = []

        service: OdmFormService = OdmFormService()

        payload: OdmFormPostInput = OdmFormPostInput(
            library_name=library_name,
            name=cls.random_if_none(name),
            oid=cls.random_if_none(oid),
            repeating=repeating,
            sdtm_version=cls.random_if_none(sdtm_version),
            translated_texts=translated_texts,
            aliases=aliases,
        )

        result: OdmForm = service.create(odm_input=payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_odm_item_group(
        cls,
        name=None,
        library_name=SPONSOR_LIBRARY_NAME,
        oid=None,
        repeating="Yes",
        is_reference_data=None,
        sas_dataset_name=None,
        origin=None,
        purpose=None,
        comment=None,
        translated_texts: list[OdmTranslatedTextModel] | None = None,
        aliases: list[OdmAliasModel] | None = None,
        sdtm_domain_uids=None,
        approve: bool = True,
    ) -> OdmItemGroup:
        if not translated_texts:
            translated_texts = []
        if not aliases:
            aliases = []
        if not sdtm_domain_uids:
            sdtm_domain_uids = []

        service: OdmItemGroupService = OdmItemGroupService()

        payload: OdmItemGroupPostInput = OdmItemGroupPostInput(
            library_name=library_name,
            name=cls.random_if_none(name),
            oid=cls.random_if_none(oid),
            repeating=repeating,
            is_reference_data=is_reference_data,
            sas_dataset_name=cls.random_if_none(sas_dataset_name),
            origin=cls.random_if_none(origin),
            purpose=cls.random_if_none(purpose),
            comment=cls.random_if_none(comment),
            translated_texts=translated_texts,
            aliases=aliases,
            sdtm_domain_uids=sdtm_domain_uids,
        )

        result: OdmItemGroup = service.create(odm_input=payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_odm_item(
        cls,
        name=None,
        library_name=SPONSOR_LIBRARY_NAME,
        oid=None,
        datatype_uid=None,
        prompt=None,
        length=None,
        significant_digits=None,
        sas_field_name=None,
        sds_var_name=None,
        origin=None,
        comment=None,
        translated_texts: list[OdmTranslatedTextModel] | None = None,
        aliases: list[OdmAliasModel] | None = None,
        codelist: OdmItemCodelist | None = None,
        unit_definitions=None,
        terms=None,
        approve: bool = True,
    ) -> OdmItem:
        if not terms:
            terms = []
        if not translated_texts:
            translated_texts = []
        if not unit_definitions:
            unit_definitions = []
        if not aliases:
            aliases = []

        service: OdmItemService = OdmItemService()

        payload: OdmItemPostInput = OdmItemPostInput(
            library_name=library_name,
            name=cls.random_if_none(name),
            oid=cls.random_if_none(oid),
            datatype_uid=datatype_uid or "string_uid",
            prompt=cls.random_if_none(prompt),
            length=length,
            significant_digits=significant_digits,
            sas_field_name=cls.random_if_none(sas_field_name),
            sds_var_name=cls.random_if_none(sds_var_name),
            origin=cls.random_if_none(origin),
            comment=cls.random_if_none(comment),
            translated_texts=translated_texts,
            aliases=aliases,
            codelist=codelist,
            unit_definitions=unit_definitions,
            terms=terms,
        )

        result: OdmItem = service.create(odm_input=payload)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_odm_condition(
        cls,
        name=None,
        library_name=SPONSOR_LIBRARY_NAME,
        oid=None,
        formal_expressions: list[OdmFormalExpressionModel] | None = None,
        translated_texts: list[OdmTranslatedTextModel] | None = None,
        aliases: list[OdmAliasModel] | None = None,
        approve: bool = True,
    ) -> OdmCondition:
        if not formal_expressions:
            formal_expressions = []
        if not translated_texts:
            translated_texts = []
        if not aliases:
            aliases = []

        service: OdmConditionService = OdmConditionService()

        payload: OdmConditionPostInput = OdmConditionPostInput(
            library_name=library_name,
            name=cls.random_if_none(name),
            oid=cls.random_if_none(oid),
            formal_expressions=formal_expressions,
            translated_texts=translated_texts,
            aliases=aliases,
        )

        result: OdmCondition = service.create(odm_input=payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_odm_method(
        cls,
        name=None,
        library_name=SPONSOR_LIBRARY_NAME,
        oid=None,
        method_type=None,
        formal_expressions: list[OdmFormalExpressionModel] | None = None,
        translated_texts: list[OdmTranslatedTextModel] | None = None,
        aliases: list[OdmAliasModel] | None = None,
        approve: bool = True,
    ) -> OdmMethod:
        if not formal_expressions:
            formal_expressions = []
        if not translated_texts:
            translated_texts = []
        if not aliases:
            aliases = []

        service: OdmMethodService = OdmMethodService()

        payload: OdmMethodPostInput = OdmMethodPostInput(
            library_name=library_name,
            name=cls.random_if_none(name),
            oid=cls.random_if_none(oid),
            method_type=method_type,
            formal_expressions=formal_expressions,
            translated_texts=translated_texts,
            aliases=aliases,
        )

        result: OdmMethod = service.create(odm_input=payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_odm_vendor_namespace(
        cls,
        name=None,
        library_name=SPONSOR_LIBRARY_NAME,
        prefix=None,
        url=None,
        approve: bool = True,
    ) -> OdmVendorNamespace:
        service: OdmVendorNamespaceService = OdmVendorNamespaceService()

        payload: OdmVendorNamespacePostInput = OdmVendorNamespacePostInput(
            library_name=library_name,
            name=cls.random_if_none(name),
            prefix=prefix,
            url=url,
        )

        result: OdmVendorNamespace = service.create(odm_input=payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_odm_vendor_element(
        cls,
        name=None,
        library_name=SPONSOR_LIBRARY_NAME,
        compatible_types=None,
        vendor_namespace_uid=None,
        approve: bool = True,
    ) -> OdmVendorElement:
        if not compatible_types:
            compatible_types = []

        service: OdmVendorElementService = OdmVendorElementService()

        payload: OdmVendorElementPostInput = OdmVendorElementPostInput(
            library_name=library_name,
            name=cls.random_if_none(name),
            compatible_types=compatible_types,
            vendor_namespace_uid=vendor_namespace_uid,
        )

        result: OdmVendorElement = service.create(odm_input=payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_odm_vendor_attribute(
        cls,
        name=None,
        library_name=SPONSOR_LIBRARY_NAME,
        compatible_types=None,
        data_type=None,
        value_regex=None,
        vendor_namespace_uid=None,
        vendor_element_uid=None,
        approve: bool = True,
    ) -> OdmVendorAttribute:
        if not compatible_types:
            compatible_types = []

        service: OdmVendorAttributeService = OdmVendorAttributeService()

        payload: OdmVendorAttributePostInput = OdmVendorAttributePostInput(
            library_name=library_name,
            name=cls.random_if_none(name),
            compatible_types=compatible_types,
            data_type=data_type,
            value_regex=value_regex,
            vendor_namespace_uid=vendor_namespace_uid,
            vendor_element_uid=vendor_element_uid,
        )

        result: OdmVendorAttribute = service.create(odm_input=payload)  # type: ignore[assignment]
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_library(
        cls, name: str = SPONSOR_LIBRARY_NAME, is_editable: bool = True
    ) -> dict[str, str | bool]:
        libraries = library_service.get_libraries(is_editable)
        existing_library = next((x for x in libraries if x["name"] == name), None)

        if not existing_library:
            return library_service.create(name, is_editable)
        return existing_library

    @classmethod
    def edit_library_editable(cls, name: str, is_editable: bool) -> None:
        """Toggle the is_editable flag of a Library node.

        This is sometimes needed because certain libraries (e.g. CDISC) are set to
        is_editable=True in tests for convenience, whereas in production they are
        is_editable=False. Use this helper to restore the realistic state when a test
        requires non-editable library behaviour.
        """
        db.cypher_query(
            "MATCH (n:Library {name: $name}) SET n.is_editable=$is_editable",
            {"name": name, "is_editable": is_editable},
        )

    @classmethod
    def create_project(
        cls,
        name="Project ABC",
        project_number=PROJECT_NUMBER,
        description="Base project",
        clinical_programme_uid=None,
    ) -> Project:
        service: ProjectService = ProjectService()
        payload = ProjectCreateInput(
            name=name,
            project_number=project_number,
            description=description,
            clinical_programme_uid=clinical_programme_uid,
        )
        return service.create(payload)

    @classmethod
    def create_clinical_programme(cls, name: str = "CP") -> ClinicalProgramme:
        service: ClinicalProgrammeService = ClinicalProgrammeService()
        return service.create(ClinicalProgrammeInput(name=name))

    @classmethod
    def get_study_number(cls, number: str | None = None):
        if number:
            return number
        cls.sequential_study_number += 1
        return str(cls.sequential_study_number)

    @classmethod
    def create_study(
        cls,
        number: str | None = None,
        acronym: str | None = None,
        subpart_acronym: str | None = None,
        project_number: str = PROJECT_NUMBER,
        description: str | None = None,
        study_parent_part_uid: str | None = None,
    ) -> Study:
        service: StudyService = StudyService()
        if not study_parent_part_uid:
            payload = StudyCreateInput(
                study_number=cls.get_study_number(number),
                study_acronym=cls.random_if_none(acronym, prefix="st-"),
                project_number=project_number,
                description=cls.random_if_none(description),
            )
        else:
            payload = StudySubpartCreateInput(  # type: ignore[assignment]
                study_subpart_acronym=cls.random_if_none(
                    subpart_acronym, length=6, prefix="SUB"
                ),
                description=cls.random_if_none(description),
                study_parent_part_uid=study_parent_part_uid,
            )
        return service.create(payload)

    @classmethod
    def patch_study(
        cls,
        uid: str,
        study_parent_part_uid: str | None = None,
        dry: bool = False,
        **kwargs,
    ) -> Study:
        study_service: StudyService = StudyService()

        payload = StudyPatchRequestJsonModel(
            study_parent_part_uid=study_parent_part_uid,
            current_metadata=StudyMetadataJsonModel(
                identification_metadata=StudyIdentificationMetadataJsonModel(**kwargs)
            ),
        )

        return study_service.patch(uid=uid, dry=dry, study_patch_request=payload)

    @classmethod
    def create_study_standard_version(
        cls,
        study_uid: str,
        ct_package_uid: str,
    ) -> Study:
        service: StudyStandardVersionService = StudyStandardVersionService()
        payload = StudyStandardVersionInput(
            ct_package_uid=ct_package_uid,
        )
        return service.create(study_uid=study_uid, study_standard_version_input=payload)

    @classmethod
    def create_ct_term(
        cls,
        catalogue_name: str = CT_CATALOGUE_NAME,
        codelist_uid: str = CT_CODELIST_UIDS.default,
        submission_value: str | None = None,
        nci_preferred_name: str | None = None,
        definition: str | None = None,
        sponsor_preferred_name: str | None = None,
        sponsor_preferred_name_sentence_case: str | None = None,
        order: int | None = None,
        ordinal: float | None = None,
        library_name: str = CT_CODELIST_LIBRARY_SPONSOR,
        approve: bool = True,
        effective_date: datetime | None = None,
        term_uid: str | None = None,
        concept_id: str | None = None,
    ) -> CTTerm:
        service: CTTermService = CTTermService()
        if submission_value is None:
            submission_value = cls.random_str(length=6, prefix="submission_value-")
        codelists = [
            CTTermCodelistInput(
                codelist_uid=codelist_uid,
                submission_value=submission_value,
                order=order,
                ordinal=ordinal,
            )
        ]
        payload = CTTermCreateInput(
            catalogue_names=[catalogue_name],
            codelists=codelists,
            nci_preferred_name=cls.random_if_none(
                nci_preferred_name, prefix="nci_name-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            sponsor_preferred_name=cls.random_if_none(
                sponsor_preferred_name, prefix="name-"
            ),
            sponsor_preferred_name_sentence_case=cls.random_if_none(
                sponsor_preferred_name_sentence_case,
                prefix="name_sent_case-",
            ),
            concept_id=cls.random_if_none(concept_id, prefix="CID-"),
            library_name=library_name,
        )
        ct_term: CTTerm = service.create(payload, start_date=effective_date)
        if approve:
            CTTermAttributesService().approve(term_uid=ct_term.term_uid)
            CTTermNameService().approve(term_uid=ct_term.term_uid)
        # Override the auto-generated term uid with the provided one
        if term_uid:
            existing_uid = ct_term.term_uid
            db.cypher_query(
                """
                MATCH (t:CTTermRoot {uid: $existing_uid})
                SET t.uid = $term_uid
                """,
                params={"existing_uid": existing_uid, "term_uid": term_uid},
            )
            ct_term.term_uid = term_uid
        if effective_date:
            db.cypher_query(
                """
                MATCH (:CTTermRoot {uid: $term_uid})<-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[ht:HAS_TERM]-(:CTCodelistRoot {uid: $codelist_uid})
                SET ht.start_date = datetime($start_date)
                """,
                params={
                    "term_uid": term_uid if term_uid else ct_term.term_uid,
                    "codelist_uid": codelist_uid,
                    "start_date": effective_date,
                },
            )
        return ct_term

    @classmethod
    def add_ct_term_parent(
        cls,
        term,
        parent=None,
        relationship_type: str = "type",
        parent_uid: str | None = None,
    ):
        service: CTTermService = CTTermService()
        service.add_parent(
            term_uid=term.term_uid,
            parent_uid=parent_uid if parent_uid else parent.term_uid,
            relationship_type=TermParentType(relationship_type),
        )

    @classmethod
    def remove_term_from_codelist(
        cls,
        term_uid: str,
        codelist_uid: str,
    ):
        service: CTCodelistService = CTCodelistService()
        service.remove_term(
            term_uid=term_uid,
            codelist_uid=codelist_uid,
        )

    @classmethod
    def create_sponsor_ct_package(
        cls,
        extends_package: str,
        effective_date: date = date.today(),
        library_name: str | None = None,
    ) -> CTPackage:
        kwargs: dict[str, Any] = {
            "extends_package": extends_package,
            "effective_date": effective_date,
        }
        if library_name is not None:
            kwargs["library_name"] = library_name
        package = CTPackageService().create_sponsor_ct_package(**kwargs)
        return package

    @classmethod
    def create_ct_package(
        cls,
        number_of_codelists: int = 3,
        catalogue: str = CT_CATALOGUE_NAME,
        name: str = CT_PACKAGE_NAME,
        import_date: datetime | None = datetime.now(),
        effective_date: datetime | None = datetime.now(),
        library_name: str = CT_CODELIST_LIBRARY,
        approve_elements: bool = False,
    ) -> str:
        """
        Creates a CT Package with a number of codelists and one term per codelist
        """
        terms: list[CTTerm] = [
            cls.create_ct_term(
                library_name=library_name,
                approve=approve_elements,
                effective_date=effective_date,
            )
            for _ in range(number_of_codelists)
        ]
        codelists: list[CTCodelist] = [
            cls.create_ct_codelist(
                name=cls.random_str(length=6, prefix="CTCodelist"),
                library_name=library_name,
                approve=approve_elements,
                effective_date=effective_date,
                terms=[
                    CTCodelistTermInput(
                        term_uid=terms[i].term_uid,
                        submission_value=cls.random_str(
                            length=6, prefix="submission_value-"
                        ),
                        order=i + 1,
                    )
                ],
            )
            for i in range(number_of_codelists)
        ]
        package_uid = name
        db.cypher_query(
            """
                MATCH (cat:CTCatalogue {name: $catalogue})
                CREATE (cat)-[:CONTAINS_PACKAGE]->(pkg:CTPackage)
                SET pkg.uid = $package_uid,
                    pkg.name = $name,
                    pkg.import_date = $import_date,
                    pkg.effective_date = $effective_date,
                    pkg.author_id = "TEST"
            """,
            params={
                "catalogue": catalogue,
                "package_uid": package_uid,
                "name": name,
                "import_date": import_date,
                "effective_date": effective_date.date(),
            },
        )
        for i in range(number_of_codelists):
            db.cypher_query(
                """
                    MATCH (pkg:CTPackage {uid: $package_uid})
                    MATCH (:CTCodelistRoot {uid: $codelist_uid})-->(:CTCodelistAttributesRoot)
                        -[:LATEST]->(cl_attr_v:CTCodelistAttributesValue)
                    MATCH (:CTTermRoot {uid: $term_uid})-->(:CTTermAttributesRoot)
                        -[:LATEST]->(t_attr_v:CTTermAttributesValue)
                    WITH DISTINCT pkg, cl_attr_v, t_attr_v
                    CREATE (pkg)-[:CONTAINS_CODELIST]->(pkg_cl:CTPackageCodelist)
                            -[:CONTAINS_ATTRIBUTES]->(cl_attr_v)
                    CREATE (pkg_cl)-[:CONTAINS_TERM]->(pkg_term:CTPackageTerm)
                            -[:CONTAINS_ATTRIBUTES]->(t_attr_v)
                    SET pkg_cl.uid = $package_codelist_uid,
                        pkg_term.uid = $package_term_uid
                """,
                params={
                    "package_uid": package_uid,
                    "package_codelist_uid": f"{package_uid}_{codelists[i].codelist_uid}",
                    "package_term_uid": terms[i].term_uid,
                    "codelist_uid": codelists[i].codelist_uid,
                    "term_uid": terms[i].term_uid,
                },
            )
        return package_uid

    @classmethod
    def create_ct_codelists_using_cypher(cls):
        res = db.cypher_query("MATCH (n:CTCodelistRoot) RETURN COLLECT(n.uid) as uids")
        existing_codelist_uids = res[0][0][0]
        for attribute, value in CT_CODELIST_NAMES.__dict__.items():
            if getattr(CT_CODELIST_UIDS, attribute, None) not in existing_codelist_uids:
                db.cypher_query(
                    """
                MATCH (library:Library {name:$library})
                MATCH (catalogue:CTCatalogue {name:$catalogue})
                MERGE (library)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot {uid: $uid})-[:HAS_NAME_ROOT]->
                (codelist_ver_root:CTCodelistNameRoot)-[:LATEST]->(codelist_ver_value:CTCodelistNameValue {
                name: $name,
                name_sentence_case: $uid + 'name',
                is_ordinal: false})
                MERGE (codelist_root)-[:HAS_ATTRIBUTES_ROOT]->(codelist_a_root:CTCodelistAttributesRoot)
                -[:LATEST]->(codelist_a_value:CTCodelistAttributesValue {definition:$uid + ' DEF',
                name:$uid + ' NAME', preferred_term:$uid + ' PREF', submission_value:$submission_value, extensible:true})
                MERGE (catalogue)-[:HAS_CODELIST]->(codelist_root)
                MERGE (codelist_ver_root)-[name_final:LATEST_FINAL]->(codelist_ver_value)
                MERGE (codelist_ver_root)-[name_hasver:HAS_VERSION]->(codelist_ver_value)
                MERGE (codelist_a_root)-[attributes_final:LATEST_FINAL]->(codelist_a_value)
                MERGE (codelist_a_root)-[attributes_hasver:HAS_VERSION]->(codelist_a_value)
                """
                    + cls.set_final_props("name_hasver")
                    + cls.set_final_props("attributes_hasver"),
                    {
                        "uid": getattr(CT_CODELIST_UIDS, attribute, None),
                        "name": value,
                        "library": SPONSOR_LIBRARY_NAME,
                        "catalogue": CT_CATALOGUE_NAME,
                        "submission_value": getattr(
                            CT_CODELIST_SUBMVALS, attribute, None
                        ),
                    },
                )

    @classmethod
    def create_study_fields_ct_data(cls):
        """Creates CT codelists and terms needed by study-fields-related tests.

        Previously provided by create_study_fields_configuration() (now removed).
        Creates:
        - C99077 codelist (Study Type, needed so add_term/patch_trial_summary_parameter can reference it)
        - 10 CT terms in C66737 (Sponsor library, needed by consumer API and sponsor CT package tests)

        Terms use effective_date=2020-06-26 so they are visible to sponsor CT packages
        with any recent effective_date (the persistence tests use today-3 days).
        Names sort alphabetically in the same order as the consumer API sort key
        (codelist_uid + '_' + term_uid): C123631 < C123632 < ... < C98737.
        """
        existing = db.cypher_query("MATCH (n:CTCodelistRoot {uid: 'C99077'}) RETURN n")[
            0
        ]
        if not existing:
            cls.create_ct_codelist(
                name="Study Type",
                submission_value="STYPE",
                codelist_uid="C99077",
                approve=True,
            )

        # effective_date in the past ensures start_date on HAS_VERSION rels predates
        # any sponsor CT package effective_date used in tests (approve() preserves it).
        past_date = datetime(2020, 6, 26, tzinfo=timezone.utc)
        for term_uid, name in [
            ("C123631", "study-field-term-01"),
            ("C123632", "study-field-term-02"),
            ("C126069", "study-field-term-03"),
            ("C126070", "study-field-term-04"),
            ("C139274", "study-field-term-05"),
            ("C139275", "study-field-term-06"),
            ("C146995", "study-field-term-07"),
            ("C25196", "study-field-term-08"),
            ("C49703", "study-field-term-09"),
            ("C98737", "study-field-term-10"),
        ]:
            existing_term = db.cypher_query(
                "MATCH (n:CTTermRoot {uid: $uid}) RETURN n", {"uid": term_uid}
            )[0]
            if not existing_term:
                cls.create_ct_term(
                    term_uid=term_uid,
                    sponsor_preferred_name=name,
                    effective_date=past_date,
                )

    @classmethod
    def create_ct_codelist(
        cls,
        catalogue_name: str = CT_CATALOGUE_NAME,
        name: str = CT_CODELIST_NAMES.default,
        submission_value: str | None = None,
        nci_preferred_name: str | None = None,
        sponsor_preferred_name: str | None = None,
        definition: str | None = None,
        extensible: bool = False,
        is_ordinal: bool = False,
        template_parameter: bool = False,
        parent_codelist_uid: str | None = None,
        terms: list[CTCodelistTermInput] | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        approve: bool = False,
        effective_date: datetime | None = None,
        codelist_uid: str | None = None,
        paired_codes_codelist_uid: str | None = None,
        codelist_type: str = DEFAULT_CODELIST_TYPE,
    ) -> CTCodelist:
        if terms is None:
            terms = []

        service: CTCodelistService = CTCodelistService()
        payload = CTCodelistCreateInput(
            catalogue_names=[catalogue_name],
            name=cls.random_if_none(name, prefix="name-"),
            submission_value=cls.random_if_none(
                submission_value, prefix="submission_value-"
            ),
            nci_preferred_name=cls.random_if_none(
                nci_preferred_name, prefix="nci_name-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            extensible=extensible,
            is_ordinal=is_ordinal,
            codelist_type=codelist_type,
            sponsor_preferred_name=cls.random_if_none(
                sponsor_preferred_name, prefix="name-"
            ),
            template_parameter=template_parameter,
            parent_codelist_uid=parent_codelist_uid,
            terms=terms,
            library_name=library_name,
        )
        result: CTCodelist = service.create(payload, start_date=effective_date)
        if approve:
            CTCodelistNameService().approve(codelist_uid=result.codelist_uid)
            CTCodelistAttributesService().approve(codelist_uid=result.codelist_uid)
        # Override auto-generated codelist uid with the provided one
        if codelist_uid:
            db.cypher_query(
                """
                MATCH (c:CTCodelistRoot {uid: $codelist_uid})
                SET c.uid = $new_uid
                """,
                params={"codelist_uid": result.codelist_uid, "new_uid": codelist_uid},
            )
            result.codelist_uid = codelist_uid
        if paired_codes_codelist_uid:
            db.cypher_query(
                """
                MATCH (c:CTCodelistRoot {uid: $codelist_uid}), (cc:CTCodelistRoot {uid: $paired_codes_codelist_uid})
                MERGE (c)-[:PAIRED_CODE_CODELIST]->(cc)
                """,
                params={
                    "codelist_uid": result.codelist_uid,
                    "paired_codes_codelist_uid": paired_codes_codelist_uid,
                },
            )
            result.paired_codes_codelist_uid = paired_codes_codelist_uid
        return result

    @classmethod
    def create_dictionary_codelist(
        cls,
        name: str = DICTIONARY_CODELIST_NAME,
        template_parameter: bool = False,
        library_name: str = DICTIONARY_CODELIST_LIBRARY,
        approve: bool = True,
    ) -> DictionaryCodelist:
        service: DictionaryCodelistService = DictionaryCodelistService()
        all_codelists = service.get_all_dictionary_codelists(library=library_name)
        existing_codelist = next(
            (x for x in all_codelists.items if x.name == name), None
        )

        if not existing_codelist:
            payload = DictionaryCodelistCreateInput(
                name=name,
                template_parameter=template_parameter,
                library_name=library_name,
            )
            dictionary_codelist: DictionaryCodelist = service.create(payload)
            if approve:
                service.approve(dictionary_codelist.codelist_uid)
            return dictionary_codelist
        return existing_codelist

    @classmethod
    def create_dictionary_term(
        cls,
        codelist_uid: str,
        dictionary_id: str | None = None,
        name: str | None = None,
        name_sentence_case: str | None = None,
        abbreviation: str | None = None,
        definition: str | None = None,
        library_name: str = DICTIONARY_CODELIST_LIBRARY,
        approve: bool = True,
    ) -> DictionaryTerm:
        service: DictionaryTermService = DictionaryTermService()
        all_terms = service.get_all_dictionary_terms(codelist_uid=codelist_uid)
        existing_term = next((x for x in all_terms.items if x.name == name), None)
        if not existing_term:
            target_name = cls.random_if_none(name, prefix="name-")
            payload = DictionaryTermCreateInput(
                codelist_uid=codelist_uid,
                dictionary_id=cls.random_if_none(dictionary_id, prefix="dict-"),
                name=target_name,
                name_sentence_case=(
                    name_sentence_case if name_sentence_case else target_name
                ),
                abbreviation=cls.random_if_none(abbreviation, prefix="abbr-"),
                definition=cls.random_if_none(definition, prefix="definition-"),
                library_name=library_name,
            )
            dictionary_term: DictionaryTerm = service.create(payload)
            if approve:
                service.approve(dictionary_term.term_uid)
            return dictionary_term
        return existing_term

    @classmethod
    def create_numeric_value_with_unit(
        cls,
        *,
        unit: str | None = None,
        name: str | None = None,
        name_sentence_case: str | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        template_parameter: bool = False,
        value: float,
        unit_definition_uid: str | None = None,
    ) -> NumericValueWithUnit:
        # First make sure that the specified unit exists
        if unit_definition_uid is None:
            try:
                unit_definition = cls.create_unit_definition(
                    name=unit,
                    library_name=library_name,
                    convertible_unit=False,
                    display_unit=True,
                    master_unit=False,
                    si_unit=True,
                    us_conventional_unit=True,
                    use_complex_unit_conversion=False,
                    ct_units=[],
                    unit_subsets=[],
                    ucum=None,
                    unit_dimension=None,
                    legacy_code=None,
                    use_molecular_weight=False,
                    conversion_factor_to_master=0.001,
                    comment=unit,
                    order=1,
                    definition=unit,
                    template_parameter=True,
                    approve=True,
                )
                unit_definition_uid = unit_definition.uid
            except Exception as _:
                log.info("Unit '%s' already exists", unit)
                unit_definition_uid = cls.get_unit_uid_by_name(unit_name=unit)

        service: NumericValueWithUnitService = NumericValueWithUnitService()
        payload = NumericValueWithUnitPostInput(
            name=cls.random_if_none(name, prefix="name-"),
            name_sentence_case=cls.random_if_none(
                name_sentence_case, prefix="name_sentence_case-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbreviation-"),
            library_name=library_name,
            template_parameter=template_parameter,
            value=value,
            unit_definition_uid=unit_definition_uid,
        )

        result: NumericValueWithUnit = service.create(payload)  # type: ignore[assignment]
        return result

    @classmethod
    def create_lag_time(
        cls,
        *,
        unit: str | None = None,
        sdtm_domain_label: str = "Adverse Event Domain",
        name: str | None = None,
        name_sentence_case: str | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
        template_parameter: bool = False,
        value: float,
        unit_definition_uid: str | None = None,
        sdtm_domain_uid: str | None = None,
    ) -> LagTime:
        # First make sure that the specified unit exists
        if unit_definition_uid is None:
            try:
                unit_definition = cls.create_unit_definition(
                    name=unit,
                    library_name=library_name,
                    convertible_unit=False,
                    display_unit=True,
                    master_unit=False,
                    si_unit=True,
                    us_conventional_unit=True,
                    ct_units=[],
                    unit_subsets=[],
                    ucum=None,
                    unit_dimension=None,
                    legacy_code=None,
                    use_molecular_weight=False,
                    conversion_factor_to_master=0.001,
                    comment=unit,
                    order=1,
                    definition=unit,
                    template_parameter=True,
                    approve=True,
                )
                unit_definition_uid = unit_definition.uid
            except Exception as _:
                log.info("Unit '%s' already exists", unit)
                unit_definition_uid = cls.get_unit_uid_by_name(unit_name=unit)

        # Make sure that the specified SDTM domain exists
        if sdtm_domain_uid is None:
            try:
                sdtm_domain: CTTerm = cls.create_ct_term(
                    sponsor_preferred_name=sdtm_domain_label,
                    approve=True,
                    codelist_uid=CT_CODELIST_UIDS.adverse_events,
                )
                sdtm_domain_uid = sdtm_domain.term_uid
            except Exception as _:
                log.info("SDTM domain '%s' already exists", sdtm_domain_label)
                sdtm_domains: GenericFilteringReturn[CTTermNameAndAttributes] = (
                    cls.get_ct_terms_by_name(name=sdtm_domain_label)
                )
                sdtm_domain_uid = sdtm_domains.items[0].term_uid

        service: LagTimeService = LagTimeService()
        payload = LagTimePostInput(
            name=cls.random_if_none(name, prefix="name-"),
            name_sentence_case=cls.random_if_none(
                name_sentence_case, prefix="name_sentence_case-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbreviation-"),
            library_name=library_name,
            template_parameter=template_parameter,
            value=value,
            unit_definition_uid=unit_definition_uid,
            sdtm_domain_uid=sdtm_domain_uid,
        )

        result: NumericValueWithUnit = service.create(payload)  # type: ignore[assignment]
        return result

    @classmethod
    def get_unit_uid_by_name(cls, unit_name) -> str:
        unit_uid = MetaRepository().unit_definition_repository.find_uid_by_name(
            unit_name
        )
        return unit_uid

    @classmethod
    def get_unit_by_uid(
        cls,
        unit_uid: str,
        at_specified_datetime: datetime | None = None,
        status: str | None = None,
        version: str | None = None,
    ) -> UnitDefinitionModel:
        return UnitDefinitionService().get_by_uid(
            uid=unit_uid,
            at_specific_date=at_specified_datetime,
            status=LibraryItemStatus(status) if status is not None else None,
            version=version,
        )

    @classmethod
    def get_ct_terms_by_name(
        cls, name
    ) -> GenericFilteringReturn[CTTermNameAndAttributes]:
        return CTTermService().get_all_terms(
            codelist_name=None,
            codelist_uid=None,
            library=None,
            package=None,
            filter_by={"name.sponsor_preferred_name": {"v": [name]}},
        )

    @classmethod
    def create_brand(cls, name: str) -> Brand:
        service: BrandService = BrandService()
        return service.create(BrandCreateInput(name=name))

    @classmethod
    def create_ct_catalogue(
        cls,
        library: str = SPONSOR_LIBRARY_NAME,
        catalogue_name: str = CT_CATALOGUE_NAME,
    ):
        create_catalogue_query = """
        MATCH (library:Library {name:$library_name})
        MERGE (catalogue:CTCatalogue {name:$catalogue_name})
        MERGE (library)-[:CONTAINS_CATALOGUE]->(catalogue)
        """
        db.cypher_query(
            create_catalogue_query,
            {
                "library_name": library,
                "catalogue_name": catalogue_name,
            },
        )
        return catalogue_name

    @classmethod
    def get_null_value_code(cls) -> tuple[str, str]:
        return initialize_ct_data_map["NullValueCodes"][0]

    @classmethod
    def create_study_ct_data_map(
        cls,
        codelist_uid: str | None,
        # pylint: disable=dangerous-default-value
        ct_data_map: dict[Any, Any] | None = None,
        ct_codelist_map: dict[Any, Any] | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
    ):
        if ct_data_map is None:
            ct_data_map = initialize_ct_data_map
        if ct_codelist_map is None:
            ct_codelist_map = initialize_ct_codelist_map

        dictionary_codelist = cls.create_dictionary_codelist()
        # used cypher below to manually assign uids related to CDISC concept_ids
        create_ct_term_with_custom_uid_query = (
            """
            MATCH (codelist_root:CTCodelistRoot {uid:$codelist_uid})
            WITH codelist_root
            MERGE (term_root:CTTermRoot {uid: $uid})
            MERGE (codelist_root)-[:HAS_TERM]->(:CTCodelistTerm {submission_value:$submission_value, start_date: dateTime("2020-12-10")})-[:HAS_TERM_ROOT]->(term_root)
            MERGE (term_root)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-
                [:LATEST]->(term_name_value:CTTermNameValue {name: $name, name_sentence_case: toLower($name)})
            MERGE (term_name_root)-[:LATEST_FINAL]->(term_name_value)
            MERGE (term_name_root)-[hasnamever:HAS_VERSION {start_date: dateTime("2020-12-10")}]->(term_name_value)
            MERGE (term_root)-[:HAS_ATTRIBUTES_ROOT]->(term_attr_root:CTTermAttributesRoot)-
                [:LATEST]->(term_attr_value:CTTermAttributesValue {definition: $name, name: $name, preferred_term: $name})
            MERGE (term_attr_root)-[:LATEST_FINAL]->(term_attr_value)
            MERGE (term_attr_root)-[hasattrver:HAS_VERSION {start_date: dateTime("2020-12-10")}]->(term_attr_value)
            WITH term_root, hasnamever, hasattrver
            MATCH (library:Library {name:$library_name})
            WITH library, term_root, hasnamever, hasattrver
            MERGE (library)-[:CONTAINS_TERM]->(term_root)"""
            + cls.set_final_props("hasnamever")
            + cls.set_final_props("hasattrver")
        )
        create_dictionary_term_with_custom_uid_query = """
            MATCH (dictionary_codelist_root:DictionaryCodelistRoot {uid:$dictionary_codelist_uid})
            WITH dictionary_codelist_root
            MERGE (dictionary_term_root:DictionaryTermRoot {uid: $uid})-[:LATEST]->(dictionary_term_value:DictionaryTermValue
            {name: $name, name_sentence_case: toLower($name)})
            MERGE (dictionary_term_root)-[final:LATEST_FINAL]->(dictionary_term_value)
            MERGE (dictionary_term_root)-[hasver:HAS_VERSION]->(dictionary_term_value)
            MERGE (dictionary_codelist_root)-[:HAS_TERM]->(dictionary_term_root)
            
            WITH dictionary_term_root, final, hasver
            MATCH (library:Library {name:$library_name})
            WITH library, dictionary_term_root, final, hasver
            MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(dictionary_term_root)""" + cls.set_final_props(
            "hasver"
        )
        for field_name, value in ct_data_map.items():
            if field_name in [
                "TherapeuticAreas",
                "DiseaseConditionOrIndications",
                "DiagnosisGroups",
            ]:
                query = create_dictionary_term_with_custom_uid_query
            else:
                query = create_ct_term_with_custom_uid_query

            cl_uid = codelist_uid
            if codelist_uid is None:
                if field_name in ct_codelist_map:
                    cl_uid, codelist_name, codelist_submval = ct_codelist_map[
                        field_name
                    ]
                    cl_uid = cls.get_or_create_codelist(
                        cl_uid, codelist_name, codelist_submval
                    )

            if isinstance(value, list):
                for uid, name in value:
                    db.cypher_query(
                        query,
                        {
                            "codelist_uid": cl_uid,
                            "dictionary_codelist_uid": dictionary_codelist.codelist_uid,
                            "uid": uid,
                            "name": name,
                            "submission_value": name,
                            "library_name": library_name,
                        },
                    )
            else:
                db.cypher_query(
                    query,
                    {
                        "codelist_uid": cl_uid,
                        "dictionary_codelist_uid": dictionary_codelist.codelist_uid,
                        "uid": value[0],
                        "name": value[1],
                        "submission_value": value[1],
                        "library_name": library_name,
                    },
                )

    @classmethod
    def get_or_create_codelist(cls, codelist_uid, codelist_name, codelist_submval):
        if codelist_uid is not None:
            query = """
                MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})
                RETURN codelist_root.uid
                """
        else:
            query = """
                MATCH (codelist_root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(:CTCodelistAttributesValue {submission_value: $submission_value})
                RETURN codelist_root.uid
                """
        res = db.cypher_query(
            query, {"codelist_uid": codelist_uid, "submission_value": codelist_submval}
        )

        if len(res[0]) > 0:
            return res[0][0][0]

        codelist = cls.create_ct_codelist(
            name=codelist_name,
            submission_value=codelist_submval,
            approve=True,
            extensible=True,
            codelist_uid=codelist_uid,
        )
        codelist_uid = codelist.codelist_uid
        return codelist_uid

    @classmethod
    def create_data_model_catalogue(
        cls,
        name: str = "name",
        data_model_type: str = "data_model_type",
        library_name: str = SPONSOR_LIBRARY_NAME,
    ) -> str:
        """
        Method uses cypher query to create DataModelCatalogue nodes because we don't have POST endpoints to instantiate these entities.

        :param name
        :param data_model_type
        :param library_name
        """

        create_data_model_catalogue = """
            MERGE (data_model_catalogue:DataModelCatalogue {name: $name, data_model_type:$data_model_type})
            WITH data_model_catalogue
            MATCH (library:Library {name:$library_name})
            MERGE (library)-[:CONTAINS_CATALOGUE]->(data_model_catalogue)"""
        db.cypher_query(
            create_data_model_catalogue,
            {
                "name": name,
                "data_model_type": data_model_type,
                "library_name": library_name,
            },
        )
        return name

    @classmethod
    def create_data_model(
        cls,
        name: str = "name",
        description: str = "description",
        version_number: str = "1",
        implementation_guides=None,
        library_name: str = SPONSOR_LIBRARY_NAME,
    ) -> DataModel:
        """
        Method uses cypher query to create DataModel nodes because we don't have POST endpoints to instantiate these entities.

        :param name
        :param description
        :param implementation_guides
        :param version_number
        :param library_name
        """

        if implementation_guides is None:
            implementation_guides = []
        create_data_model = (
            """
                    MERGE (data_model_root:DataModelRoot {uid: $data_model_uid})-[:LATEST]->(data_model_value:DataModelValue
                    {name: $name, description: $description, version_number: $version_number})
                    MERGE (data_model_root)-[final:LATEST_FINAL]->(data_model_value)
                    MERGE (data_model_root)-[hv:HAS_VERSION]->(data_model_value)
                    WITH data_model_root, data_model_value, final, hv
                    MATCH (library:Library {name:$library_name})
                    WITH library, data_model_root, data_model_value, final, hv
                    MERGE (library)-[:CONTAINS_DATA_MODEL]->(data_model_root)
                    """
            + cls.set_final_props("hv")
            + """ WITH data_model_root, data_model_value, final
            UNWIND CASE WHEN $implementation_guides = [] THEN [NULL] 
            ELSE $implementation_guides END as implementation_guide
            MATCH (data_model_ig_root:DataModelIGRoot {uid:implementation_guide})-[:LATEST]->(data_model_ig_value)
            MERGE (data_model_value)<-[:IMPLEMENTS]-(data_model_ig_value)"""
        )
        data_model_uid = DataModelRoot.get_next_free_uid_and_increment_counter()
        db.cypher_query(
            create_data_model,
            {
                "data_model_uid": data_model_uid,
                "name": name,
                "description": description,
                "implementation_guides": implementation_guides,
                "library_name": library_name,
                "version_number": version_number,
            },
        )
        return DataModelService().get_by_uid(uid=data_model_uid)

    @classmethod
    def create_data_model_ig(
        cls,
        name: str = "name",
        version_number: str = "1",
        description: str = "description",
        implemented_data_model: str | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
    ) -> DataModelIG:
        """
        Method uses cypher query to create DataModelIG nodes because we don't have POST endpoints to instantiate these entities.

        :param name
        :param description
        :param implemented_data_model
        :param version_number
        :param library_name
        """
        create_data_model_ig = (
            """
                    MERGE (data_model_ig_root:DataModelIGRoot {uid: $data_model_ig_uid})-[:LATEST]->(data_model_ig_value:DataModelIGValue
                    {name: $name, description: $description, version_number: $version_number})
                    MERGE (data_model_ig_root)-[final:LATEST_FINAL]->(data_model_ig_value)
                    MERGE (data_model_ig_root)-[hv:HAS_VERSION]->(data_model_ig_value)
                    WITH data_model_ig_root, data_model_ig_value, final, hv
                    MATCH (library:Library {name:$library_name})
                    WITH library, data_model_ig_root, data_model_ig_value, final, hv
                    MERGE (library)-[:CONTAINS_DATA_MODEL_IG]->(data_model_ig_root)
                    """
            + cls.set_final_props("hv")
            + """WITH data_model_ig_root, data_model_ig_value, final
            MATCH (data_model_root:DataModelRoot {uid:$implemented_data_model})-[:LATEST]->(data_model_value)
            MERGE (data_model_ig_value)-[:IMPLEMENTS]->(data_model_value)"""
        )
        data_model_ig_uid = DataModelIGRoot.get_next_free_uid_and_increment_counter()
        db.cypher_query(
            create_data_model_ig,
            {
                "data_model_ig_uid": data_model_ig_uid,
                "name": name,
                "description": description,
                "implemented_data_model": implemented_data_model,
                "library_name": library_name,
                "version_number": version_number,
            },
        )
        return DataModelIGService().get_by_uid(uid=data_model_ig_uid)

    @classmethod
    def create_dataset_class(
        cls,
        data_model_uid: str,
        data_model_name: str,
        data_model_catalogue_name: str,
        label: str = "label",
        description: str = "description",
        title: str = "title",
        library_name: str = SPONSOR_LIBRARY_NAME,
    ) -> DatasetClassAPIModel:
        """
        Method uses cypher query to create DatasetClass nodes because we don't have POST endpoints to instantiate these entities.

        :param data_model_uid
        :param data_model_catalogue_name
        :param label
        :param description
        :param title
        :param library_name
        """

        create_dataset_class = """
            MERGE (dataset_class_root:DatasetClass {uid: $implemented_dataset_class_name})-[:HAS_INSTANCE]->(dataset_class_value:DatasetClassInstance
            {label: $label, description: $description, title: $title})
            WITH dataset_class_root, dataset_class_value
            MATCH (data_model_catalogue:DataModelCatalogue {name: $data_model_catalogue_name})
            MERGE (data_model_catalogue)-[:HAS_DATASET_CLASS]->(dataset_class_root)
            WITH dataset_class_root, dataset_class_value
            MATCH (data_model_root:DataModelRoot {uid:$data_model_uid})-[:LATEST]->(data_model_value)
            MERGE (dataset_class_value)<-[:HAS_DATASET_CLASS]-(data_model_value)"""
        dataset_class_uid = DatasetClass.get_next_free_uid_and_increment_counter()
        db.cypher_query(
            create_dataset_class,
            {
                "implemented_dataset_class_name": dataset_class_uid,
                "data_model_catalogue_name": data_model_catalogue_name,
                "label": label,
                "title": title,
                "description": description,
                "data_model_uid": data_model_uid,
                "library_name": library_name,
            },
        )
        return DatasetClassService().get_by_uid(
            uid=dataset_class_uid, data_model_name=data_model_name
        )

    @classmethod
    def create_dataset(
        cls,
        data_model_ig_uid: str,
        data_model_ig_version_number: str,
        implemented_dataset_class_name: str,
        data_model_catalogue_name: str,
        label: str = "label",
        description: str = "description",
        title: str = "title",
        library_name: str = SPONSOR_LIBRARY_NAME,
    ) -> DatasetAPIModel:
        """
        Method uses cypher query to create Dataset nodes because we don't have POST endpoints to instantiate these entities.

        :param data_model_ig_uid
        :param data_model_ig_version_number
        :param implemented_dataset_class_name
        :param data_model_catalogue_name
        :param label
        :param description
        :param title
        :param library_name
        """

        create_dataset = """
            MERGE (dataset_root:Dataset {uid: $dataset_uid})-[:HAS_INSTANCE]->(dataset_value:DatasetInstance
            {label: $label, description: $description, title: $title})
            WITH dataset_root, dataset_value
            MATCH (data_model_catalogue:DataModelCatalogue {name: $data_model_catalogue_name})
            MERGE (data_model_catalogue)-[:HAS_DATASET]->(dataset_root)
            WITH dataset_root, dataset_value
            MATCH (data_model_ig_root:DataModelIGRoot {uid:$data_model_ig_uid})-[:LATEST]->(data_model_ig_value)
            MERGE (dataset_value)<-[:HAS_DATASET]-(data_model_ig_value)
            WITH dataset_root, dataset_value, data_model_ig_value
            MATCH (dataset_class_root:DatasetClass {uid: $implemented_dataset_class_name})-[:HAS_INSTANCE]->(dataset_class_value)
            MERGE (dataset_value)-[implements:IMPLEMENTS_DATASET_CLASS]->(dataset_class_value)
            SET implements.version_number=data_model_ig_value.version_number"""
        dataset_uid = Dataset.get_next_free_uid_and_increment_counter()
        db.cypher_query(
            create_dataset,
            {
                "dataset_uid": dataset_uid,
                "data_model_ig_uid": data_model_ig_uid,
                "implemented_dataset_class_name": implemented_dataset_class_name,
                "data_model_catalogue_name": data_model_catalogue_name,
                "label": label,
                "title": title,
                "description": description,
                "library_name": library_name,
            },
        )
        return DatasetService().get_by_uid(
            uid=dataset_uid,
            data_model_ig_name=data_model_ig_uid,
            data_model_ig_version=data_model_ig_version_number,
        )

    @classmethod
    def create_sponsor_model(
        cls,
        ig_uid: str,
        ig_version_number: str,
        version_number: str,
        library_name: str = SPONSOR_LIBRARY_NAME,
    ) -> SponsorModelAPIModel:
        service: SponsorModelService = SponsorModelService()
        result: SponsorModelAPIModel = service.create(  # type: ignore[assignment]
            item_input=SponsorModelCreateInput(
                ig_uid=ig_uid,
                ig_version_number=ig_version_number,
                version_number=version_number,
                library_name=library_name,
            )
        )
        return result

    @classmethod
    def create_sponsor_dataset(
        cls,
        dataset_uid: str,
        sponsor_model_name: str,
        sponsor_model_version_number: str,
        implemented_dataset_class: str,
        is_basic_std: bool = False,
        xml_path: str | None = "xml_path",
        xml_title: str | None = "xml_title",
        structure: str | None = "structure",
        purpose: str | None = "purpose",
        keys: list[str] | None = None,
        sort_keys: list[str] | None = None,
        is_cdisc_std: bool = False,
        source_ig: str | None = "source_ig",
        comment: str | None = "comment",
        ig_comment: str | None = "ig_comment",
        map_domain_flag: bool = False,
        suppl_qual_flag: bool = False,
        include_in_raw: bool = False,
        gen_raw_seqno_flag: bool = False,
        enrich_build_order: int | None = 100,
        label: str | None = "label",
        state: str | None = "state",
        extended_domain: str | None = "extended_domain",
    ) -> SponsorModelDatasetAPIModel:
        service: SponsorModelDatasetService = SponsorModelDatasetService()
        # Separate declared fields from sponsor-defined extensible fields
        extra_properties: dict[str, Any] = {
            "is_basic_std": is_basic_std,
            "xml_path": xml_path,
            "xml_title": xml_title,
            "structure": structure,
            "purpose": purpose,
            "is_cdisc_std": is_cdisc_std,
            "source_ig": source_ig,
            "comment": comment,
            "ig_comment": ig_comment,
            "map_domain_flag": map_domain_flag,
            "suppl_qual_flag": suppl_qual_flag,
            "include_in_raw": include_in_raw,
            "gen_raw_seqno_flag": gen_raw_seqno_flag,
            "label": label,
            "state": state,
            "extended_domain": extended_domain,
        }
        result: SponsorModelDatasetAPIModel = service.create(  # type: ignore[assignment]
            item_input=SponsorModelDatasetInput(
                dataset_uid=dataset_uid,
                sponsor_model_name=sponsor_model_name,
                sponsor_model_version_number=sponsor_model_version_number,
                implemented_dataset_class=implemented_dataset_class,
                keys=keys,
                sort_keys=sort_keys,
                enrich_build_order=enrich_build_order,
                **extra_properties,
            )
        )

        return result

    @classmethod
    def create_sponsor_dataset_variable(
        cls,
        dataset_uid: str,
        dataset_variable_uid: str,
        sponsor_model_name: str,
        sponsor_model_version_number: str,
        target_data_model_catalogue: str | None = "SDTMIG",
        is_basic_std: bool = False,
        implemented_parent_dataset_class: str | None = None,
        implemented_variable_class: str | None = None,
        label: str | None = "label",
        order: int | None = 1,
        variable_type: str | None = "variable_type",
        length: int | None = 12,
        display_format: str | None = "display_format",
        xml_datatype: str | None = "xml_datatype",
        core: str | None = "core",
        origin: str | None = "origin",
        role: str | None = "role",
        term: str | None = "term",
        algorithm: str | None = "algorithm",
        qualifiers: list[str] | None = ["qualifiers"],
        is_cdisc_std: bool = False,
        comment: str | None = "comment",
        ig_comment: str | None = "ig_comment",
        class_table: str | None = "class_table",
        class_column: str | None = "class_column",
        map_var_flag: str | None = "Y",
        fixed_mapping: str | None = "fixed_mapping",
        include_in_raw: bool = False,
        nn_internal: bool = False,
        value_lvl_where_cols: str | None = "value_lvl_where_cols",
        value_lvl_label_col: str | None = "value_lvl_label_col",
        value_lvl_collect_ct_val: str | None = "value_lvl_collect_ct_val",
        value_lvl_ct_codelist_id_col: str | None = "value_lvl_ct_codelist_id_col",
        enrich_build_order: int | None = 100,
        enrich_rule: str | None = "enrich_rule",
        references_codelists: list[str] | None = None,
        references_terms: list[str] | None = None,
    ) -> SponsorModelDatasetVariableAPIModel:
        service: SponsorModelDatasetVariableService = (
            SponsorModelDatasetVariableService()
        )
        # Separate declared fields from sponsor-defined extensible fields
        extra_properties: dict[str, Any] = {
            "is_basic_std": is_basic_std,
            "label": label,
            "variable_type": variable_type,
            "length": length,
            "display_format": display_format,
            "xml_datatype": xml_datatype,
            "core": core,
            "origin": origin,
            "role": role,
            "term": term,
            "algorithm": algorithm,
            "qualifiers": qualifiers,
            "is_cdisc_std": is_cdisc_std,
            "comment": comment,
            "ig_comment": ig_comment,
            "class_table": class_table,
            "class_column": class_column,
            "map_var_flag": map_var_flag,
            "fixed_mapping": fixed_mapping,
            "include_in_raw": include_in_raw,
            "nn_internal": nn_internal,
            "value_lvl_where_cols": value_lvl_where_cols,
            "value_lvl_label_col": value_lvl_label_col,
            "value_lvl_collect_ct_val": value_lvl_collect_ct_val,
            "value_lvl_ct_codelist_id_col": value_lvl_ct_codelist_id_col,
            "enrich_build_order": enrich_build_order,
            "enrich_rule": enrich_rule,
        }
        result: SponsorModelDatasetVariableAPIModel = service.create(  # type: ignore[assignment]
            item_input=SponsorModelDatasetVariableInput(
                target_data_model_catalogue=target_data_model_catalogue,
                dataset_uid=dataset_uid,
                dataset_variable_uid=dataset_variable_uid,
                sponsor_model_name=sponsor_model_name,
                sponsor_model_version_number=sponsor_model_version_number,
                implemented_parent_dataset_class=implemented_parent_dataset_class,
                implemented_variable_class=implemented_variable_class,
                order=order,
                references_codelists=references_codelists,
                references_terms=references_terms,
                **extra_properties,
            )
        )

        return result

    @classmethod
    def create_disease_milestone(
        cls,
        study_uid,
        disease_milestone_type=None,
        repetition_indicator=None,
    ) -> StudyDiseaseMilestone:
        service: StudyDiseaseMilestoneService = StudyDiseaseMilestoneService()
        payload = StudyDiseaseMilestoneCreateInput(
            study_uid=study_uid,
            disease_milestone_type=disease_milestone_type,
            repetition_indicator=repetition_indicator,
        )

        result: StudyDiseaseMilestone = service.create(
            study_uid, study_disease_milestone_input=payload
        )
        return result

    @classmethod
    def create_variable_class(
        cls,
        dataset_class_uid: str,
        data_model_catalogue_name: str,
        data_model_name: str,
        data_model_version: str,
        label: str = "label",
        description: str = "description",
        title: str = "title",
        implementation_notes: str = "implementation_notes",
        mapping_instructions: str = "mapping_instructions",
        prompt: str = "prompt",
        question_text: str = "question_text",
        simple_datatype: str = "simple_datatype",
        role: str = "role",
        library_name: str = SPONSOR_LIBRARY_NAME,
    ) -> VariableClassAPIModel:
        """
        Method uses cypher query to create VariableClass nodes because we don't have POST endpoints to instantiate these entities.

        :param dataset_class_uid
        :param data_model_catalogue_name
        :param data_model_name
        :param data_model_version
        :param label
        :param description
        :param title
        :param implementation_notes
        :param mapping_instructions
        :param prompt
        :param question_text
        :param simple_datatype
        :param role
        :param library_name
        """

        create_class_variable = """
            MERGE (class_variable_root:VariableClass {uid: $class_variable_uid})-[:HAS_INSTANCE]->(class_variable_value:VariableClassInstance
            {label: $label, description: $description, title: $title,
            implementation_notes: $implementation_notes, mapping_instructions: $mapping_instructions, prompt: $prompt,
            question_text: $question_text, simple_datatype: $simple_datatype, role: $role})
            WITH class_variable_root, class_variable_value
            MATCH (data_model_catalogue:DataModelCatalogue {name: $data_model_catalogue_name})
            MERGE (data_model_catalogue)-[:HAS_VARIABLE_CLASS]->(class_variable_root)
            WITH class_variable_root, class_variable_value
            MATCH (dataset_class_root:DatasetClass {uid:$dataset_class_uid})-[:HAS_INSTANCE]->(dataset_class_value)
            MERGE (class_variable_value)<-[has_variable_class:HAS_VARIABLE_CLASS]-(dataset_class_value)
            WITH dataset_class_value, has_variable_class
            MATCH (data_model_value:DataModelValue)-[:HAS_DATASET_CLASS]->(dataset_class_value)
            SET has_variable_class.version_number = data_model_value.version_number"""
        class_variable_uid = VariableClass.get_next_free_uid_and_increment_counter()
        db.cypher_query(
            create_class_variable,
            {
                "class_variable_uid": class_variable_uid,
                "dataset_class_uid": dataset_class_uid,
                "data_model_catalogue_name": data_model_catalogue_name,
                "label": label,
                "description": description,
                "title": title,
                "implementation_notes": implementation_notes,
                "mapping_instructions": mapping_instructions,
                "prompt": prompt,
                "question_text": question_text,
                "simple_datatype": simple_datatype,
                "role": role,
                "library_name": library_name,
            },
        )
        return VariableClassService().get_by_uid(
            uid=class_variable_uid,
            data_model_name=data_model_name,
            data_model_version=data_model_version,
        )

    @classmethod
    def create_dataset_variable(
        cls,
        dataset_uid: str,
        data_model_catalogue_name: str,
        data_model_ig_name: str,
        data_model_ig_version: str,
        class_variable_uid: str | None = None,
        label: str = "label",
        description: str = "description",
        title: str = "title",
        simple_datatype: str = "simple_datatype",
        role: str = "role",
        core: str = "core",
        references_codelist_uids: list[str] | None = None,
        library_name: str = SPONSOR_LIBRARY_NAME,
    ) -> DatasetVariableAPIModel:
        """
        Method uses cypher query to create DatasetVariable nodes because we don't have POST endpoints to instantiate these entities.

        :param dataset_uid
        :param data_model_catalogue_name
        :param data_model_ig_name
        :param data_model_ig_version
        :param class_variable_uid
        :param label
        :param description
        :param title
        :param simple_datatype
        :param role
        :param core
        :param references_codelist
        :param library_name
        """

        create_dataset_variable = """
            MERGE (dataset_variable_root:DatasetVariable {uid: $dataset_variable_uid})-[:HAS_INSTANCE]->(dataset_variable_value:DatasetVariableInstance
            {label: $label, description: $description, title: $title,
            simple_datatype: $simple_datatype, role: $role, core: $core})
            WITH dataset_variable_root, dataset_variable_value
            MATCH (data_model_catalogue:DataModelCatalogue {name: $data_model_catalogue_name})
            MERGE (data_model_catalogue)-[:HAS_DATASET_VARIABLE]->(dataset_variable_root)
            WITH dataset_variable_root, dataset_variable_value
            MATCH (dataset_root:Dataset {uid:$dataset_uid})-[:HAS_INSTANCE]->(dataset_value)
            MERGE (dataset_variable_value)<-[has_dataset_variable:HAS_DATASET_VARIABLE]-(dataset_value)
            WITH dataset_variable_root, dataset_variable_value, dataset_value, has_dataset_variable
            MATCH (class_variable_root:VariableClass {uid: $class_variable_uid})-[:HAS_INSTANCE]->(class_variable_value)
            MERGE (dataset_variable_value)-[:IMPLEMENTS_VARIABLE]->(class_variable_value)
            WITH dataset_value, has_dataset_variable, dataset_variable_value
            MATCH (dataset_value)<-[:HAS_DATASET]-(data_model_ig_value:DataModelIGValue)
            SET has_dataset_variable.version_number = data_model_ig_value.version_number
            WITH dataset_variable_value
            MATCH (codelist:CTCodelistRoot)
            WHERE codelist.uid IN $referenced_codelist_uids
            MERGE (dataset_variable_value)-[:REFERENCES_CODELIST]->(codelist)
            """
        dataset_variable_uid = DatasetVariable.get_next_free_uid_and_increment_counter()
        db.cypher_query(
            create_dataset_variable,
            {
                "dataset_variable_uid": dataset_variable_uid,
                "dataset_uid": dataset_uid,
                "data_model_catalogue_name": data_model_catalogue_name,
                "class_variable_uid": class_variable_uid,
                "label": label,
                "description": description,
                "title": title,
                "simple_datatype": simple_datatype,
                "role": role,
                "core": core,
                "referenced_codelist_uids": references_codelist_uids,
                "library_name": library_name,
            },
        )
        return DatasetVariableService().get_by_uid(
            uid=dataset_variable_uid,
            data_model_ig_name=data_model_ig_name,
            data_model_ig_version=data_model_ig_version,
        )

    @classmethod
    def create_dataset_scenario(
        cls,
        dataset_uid: str,
        data_model_catalogue_name: str,
        data_model_ig_name: str,
        data_model_ig_version: str,
        label: str = "label",
        library_name: str = SPONSOR_LIBRARY_NAME,
    ) -> DatasetScenarioAPIModel:
        """
        Method uses cypher query to create DatasetScenario nodes because we don't have POST endpoints to instantiate these entities.

        :param dataset_uid
        :param data_model_catalogue_name
        :param data_model_ig_name
        :param data_model_ig_version
        :param label
        :param library_name
        """

        create_dataset_scenario = """
            MERGE (dataset_scenario_root:DatasetScenario {uid: $dataset_scenario_uid})-[:HAS_INSTANCE]->
            (dataset_scenario_value:DatasetScenarioInstance{label: $label})
            WITH dataset_scenario_root, dataset_scenario_value
            MATCH (data_model_catalogue:DataModelCatalogue {name: $data_model_catalogue_name})
            MERGE (data_model_catalogue)-[:HAS_DATASET_SCENARIO]->(dataset_scenario_root)
            WITH dataset_scenario_root, dataset_scenario_value
            MATCH (dataset_root:Dataset {uid:$dataset_uid})-[:HAS_INSTANCE]->(dataset_value)
            MERGE (dataset_scenario_value)<-[has_dataset_scenario:HAS_DATASET_SCENARIO]-(dataset_value)
            WITH dataset_scenario_root, dataset_scenario_value, dataset_value, has_dataset_scenario
            MATCH (dataset_value)<-[:HAS_DATASET]-(data_model_ig_value:DataModelIGValue)
            SET has_dataset_scenario.version_number = data_model_ig_value.version_number"""
        dataset_scenario_uid = DatasetScenario.get_next_free_uid_and_increment_counter()
        db.cypher_query(
            create_dataset_scenario,
            {
                "dataset_scenario_uid": dataset_scenario_uid,
                "dataset_uid": dataset_uid,
                "data_model_catalogue_name": data_model_catalogue_name,
                "label": label,
                "library_name": library_name,
            },
        )
        return DatasetScenarioService().get_by_uid(
            uid=dataset_scenario_uid,
            data_model_ig_name=data_model_ig_name,
            data_model_ig_version=data_model_ig_version,
        )

    @classmethod
    def create_study_epoch(
        cls,
        *,
        study_uid: str,
        start_rule: str | None = None,
        end_rule: str | None = None,
        epoch: str | None = None,
        epoch_subtype: str,
        duration_unit: str | None = None,
        order: int | None = None,
        description: str | None = None,
        duration: int | None = 0,
        color_hash: str | None = None,
    ) -> StudyEpoch:
        epoch_create_input = StudyEpochCreateInput(
            study_uid=study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            epoch=epoch,
            epoch_subtype=epoch_subtype,
            duration_unit=duration_unit,
            order=order,
            description=description,
            duration=duration,
            color_hash=color_hash,
        )

        result: StudyEpoch = StudyEpochService().create(
            study_uid=study_uid, study_epoch_input=epoch_create_input
        )
        return result

    @classmethod
    def create_study_design_cell(
        cls,
        study_uid: str,
        study_epoch_uid: str,
        study_element_uid: str,
        study_arm_uid: str | None = None,
        study_branch_arm_uid: str | None = None,
        transition_rule: str | None = None,
        order: int | None = None,
    ) -> StudyDesignCell:
        design_cell_input = StudyDesignCellCreateInput(
            study_epoch_uid=study_epoch_uid,
            study_element_uid=study_element_uid,
            study_arm_uid=study_arm_uid,
            study_branch_arm_uid=study_branch_arm_uid,
            transition_rule=transition_rule,
            order=order,
        )

        result: StudyDesignCell = StudyDesignCellService().create(
            study_uid=study_uid, design_cell_input=design_cell_input
        )
        return result

    @classmethod
    def create_study_design_class(
        cls,
        study_uid: str,
        value: StudyDesignClassEnum,
    ) -> StudyDesignClass:
        study_design_class_input = StudyDesignClassInput(
            value=value,
        )

        result: StudyDesignClass = StudyDesignClassService().create(
            study_uid=study_uid, study_design_class_input=study_design_class_input
        )
        return result

    @classmethod
    def create_study_source_variable(
        cls,
        study_uid: str,
        source_variable: StudySourceVariableEnum,
        source_variable_description: str | None = None,
    ) -> StudySourceVariable:
        study_source_variable_input = StudySourceVariableInput(
            source_variable=source_variable,
            source_variable_description=source_variable_description,
        )

        result: StudySourceVariable = StudySourceVariableService().create(
            study_uid=study_uid, study_source_variable_input=study_source_variable_input
        )
        return result

    @classmethod
    def create_study_arm(
        cls,
        study_uid: str,
        name: str,
        short_name: str,
        label: str | None = None,
        code: str | None = None,
        description: str | None = None,
        randomization_group: str | None = None,
        number_of_subjects: int | None = None,
        arm_type_uid: str | None = None,
        merge_branch_for_this_arm_for_sdtm_adam: bool = False,
    ) -> StudySelectionArm:
        arm_input = StudySelectionArmCreateInput(
            name=name,
            short_name=short_name,
            label=label,
            code=code,
            description=description,
            randomization_group=randomization_group,
            number_of_subjects=number_of_subjects,
            arm_type_uid=arm_type_uid,
            merge_branch_for_this_arm_for_sdtm_adam=merge_branch_for_this_arm_for_sdtm_adam,
        )

        result: StudySelectionArm = StudyArmSelectionService().make_selection(
            study_uid=study_uid, selection_create_input=arm_input
        )
        return result

    @classmethod
    def create_study_cohort(
        cls,
        study_uid: str,
        name: str,
        short_name: str,
        code: str | None = None,
        description: str | None = None,
        number_of_subjects: int | None = None,
        branch_arm_uids: list[str] | None = None,
        arm_uids: list[str] | None = None,
    ) -> StudySelectionCohort:
        cohort_input = StudySelectionCohortCreateInput(
            name=name,
            short_name=short_name,
            code=code,
            description=description,
            number_of_subjects=number_of_subjects,
            branch_arm_uids=branch_arm_uids,
            arm_uids=arm_uids,
        )

        result: StudySelectionCohort = StudyCohortSelectionService().make_selection(
            study_uid=study_uid, selection_create_input=cohort_input
        )
        return result

    @classmethod
    def create_study_branch_arm(
        cls,
        study_uid: str,
        name: str,
        short_name: str,
        study_arm_uid: str,
        code: str | None = None,
        randomization_group: str | None = None,
        number_of_subjects: int | None = None,
        study_cohort_uid: str | None = None,
    ) -> StudySelectionBranchArm:
        branch_arm_input = StudySelectionBranchArmCreateInput(
            name=name,
            short_name=short_name,
            code=code,
            randomization_group=randomization_group,
            number_of_subjects=number_of_subjects,
            arm_uid=study_arm_uid,
            study_cohort_uid=study_cohort_uid,
        )

        result: (
            StudySelectionBranchArm
        ) = StudyBranchArmSelectionService().make_selection(
            study_uid=study_uid, selection_create_input=branch_arm_input
        )
        return result

    @classmethod
    def create_comment_thread(
        cls,
        topic_path="topic A",
        text="some thread text",
    ) -> CommentThread:
        service: CommentsService = CommentsService()
        payload = CommentThreadCreateInput(
            text=text,
            topic_path=topic_path,
        )
        return service.create_comment_thread(payload)

    @classmethod
    def create_comment_thread_reply(
        cls,
        thread_uid=None,
        text="some reply text",
    ) -> CommentReply:
        service: CommentsService = CommentsService()
        payload = CommentReplyCreateInput(
            text=text,
        )
        return service.create_comment_reply(thread_uid, payload)

    @classmethod
    def lock_study(cls, study_uid, reason_for_lock_term_uid: str) -> str:
        """locks a study version (giving it a study-title first), returns locked study version"""

        cls.set_study_title(study_uid)

        study_service = StudyService()
        study = study_service.lock(
            uid=study_uid,
            change_description=cls.random_str(prefix="v"),
            reason_for_lock_term_uid=reason_for_lock_term_uid,
        )
        latest_study_version = study.current_metadata.version_metadata.version_number

        return str(latest_study_version)

    @classmethod
    def release_study(cls, study_uid: str, reason_for_release_term_uid: str) -> str:
        """releases a study version, returns released study version"""

        cls.set_study_title(study_uid)

        study_service = StudyService()

        study_service.release(
            uid=study_uid,
            change_description=cls.random_str(prefix="release "),
            reason_for_release_uid=reason_for_release_term_uid,
        )

        study_history = study_service.get_study_snapshot_history(
            study_uid=study_uid
        ).items
        release_history = sorted(
            (
                item
                for item in study_history
                if StudyStatus.RELEASED in item.study_status
            ),
            key=lambda item: item.modified_date,
            reverse=True,
        )

        if not release_history:
            raise RuntimeError(
                f"No released study version was found in history of study {study_uid}"
            )

        return str(release_history[0].metadata_version)

    @classmethod
    def unlock_study(cls, study_uid, reason_for_unlock_term_uid: str):
        """unlocks study"""
        StudyService().unlock(
            uid=study_uid, reason_for_unlock_term_uid=reason_for_unlock_term_uid
        )

    @classmethod
    def lock_and_unlock_study(
        cls, study_uid, reason_for_lock_term_uid: str, reason_for_unlock_term_uid: str
    ) -> str:
        """locks a study version (giving it a study-title first), then unlocks it, returns locked study version"""

        latest_study_version = cls.lock_study(
            study_uid, reason_for_lock_term_uid=reason_for_lock_term_uid
        )
        cls.unlock_study(
            study_uid, reason_for_unlock_term_uid=reason_for_unlock_term_uid
        )
        return latest_study_version

    @classmethod
    def set_study_title(cls, study_uid, study_title: str | None = None) -> None:
        if study_title is None:
            study_title = cls.random_str(8, prefix="Study title ")

        StudyService().patch(
            uid=study_uid,
            dry=False,
            study_patch_request=StudyPatchRequestJsonModel(
                current_metadata=StudyMetadataJsonModel(
                    study_description=StudyDescriptionJsonModel(study_title=study_title)
                )
            ),
        )

    @classmethod
    def set_study_standard_version(
        cls,
        study_uid: str,
        package_name: str | None = None,
        catalogue: str | None = None,
        effective_date: datetime | None = None,
        create_codelists_and_terms_for_package: bool = True,
    ) -> None:
        date_now = datetime.now().date()
        if not catalogue:
            catalogue = settings.sdtm_ct_catalogue_name
        if not package_name:
            package_name = f"{catalogue} {date_now}"
        if not effective_date:
            effective_date = effective_date = datetime(
                date_now.year, date_now.month, date_now.day, tzinfo=timezone.utc
            )

        all_ct_packages = {
            ct_package.name: ct_package.uid
            for ct_package in CTPackageService().get_all_ct_packages(
                catalogue_name=catalogue
            )
        }
        if package_name not in all_ct_packages:
            # Create CTPackage
            standards_ct_package_uid = TestUtils.create_ct_package(
                catalogue=catalogue,
                name=package_name,
                approve_elements=False,
                effective_date=effective_date,
                number_of_codelists=3 if create_codelists_and_terms_for_package else 0,
            )
        else:
            standards_ct_package_uid = all_ct_packages[package_name]

        # StudyStandardVersion must be created before locking
        cls.create_study_standard_version(
            study_uid=study_uid, ct_package_uid=standards_ct_package_uid
        )

    @classmethod
    def edit_study_standard_version(
        cls,
        study_uid: str,
        study_standard_version_uid: str,
        ct_package_uid: str,
    ) -> None:
        service: StudyStandardVersionService = StudyStandardVersionService()
        payload = StudyStandardVersionEditInput(
            ct_package_uid=ct_package_uid,
        )
        return service.edit(
            study_uid=study_uid,
            study_standard_version_uid=study_standard_version_uid,
            study_standard_version_input=payload,
        )

    @classmethod
    def get_codelists_by_names(cls, codelist_names: list[str]) -> str:
        relevant_codelists = ",".join([f'"{item}"' for item in codelist_names])
        codelists_url = 'ct/codelists/names?page_size=10&filters={"name":{"v":[{relevant_codelists}], "op":"in"}}'.replace(
            "{relevant_codelists}", relevant_codelists
        )
        return TestClient(app).get(codelists_url).json()["items"]

    @classmethod
    def get_codelist_uid_by_name(cls, codelists: Any, name: str) -> str:
        return next(item for item in codelists if item["name"] == name)["codelist_uid"]

    @staticmethod
    def patch_soa_preferences(study_uid: str, **kwargs) -> StudySoaPreferences:
        return StudyService().patch_study_soa_preferences(
            study_uid, StudySoaPreferencesInput(**kwargs)
        )

    @staticmethod
    def post_study_preferred_time_unit(
        study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> StudyPreferredTimeUnit:
        return StudyService().post_study_preferred_time_unit(
            study_uid=study_uid,
            unit_definition_uid=unit_definition_uid,
            for_protocol_soa=for_protocol_soa,
        )

    @staticmethod
    def _get_version_from_list(versions, version):
        for v in versions:
            if v["version"] == version:
                return v
        return None

    @classmethod
    def run_integrity_checks_for_all_studies(
        cls, api_client: TestClient, mode: ValidationMode = ValidationMode.STRICT
    ) -> None:
        """
        Run integrity checks for all available studies in the database.

        Args:
            api_client: FastAPI test client to use for API calls
            mode: Validation mode - ValidationMode.STRICT raises exceptions on failure (default),
                  ValidationMode.WARNING logs failures but doesn't raise exceptions

        Raises:
            AssertionError: If no studies are found or if mode is strict and checks fail
        """
        # Get all studies from the API
        response = api_client.get("/studies/list")
        assert_response_status_code(response, 200)
        studies = response.json()

        assert len(studies) > 0, "No studies found to check"

        # Run integrity checks for each study
        all_failures = []

        for study_item in studies:
            study_uid = study_item["uid"]
            try:
                # Run checks with the specified mode
                results = execute_all_checks_for_study(study_uid, mode=mode)

                # Check if any checks failed
                failed_checks = [r for r in results if not r.passed]
                if failed_checks:
                    failure_info = {
                        "study_uid": study_uid,
                        "study_number": study_item.get("number", "N/A"),
                        "study_acronym": study_item.get("acronym", "N/A"),
                        "failed_checks": [
                            {
                                "check_id": check.check_id,
                                "description": check.description,
                                "noncompliant_count": check.noncompliant_count,
                                "error": check.error,
                            }
                            for check in failed_checks
                        ],
                    }
                    all_failures.append(failure_info)
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch any unexpected errors during integrity checks
                # We catch Exception here because integrity checks can raise various exceptions
                # (BusinessLogicException, database errors, etc.) and we want to report all of them
                all_failures.append(
                    {
                        "study_uid": study_uid,
                        "study_number": study_item.get("number", "N/A"),
                        "study_acronym": study_item.get("acronym", "N/A"),
                        "error": str(e),
                    }
                )

        # Report any failures found
        if all_failures:
            failure_messages = []
            for failure in all_failures:
                msg = (
                    f"Study {failure['study_uid']} "
                    f"({failure.get('study_acronym', 'N/A')}): "
                )
                if "failed_checks" in failure:
                    msg += f"{len(failure['failed_checks'])} integrity check(s) failed"
                    for check in failure["failed_checks"]:
                        msg += (
                            f"\n  - {check['check_id']}: {check['description']} "
                            f"(found {check['noncompliant_count']} noncompliant entities)"
                        )
                else:
                    msg += f"Error during integrity check: {failure.get('error', 'Unknown error')}"
                failure_messages.append(msg)

            # Log the failures
            logger = logging.getLogger(__name__)
            logger.warning(
                "Integrity check failures found for %d study(ies):\n%s",
                len(all_failures),
                "\n".join(failure_messages),
            )

            # In strict mode, raise an exception if any checks failed
            if mode == ValidationMode.STRICT:
                raise AssertionError(
                    f"Integrity checks failed for {len(all_failures)} study(ies):\n"
                    + "\n".join(failure_messages)
                )

        # Assert that we successfully checked all studies
        assert len(studies) > 0, "No studies were checked"

    @staticmethod
    def archive_activity(uid: str):
        service = ActivityService()
        service.archive(uid)

    @staticmethod
    def archive_activity_group(uid: str):
        service = ActivityGroupService()
        service.archive(uid)

    @staticmethod
    def archive_activity_subgroup(uid: str):
        service = ActivitySubGroupService()
        service.archive(uid)

    @staticmethod
    def archive_activity_instance(uid: str):
        service = ActivityInstanceService()
        service.archive(uid)

    @staticmethod
    def archive_activity_item_class(uid: str):
        service = ActivityItemClassService()
        service.archive(uid)

    @staticmethod
    def archive_compound(uid: str):
        service = CompoundService()
        service.archive(uid)

    @staticmethod
    def archive_compound_alias(uid: str):
        service = CompoundAliasService()
        service.archive(uid)

    @staticmethod
    def archive_active_substance(uid: str):
        service = ActiveSubstanceService()
        service.archive(uid)

    @staticmethod
    def archive_medicinal_product(uid: str):
        service = MedicinalProductService()
        service.archive(uid)

    @staticmethod
    def archive_pharmaceutical_product(uid: str):
        service = PharmaceuticalProductService()
        service.archive(uid)

    @staticmethod
    def archive_unit_definition(uid: str):
        service = UnitDefinitionService()
        service.archive(uid)
