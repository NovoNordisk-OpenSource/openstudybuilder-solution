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
from clinical_mdr_api.domain_repositories.concepts.odms.alias_repository import (
    AliasRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.condition_repository import (
    ConditionRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.description_repository import (
    DescriptionRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.form_repository import (
    FormRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.formal_expression_repository import (
    FormalExpressionRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.item_group_repository import (
    ItemGroupRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.item_repository import (
    ItemRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.method_repository import (
    MethodRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.study_event_repository import (
    StudyEventRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.vendor_attribute_repository import (
    VendorAttributeRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.vendor_element_repository import (
    VendorElementRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.vendor_namespace_repository import (
    VendorNamespaceRepository,
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
from clinical_mdr_api.domain_repositories.controlled_terminologies.configuration_repository import (
    CTConfigRepository,
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
from clinical_mdr_api.domain_repositories.study_selections.study_design_cell_repository import (
    StudyDesignCellRepository,
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
from clinical_mdr_api.domain_repositories.study_selections.study_standard_version_repository import (
    StudyStandardVersionRepository,
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
            repo.close()
        self._repositories = {}

    def __del__(self):
        self.close()

    def _build_repository_instance(self, repo_interface: type) -> Any:
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
            raise NotImplementedError(
                f"This class doesn't know how to provide {repo_interface} implementation."
            )

        return repository_configuration[repo_interface]()

    def get_repository_instance(self, repo_interface: type) -> Any:
        if repo_interface not in self._repositories:
            self._repositories[repo_interface] = self._build_repository_instance(
                repo_interface
            )
        return self._repositories[repo_interface]

    # convenience properties for retrieving repository instances

    @property
    def activity_instance_repository(self) -> ActivityInstanceRepository:
        return ActivityInstanceRepository()

    @property
    def activity_instance_class_repository(self) -> ActivityInstanceClassRepository:
        return ActivityInstanceClassRepository()

    @property
    def data_model_ig_repository(self) -> DataModelIGRepository:
        return DataModelIGRepository()

    @property
    def dataset_repository(self) -> DatasetRepository:
        return DatasetRepository()

    @property
    def dataset_class_repository(self) -> DatasetClassRepository:
        return DatasetClassRepository()

    @property
    def dataset_variable_repository(self) -> DatasetVariableRepository:
        return DatasetVariableRepository()

    @property
    def activity_item_class_repository(self) -> ActivityItemClassRepository:
        return ActivityItemClassRepository()

    @property
    def compound_repository(self) -> CompoundRepository:
        return CompoundRepository()

    @property
    def compound_alias_repository(self) -> CompoundAliasRepository:
        return CompoundAliasRepository()

    @property
    def medicinal_product_repository(self) -> MedicinalProductRepository:
        return MedicinalProductRepository()

    @property
    def active_substance_repository(self) -> ActiveSubstanceRepository:
        return ActiveSubstanceRepository()

    @property
    def pharmaceutical_product_repository(self) -> PharmaceuticalProductRepository:
        return PharmaceuticalProductRepository()

    @property
    def activity_repository(self) -> ActivityRepository:
        return ActivityRepository()

    @property
    def activity_subgroup_repository(self) -> ActivitySubGroupRepository:
        return ActivitySubGroupRepository()

    @property
    def activity_group_repository(self) -> ActivityGroupRepository:
        return ActivityGroupRepository()

    @property
    def numeric_value_repository(self) -> NumericValueRepository:
        return NumericValueRepository()

    @property
    def numeric_value_with_unit_repository(self) -> NumericValueWithUnitRepository:
        return NumericValueWithUnitRepository()

    @property
    def lag_time_repository(self) -> LagTimeRepository:
        return LagTimeRepository()

    @property
    def text_value_repository(self) -> TextValueRepository:
        return TextValueRepository()

    @property
    def visit_name_repository(self) -> VisitNameRepository:
        return VisitNameRepository()

    @property
    def study_day_repository(self) -> StudyDayRepository:
        return StudyDayRepository()

    @property
    def study_week_repository(self) -> StudyWeekRepository:
        return StudyWeekRepository()

    @property
    def study_duration_days_repository(self) -> StudyDurationDaysRepository:
        return StudyDurationDaysRepository()

    @property
    def study_duration_weeks_repository(self) -> StudyDurationWeeksRepository:
        return StudyDurationWeeksRepository()

    @property
    def week_in_study_repository(self) -> WeekInStudyRepository:
        return WeekInStudyRepository()

    @property
    def time_point_repository(self) -> TimePointRepository:
        return TimePointRepository()

    @property
    def unit_definition_repository(self) -> UnitDefinitionRepository:
        return UnitDefinitionRepository()

    @property
    def odm_method_repository(self) -> MethodRepository:
        return MethodRepository()

    @property
    def odm_condition_repository(self) -> ConditionRepository:
        return ConditionRepository()

    @property
    def odm_formal_expression_repository(self) -> FormalExpressionRepository:
        return FormalExpressionRepository()

    @property
    def odm_form_repository(self) -> FormRepository:
        return FormRepository()

    @property
    def odm_item_group_repository(self) -> ItemGroupRepository:
        return ItemGroupRepository()

    @property
    def odm_item_repository(self) -> ItemRepository:
        return ItemRepository()

    @property
    def odm_study_event_repository(self) -> StudyEventRepository:
        return StudyEventRepository()

    @property
    def odm_description_repository(self) -> DescriptionRepository:
        return DescriptionRepository()

    @property
    def odm_alias_repository(self) -> AliasRepository:
        return AliasRepository()

    @property
    def odm_vendor_namespace_repository(self) -> VendorNamespaceRepository:
        return VendorNamespaceRepository()

    @property
    def odm_vendor_element_repository(self) -> VendorElementRepository:
        return VendorElementRepository()

    @property
    def odm_vendor_attribute_repository(self) -> VendorAttributeRepository:
        return VendorAttributeRepository()

    @property
    def criteria_repository(self) -> CriteriaRepository:
        return CriteriaRepository()

    @property
    def objective_repository(self) -> ObjectiveRepository:
        return ObjectiveRepository()

    @property
    def endpoint_repository(self) -> EndpointRepository:
        return EndpointRepository()

    @property
    def timeframe_repository(self) -> TimeframeRepository:
        return TimeframeRepository()

    @property
    def footnote_repository(self) -> FootnoteRepository:
        return FootnoteRepository()

    @property
    def parameter_repository(self) -> TemplateParameterRepository:
        return TemplateParameterRepository()

    @property
    def footnote_template_repository(
        self,
    ) -> FootnoteTemplateRepository:
        return FootnoteTemplateRepository(self._author_id)

    @property
    def activity_instruction_template_repository(
        self,
    ) -> ActivityInstructionTemplateRepository:
        return ActivityInstructionTemplateRepository(self._author_id)

    @property
    def criteria_template_repository(self) -> CriteriaTemplateRepository:
        return CriteriaTemplateRepository(self._author_id)

    @property
    def endpoint_template_repository(self) -> EndpointTemplateRepository:
        return EndpointTemplateRepository(self._author_id)

    @property
    def objective_template_repository(self) -> ObjectiveTemplateRepository:
        return ObjectiveTemplateRepository(self._author_id)

    @property
    def timeframe_template_repository(self) -> TimeframeTemplateRepository:
        return TimeframeTemplateRepository(self._author_id)

    @property
    def activity_instruction_pre_instance_repository(
        self,
    ) -> ActivityInstructionPreInstanceRepository:
        return ActivityInstructionPreInstanceRepository(self._author_id)

    @property
    def footnote_pre_instance_repository(self) -> FootnotePreInstanceRepository:
        return FootnotePreInstanceRepository(self._author_id)

    @property
    def criteria_pre_instance_repository(self) -> CriteriaPreInstanceRepository:
        return CriteriaPreInstanceRepository(self._author_id)

    @property
    def endpoint_pre_instance_repository(self) -> EndpointPreInstanceRepository:
        return EndpointPreInstanceRepository(self._author_id)

    @property
    def objective_pre_instance_repository(self) -> ObjectivePreInstanceRepository:
        return ObjectivePreInstanceRepository(self._author_id)

    @property
    def library_repository(self) -> LibraryRepository:
        return LibraryRepository()

    @property
    def ct_catalogue_repository(self) -> CTCatalogueRepository:
        return CTCatalogueRepository()

    @property
    def ct_package_repository(self) -> CTPackageRepository:
        return CTPackageRepository()

    @property
    def ct_codelist_name_repository(self) -> CTCodelistNameRepository:
        return CTCodelistNameRepository()

    @property
    def ct_codelist_attribute_repository(self) -> CTCodelistAttributesRepository:
        return CTCodelistAttributesRepository()

    @property
    def ct_codelist_aggregated_repository(self) -> CTCodelistAggregatedRepository:
        return CTCodelistAggregatedRepository()

    @property
    def ct_term_name_repository(self) -> CTTermNameRepository:
        return CTTermNameRepository()

    @property
    def ct_term_attributes_repository(self) -> CTTermAttributesRepository:
        return CTTermAttributesRepository()

    @property
    def ct_term_aggregated_repository(self) -> CTTermAggregatedRepository:
        return CTTermAggregatedRepository()

    @property
    def dictionary_codelist_generic_repository(
        self,
    ) -> DictionaryCodelistGenericRepository:
        return DictionaryCodelistGenericRepository()

    @property
    def dictionary_term_generic_repository(self) -> DictionaryTermGenericRepository:
        return DictionaryTermGenericRepository()

    @property
    def dictionary_term_substance_repository(self) -> DictionaryTermSubstanceRepository:
        return DictionaryTermSubstanceRepository()

    @property
    def study_definition_repository(self) -> StudyDefinitionRepository:
        return self.get_repository_instance(StudyDefinitionRepository)

    @property
    def project_repository(self) -> ProjectRepository:
        return ProjectRepository()

    @property
    def brand_repository(self) -> BrandRepository:
        return BrandRepository()

    @property
    def comments_repository(self) -> CommentsRepository:
        return CommentsRepository()

    @property
    def clinical_programme_repository(self) -> ClinicalProgrammeRepository:
        return ClinicalProgrammeRepository()

    @property
    def study_objective_repository(self) -> StudySelectionObjectiveRepository:
        return StudySelectionObjectiveRepository()

    @property
    def study_endpoint_repository(self) -> StudySelectionEndpointRepository:
        return StudySelectionEndpointRepository()

    @property
    def study_compound_repository(self) -> StudySelectionCompoundRepository:
        return StudySelectionCompoundRepository()

    @property
    def study_compound_dosing_repository(self) -> StudyCompoundDosingRepository:
        return StudyCompoundDosingRepository()

    @property
    def study_criteria_repository(self) -> StudySelectionCriteriaRepository:
        return StudySelectionCriteriaRepository()

    @property
    def study_activity_instance_repository(
        self,
    ) -> StudySelectionActivityInstanceRepository:
        return StudySelectionActivityInstanceRepository()

    @property
    def study_activity_repository(
        self,
    ) -> StudySelectionActivityRepository:
        return StudySelectionActivityRepository()

    @property
    def study_activity_subgroup_repository(
        self,
    ) -> StudySelectionActivitySubGroupRepository:
        return StudySelectionActivitySubGroupRepository()

    @property
    def study_activity_group_repository(
        self,
    ) -> StudySelectionActivityGroupRepository:
        return StudySelectionActivityGroupRepository()

    @property
    def study_soa_group_repository(
        self,
    ) -> StudySoAGroupRepository:
        return StudySoAGroupRepository()

    @property
    def study_activity_schedule_repository(self) -> StudyActivityScheduleRepository:
        return StudyActivityScheduleRepository()

    @property
    def study_soa_footnote_repository(self) -> StudySoAFootnoteRepository:
        return StudySoAFootnoteRepository()

    @property
    def study_design_cell_repository(self) -> StudyDesignCellRepository:
        return StudyDesignCellRepository()

    @property
    def study_activity_instruction_repository(
        self,
    ) -> StudyActivityInstructionRepository:
        return StudyActivityInstructionRepository()

    @property
    def study_title_repository(self) -> StudyTitleRepository:
        return StudyTitleRepository()

    @property
    def study_epoch_repository(self) -> StudyEpochRepository:
        return StudyEpochRepository(self._author_id)

    @property
    def study_disease_milestone_repository(self) -> StudyDiseaseMilestoneRepository:
        return StudyDiseaseMilestoneRepository(self._author_id)

    @property
    def study_standard_version_repository(self) -> StudyStandardVersionRepository:
        return StudyStandardVersionRepository(self._author_id)

    @property
    def study_visit_repository(self) -> StudyVisitRepository:
        return StudyVisitRepository(self._author_id)

    @property
    def ct_config_repository(self) -> CTConfigRepository:
        return CTConfigRepository(self._author_id)

    @property
    def study_arm_repository(self) -> StudySelectionArmRepository:
        return StudySelectionArmRepository()

    @property
    def study_element_repository(self) -> StudySelectionElementRepository:
        return StudySelectionElementRepository()

    @property
    def study_branch_arm_repository(
        self,
    ) -> StudySelectionBranchArmRepository:
        return StudySelectionBranchArmRepository()

    @property
    def study_cohort_repository(self) -> StudySelectionCohortRepository:
        return StudySelectionCohortRepository()
