# pylint: disable=broad-except
# pylint: disable=too-many-arguments
# pylint: disable=too-many-public-methods
# pylint: disable=dangerous-default-value
import csv
import io
import logging
from datetime import date, datetime, timedelta, timezone
from random import randint
from typing import Any
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
from clinical_mdr_api.main import app
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
    ActivityInstanceClassInput,
)
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityInstanceClassRelInput,
    ActivityItemClass,
    ActivityItemClassCreateInput,
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
from clinical_mdr_api.models.concepts.odms.odm_item import OdmItem, OdmItemPostInput
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    PharmaceuticalProduct,
    PharmaceuticalProductCreateInput,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
    UnitDefinitionPostInput,
)
from clinical_mdr_api.models.controlled_terminologies.configuration import (
    CTConfigPostInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelist,
    CTCodelistCreateInput,
    CTCodelistTermInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_package import CTPackage
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTerm,
    CTTermCreateInput,
    CTTermNameAndAttributes,
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
from clinical_mdr_api.models.standard_data_models.sponsor_model import SponsorModelInput
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
    Study,
    StudyCreateInput,
    StudyDescriptionJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
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
    StudySelectionActivity,
    StudySelectionActivityCreateInput,
    StudySelectionActivityInput,
    StudySelectionArm,
    StudySelectionArmCreateInput,
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
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    MultiTemplateParameterTerm,
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
from clinical_mdr_api.services.concepts.odms.odm_items import OdmItemService
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
from clinical_mdr_api.services.controlled_terminologies.configuration import (
    CTConfigService,
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
from clinical_mdr_api.services.dictionaries.dictionary_codelist_generic_service import (
    DictionaryCodelistGenericService as DictionaryCodelistService,
)
from clinical_mdr_api.services.dictionaries.dictionary_term_generic_service import (
    DictionaryTermGenericService as DictionaryTermService,
)
from clinical_mdr_api.services.feature_flags import FeatureFlagService
from clinical_mdr_api.services.libraries import libraries as library_service
from clinical_mdr_api.services.notifications import NotificationService
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
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_arm_selection import (
    StudyArmSelectionService,
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
    initialize_ct_data_map,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common import config
from common.auth.dependencies import dummy_user_auth
from common.auth.user import clear_users_cache
from common.config import DEFAULT_STUDY_FIELD_CONFIG_FILE

log = logging.getLogger(__name__)


class CTCodelistConfig:
    default: str
    dosage_form: str
    delivery_device: str
    frequency: str
    dispenser: str
    roa: str
    adverse_events: str

    def __init__(self, **kwargs: str):
        for key, value in kwargs.items():
            setattr(self, key, value)


AUTHOR = "test"
STUDY_UID = "study_root"
PROJECT_NUMBER = "123"
LIBRARY_NAME = "Sponsor"
CDISC_LIBRARY_NAME = "CDISC"
CT_CATALOGUE_NAME = "SDTM CT"
CT_CODELIST_UIDS: CTCodelistConfig = CTCodelistConfig(
    default="C66737",
    dosage_form="C66726",
    delivery_device="CDEVICE123",
    frequency="C71113",
    dispenser="CDISP123",
    roa="C66729",
    adverse_events="C66734",
)
CT_CODELIST_NAMES = CTCodelistConfig(
    default="CT Codelist",
    dosage_form="Pharmaceutical Dosage Form",
    delivery_device="Delivery Device",
    frequency="Frequency",
    dispenser="Compound Dispensed In",
    roa="Route of Administration",
    adverse_events="SDTM Domain Abbreviation",
)

CT_CODELIST_LIBRARY = "CDISC"
CT_CODELIST_LIBRARY_SPONSOR = "Sponsor"
CT_PACKAGE_NAME = f"SDTM CT {datetime.now().strftime('%Y-%m-%d')}"
DICTIONARY_CODELIST_NAME = "UCUM"
DICTIONARY_CODELIST_LIBRARY = "UCUM"


class TestUtils:
    """Class containing methods that create all kinds of entities, e.g. library compounds"""

    sequential_study_number: int = 0

    @classmethod
    def assert_response_shape_ok(
        cls,
        response_json: any,
        expected_fields: list[str],
        expected_not_null_fields: list[str],
    ):
        assert set(list(response_json.keys())) == set(expected_fields)
        for key in expected_not_null_fields:
            assert response_json[key] is not None, f"Field '{key}' is None"

    @classmethod
    def assert_timestamp_is_in_utc_zone(cls, val: str):
        datetime_ts: datetime = datetime.strptime(val, config.DATE_TIME_FORMAT)
        assert datetime_ts.tzinfo == timezone.utc

    @classmethod
    def assert_timestamp_is_newer_than(cls, val: str, seconds: int):
        datetime_ts: datetime = datetime.strptime(val, config.DATE_TIME_FORMAT)
        assert abs(datetime.now(timezone.utc) - datetime_ts) < timedelta(
            seconds=seconds
        )

    @classmethod
    def assert_chronological_sequence(cls, val1: str, val2: str):
        """Asserts that val1 timestamp is chronologically older than val2 timestamp"""
        ts1: datetime = datetime.strptime(val1, config.DATE_TIME_FORMAT)
        ts2: datetime = datetime.strptime(val2, config.DATE_TIME_FORMAT)
        assert ts1 - ts2 < timedelta(seconds=0)

    @classmethod
    def assert_sort_order(cls, items: list[dict], key: str, desc: bool = False):
        """Asserts that the supplied list of dictionaries is sorted by `key` in expected order"""
        sorted_items = sorted(items, key=lambda x: x[key], reverse=desc)
        assert items == sorted_items

    @classmethod
    def get_datetime(cls, val: str) -> datetime:
        """Returns datetime object from supplied string value"""
        return datetime.strptime(val, config.DATE_TIME_FORMAT)

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
        params: dict | None = None,
    ):
        """Verifies that the specified endpoint returns valid csv/xml/Excel content"""
        headers = {"Accept": export_format}
        log.info("GET %s | %s", url, headers)
        response = api_client.get(url, headers=headers, params=params)

        assert_response_status_code(response, 200)
        assert export_format in response.headers["content-type"]

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
        return prefix + str(randint(1, 10**length - 1))

    @classmethod
    def random_if_none(cls, val, length: int = 10, prefix: str = ""):
        """Return supplied `val` if its value is not None.
        Otherwise, return random numerical string of `length` with optional string prefix (length excludes prefix)
        """
        return val if val else cls.random_str(length, prefix)

    @classmethod
    def create_dummy_user(cls):
        clear_users_cache()
        dummy_user_auth()

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
        name: str = "Feature Flag Name",
        enabled: bool = False,
        description: str | None = "Feature Flag Description",
    ) -> FeatureFlag:
        service = FeatureFlagService()
        payload = FeatureFlagInput(name=name, enabled=enabled, description=description)
        return service.create_feature_flag(payload)

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
        service = NotificationService()
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
        library_name: str | None = LIBRARY_NAME,
        name: str | None = None,
        name_sentence_case: str | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        template_parameter: bool | None = True,
    ) -> TextValue:
        service = TextValueService()
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

        result: TextValue = service.create(payload)
        return result

    @classmethod
    def create_objective_template(
        cls,
        name: str | None = None,
        guidance_text: str | None = None,
        study_uid: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        indication_uids: list[str] | None = None,
        is_confirmatory_testing: bool = False,
        category_uids: list[str] | None = None,
        approve: bool = True,
    ) -> ObjectiveTemplate:
        service = ObjectiveTemplateService()
        payload: ObjectiveTemplateCreateInput = ObjectiveTemplateCreateInput(
            name=cls.random_if_none(name, prefix="ot-"),
            guidance_text=guidance_text,
            study_uid=study_uid,
            library_name=library_name,
            indication_uids=indication_uids,
            is_confirmatory_testing=is_confirmatory_testing,
            category_uids=category_uids,
        )

        result: ObjectiveTemplate = service.create(payload)
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_endpoint_template(
        cls,
        name: str | None = None,
        guidance_text: str | None = None,
        study_uid: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        indication_uids: list[str] | None = None,
        category_uids: list[str] | None = None,
        sub_category_uids: list[str] | None = None,
        approve: bool = True,
    ) -> EndpointTemplate:
        service = EndpointTemplateService()
        payload: EndpointTemplateCreateInput = EndpointTemplateCreateInput(
            name=cls.random_if_none(name, prefix="et-"),
            guidance_text=guidance_text,
            study_uid=study_uid,
            library_name=library_name,
            indication_uids=indication_uids,
            category_uids=category_uids,
            sub_category_uids=sub_category_uids,
        )

        result: EndpointTemplate = service.create(payload)
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_activity_instruction_template(
        cls,
        name: str | None = None,
        guidance_text: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        indication_uids: list[str] | None = None,
        activity_uids: list[str] | None = None,
        activity_group_uids: list[str] | None = None,
        activity_subgroup_uids: list[str] | None = None,
        approve: bool = True,
    ) -> ActivityInstructionTemplate:
        service = ActivityInstructionTemplateService()
        payload: ActivityInstructionTemplateCreateInput = (
            ActivityInstructionTemplateCreateInput(
                name=cls.random_if_none(name, prefix="ct-"),
                guidance_text=cls.random_if_none(guidance_text),
                library_name=library_name,
                indication_uids=indication_uids,
                activity_uids=activity_uids,
                activity_group_uids=activity_group_uids,
                activity_subgroup_uids=activity_subgroup_uids,
            )
        )

        result: ActivityInstructionTemplate = service.create(payload)
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_criteria_template(
        cls,
        name: str | None = None,
        guidance_text: str | None = None,
        study_uid: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        type_uid: str | None = None,
        indication_uids: list[str] | None = None,
        category_uids: list[str] | None = None,
        sub_category_uids: list[str] | None = None,
        approve: bool = True,
    ) -> CriteriaTemplate:
        service = CriteriaTemplateService()
        payload: CriteriaTemplateCreateInput = CriteriaTemplateCreateInput(
            name=cls.random_if_none(name, prefix="ct-"),
            guidance_text=cls.random_if_none(guidance_text),
            study_uid=study_uid,
            library_name=library_name,
            type_uid=type_uid,
            indication_uids=indication_uids,
            category_uids=category_uids,
            sub_category_uids=sub_category_uids,
        )

        result: CriteriaTemplate = service.create(payload)
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_footnote_template(
        cls,
        name: str | None = None,
        study_uid: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        type_uid: str | None = None,
        indication_uids: list[str] | None = None,
        activity_uids: list[str] | None = None,
        activity_group_uids: list[str] | None = None,
        activity_subgroup_uids: list[str] | None = None,
        approve: bool = True,
    ) -> FootnoteTemplate:
        service = FootnoteTemplateService()
        payload: FootnoteTemplateCreateInput = FootnoteTemplateCreateInput(
            name=cls.random_if_none(name, prefix="ct-"),
            study_uid=study_uid,
            library_name=library_name,
            type_uid=type_uid,
            indication_uids=indication_uids,
            activity_uids=activity_uids,
            activity_group_uids=activity_group_uids,
            activity_subgroup_uids=activity_subgroup_uids,
        )

        result: FootnoteTemplate = service.create(payload)
        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_timeframe_template(
        cls,
        name: str | None = None,
        guidance_text: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        approve: bool = True,
    ) -> TimeframeTemplate:
        service = TimeframeTemplateService()
        payload: TimeframeTemplateCreateInput = TimeframeTemplateCreateInput(
            name=cls.random_if_none(name, prefix="tt-"),
            guidance_text=guidance_text,
            library_name=library_name,
        )

        result: TimeframeTemplate = service.create(payload)
        if approve:
            result = service.approve(result.uid)
        return result

    # endregion

    # region Syntax Instances
    @classmethod
    def create_activity_instruction(
        cls,
        activity_instruction_template_uid: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        parameter_terms: list[MultiTemplateParameterTerm] | None = None,
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

        service = ActivityInstructionService()
        payload: ActivityInstructionCreateInput = ActivityInstructionCreateInput(
            activity_instruction_template_uid=activity_instruction_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms,
        )

        result = service.create(payload)
        if approve:
            result: ActivityInstruction = service.approve(result.uid)
        return result

    @classmethod
    def create_footnote(
        cls,
        footnote_template_uid: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        parameter_terms: list[MultiTemplateParameterTerm] = [],
        approve: bool = True,
    ) -> Footnote:
        if not footnote_template_uid:
            footnote_template_uid = cls.create_footnote_template(
                name="test name",
                study_uid=None,
                library_name="Sponsor",
                type_uid=cls.create_ct_term(
                    sponsor_preferred_name="INCLUSION FOOTNOTE"
                ).term_uid,
                indication_uids=[],
                activity_uids=[],
                activity_group_uids=[],
                activity_subgroup_uids=[],
            ).uid

        service = FootnoteService()
        payload: FootnoteCreateInput = FootnoteCreateInput(
            footnote_template_uid=footnote_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms,
        )

        result = service.create(payload)
        if approve:
            result: Footnote = service.approve(result.uid)
        return result

    @classmethod
    def create_criteria(
        cls,
        criteria_template_uid: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        parameter_terms: list[MultiTemplateParameterTerm] | None = None,
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

        service = CriteriaService()
        payload: CriteriaCreateInput = CriteriaCreateInput(
            criteria_template_uid=criteria_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms,
        )

        result = service.create(payload)
        if approve:
            result: Criteria = service.approve(result.uid)
        return result

    @classmethod
    def create_endpoint(
        cls,
        endpoint_template_uid: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        parameter_terms: list[MultiTemplateParameterTerm] | None = None,
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

        service = EndpointService()
        payload: EndpointCreateInput = EndpointCreateInput(
            endpoint_template_uid=endpoint_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms,
        )

        result = service.create(payload)
        if approve:
            result: Endpoint = service.approve(result.uid)
        return result

    @classmethod
    def create_objective(
        cls,
        objective_template_uid: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        parameter_terms: list[MultiTemplateParameterTerm] | None = None,
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

        service = ObjectiveService()
        payload: ObjectiveCreateInput = ObjectiveCreateInput(
            objective_template_uid=objective_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms,
        )

        result = service.create(payload)
        if approve:
            result: Objective = service.approve(result.uid)
        return result

    @classmethod
    def create_timeframe(
        cls,
        timeframe_template_uid: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        parameter_terms: list[MultiTemplateParameterTerm] | None = None,
        approve: bool = True,
    ) -> Timeframe:
        if not timeframe_template_uid:
            timeframe_template_uid = cls.create_timeframe_template(
                name="test name",
                guidance_text="guidance text",
                library_name="Sponsor",
            ).uid

        service = TimeframeService()
        payload: TimeframeCreateInput = TimeframeCreateInput(
            timeframe_template_uid=timeframe_template_uid,
            library_name=library_name,
            parameter_terms=parameter_terms,
        )

        result = service.create(payload)
        if approve:
            result: Timeframe = service.approve(result.uid)
        return result

    # endregion

    # region Syntax Pre-Instances

    @classmethod
    def create_activity_instruction_pre_instance(
        cls,
        template_uid: str | None = None,
        parameter_terms: list[MultiTemplateParameterTerm] | None = None,
        indication_uids: list[str] | None = None,
        activity_uids: list[str] | None = None,
        activity_group_uids: list[str] | None = None,
        activity_subgroup_uids: list[str] | None = None,
        library_name: str | None = LIBRARY_NAME,
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
                activity_subgroup_uids=[
                    cls.create_activity_subgroup(
                        name="test", activity_groups=[activity_group_uid]
                    ).uid
                ],
                approve=False,
            ).uid

        service = ActivityInstructionPreInstanceService()
        payload: ActivityInstructionPreInstanceCreateInput = (
            ActivityInstructionPreInstanceCreateInput(
                library_name=library_name,
                parameter_terms=parameter_terms,
                indication_uids=indication_uids,
                activity_uids=activity_uids,
                activity_group_uids=activity_group_uids,
                activity_subgroup_uids=activity_subgroup_uids,
            )
        )

        result: ActivityInstructionPreInstance = service.create(
            payload, template_uid=template_uid
        )

        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_endpoint_pre_instance(
        cls,
        template_uid: str | None = None,
        parameter_terms: list[MultiTemplateParameterTerm] | None = None,
        indication_uids: list[str] | None = None,
        category_uids: list[str] | None = None,
        sub_category_uids: list[str] | None = None,
        library_name: str | None = LIBRARY_NAME,
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

        service = EndpointPreInstanceService()
        payload: EndpointPreInstanceCreateInput = EndpointPreInstanceCreateInput(
            library_name=library_name,
            parameter_terms=parameter_terms,
            indication_uids=indication_uids,
            category_uids=category_uids,
            sub_category_uids=sub_category_uids,
        )

        result: EndpointPreInstance = service.create(payload, template_uid=template_uid)

        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_objective_pre_instance(
        cls,
        template_uid: str | None = None,
        is_confirmatory_testing: bool = False,
        parameter_terms: list[MultiTemplateParameterTerm] | None = None,
        indication_uids: list[str] | None = None,
        category_uids: list[str] | None = None,
        library_name: str | None = LIBRARY_NAME,
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

        service = ObjectivePreInstanceService()
        payload: ObjectivePreInstanceCreateInput = ObjectivePreInstanceCreateInput(
            library_name=library_name,
            is_confirmatory_testing=is_confirmatory_testing,
            parameter_terms=parameter_terms,
            indication_uids=indication_uids,
            category_uids=category_uids,
        )

        result: ObjectivePreInstance = service.create(
            payload, template_uid=template_uid
        )

        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_footnote_pre_instance(
        cls,
        template_uid: str | None = None,
        parameter_terms: list[MultiTemplateParameterTerm] | None = None,
        indication_uids: list[str] | None = None,
        activity_uids: list[str] | None = None,
        activity_group_uids: list[str] | None = None,
        activity_subgroup_uids: list[str] | None = None,
        library_name: str | None = LIBRARY_NAME,
        approve: bool = True,
    ) -> FootnotePreInstance:
        if not template_uid:
            activity_group_uid = cls.create_activity_group(name="test").uid
            template_uid = cls.create_footnote_template(
                name="name",
                study_uid=None,
                library_name="Sponsor",
                indication_uids=[],
                activity_uids=[],
                activity_group_uids=[activity_group_uid],
                activity_subgroup_uids=[
                    cls.create_activity_subgroup(
                        name="test", activity_groups=[activity_group_uid]
                    ).uid
                ],
            ).uid

        service = FootnotePreInstanceService()
        payload: FootnotePreInstanceCreateInput = FootnotePreInstanceCreateInput(
            library_name=library_name,
            parameter_terms=parameter_terms,
            indication_uids=indication_uids,
            activity_uids=activity_uids,
            activity_group_uids=activity_group_uids,
            activity_subgroup_uids=activity_subgroup_uids,
        )

        result: FootnotePreInstance = service.create(payload, template_uid=template_uid)

        if approve:
            result = service.approve(result.uid)
        return result

    @classmethod
    def create_criteria_pre_instance(
        cls,
        template_uid: str | None = None,
        parameter_terms: list[MultiTemplateParameterTerm] | None = None,
        indication_uids: list[str] | None = None,
        category_uids: list[str] | None = None,
        sub_category_uids: list[str] | None = None,
        library_name: str | None = LIBRARY_NAME,
        approve: bool = True,
    ) -> CriteriaPreInstance:
        if not template_uid:
            template_uid = cls.create_criteria_template(
                name="name",
                guidance_text="guidance text",
                study_uid=None,
                library_name="Sponsor",
                indication_uids=[],
                category_uids=[],
            ).uid

        service = CriteriaPreInstanceService()
        payload: CriteriaPreInstanceCreateInput = CriteriaPreInstanceCreateInput(
            library_name=library_name,
            parameter_terms=parameter_terms,
            indication_uids=indication_uids,
            category_uids=category_uids,
            sub_category_uids=sub_category_uids,
        )

        result: CriteriaPreInstance = service.create(payload, template_uid=template_uid)

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
        library_name=LIBRARY_NAME,
        is_sponsor_compound=True,
        external_id=None,
        approve: bool = False,
    ) -> Compound:
        service = CompoundService()
        payload: CompoundCreateInput = CompoundCreateInput(
            name=cls.random_if_none(name, prefix="name-"),
            name_sentence_case=cls.random_if_none(
                name_sentence_case, prefix="name_sentence_case-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbreviation-"),
            library_name=library_name,
            is_sponsor_compound=is_sponsor_compound if is_sponsor_compound else True,
            external_id=cls.random_if_none(external_id, prefix="prodex-id-"),
        )

        result: Compound = service.create(payload)
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
        library_name=LIBRARY_NAME,
        is_preferred_synonym=None,
        compound_uid=None,
        approve: bool = False,
    ) -> CompoundAlias:
        service = CompoundAliasService()
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
            compound_uid=compound_uid if compound_uid else None,
        )

        result: CompoundAlias = service.create(payload)
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
        library_name=LIBRARY_NAME,
        unii_term_uid=None,
        approve: bool = False,
    ) -> ActiveSubstance:
        service = ActiveSubstanceService()
        payload: ActiveSubstanceCreateInput = ActiveSubstanceCreateInput(
            external_id=cls.random_if_none(external_id, prefix="prodex-id-"),
            analyte_number=cls.random_if_none(analyte_number, prefix="analyte-"),
            short_number=cls.random_if_none(short_number, prefix="short-number-"),
            long_number=cls.random_if_none(long_number, prefix="long-number-"),
            inn=cls.random_if_none(inn, prefix="inn-"),
            library_name=library_name,
            unii_term_uid=unii_term_uid if unii_term_uid else None,
        )

        result: ActiveSubstance = service.create(payload)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_pharmaceutical_product(
        cls,
        external_id=None,
        library_name=LIBRARY_NAME,
        dosage_form_uids=None,
        route_of_administration_uids=None,
        formulations=None,
        approve: bool = False,
    ) -> PharmaceuticalProduct:
        service = PharmaceuticalProductService()
        payload: PharmaceuticalProductCreateInput = PharmaceuticalProductCreateInput(
            external_id=cls.random_if_none(external_id, prefix="prodex-id-"),
            library_name=library_name,
            dosage_form_uids=dosage_form_uids if dosage_form_uids else [],
            route_of_administration_uids=(
                route_of_administration_uids if route_of_administration_uids else []
            ),
            formulations=formulations if formulations else [],
        )

        result: PharmaceuticalProduct = service.create(payload)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_medicinal_product(
        cls,
        external_id=None,
        name=None,
        name_sentence_case=None,
        library_name=LIBRARY_NAME,
        dose_value_uids=None,
        dose_frequency_uid=None,
        delivery_device_uid=None,
        dispenser_uid=None,
        pharmaceutical_product_uids=None,
        compound_uid=None,
        approve: bool = False,
    ) -> MedicinalProduct:
        service = MedicinalProductService()
        payload: MedicinalProductCreateInput = MedicinalProductCreateInput(
            name=cls.random_if_none(name, prefix="name-"),
            name_sentence_case=cls.random_if_none(
                name_sentence_case, prefix="name_sentence_case-"
            ),
            external_id=cls.random_if_none(external_id, prefix="prodex-id-"),
            library_name=library_name,
            dose_value_uids=dose_value_uids if dose_value_uids else [],
            dose_frequency_uid=dose_frequency_uid,
            delivery_device_uid=delivery_device_uid,
            dispenser_uid=dispenser_uid,
            pharmaceutical_product_uids=(
                pharmaceutical_product_uids if pharmaceutical_product_uids else []
            ),
            compound_uid=compound_uid if compound_uid else None,
        )

        result: MedicinalProduct = service.create(payload)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_activity_instance(
        cls,
        activity_instance_class_uid: str,
        name: str = None,
        name_sentence_case: str | None = None,
        nci_concept_name: str | None = None,
        nci_concept_id: str | None = None,
        topic_code: str | None = None,
        molecular_weight: float | None = None,
        is_research_lab: bool = False,
        adam_param_code: str | None = None,
        is_required_for_activity: bool | None = False,
        is_default_selected_for_activity: bool | None = False,
        is_data_sharing: bool | None = False,
        is_legacy_usage: bool | None = False,
        is_derived: bool | None = False,
        legacy_description: bool | None = None,
        activities: list[Any] | None = None,
        activity_subgroups: list[Any] | None = None,
        activity_groups: list[Any] | None = None,
        activity_items: list[Any] | None = None,
        library_name: str | None = LIBRARY_NAME,
        approve: bool = True,
        retire_after_approve: bool = False,
        preview=False,
    ) -> ActivityInstance:
        service = ActivityInstanceService()
        groupings = []
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
        result: ActivityInstance = service.create(
            concept_input=activity_instance_input, preview=preview
        )
        if approve and not preview:
            service.approve(result.uid)
            if retire_after_approve:
                service.inactivate_final(result.uid)
        return result

    @classmethod
    def create_activity_instance_class(
        cls,
        name: str,
        order: int | None = None,
        definition: str | None = None,
        is_domain_specific: bool | None = None,
        level: int | None = None,
        parent_uid: str | None = None,
        data_domain_uids: list[str] | None = None,
        library_name: str | None = LIBRARY_NAME,
        approve: bool = True,
    ) -> ActivityInstanceClass:
        service = ActivityInstanceClassService()
        activity_instance_class_input: ActivityInstanceClassInput = (
            ActivityInstanceClassInput(
                name=name,
                order=order,
                definition=definition,
                is_domain_specific=is_domain_specific,
                level=level,
                parent_uid=parent_uid,
                data_domain_uids=data_domain_uids,
                library_name=library_name,
            )
        )
        result: ActivityInstanceClass = service.create(
            item_input=activity_instance_class_input
        )
        if approve:
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
        codelist_uids: list[str] | None = None,
        definition: str | None = None,
        nci_concept_id: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        approve: bool = True,
    ) -> ActivityItemClass:
        service = ActivityItemClassService()
        activity_item_class_input: ActivityItemClassCreateInput = (
            ActivityItemClassCreateInput(
                name=name,
                definition=definition,
                nci_concept_id=nci_concept_id,
                order=order,
                role_uid=role_uid,
                data_type_uid=data_type_uid,
                activity_instance_classes=activity_instance_classes,
                codelist_uids=codelist_uids or [],
                library_name=library_name,
            )
        )
        result: ActivityItemClass = service.create(item_input=activity_item_class_input)
        if approve:
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
        is_data_collected: bool | None = True,
        is_multiple_selection_allowed: bool | None = True,
        library_name: str | None = LIBRARY_NAME,
        approve: bool = True,
    ) -> Activity:
        service = ActivityService()
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
        result: Activity = service.create(concept_input=activity_create_input)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_activity_subgroup(
        cls,
        name: str,
        activity_groups: list[str],
        name_sentence_case: str | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        library_name: str | None = LIBRARY_NAME,
        approve: bool = True,
    ) -> ActivitySubGroup:
        service = ActivitySubGroupService()
        activity_subgroup_create_input: ActivitySubGroupCreateInput = (
            ActivitySubGroupCreateInput(
                name=name,
                name_sentence_case=name_sentence_case if name_sentence_case else name,
                definition=definition,
                abbreviation=abbreviation,
                activity_groups=activity_groups,
                library_name=library_name,
            )
        )
        result: ActivitySubGroup = service.create(
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
        library_name: str | None = LIBRARY_NAME,
        approve: bool = True,
    ) -> ActivityGroup:
        service = ActivityGroupService()
        activity_group_create_input: ActivityGroupCreateInput = (
            ActivityGroupCreateInput(
                name=name,
                name_sentence_case=name_sentence_case if name_sentence_case else name,
                definition=definition,
                abbreviation=abbreviation,
                library_name=library_name,
            )
        )
        result: ActivityGroup = service.create(
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
        service = StudyActivitySelectionService()
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

    @classmethod
    def delete_study(cls, study_uid: str):
        db.cypher_query(
            f"MATCH (r:StudyRoot {{uid:'{study_uid}'}})-[]-(v:StudyValue) DETACH DELETE r, v"
        )

    @classmethod
    def create_study_activity_schedule(
        cls,
        study_uid: str,
        study_visit_uid: str,
        study_activity_uid: str,
    ) -> StudyActivitySchedule:
        service = StudyActivityScheduleService()
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
        show_activity_in_protocol_flowchart: bool | None = None,
        show_activity_subgroup_in_protocol_flowchart: bool | None = None,
        show_activity_group_in_protocol_flowchart: bool | None = None,
        show_soa_group_in_protocol_flowchart: bool = False,
        soa_group_term_uid: str | None = None,
    ) -> StudyActivitySchedule:
        service = StudyActivitySelectionService()
        update = StudySelectionActivityInput(
            show_activity_in_protocol_flowchart=show_activity_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=show_activity_subgroup_in_protocol_flowchart,
            show_activity_group_in_protocol_flowchart=show_activity_group_in_protocol_flowchart,
            show_soa_group_in_protocol_flowchart=show_soa_group_in_protocol_flowchart,
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
        footnote_template_uid: str,
        referenced_items: list[ReferencedItem],
    ) -> StudySoAFootnote:
        service = StudySoAFootnoteService()
        study_soa_footnote_input: StudySoAFootnoteCreateInput = (
            StudySoAFootnoteCreateInput(
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
        study_epoch_uid: str,
        visit_type_uid: str,
        show_visit: bool,
        visit_contact_mode_uid: str,
        visit_class: str,
        is_global_anchor_visit: bool,
        time_reference_uid: str | None = None,
        time_value: int | None = None,
        time_unit_uid: str | None = None,
        visit_sublabel_reference: str | None = None,
        consecutive_visit_group: str | None = None,
        min_visit_window_value: int | None = None,
        max_visit_window_value: int | None = None,
        visit_window_unit_uid: str | None = None,
        description: str | None = None,
        start_rule: str | None = None,
        end_rule: str | None = None,
        epoch_allocation_uid: str | None = None,
        visit_subclass: str | None = None,
    ) -> StudyVisit:
        service = StudyVisitService(study_uid=study_uid)
        study_visit_input: StudyVisitCreateInput = StudyVisitCreateInput(
            study_epoch_uid=study_epoch_uid,
            visit_type_uid=visit_type_uid,
            time_reference_uid=time_reference_uid,
            time_value=time_value,
            time_unit_uid=time_unit_uid,
            visit_sublabel_reference=visit_sublabel_reference,
            consecutive_visit_group=consecutive_visit_group,
            show_visit=show_visit,
            min_visit_window_value=min_visit_window_value,
            max_visit_window_value=max_visit_window_value,
            visit_window_unit_uid=visit_window_unit_uid,
            description=description,
            start_rule=start_rule,
            end_rule=end_rule,
            visit_contact_mode_uid=visit_contact_mode_uid,
            epoch_allocation_uid=epoch_allocation_uid,
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
        library_name: str | None = LIBRARY_NAME,
        objective_level_uid: str | None = None,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
    ) -> StudySelectionObjective:
        if not parameter_terms:
            parameter_terms = []

        service = StudyObjectiveSelectionService()
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
        library_name: str | None = LIBRARY_NAME,
        study_objective_uid: str | None = None,
        endpoint_level_uid: str | None = None,
        endpoint_sublevel_uid: str | None = None,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
        endpoint_units: EndpointUnitsInput | None = None,
        timeframe_uid: str | None = None,
    ) -> StudySelectionEndpoint:
        service = StudyEndpointSelectionService()
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
        library_name: str | None = LIBRARY_NAME,
        parameter_terms: list[TemplateParameterMultiSelectInput] | None = None,
    ) -> StudySelectionCriteria:
        service = StudyCriteriaSelectionService()
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
    def create_study_compound(
        cls,
        study_uid: str,
        medicinal_product_uid=None,
        compound_alias_uid=None,
        type_of_treatment_uid=None,
        other_info=None,
        reason_for_missing_null_value_uid=None,
        delivery_device_uid=None,
        dispenser_uid=None,
        dose_frequency_uid=None,
        dose_value_uid=None,
    ) -> StudySelectionCompound:
        service = StudyCompoundSelectionService()
        payload: StudySelectionCompoundCreateInput = StudySelectionCompoundCreateInput(
            medicinal_product_uid=medicinal_product_uid,
            compound_alias_uid=compound_alias_uid,
            type_of_treatment_uid=type_of_treatment_uid,
            other_info=cls.random_if_none(other_info, prefix="other_info-"),
            reason_for_missing_null_value_uid=reason_for_missing_null_value_uid,
            delivery_device_uid=delivery_device_uid if delivery_device_uid else None,
            dispenser_uid=dispenser_uid if dispenser_uid else None,
            dose_frequency_uid=dose_frequency_uid if dose_frequency_uid else None,
            dose_value_uid=dose_value_uid if dose_value_uid else None,
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
        service = StudyCompoundDosingSelectionService()
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
        service = StudyElementSelectionService()
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
        library_name=LIBRARY_NAME,
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
        service = UnitDefinitionService(meta_repository=MetaRepository(AUTHOR))

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

        result: UnitDefinitionModel = service.post(post_input=payload)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_odm_item(
        cls,
        name=None,
        library_name=LIBRARY_NAME,
        oid=None,
        datatype=None,
        prompt=None,
        length=None,
        significant_digits=None,
        sas_field_name=None,
        sds_var_name=None,
        origin=None,
        comment=None,
        descriptions=None,
        alias_uids=None,
        codelist_uid=None,
        unit_definitions=None,
        terms=None,
        approve: bool = True,
    ) -> UnitDefinitionModel:
        if not terms:
            terms = []
        if not descriptions:
            descriptions = []
        if not unit_definitions:
            unit_definitions = []
        if not alias_uids:
            alias_uids = []

        service = OdmItemService()

        payload: OdmItemPostInput = OdmItemPostInput(
            library_name=library_name,
            name=cls.random_if_none(name),
            oid=cls.random_if_none(oid),
            datatype=cls.random_if_none(datatype),
            prompt=cls.random_if_none(prompt),
            length=length,
            significant_digits=significant_digits,
            sas_field_name=cls.random_if_none(sas_field_name),
            sds_var_name=cls.random_if_none(sds_var_name),
            origin=cls.random_if_none(origin),
            comment=cls.random_if_none(comment),
            descriptions=descriptions,
            alias_uids=alias_uids,
            codelist_uid=codelist_uid,
            unit_definitions=unit_definitions,
            terms=terms,
        )

        result: OdmItem = service.create_with_relations(concept_input=payload)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_library(cls, name: str = LIBRARY_NAME, is_editable: bool = True) -> dict:
        libraries = library_service.get_libraries(is_editable)
        existing_library = next((x for x in libraries if x["name"] == name), None)

        if not existing_library:
            return library_service.create(name, is_editable)
        return existing_library

    @classmethod
    def create_project(
        cls,
        name="Project ABC",
        project_number=PROJECT_NUMBER,
        description="Base project",
        clinical_programme_uid=None,
    ) -> Project:
        service = ProjectService()
        payload = ProjectCreateInput(
            name=name,
            project_number=project_number,
            description=description,
            clinical_programme_uid=clinical_programme_uid,
        )
        return service.create(payload)

    @classmethod
    def create_clinical_programme(cls, name: str = "CP") -> ClinicalProgramme:
        service = ClinicalProgrammeService()
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
        project_number: str | None = PROJECT_NUMBER,
        description: str | None = None,
        study_parent_part_uid: str | None = None,
    ) -> Study:
        service = StudyService()
        if not study_parent_part_uid:
            payload = StudyCreateInput(
                study_number=cls.get_study_number(number),
                study_acronym=cls.random_if_none(acronym, prefix="st-"),
                project_number=project_number,
                description=cls.random_if_none(description),
            )
        else:
            payload = StudySubpartCreateInput(
                study_acronym=cls.random_if_none(acronym, prefix="st-"),
                study_subpart_acronym=cls.random_if_none(subpart_acronym, prefix="st-"),
                description=cls.random_if_none(description),
                study_parent_part_uid=study_parent_part_uid,
            )
        return service.create(payload)

    @classmethod
    def create_study_standard_version(
        cls,
        study_uid: str,
        ct_package_uid: str,
    ) -> Study:
        service = StudyStandardVersionService()
        payload = StudyStandardVersionInput(
            ct_package_uid=ct_package_uid,
        )
        return service.create(study_uid=study_uid, study_standard_version_input=payload)

    @classmethod
    def create_ct_term(
        cls,
        catalogue_name: str = CT_CATALOGUE_NAME,
        codelist_uid: str = CT_CODELIST_UIDS.default,
        code_submission_value: str | None = None,
        name_submission_value: str | None = None,
        nci_preferred_name: str | None = None,
        definition: str | None = None,
        sponsor_preferred_name: str | None = None,
        sponsor_preferred_name_sentence_case: str | None = None,
        order: int | None = None,
        library_name: str = CT_CODELIST_LIBRARY_SPONSOR,
        approve: bool = True,
        effective_date: datetime | None = None,
    ) -> CTTerm:
        service = CTTermService()
        payload = CTTermCreateInput(
            catalogue_name=catalogue_name,
            codelist_uid=codelist_uid,
            code_submission_value=cls.random_if_none(
                code_submission_value, prefix="code_submission_value-"
            ),
            name_submission_value=cls.random_if_none(
                name_submission_value, prefix="name_submission_value-"
            ),
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
            order=order,
            library_name=library_name,
        )
        ct_term: CTTerm = service.create(payload, start_date=effective_date)
        if approve:
            CTTermAttributesService().approve(term_uid=ct_term.term_uid)
            CTTermNameService().approve(term_uid=ct_term.term_uid)
        return ct_term

    @classmethod
    def add_ct_term_parent(
        cls,
        term,
        parent=None,
        relationship_type: str = "type",
        parent_uid: str | None = None,
    ) -> CTTerm:
        service = CTTermService()
        service.add_parent(
            term_uid=term.term_uid,
            parent_uid=parent_uid if parent_uid else parent.term_uid,
            relationship_type=relationship_type,
        )

    @classmethod
    def create_sponsor_ct_package(
        cls,
        extends_package: str | None = None,
        effective_date: date | None = date.today(),
    ) -> CTPackage:
        package = CTPackageService().create_sponsor_ct_package(
            extends_package=extends_package, effective_date=effective_date
        )
        return package

    @classmethod
    def create_ct_package(
        cls,
        number_of_codelists: int = 3,
        catalogue: str = CT_CATALOGUE_NAME,
        name: str = CT_PACKAGE_NAME,
        import_date: datetime | None = datetime.now(),
        effective_date: datetime | None = datetime.now(),
        library_name: str | None = CT_CODELIST_LIBRARY,
        approve_elements: bool = False,
    ) -> CTPackage:
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
                terms=[CTCodelistTermInput(term_uid=terms[i].term_uid)],
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
        for attribute, value in CT_CODELIST_NAMES.__dict__.items():
            db.cypher_query(
                """
            MATCH (library:Library {name:$library})
            MATCH (catalogue:CTCatalogue {name:$catalogue})
            MERGE (library)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot {uid: $uid})-[:HAS_NAME_ROOT]->
            (codelist_ver_root:CTCodelistNameRoot)-[:LATEST]->(codelist_ver_value:CTCodelistNameValue {
            name: $name,
            name_sentence_case: $uid + 'name'})
            MERGE (codelist_root)-[:HAS_ATTRIBUTES_ROOT]->(codelist_a_root:CTCodelistAttributesRoot)
            -[:LATEST]->(codelist_a_value:CTCodelistAttributesValue {definition:$uid + ' DEF',
            name:$uid + ' NAME', preferred_term:$uid + ' PREF', submission_value:$uid + ' SUMBVAL', extensible:true})
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
                    "library": LIBRARY_NAME,
                    "catalogue": CT_CATALOGUE_NAME,
                },
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
        template_parameter: bool = False,
        parent_codelist_uid: str | None = None,
        terms: list[CTCodelistTermInput] | None = None,
        library_name: str = LIBRARY_NAME,
        approve: bool = False,
        effective_date: datetime | None = None,
    ) -> CTCodelist:
        if terms is None:
            terms = []

        service = CTCodelistService()
        payload = CTCodelistCreateInput(
            catalogue_name=catalogue_name,
            name=cls.random_if_none(name, prefix="name-"),
            submission_value=cls.random_if_none(
                submission_value, prefix="submission_value-"
            ),
            nci_preferred_name=cls.random_if_none(
                nci_preferred_name, prefix="nci_name-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            extensible=extensible,
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
        return result

    @classmethod
    def create_dictionary_codelist(
        cls,
        name: str | None = DICTIONARY_CODELIST_NAME,
        template_parameter: bool | None = False,
        library_name: str | None = DICTIONARY_CODELIST_LIBRARY,
        approve: bool | None = True,
    ) -> DictionaryCodelist:
        service = DictionaryCodelistService()
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
        library_name: str | None = DICTIONARY_CODELIST_LIBRARY,
        approve: bool | None = True,
    ) -> DictionaryTerm:
        service = DictionaryTermService()
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
        unit: str | None = None,
        name: str | None = None,
        name_sentence_case: str | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        library_name: str = LIBRARY_NAME,
        template_parameter: bool = False,
        value: float | None = None,
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

        service = NumericValueWithUnitService()
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

        result: NumericValueWithUnit = service.create(payload)
        return result

    @classmethod
    def create_lag_time(
        cls,
        unit: str | None = None,
        sdtm_domain_label: str = "Adverse Event Domain",
        name: str | None = None,
        name_sentence_case: str | None = None,
        definition: str | None = None,
        abbreviation: str | None = None,
        library_name: str = LIBRARY_NAME,
        template_parameter: bool = False,
        value: float | None = None,
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

        service = LagTimeService()
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

        result: NumericValueWithUnit = service.create(payload)
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
        return UnitDefinitionService(meta_repository=MetaRepository(AUTHOR)).get_by_uid(
            uid=unit_uid,
            at_specified_datetime=at_specified_datetime,
            status=status,
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
    def create_brand(
        cls,
        name: str | None = None,
    ) -> Brand:
        service = BrandService()
        return service.create(BrandCreateInput(name=name))

    @classmethod
    def create_ct_catalogue(
        cls, library: str = LIBRARY_NAME, catalogue_name: str = CT_CATALOGUE_NAME
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
    def create_study_ct_data_map(
        cls,
        codelist_uid: str,
        # pylint: disable=dangerous-default-value
        ct_data_map: dict = initialize_ct_data_map,
        library_name: str = LIBRARY_NAME,
    ):
        dictionary_codelist = cls.create_dictionary_codelist()
        # used cypher below to manually assign uids related to CDISC concept_ids
        create_ct_term_with_custom_uid_query = """
            MATCH (codelist_root:CTCodelistRoot {uid:$codelist_uid})
            WITH codelist_root
            MERGE (term_root:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->(term_ver_root:CTTermNameRoot)-
                [:LATEST]->(term_ver_value:CTTermNameValue {name: $name, name_sentence_case: toLower($name)})
            MERGE (term_ver_root)-[final:LATEST_FINAL]->(term_ver_value)
            MERGE (term_ver_root)-[hasver:HAS_VERSION]->(term_ver_value)
            MERGE (codelist_root)-[:HAS_TERM]->(term_root)
            WITH term_root, final, hasver
            MATCH (library:Library {name:$library_name})
            WITH library, term_root, final, hasver
            MERGE (library)-[:CONTAINS_TERM]->(term_root)""" + cls.set_final_props(
            "hasver"
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

            if isinstance(value, list):
                for uid, name in value:
                    db.cypher_query(
                        query,
                        {
                            "codelist_uid": codelist_uid,
                            "dictionary_codelist_uid": dictionary_codelist.codelist_uid,
                            "uid": uid,
                            "name": name,
                            "library_name": library_name,
                        },
                    )
            else:
                db.cypher_query(
                    query,
                    {
                        "codelist_uid": codelist_uid,
                        "dictionary_codelist_uid": dictionary_codelist.codelist_uid,
                        "uid": value[0],
                        "name": value[1],
                        "library_name": library_name,
                    },
                )

    @classmethod
    def create_study_fields_configuration(cls):
        config_service = CTConfigService()
        with open(DEFAULT_STUDY_FIELD_CONFIG_FILE, encoding="UTF-8") as file:
            res = db.cypher_query(
                "MATCH (n:CTCodelistRoot) RETURN COLLECT(n.uid) as uids"
            )
            existing_codelist_uids = res[0][0][0]

            dict_reader = csv.DictReader(file)
            for line in dict_reader:
                # Create codelist only if a codelist with {uid: configured_codelist_uid} doesn't exist
                if (
                    line.get("configured_codelist_uid") != ""
                    and line.get("configured_codelist_uid")
                    not in existing_codelist_uids
                ):
                    db.cypher_query(
                        """
                    MATCH (library:Library {name:$library})
                    MATCH (catalogue:CTCatalogue {name:$catalogue})
                    MERGE (library)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot {uid: $uid})-[:HAS_NAME_ROOT]->
                    (codelist_ver_root:CTCodelistNameRoot)-[:LATEST]->(codelist_ver_value:CTCodelistNameValue {
                    name: $uid + 'name',
                    name_sentence_case: $uid + 'name'
                    })
                    MERGE (codelist_root)-[:HAS_ATTRIBUTES_ROOT]->(codelist_a_root:CTCodelistAttributesRoot)
                    -[:LATEST]->(codelist_a_value:CTCodelistAttributesValue {definition:$uid + ' DEF',
                    name:$uid + ' NAME', preferred_term:$uid + ' PREF', submission_value:$uid + ' SUMBVAL', extensible:true})
                    MERGE (catalogue)-[:HAS_CODELIST]->(codelist_root)
                    MERGE (codelist_ver_root)-[name_final:LATEST_FINAL]->(codelist_ver_value)
                    MERGE (codelist_ver_root)-[name_hasver:HAS_VERSION]->(codelist_ver_value)
                    MERGE (codelist_a_root)-[attributes_final:LATEST_FINAL]->(codelist_a_value)
                    MERGE (codelist_a_root)-[attributes_hasver:HAS_VERSION]->(codelist_a_value)
                    """
                        + cls.set_final_props("name_hasver")
                        + cls.set_final_props("attributes_hasver"),
                        {
                            "uid": line.get("configured_codelist_uid"),
                            "library": LIBRARY_NAME,
                            "catalogue": CT_CATALOGUE_NAME,
                        },
                    )
                elif line.get("configured_term_uid") != "":
                    db.cypher_query(
                        """
                    MATCH (library:Library {name:$library})
                    MATCH (catalogue:CTCatalogue {name:$catalogue})
                    // common codelist for all terms that we create for tests
                    MERGE (codelist_root:CTCodelistRoot{uid:$codelist})
                    MERGE (library)-[:CONTAINS_TERM]->(term_root:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->
                    (term_ver_root:CTTermNameRoot)-[:LATEST]->(term_ver_value:CTTermNameValue)
                    SET term_ver_value.name=$uid + 'name'
                    SET term_ver_value.name_sentence_case=$uid + 'name'
                    MERGE (term_root)-[:HAS_ATTRIBUTES_ROOT]->(term_a_root:CTTermAttributesRoot)
                    -[:LATEST]->(term_a_value:CTTermAttributesValue {
                    preferred_term: $uid + 'nci', definition: $uid + 'def', name:$uid + ' NAME', submission_value:$uid + 'submval'})
                    MERGE (codelist_root)-[:HAS_TERM]->(term_root)
                    MERGE (catalogue)-[:HAS_CODELIST]->(codelist_root)
                    MERGE (term_ver_root)-[name_final:LATEST_FINAL]->(term_ver_value)
                    MERGE (term_ver_root)-[name_hasver:HAS_VERSION]->(term_ver_value)
                    MERGE (term_a_root)-[attributes_final:LATEST_FINAL]->(term_a_value)
                    MERGE (term_a_root)-[attributes_hasver:HAS_VERSION]->(term_a_value)
                    """
                        + cls.set_final_props("name_hasver")
                        + cls.set_final_props("attributes_hasver"),
                        {
                            "uid": line.get("configured_term_uid"),
                            "codelist": CT_CODELIST_UIDS.default,
                            "library": LIBRARY_NAME,
                            "catalogue": CT_CATALOGUE_NAME,
                        },
                    )
                line = {k: v if v != "" else None for k, v in line.items()}
                input_data = CTConfigPostInput(**line)
                config_service.post(input_data)

    @classmethod
    def create_data_model_catalogue(
        cls,
        name: str = "name",
        data_model_type: str = "data_model_type",
        library_name: str = LIBRARY_NAME,
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
        library_name: str = LIBRARY_NAME,
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
        library_name: str = LIBRARY_NAME,
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
        data_model_catalogue_name: str,
        label: str = "label",
        description: str = "description",
        title: str = "title",
        library_name: str = LIBRARY_NAME,
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
        return DatasetClassService().get_by_uid(uid=dataset_class_uid)

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
        library_name: str = LIBRARY_NAME,
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
        change_description: str | None = None,
        library_name: str | None = LIBRARY_NAME,
    ) -> SponsorModelAPIModel:
        service = SponsorModelService()
        result: SponsorModelAPIModel = service.create(
            item_input=SponsorModelInput(
                ig_uid=ig_uid,
                ig_version_number=ig_version_number,
                version_number=version_number,
                change_description=change_description,
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
        is_basic_std: bool | None = False,
        xml_path: str | None = "xml_path",
        xml_title: str | None = "xml_title",
        structure: str | None = "structure",
        purpose: str | None = "purpose",
        keys: list[str] | None = None,
        sort_keys: list[str] | None = None,
        source_ig: str | None = "source_ig",
        comment: str | None = "comment",
        ig_comment: str | None = "ig_comment",
        map_domain_flag: bool | None = False,
        suppl_qual_flag: bool | None = False,
        include_in_raw: bool | None = False,
        gen_raw_seqno_flag: bool | None = False,
        enrich_build_order: int | None = 100,
        label: str | None = "state",
        state: str | None = "state",
        extended_domain: str | None = "extended_domain",
    ) -> SponsorModelDatasetAPIModel:
        service = SponsorModelDatasetService()
        result: SponsorModelDatasetAPIModel = service.create(
            item_input=SponsorModelDatasetInput(
                dataset_uid=dataset_uid,
                sponsor_model_name=sponsor_model_name,
                sponsor_model_version_number=sponsor_model_version_number,
                implemented_dataset_class=implemented_dataset_class,
                is_basic_std=is_basic_std,
                xml_path=xml_path,
                xml_title=xml_title,
                structure=structure,
                purpose=purpose,
                keys=keys,
                sort_keys=sort_keys,
                source_ig=source_ig,
                comment=comment,
                ig_comment=ig_comment,
                map_domain_flag=map_domain_flag,
                suppl_qual_flag=suppl_qual_flag,
                include_in_raw=include_in_raw,
                gen_raw_seqno_flag=gen_raw_seqno_flag,
                enrich_build_order=enrich_build_order,
                label=label,
                state=state,
                extended_domain=extended_domain,
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
        is_basic_std: bool | None = False,
        label: str | None = "label",
        order: int | None = 1,
        variable_type: str | None = "variable_type",
        length: int | None = 12,
        display_format: str | None = "display_format",
        xml_datatype: str | None = "xml_datatype",
        xml_codelist: str | None = "xml_codelist",
        xml_codelist_multi: list[str] | None = None,
        core: str | None = "core",
        origin: str | None = "origin",
        role: str | None = "role",
        term: str | None = "term",
        algorithm: str | None = "algorithm",
        qualifiers: list[str] | None = ["qualifiers"],
        comment: str | None = "comment",
        ig_comment: str | None = "ig_comment",
        class_table: str | None = "class_table",
        class_column: str | None = "class_column",
        map_var_flag: str | None = "Y",
        fixed_mapping: str | None = "fixed_mapping",
        include_in_raw: bool | None = False,
        nn_internal: bool | None = False,
        value_lvl_where_cols: str | None = "value_lvl_where_cols",
        value_lvl_label_col: str | None = "value_lvl_label_col",
        value_lvl_collect_ct_val: str | None = "value_lvl_collect_ct_val",
        value_lvl_ct_codelist_id_col: str | None = "value_lvl_ct_codelist_id_col",
        enrich_build_order: int | None = 100,
        enrich_rule: str | None = "enrich_rule",
        incl_cre_domain: bool | None = False,
        xml_codelist_values: str | None = "xml_codelist_values",
    ) -> SponsorModelDatasetVariableAPIModel:
        service = SponsorModelDatasetVariableService()
        result: SponsorModelDatasetVariableAPIModel = service.create(
            item_input=SponsorModelDatasetVariableInput(
                dataset_uid=dataset_uid,
                dataset_variable_uid=dataset_variable_uid,
                sponsor_model_name=sponsor_model_name,
                sponsor_model_version_number=sponsor_model_version_number,
                is_basic_std=is_basic_std,
                label=label,
                order=order,
                variable_type=variable_type,
                length=length,
                display_format=display_format,
                xml_datatype=xml_datatype,
                xml_codelist=xml_codelist,
                xml_codelist_multi=xml_codelist_multi,
                core=core,
                origin=origin,
                role=role,
                term=term,
                algorithm=algorithm,
                qualifiers=qualifiers,
                comment=comment,
                ig_comment=ig_comment,
                class_table=class_table,
                class_column=class_column,
                map_var_flag=map_var_flag,
                fixed_mapping=fixed_mapping,
                include_in_raw=include_in_raw,
                nn_internal=nn_internal,
                value_lvl_where_cols=value_lvl_where_cols,
                value_lvl_label_col=value_lvl_label_col,
                value_lvl_collect_ct_val=value_lvl_collect_ct_val,
                value_lvl_ct_codelist_id_col=value_lvl_ct_codelist_id_col,
                enrich_build_order=enrich_build_order,
                enrich_rule=enrich_rule,
                incl_cre_domain=incl_cre_domain,
                xml_codelist_values=xml_codelist_values,
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
        service = StudyDiseaseMilestoneService()
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
        library_name: str = LIBRARY_NAME,
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
        library_name: str = LIBRARY_NAME,
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
            WITH *
            MATCH (dataset_value)<-[:HAS_DATASET]-(data_model_ig_value:DataModelIGValue)
            SET has_dataset_variable.version_number = data_model_ig_value.version_number"""
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
        library_name: str = LIBRARY_NAME,
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
        study_uid: str,
        start_rule: str | None = None,
        end_rule: str | None = None,
        epoch: str | None = None,
        epoch_subtype: str | None = None,
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
    def create_study_arm(
        cls,
        study_uid: str,
        name: str,
        short_name: str,
        code: str | None = None,
        description: str | None = None,
        arm_colour: str | None = None,
        randomization_group: str | None = None,
        number_of_subjects: int | None = None,
        arm_type_uid: str | None = None,
    ) -> StudySelectionArm:
        arm_input = StudySelectionArmCreateInput(
            name=name,
            short_name=short_name,
            code=code,
            description=description,
            arm_colour=arm_colour,
            randomization_group=randomization_group,
            number_of_subjects=number_of_subjects,
            arm_type_uid=arm_type_uid,
        )

        result: StudySelectionArm = StudyArmSelectionService().make_selection(
            study_uid=study_uid, selection_create_input=arm_input
        )
        return result

    @classmethod
    def create_comment_thread(
        cls,
        topic_path="topic A",
        text="some thread text",
    ) -> CommentThread:
        service = CommentsService()
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
        service = CommentsService()
        payload = CommentReplyCreateInput(
            text=text,
        )
        return service.create_comment_reply(thread_uid, payload)

    @classmethod
    def lock_and_unlock_study(cls, study_uid) -> str:
        """locks a study version (giving it a study-title first), then unlocks it, returns locked study version"""

        study_service = StudyService()

        study_service.patch(
            uid=study_uid,
            dry=False,
            study_patch_request=StudyPatchRequestJsonModel(
                current_metadata=StudyMetadataJsonModel(
                    study_description=StudyDescriptionJsonModel(
                        study_title=cls.random_str(prefix="Title ")
                    )
                )
            ),
        )

        study = study_service.lock(
            uid=study_uid, change_description=cls.random_str(prefix="v")
        )
        latest_study_version = str(
            study.current_metadata.version_metadata.version_number
        )

        study_service.unlock(uid=study_uid)

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
            catalogue = config.SDTM_CT_CATALOGUE_NAME
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
        service = StudyStandardVersionService()
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
    def get_codelist_uid_by_name(cls, codelists: any, name: str) -> str:
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
