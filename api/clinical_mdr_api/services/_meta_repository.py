from typing import Any, Callable, Mapping, MutableMapping

from clinical_mdr_api.domain_repositories.biomedical_concepts.activity_instance_class_repository import (
    ActivityInstanceClassRepository,
)
from clinical_mdr_api.domain_repositories.biomedical_concepts.activity_item_class_repository import (
    ActivityItemClassRepository,
)
from clinical_mdr_api.domain_repositories.brands.brand_repository import BrandRepository
from clinical_mdr_api.domain_repositories.clinical_programmes.clinical_programme_repository import (
    ClinicalProgrammeRepository,
)
from clinical_mdr_api.domain_repositories.comments.comments_repository import (
    CommentsRepository,
)
from clinical_mdr_api.domain_repositories.concepts.active_substance_repository import (
    ActiveSubstanceRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_group_repository import (
    ActivityGroupRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceAttributesRepository,
    ActivityInstanceGroupingsRepository,
    ActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    ActivityRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_sub_group_repository import (
    ActivitySubGroupRepository,
)
from clinical_mdr_api.domain_repositories.concepts.compound_alias_repository import (
    CompoundAliasRepository,
)
from clinical_mdr_api.domain_repositories.concepts.compound_repository import (
    CompoundRepository,
)
from clinical_mdr_api.domain_repositories.concepts.medicinal_product_repository import (
    MedicinalProductRepository,
)
from clinical_mdr_api.domain_repositories.concepts.pharmaceutical_product_repository import (
    PharmaceuticalProductRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.lag_time_repository import (
    LagTimeRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_repository import (
    NumericValueRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_with_unit_repository import (
    NumericValueWithUnitRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_day_repository import (
    StudyDayRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_duration_days_repository import (
    StudyDurationDaysRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_duration_weeks_repository import (
    StudyDurationWeeksRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_week_repository import (
    StudyWeekRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.text_value_repository import (
    TextValueRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.time_point_repository import (
    TimePointRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.visit_name_repository import (
    VisitNameRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.week_in_study_repository import (
    WeekInStudyRepository,
)
from clinical_mdr_api.domain_repositories.concepts.unit_definitions.unit_definition_repository import (
    UnitDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_catalogue_repository import (
    CTCatalogueRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_aggregated_repository import (
    CTCodelistAggregatedRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_package_repository import (
    CTPackageRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_aggregated_repository import (
    CTTermAggregatedRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_attributes_repository import (
    CTTermAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.domain_repositories.data_suppliers.data_supplier_repository import (
    DataSupplierRepository,
)
from clinical_mdr_api.domain_repositories.dictionaries.dictionary_codelist_repository import (
    DictionaryCodelistGenericRepository,
)
from clinical_mdr_api.domain_repositories.dictionaries.dictionary_term_repository import (
    DictionaryTermGenericRepository,
)
from clinical_mdr_api.domain_repositories.dictionaries.dictionary_term_substance_repository import (
    DictionaryTermSubstanceRepository,
)
from clinical_mdr_api.domain_repositories.libraries.library_repository import (
    LibraryRepository,
)
from clinical_mdr_api.domain_repositories.odms.condition_repository import (
    ConditionRepository,
)
from clinical_mdr_api.domain_repositories.odms.form_repository import FormRepository
from clinical_mdr_api.domain_repositories.odms.item_group_repository import (
    ItemGroupRepository,
)
from clinical_mdr_api.domain_repositories.odms.item_repository import ItemRepository
from clinical_mdr_api.domain_repositories.odms.method_repository import MethodRepository
from clinical_mdr_api.domain_repositories.odms.study_event_repository import (
    StudyEventRepository,
)
from clinical_mdr_api.domain_repositories.odms.vendor_attribute_repository import (
    VendorAttributeRepository,
)
from clinical_mdr_api.domain_repositories.odms.vendor_element_repository import (
    VendorElementRepository,
)
from clinical_mdr_api.domain_repositories.odms.vendor_namespace_repository import (
    VendorNamespaceRepository,
)
from clinical_mdr_api.domain_repositories.projects.project_repository import (
    ProjectRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.data_model_ig_repository import (
    DataModelIGRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.dataset_class_repository import (
    DatasetClassRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.dataset_repository import (
    DatasetRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.dataset_variable_repository import (
    DatasetVariableRepository,
)
from clinical_mdr_api.domain_repositories.studies.study_template_repository import (
    StudyTemplateRepository,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository_impl import (
    StudyDefinitionRepositoryImpl,
)

# noinspection PyProtectedMember
from clinical_mdr_api.domain_repositories.study_definitions.study_title.study_title_repository import (
    StudyTitleRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_group_repository import (
    StudySelectionActivityGroupRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_instance_repository import (
    StudySelectionActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_instruction_repository import (
    StudyActivityInstructionRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_repository import (
    StudySelectionActivityRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_schedule_repository import (
    StudyActivityScheduleRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_subgroup_repository import (
    StudySelectionActivitySubGroupRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_arm_repository import (
    StudySelectionArmRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_branch_arm_repository import (
    StudySelectionBranchArmRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_cohort_repository import (
    StudySelectionCohortRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_compound_dosing_repository import (
    StudyCompoundDosingRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_compound_repository import (
    StudySelectionCompoundRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_criteria_repository import (
    StudySelectionCriteriaRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_data_supplier_repository import (
    StudyDataSupplierRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_definition_document_repository import (
    StudyDefinitionDocumentRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_design_cell_repository import (
    StudyDesignCellRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_design_class_repository import (
    StudyDesignClassRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_disease_milestone_repository import (
    StudyDiseaseMilestoneRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_element_repository import (
    StudySelectionElementRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_endpoint_repository import (
    StudySelectionEndpointRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_epoch_repository import (
    StudyEpochRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_objective_repository import (
    StudySelectionObjectiveRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_soa_footnote_repository import (
    StudySoAFootnoteRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_soa_group_repository import (
    StudySoAGroupRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_source_variable_repository import (
    StudySourceVariableRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_standard_version_repository import (
    StudyStandardVersionRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_version_repository import (
    StudyVersionRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_visit_repository import (
    StudyVisitRepository,
)
from clinical_mdr_api.domain_repositories.syntax_instances.criteria_repository import (
    CriteriaRepository,
)
from clinical_mdr_api.domain_repositories.syntax_instances.endpoint_repository import (
    EndpointRepository,
)
from clinical_mdr_api.domain_repositories.syntax_instances.footnote_repository import (
    FootnoteRepository,
)
from clinical_mdr_api.domain_repositories.syntax_instances.objective_repository import (
    ObjectiveRepository,
)
from clinical_mdr_api.domain_repositories.syntax_instances.template_parameters_repository import (
    TemplateParameterRepository,
)
from clinical_mdr_api.domain_repositories.syntax_instances.timeframe_repository import (
    TimeframeRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.activity_instruction_pre_instance_repository import (
    ActivityInstructionPreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.criteria_pre_instance_repository import (
    CriteriaPreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.endpoint_pre_instance_repository import (
    EndpointPreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.footnote_pre_instance_repository import (
    FootnotePreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.objective_pre_instance_repository import (
    ObjectivePreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.activity_instruction_template_repository import (
    ActivityInstructionTemplateRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.criteria_template_repository import (
    CriteriaTemplateRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.endpoint_template_repository import (
    EndpointTemplateRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.footnote_template_repository import (
    FootnoteTemplateRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.objective_template_repository import (
    ObjectiveTemplateRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.timeframe_template_repository import (
    TimeframeTemplateRepository,
)
from clinical_mdr_api.domain_repositories.user_repository import UserRepository


# pylint: disable=too-many-public-methods
class MetaRepository:
    """
    Utility class to provide repository instances and simplify lifecycle management (close) for them.
    It also allows us to define different repositories creation in single piece of code (not spreading out
    all over different services), which is important since we do not have any dependency injection framework in place.
    This serves are poor man's dependency injection framework for domain repositories implementations.
    """

    _repositories: MutableMapping[type, Any]

    # service instance specific variables needed for repository creation
    _author_id: str

    def __init__(self, author_id: str = "unknown-user"):
        self._author_id = author_id
        self._repositories = {}

    def close(self) -> None:
        for repo in self._repositories.values():
            if hasattr(repo, "close"):
                repo.close()
        self._repositories = {}

    def __del__(self):
        self.close()

    def _build_repository_instance(self, repo_interface: type, **kwargs) -> Any:
        """
        here we put code for build different repo classes.
        :param repo_interface: An interface to retrieve a configured implementation.
        :return:
        """

        # below you configure implementations for various repository interfaces
        # it's a dictionary which maps interface type, to (no param) Callable which creates a new instance
        # of implementing class
        repository_configuration: Mapping[type, Callable[[], Any]] = {
            StudyDefinitionRepository: lambda: StudyDefinitionRepositoryImpl(
                self._author_id
            )
        }

        if repo_interface not in repository_configuration:
            return repo_interface(**kwargs)

        return repository_configuration[repo_interface](**kwargs)

    def get_repository_instance(self, repo_interface: type, **kwargs) -> Any:
        if repo_interface not in self._repositories:
            self._repositories[repo_interface] = self._build_repository_instance(
                repo_interface, **kwargs
            )
        return self._repositories[repo_interface]

    # convenience properties for retrieving repository instances

    @property
    def activity_instance_repository(self) -> ActivityInstanceRepository:
        return self.get_repository_instance(ActivityInstanceRepository)

    @property
    def activity_instance_groupings_repository(
        self,
    ) -> ActivityInstanceGroupingsRepository:
        return ActivityInstanceGroupingsRepository()

    @property
    def activity_instance_attributes_repository(
        self,
    ) -> ActivityInstanceAttributesRepository:
        return ActivityInstanceAttributesRepository()

    @property
    def activity_instance_class_repository(self) -> ActivityInstanceClassRepository:
        return self.get_repository_instance(ActivityInstanceClassRepository)

    @property
    def data_supplier_repository(self) -> DataSupplierRepository:
        return self.get_repository_instance(DataSupplierRepository)

    @property
    def data_model_ig_repository(self) -> DataModelIGRepository:
        return self.get_repository_instance(DataModelIGRepository)

    @property
    def dataset_repository(self) -> DatasetRepository:
        return self.get_repository_instance(DatasetRepository)

    @property
    def dataset_class_repository(self) -> DatasetClassRepository:
        return self.get_repository_instance(DatasetClassRepository)

    @property
    def dataset_variable_repository(self) -> DatasetVariableRepository:
        return self.get_repository_instance(DatasetVariableRepository)

    @property
    def activity_item_class_repository(self) -> ActivityItemClassRepository:
        return self.get_repository_instance(ActivityItemClassRepository)

    @property
    def compound_repository(self) -> CompoundRepository:
        return self.get_repository_instance(CompoundRepository)

    @property
    def compound_alias_repository(self) -> CompoundAliasRepository:
        return self.get_repository_instance(CompoundAliasRepository)

    @property
    def medicinal_product_repository(self) -> MedicinalProductRepository:
        return self.get_repository_instance(MedicinalProductRepository)

    @property
    def active_substance_repository(self) -> ActiveSubstanceRepository:
        return self.get_repository_instance(ActiveSubstanceRepository)

    @property
    def pharmaceutical_product_repository(self) -> PharmaceuticalProductRepository:
        return self.get_repository_instance(PharmaceuticalProductRepository)

    @property
    def activity_repository(self) -> ActivityRepository:
        return self.get_repository_instance(ActivityRepository)

    @property
    def activity_subgroup_repository(self) -> ActivitySubGroupRepository:
        return self.get_repository_instance(ActivitySubGroupRepository)

    @property
    def activity_group_repository(self) -> ActivityGroupRepository:
        return self.get_repository_instance(ActivityGroupRepository)

    @property
    def numeric_value_repository(self) -> NumericValueRepository:
        return self.get_repository_instance(NumericValueRepository)

    @property
    def numeric_value_with_unit_repository(self) -> NumericValueWithUnitRepository:
        return self.get_repository_instance(NumericValueWithUnitRepository)

    @property
    def lag_time_repository(self) -> LagTimeRepository:
        return self.get_repository_instance(LagTimeRepository)

    @property
    def text_value_repository(self) -> TextValueRepository:
        return self.get_repository_instance(TextValueRepository)

    @property
    def visit_name_repository(self) -> VisitNameRepository:
        return self.get_repository_instance(VisitNameRepository)

    @property
    def study_day_repository(self) -> StudyDayRepository:
        return self.get_repository_instance(StudyDayRepository)

    @property
    def study_week_repository(self) -> StudyWeekRepository:
        return self.get_repository_instance(StudyWeekRepository)

    @property
    def study_duration_days_repository(self) -> StudyDurationDaysRepository:
        return self.get_repository_instance(StudyDurationDaysRepository)

    @property
    def study_duration_weeks_repository(self) -> StudyDurationWeeksRepository:
        return self.get_repository_instance(StudyDurationWeeksRepository)

    @property
    def week_in_study_repository(self) -> WeekInStudyRepository:
        return self.get_repository_instance(WeekInStudyRepository)

    @property
    def time_point_repository(self) -> TimePointRepository:
        return self.get_repository_instance(TimePointRepository)

    @property
    def unit_definition_repository(self) -> UnitDefinitionRepository:
        return self.get_repository_instance(UnitDefinitionRepository)

    @property
    def odm_method_repository(self) -> MethodRepository:
        return self.get_repository_instance(MethodRepository)

    @property
    def odm_condition_repository(self) -> ConditionRepository:
        return self.get_repository_instance(ConditionRepository)

    @property
    def odm_form_repository(self) -> FormRepository:
        return self.get_repository_instance(FormRepository)

    @property
    def odm_item_group_repository(self) -> ItemGroupRepository:
        return self.get_repository_instance(ItemGroupRepository)

    @property
    def odm_item_repository(self) -> ItemRepository:
        return self.get_repository_instance(ItemRepository)

    @property
    def odm_study_event_repository(self) -> StudyEventRepository:
        return self.get_repository_instance(StudyEventRepository)

    @property
    def odm_vendor_namespace_repository(self) -> VendorNamespaceRepository:
        return self.get_repository_instance(VendorNamespaceRepository)

    @property
    def odm_vendor_element_repository(self) -> VendorElementRepository:
        return self.get_repository_instance(VendorElementRepository)

    @property
    def odm_vendor_attribute_repository(self) -> VendorAttributeRepository:
        return self.get_repository_instance(VendorAttributeRepository)

    @property
    def criteria_repository(self) -> CriteriaRepository:
        return self.get_repository_instance(CriteriaRepository)

    @property
    def objective_repository(self) -> ObjectiveRepository:
        return self.get_repository_instance(ObjectiveRepository)

    @property
    def endpoint_repository(self) -> EndpointRepository:
        return self.get_repository_instance(EndpointRepository)

    @property
    def timeframe_repository(self) -> TimeframeRepository:
        return self.get_repository_instance(TimeframeRepository)

    @property
    def footnote_repository(self) -> FootnoteRepository:
        return self.get_repository_instance(FootnoteRepository)

    @property
    def parameter_repository(self) -> TemplateParameterRepository:
        return self.get_repository_instance(TemplateParameterRepository)

    @property
    def footnote_template_repository(
        self,
    ) -> FootnoteTemplateRepository:
        return self.get_repository_instance(
            FootnoteTemplateRepository, user=self._author_id
        )

    @property
    def activity_instruction_template_repository(
        self,
    ) -> ActivityInstructionTemplateRepository:
        return self.get_repository_instance(
            ActivityInstructionTemplateRepository, user=self._author_id
        )

    @property
    def criteria_template_repository(self) -> CriteriaTemplateRepository:
        return self.get_repository_instance(
            CriteriaTemplateRepository, user=self._author_id
        )

    @property
    def endpoint_template_repository(self) -> EndpointTemplateRepository:
        return self.get_repository_instance(
            EndpointTemplateRepository, user=self._author_id
        )

    @property
    def objective_template_repository(self) -> ObjectiveTemplateRepository:
        return self.get_repository_instance(
            ObjectiveTemplateRepository, user=self._author_id
        )

    @property
    def timeframe_template_repository(self) -> TimeframeTemplateRepository:
        return self.get_repository_instance(
            TimeframeTemplateRepository, user=self._author_id
        )

    @property
    def activity_instruction_pre_instance_repository(
        self,
    ) -> ActivityInstructionPreInstanceRepository:
        return self.get_repository_instance(
            ActivityInstructionPreInstanceRepository, user=self._author_id
        )

    @property
    def footnote_pre_instance_repository(self) -> FootnotePreInstanceRepository:
        return self.get_repository_instance(
            FootnotePreInstanceRepository, user=self._author_id
        )

    @property
    def criteria_pre_instance_repository(self) -> CriteriaPreInstanceRepository:
        return self.get_repository_instance(
            CriteriaPreInstanceRepository, user=self._author_id
        )

    @property
    def endpoint_pre_instance_repository(self) -> EndpointPreInstanceRepository:
        return self.get_repository_instance(
            EndpointPreInstanceRepository, user=self._author_id
        )

    @property
    def objective_pre_instance_repository(self) -> ObjectivePreInstanceRepository:
        return self.get_repository_instance(
            ObjectivePreInstanceRepository, user=self._author_id
        )

    @property
    def library_repository(self) -> LibraryRepository:
        return self.get_repository_instance(LibraryRepository)

    @property
    def ct_catalogue_repository(self) -> CTCatalogueRepository:
        return self.get_repository_instance(CTCatalogueRepository)

    @property
    def ct_package_repository(self) -> CTPackageRepository:
        return self.get_repository_instance(CTPackageRepository)

    @property
    def ct_codelist_name_repository(self) -> CTCodelistNameRepository:
        return self.get_repository_instance(CTCodelistNameRepository)

    @property
    def ct_codelist_attribute_repository(self) -> CTCodelistAttributesRepository:
        return self.get_repository_instance(CTCodelistAttributesRepository)

    @property
    def ct_codelist_aggregated_repository(self) -> CTCodelistAggregatedRepository:
        return self.get_repository_instance(CTCodelistAggregatedRepository)

    @property
    def ct_term_name_repository(self) -> CTTermNameRepository:
        return self.get_repository_instance(CTTermNameRepository)

    @property
    def ct_term_attributes_repository(self) -> CTTermAttributesRepository:
        return self.get_repository_instance(CTTermAttributesRepository)

    @property
    def ct_term_aggregated_repository(self) -> CTTermAggregatedRepository:
        return self.get_repository_instance(CTTermAggregatedRepository)

    @property
    def dictionary_codelist_generic_repository(
        self,
    ) -> DictionaryCodelistGenericRepository:
        return self.get_repository_instance(DictionaryCodelistGenericRepository)

    @property
    def dictionary_term_generic_repository(self) -> DictionaryTermGenericRepository:
        return self.get_repository_instance(DictionaryTermGenericRepository)

    @property
    def dictionary_term_substance_repository(self) -> DictionaryTermSubstanceRepository:
        return self.get_repository_instance(DictionaryTermSubstanceRepository)

    @property
    def study_definition_repository(self) -> StudyDefinitionRepository:
        return self.get_repository_instance(StudyDefinitionRepository)

    @property
    def study_definition_document_repository(self) -> StudyDefinitionDocumentRepository:
        return self.get_repository_instance(StudyDefinitionDocumentRepository)

    @property
    def study_version_repository(self) -> StudyVersionRepository:
        return self.get_repository_instance(StudyVersionRepository)

    @property
    def project_repository(self) -> ProjectRepository:
        return self.get_repository_instance(ProjectRepository)

    @property
    def brand_repository(self) -> BrandRepository:
        return self.get_repository_instance(BrandRepository)

    @property
    def comments_repository(self) -> CommentsRepository:
        return self.get_repository_instance(CommentsRepository)

    @property
    def clinical_programme_repository(self) -> ClinicalProgrammeRepository:
        return self.get_repository_instance(ClinicalProgrammeRepository)

    @property
    def study_data_supplier_repository(self) -> StudyDataSupplierRepository:
        return self.get_repository_instance(StudyDataSupplierRepository)

    @property
    def study_objective_repository(self) -> StudySelectionObjectiveRepository:
        return self.get_repository_instance(StudySelectionObjectiveRepository)

    @property
    def study_endpoint_repository(self) -> StudySelectionEndpointRepository:
        return self.get_repository_instance(StudySelectionEndpointRepository)

    @property
    def study_compound_repository(self) -> StudySelectionCompoundRepository:
        return self.get_repository_instance(StudySelectionCompoundRepository)

    @property
    def study_compound_dosing_repository(self) -> StudyCompoundDosingRepository:
        return self.get_repository_instance(StudyCompoundDosingRepository)

    @property
    def study_criteria_repository(self) -> StudySelectionCriteriaRepository:
        return self.get_repository_instance(StudySelectionCriteriaRepository)

    @property
    def study_activity_instance_repository(
        self,
    ) -> StudySelectionActivityInstanceRepository:
        return self.get_repository_instance(StudySelectionActivityInstanceRepository)

    @property
    def study_activity_repository(
        self,
    ) -> StudySelectionActivityRepository:
        return self.get_repository_instance(StudySelectionActivityRepository)

    @property
    def study_activity_subgroup_repository(
        self,
    ) -> StudySelectionActivitySubGroupRepository:
        return self.get_repository_instance(StudySelectionActivitySubGroupRepository)

    @property
    def study_activity_group_repository(
        self,
    ) -> StudySelectionActivityGroupRepository:
        return self.get_repository_instance(StudySelectionActivityGroupRepository)

    @property
    def study_soa_group_repository(
        self,
    ) -> StudySoAGroupRepository:
        return self.get_repository_instance(StudySoAGroupRepository)

    @property
    def study_activity_schedule_repository(self) -> StudyActivityScheduleRepository:
        return self.get_repository_instance(StudyActivityScheduleRepository)

    @property
    def study_soa_footnote_repository(self) -> StudySoAFootnoteRepository:
        return self.get_repository_instance(StudySoAFootnoteRepository)

    @property
    def study_design_cell_repository(self) -> StudyDesignCellRepository:
        return self.get_repository_instance(StudyDesignCellRepository)

    @property
    def study_activity_instruction_repository(
        self,
    ) -> StudyActivityInstructionRepository:
        return self.get_repository_instance(StudyActivityInstructionRepository)

    @property
    def study_title_repository(self) -> StudyTitleRepository:
        return self.get_repository_instance(StudyTitleRepository)

    @property
    def study_epoch_repository(self) -> StudyEpochRepository:
        return self.get_repository_instance(StudyEpochRepository)

    @property
    def study_disease_milestone_repository(self) -> StudyDiseaseMilestoneRepository:
        return self.get_repository_instance(
            StudyDiseaseMilestoneRepository, author_id=self._author_id
        )

    @property
    def study_standard_version_repository(self) -> StudyStandardVersionRepository:
        return self.get_repository_instance(
            StudyStandardVersionRepository, author_id=self._author_id
        )

    @property
    def study_visit_repository(self) -> StudyVisitRepository:
        return self.get_repository_instance(StudyVisitRepository)

    @property
    def study_arm_repository(self) -> StudySelectionArmRepository:
        return self.get_repository_instance(StudySelectionArmRepository)

    @property
    def study_element_repository(self) -> StudySelectionElementRepository:
        return self.get_repository_instance(StudySelectionElementRepository)

    @property
    def study_branch_arm_repository(
        self,
    ) -> StudySelectionBranchArmRepository:
        return self.get_repository_instance(StudySelectionBranchArmRepository)

    @property
    def study_cohort_repository(self) -> StudySelectionCohortRepository:
        return self.get_repository_instance(StudySelectionCohortRepository)

    @property
    def study_design_class_repository(self) -> StudyDesignClassRepository:
        return self.get_repository_instance(StudyDesignClassRepository)

    @property
    def study_source_variable_repository(self) -> StudySourceVariableRepository:
        return self.get_repository_instance(StudySourceVariableRepository)

    @property
    def study_template_repository(self) -> StudyTemplateRepository:
        return self.get_repository_instance(
            StudyTemplateRepository, user=self._author_id
        )

    @property
    def user_repository(self) -> UserRepository:
        return self.get_repository_instance(UserRepository)
