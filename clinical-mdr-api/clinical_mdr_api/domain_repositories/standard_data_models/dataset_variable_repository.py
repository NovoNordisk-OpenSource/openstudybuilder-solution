from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DatasetVariable,
    DatasetVariableInstance,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.dataset_variable import (
    DatasetVariable as DatasetVariableAPIModel,
)
from common.exceptions import ValidationException


class DatasetVariableRepository(StandardDataModelRepository):
    root_class = DatasetVariable
    value_class = DatasetVariableInstance
    return_model = DatasetVariableAPIModel

    # pylint: disable=unused-argument
    def generic_match_clause(
        self, versioning_relationship: str, uid: str | None = None
    ):
        standard_data_model_label = self.root_class.__label__
        standard_data_model_value_label = self.value_class.__label__
        uid_filter = ""
        if uid:
            uid_filter = f"{{uid: '{uid}'}}"
        return f"""MATCH (standard_root:{standard_data_model_label} {uid_filter})-[:HAS_INSTANCE]->
                (standard_value:{standard_data_model_value_label})<-[has_dataset_variable_rel:HAS_DATASET_VARIABLE]-
                (dataset_value:DatasetInstance)<-[:HAS_DATASET]-(data_model_ig_value:DataModelIGValue)
                <-[:HAS_VERSION]-(data_model_ig_root:DataModelIGRoot)"""

    def union_match_clause(
        self, filter_query_parameters: dict | None = None
    ) -> str | None:
        filter_query_parameters = filter_query_parameters or {}

        if "dataset_scenario_uid" in filter_query_parameters:
            standard_data_model_label = self.root_class.__label__
            standard_data_model_value_label = self.value_class.__label__
            return f"""
                    MATCH (data_model_ig_root:DataModelIGRoot)-[:HAS_VERSION]->(data_model_ig_value:DataModelIGValue)-
                    [:HAS_DATASET]->(dataset_value:DatasetInstance)
                    MATCH (scenario_root:DatasetScenario {{uid: $dataset_scenario_uid}})-[:HAS_INSTANCE]->(scenario_value)
                    MATCH (dataset_value)-[:HAS_DATASET_SCENARIO]->(scenario_value:DatasetScenarioInstance)
                    -[has_dataset_variable_rel:HAS_DATASET_VARIABLE]->
                    (standard_value:{standard_data_model_value_label})<-[:HAS_INSTANCE]-(standard_root:{standard_data_model_label})"""
        return None

    def create_query_filter_statement(self, **kwargs) -> tuple[str, dict]:
        (
            filter_statements_from_standard,
            filter_query_parameters,
        ) = super().create_query_filter_statement()
        filter_parameters = []
        if kwargs.get("dataset_scenario_uid"):
            filter_query_parameters["dataset_scenario_uid"] = kwargs.get(
                "dataset_scenario_uid"
            )

        ValidationException.raise_if(
            not kwargs.get("data_model_ig_name")
            or not kwargs.get("data_model_ig_version"),
            msg="Please provide data_model_ig_name and data_model_ig_version params",
        )

        data_model_ig_name = kwargs.get("data_model_ig_name")
        data_model_ig_version = kwargs.get("data_model_ig_version")

        filter_by_data_model_ig_uid = "data_model_ig_root.uid = $data_model_ig_name"
        filter_parameters.append(filter_by_data_model_ig_uid)

        filter_by_data_model_ig_version = (
            "data_model_ig_value.version_number = $data_model_ig_version"
        )
        filter_parameters.append(filter_by_data_model_ig_version)

        filter_by_has_dataset_variable_version = (
            "has_dataset_variable_rel.version_number = $data_model_ig_version"
        )
        filter_parameters.append(filter_by_has_dataset_variable_version)

        filter_query_parameters["data_model_ig_name"] = data_model_ig_name
        filter_query_parameters["data_model_ig_version"] = data_model_ig_version

        extended_filter_statements = " AND ".join(filter_parameters)
        if filter_statements_from_standard != "":
            if len(extended_filter_statements) > 0:
                filter_statements_to_return = " AND ".join(
                    [filter_statements_from_standard, extended_filter_statements]
                )
            else:
                filter_statements_to_return = filter_statements_from_standard
        else:
            filter_statements_to_return = (
                "WHERE " + extended_filter_statements
                if len(extended_filter_statements) > 0
                else ""
            )
        return filter_statements_to_return, filter_query_parameters

    def sort_by(self) -> dict | None:
        return {"dataset.ordinal": True}

    def specific_alias_clause(self) -> str:
        return """
        WITH 
            standard_root,
            uid,
            name,
            description,
            standard_value,
            has_dataset_variable_rel, 
            dataset_value,
            standard_value.label AS label,
            standard_value.title AS title,
            standard_value.core AS core,
            standard_value.simple_datatype AS simple_datatype,
            standard_value.role AS role,
            standard_value.question_text AS question_text,
            standard_value.prompt AS prompt,
            standard_value.completion_instructions AS completion_instructions,
            standard_value.implementation_notes AS implementation_notes,
            standard_value.mapping_instructions AS mapping_instructions,
            standard_value.described_value_domain AS described_value_domain,
            standard_value.value_list AS value_list,
            apoc.coll.toSet([(standard_value)<-[:HAS_DATASET_VARIABLE]-
                (:DatasetInstance)<-[:HAS_DATASET]-(data_model_ig_value:DataModelIGValue) 
                | data_model_ig_value.name]) AS data_model_ig_names,
            {ordinal:has_dataset_variable_rel.ordinal, name:dataset_value.label} AS dataset,
            head([(standard_value)-[:IMPLEMENTS_VARIABLE]->(class_variable_value:VariableClassInstance)<-[:HAS_INSTANCE]-(class_variable_root) | {
            uid:class_variable_root.uid, name:class_variable_value.label }]) AS implements_variable,
            head([(standard_value)-[:HAS_MAPPING_TARGET]->(dataset_variable_value:DatasetVariableInstance)
            <-[:HAS_INSTANCE]-(dataset_variable_root:DatasetVariable) | {uid:dataset_variable_root.uid, name:dataset_variable_value.label}]) AS has_mapping_target,
            head([(standard_root)<-[:HAS_DATASET_VARIABLE]-(catalogue:DataModelCatalogue) | catalogue.name]) AS catalogue_name,
            head([(standard_value)-[:REFERENCES_CODELIST]->(codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]-()-[:LATEST]->(codelist_value:CTCodelistNameValue) | {
            uid:codelist_root.uid, name:codelist_value.name }]) AS referenced_codelist
        """
