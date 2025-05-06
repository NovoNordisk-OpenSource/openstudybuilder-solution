import clinical_mdr_api.routers.integrations
from clinical_mdr_api.routers.admin import router as admin_router
from clinical_mdr_api.routers.biomedical_concepts.activity_instance_classes import (
    router as activity_instance_classes_router,
)
from clinical_mdr_api.routers.biomedical_concepts.activity_item_classes import (
    router as activity_item_classes_router,
)
from clinical_mdr_api.routers.brands.brands import router as brands_router
from clinical_mdr_api.routers.clinical_programmes.clinical_programmes import (
    router as clinical_programmes_router,
)
from clinical_mdr_api.routers.comments.comments import router as comments_router
from clinical_mdr_api.routers.concepts.active_substances import (
    router as active_substances_router,
)
from clinical_mdr_api.routers.concepts.activities.activities import (
    router as activities_router,
)
from clinical_mdr_api.routers.concepts.activities.activity_groups import (
    router as activity_groups_router,
)
from clinical_mdr_api.routers.concepts.activities.activity_instances import (
    router as activity_instances_router,
)
from clinical_mdr_api.routers.concepts.activities.activity_sub_groups import (
    router as activity_subgroups_router,
)
from clinical_mdr_api.routers.concepts.compound_aliases import (
    router as compound_aliases_router,
)
from clinical_mdr_api.routers.concepts.compounds import router as compounds_router
from clinical_mdr_api.routers.concepts.lag_times import router as lag_times_router
from clinical_mdr_api.routers.concepts.medicinal_products import (
    router as medicinal_products_router,
)
from clinical_mdr_api.routers.concepts.numeric_values import (
    router as numeric_values_router,
)
from clinical_mdr_api.routers.concepts.numeric_values_with_unit import (
    router as numeric_values_with_unit_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_aliases import (
    router as odm_aliases_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_conditions import (
    router as odm_conditions_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_descriptions import (
    router as odm_descriptions_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_formal_expressions import (
    router as odm_formal_expressions_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_forms import router as odm_forms_router
from clinical_mdr_api.routers.concepts.odms.odm_item_groups import (
    router as odm_item_groups_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_items import router as odm_item_router
from clinical_mdr_api.routers.concepts.odms.odm_metadata import (
    router as odm_metadata_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_methods import (
    router as odm_methods_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_study_events import (
    router as odm_study_events_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_vendor_attributes import (
    router as odm_vendor_attribute_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_vendor_elements import (
    router as odm_vendor_element_router,
)
from clinical_mdr_api.routers.concepts.odms.odm_vendor_namespaces import (
    router as odm_vendor_namespace_router,
)
from clinical_mdr_api.routers.concepts.pharmaceutical_products import (
    router as pharmaceutical_products_router,
)
from clinical_mdr_api.routers.concepts.text_values import router as text_values_router
from clinical_mdr_api.routers.concepts.unit_definitions.unit_definitions import (
    router as unit_definition_router,
)
from clinical_mdr_api.routers.concepts.visit_names import router as visit_names_router
from clinical_mdr_api.routers.controlled_terminologies.configuration import (
    router as configuration_router,
)
from clinical_mdr_api.routers.controlled_terminologies.ct_catalogues import (
    router as ct_catalogues_router,
)
from clinical_mdr_api.routers.controlled_terminologies.ct_codelist_attributes import (
    router as ct_codelist_attributes_router,
)
from clinical_mdr_api.routers.controlled_terminologies.ct_codelist_names import (
    router as ct_codelist_names_router,
)
from clinical_mdr_api.routers.controlled_terminologies.ct_codelists import (
    router as ct_codelists_router,
)
from clinical_mdr_api.routers.controlled_terminologies.ct_packages import (
    router as ct_packages_router,
)
from clinical_mdr_api.routers.controlled_terminologies.ct_stats import (
    router as ct_stats_router,
)
from clinical_mdr_api.routers.controlled_terminologies.ct_term_attributes import (
    router as ct_term_attributes_router,
)
from clinical_mdr_api.routers.controlled_terminologies.ct_term_names import (
    router as ct_term_names_router,
)
from clinical_mdr_api.routers.controlled_terminologies.ct_terms import (
    router as ct_terms_router,
)
from clinical_mdr_api.routers.ctr_xml.ctr_xml import router as ctr_xml_router
from clinical_mdr_api.routers.ddf.study_definitions import router as ddf_router
from clinical_mdr_api.routers.dictionaries.dictionary_codelists import (
    router as dictionary_codelists_router,
)
from clinical_mdr_api.routers.dictionaries.dictionary_terms import (
    router as dictionary_terms_router,
)
from clinical_mdr_api.routers.feature_flags import router as feature_flags_router
from clinical_mdr_api.routers.libraries.libraries import router as libraries_router
from clinical_mdr_api.routers.libraries.time_points import router as time_points_router
from clinical_mdr_api.routers.listings.listings import metadata_router
from clinical_mdr_api.routers.listings.listings import router as listing_router
from clinical_mdr_api.routers.listings.listings_adam import (
    router as adam_listing_router,
)
from clinical_mdr_api.routers.listings.listings_sdtm import (
    router as sdtm_listing_router,
)
from clinical_mdr_api.routers.listings.listings_study import (
    router as study_listing_router,
)
from clinical_mdr_api.routers.notifications import router as notifications_router
from clinical_mdr_api.routers.projects.projects import router as projects_router
from clinical_mdr_api.routers.standard_data_models.data_model_igs import (
    router as data_model_igs_router,
)
from clinical_mdr_api.routers.standard_data_models.data_models import (
    router as data_models_router,
)
from clinical_mdr_api.routers.standard_data_models.dataset_classes import (
    router as dataset_classes_router,
)
from clinical_mdr_api.routers.standard_data_models.dataset_scenarios import (
    router as dataset_scenarios_router,
)
from clinical_mdr_api.routers.standard_data_models.dataset_variables import (
    router as dataset_variables_router,
)
from clinical_mdr_api.routers.standard_data_models.datasets import (
    router as datasets_router,
)
from clinical_mdr_api.routers.standard_data_models.sponsor_model_dataset_variables import (
    router as sponsor_model_dataset_variables_router,
)
from clinical_mdr_api.routers.standard_data_models.sponsor_model_datasets import (
    router as sponsor_model_datasets_router,
)
from clinical_mdr_api.routers.standard_data_models.sponsor_models import (
    router as sponsor_models_router,
)
from clinical_mdr_api.routers.standard_data_models.variable_classes import (
    router as class_variables_router,
)
from clinical_mdr_api.routers.studies.studies import router as studies_router
from clinical_mdr_api.routers.studies.study import router as study_router
from clinical_mdr_api.routers.studies.study_activity_instructions import (
    router as study_activity_instructions_router,
)
from clinical_mdr_api.routers.studies.study_activity_schedule import (
    router as study_activity_schedule_router,
)
from clinical_mdr_api.routers.studies.study_compound_dosing import (
    router as study_compound_dosing_router,
)
from clinical_mdr_api.routers.studies.study_days import router as study_days_router
from clinical_mdr_api.routers.studies.study_design_cell import (
    router as study_design_cell_router,
)
from clinical_mdr_api.routers.studies.study_design_figure import (
    router as study_design_figure,
)
from clinical_mdr_api.routers.studies.study_disease_milestones import (
    router as study_disease_milestone_router,
)
from clinical_mdr_api.routers.studies.study_duration_days import (
    router as study_duration_days_router,
)
from clinical_mdr_api.routers.studies.study_duration_weeks import (
    router as study_duration_weeks_router,
)
from clinical_mdr_api.routers.studies.study_epochs import router as study_epoch_router
from clinical_mdr_api.routers.studies.study_flowchart import (
    router as study_flowchart_router,
)
from clinical_mdr_api.routers.studies.study_interventions import (
    router as study_interventions_router,
)
from clinical_mdr_api.routers.studies.study_soa_footnotes import (
    router as study_soa_footnotes_router,
)
from clinical_mdr_api.routers.studies.study_standard_version import (
    router as study_standard_version_router,
)
from clinical_mdr_api.routers.studies.study_visits import router as study_visit_router
from clinical_mdr_api.routers.studies.study_weeks import router as study_weeks_router
from clinical_mdr_api.routers.syntax_instances.activity_instructions import (
    router as activity_instructions_router,
)
from clinical_mdr_api.routers.syntax_instances.criteria import router as criteria_router
from clinical_mdr_api.routers.syntax_instances.endpoints import (
    router as endpoints_router,
)
from clinical_mdr_api.routers.syntax_instances.footnotes import (
    router as footnote_router,
)
from clinical_mdr_api.routers.syntax_instances.objectives import (
    router as objectives_router,
)
from clinical_mdr_api.routers.syntax_instances.timeframes import (
    router as timeframes_router,
)
from clinical_mdr_api.routers.syntax_pre_instances.activity_instruction_pre_instances import (
    router as activity_instruction_pre_instances_router,
)
from clinical_mdr_api.routers.syntax_pre_instances.criteria_pre_instances import (
    router as criteria_pre_instances_router,
)
from clinical_mdr_api.routers.syntax_pre_instances.endpoint_pre_instances import (
    router as endpoint_pre_instances_router,
)
from clinical_mdr_api.routers.syntax_pre_instances.footnote_pre_instances import (
    router as footnote_pre_instances_router,
)
from clinical_mdr_api.routers.syntax_pre_instances.objective_pre_instances import (
    router as objective_pre_instances_router,
)
from clinical_mdr_api.routers.syntax_templates.activity_instruction_templates import (
    router as activity_instruction_templates_router,
)
from clinical_mdr_api.routers.syntax_templates.criteria_templates import (
    router as criteria_templates_router,
)
from clinical_mdr_api.routers.syntax_templates.endpoint_templates import (
    router as endpoint_templates_router,
)
from clinical_mdr_api.routers.syntax_templates.footnote_templates import (
    router as footnote_templates_router,
)
from clinical_mdr_api.routers.syntax_templates.objective_templates import (
    router as objective_templates_router,
)
from clinical_mdr_api.routers.syntax_templates.timeframe_templates import (
    router as timeframe_templates_router,
)
from clinical_mdr_api.routers.system import router as system_router
from clinical_mdr_api.routers.template_parameters import (
    router as template_parameters_router,
)

__all__ = [
    "feature_flags_router",
    "notifications_router",
    "activities_router",
    "active_substances_router",
    "pharmaceutical_products_router",
    "medicinal_products_router",
    "odm_study_events_router",
    "odm_forms_router",
    "odm_item_groups_router",
    "odm_item_router",
    "odm_conditions_router",
    "odm_methods_router",
    "odm_formal_expressions_router",
    "odm_descriptions_router",
    "odm_aliases_router",
    "odm_vendor_namespace_router",
    "odm_vendor_element_router",
    "odm_vendor_attribute_router",
    "activity_instances_router",
    "activity_instance_classes_router",
    "activity_item_classes_router",
    "odm_metadata_router",
    "compounds_router",
    "compound_aliases_router",
    "activity_subgroups_router",
    "activity_groups_router",
    "numeric_values_router",
    "numeric_values_with_unit_router",
    "lag_times_router",
    "text_values_router",
    "time_points_router",
    "libraries_router",
    "ct_catalogues_router",
    "ct_packages_router",
    "ct_codelists_router",
    "ct_codelist_names_router",
    "ct_codelist_attributes_router",
    "ct_terms_router",
    "ct_term_names_router",
    "ct_term_attributes_router",
    "ct_stats_router",
    "ctr_xml_router",
    "dictionary_codelists_router",
    "dictionary_terms_router",
    "activity_instructions_router",
    "activity_instruction_pre_instances_router",
    "footnote_pre_instances_router",
    "criteria_pre_instances_router",
    "endpoint_pre_instances_router",
    "objective_pre_instances_router",
    "activity_instruction_templates_router",
    "footnote_templates_router",
    "footnote_router",
    "criteria_templates_router",
    "criteria_router",
    "objective_templates_router",
    "objectives_router",
    "template_parameters_router",
    "endpoint_templates_router",
    "endpoints_router",
    "projects_router",
    "brands_router",
    "comments_router",
    "admin_router",
    "clinical_programmes_router",
    "studies_router",
    "system_router",
    "timeframe_templates_router",
    "timeframes_router",
    "study_router",
    "study_epoch_router",
    "study_disease_milestone_router",
    "study_standard_version_router",
    "study_visit_router",
    "study_activity_instructions_router",
    "study_activity_schedule_router",
    "study_soa_footnotes_router",
    "study_design_cell_router",
    "study_duration_days_router",
    "study_duration_weeks_router",
    "study_days_router",
    "study_weeks_router",
    "metadata_router",
    "listing_router",
    "sdtm_listing_router",
    "adam_listing_router",
    "study_listing_router",
    "unit_definition_router",
    "configuration_router",
    "study_design_figure",
    "study_interventions_router",
    "study_flowchart_router",
    "study_compound_dosing_router",
    "visit_names_router",
    "data_models_router",
    "data_model_igs_router",
    "sponsor_models_router",
    "sponsor_model_datasets_router",
    "sponsor_model_dataset_variables_router",
    "datasets_router",
    "dataset_scenarios_router",
    "dataset_classes_router",
    "class_variables_router",
    "dataset_variables_router",
    "ddf_router",
]
