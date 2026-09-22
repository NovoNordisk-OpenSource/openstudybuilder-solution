from typing import Any

from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    VariableClass,
    VariableClassInstance,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.variable_class import (
    VariableClass as VariableClassAPIModel,
)
from common.exceptions import ValidationException


class VariableClassRepository(StandardDataModelRepository):
    root_class = VariableClass
    value_class = VariableClassInstance
    return_model = VariableClassAPIModel

    # pylint: disable=unused-argument
    def generic_match_clause(self, versioning_relationship: str):
        standard_data_model_label = self.root_class.__label__
        standard_data_model_value_label = self.value_class.__label__
        return f"""MATCH (standard_root:{standard_data_model_label})-[:HAS_INSTANCE]->
                (standard_value:{standard_data_model_value_label})<-[has_variable_class_rel:HAS_VARIABLE_CLASS]-
                (dataset_class_value:DatasetClassInstance)<-[:HAS_DATASET_CLASS]-(data_model_value:DataModelValue)
                <-[:HAS_VERSION]-(data_model_root:DataModelRoot)"""

    def create_query_filter_statement(self, **kwargs) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_standard,
            filter_query_parameters,
        ) = super().create_query_filter_statement(**kwargs)
        filter_parameters = []
        if kwargs.get("dataset_class_name"):
            dataset_class_name = kwargs.get("dataset_class_name")
            filter_by_dataset_class_name = (
                "$dataset_class_name IN [(dataset_class_value)<-[:HAS_PARENT_CLASS*0..5]-(dataset_class) "
                "| dataset_class.label] "
            )
            filter_parameters.append(filter_by_dataset_class_name)
            filter_query_parameters["dataset_class_name"] = dataset_class_name

        ValidationException.raise_if(
            not kwargs.get("data_model_name") or not kwargs.get("data_model_version"),
            msg="Please provide data_model_name and data_model_version params",
        )

        data_model_name = kwargs.get("data_model_name")
        data_model_version = kwargs.get("data_model_version")

        filter_by_data_model_uid = "data_model_root.uid = $data_model_name"
        filter_parameters.append(filter_by_data_model_uid)

        filter_by_data_model_version = (
            "data_model_value.version_number = $data_model_version"
        )
        filter_parameters.append(filter_by_data_model_version)

        filter_by_has_variable_class_version = (
            "has_variable_class_rel.version_number = $data_model_version"
        )
        filter_parameters.append(filter_by_has_variable_class_version)

        filter_query_parameters["data_model_name"] = data_model_name
        filter_query_parameters["data_model_version"] = data_model_version

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

    def sort_by(self) -> dict[str, bool] | None:
        return {"dataset_class.ordinal": True}

    def specific_alias_clause(self) -> str:
        return """
            *,
            standard_root.uid AS uid,
            standard_value.label AS label,
            standard_value.description AS description,
            standard_value.implementation_notes AS implementation_notes,
            standard_value.title AS title,
            standard_value.core AS core,
            standard_value.completion_instructions AS completion_instructions,
            standard_value.mapping_instructions AS mapping_instructions,
            standard_value.prompt AS prompt,
            standard_value.question_text AS question_text,
            standard_value.simple_datatype AS simple_datatype,
            standard_value.role AS role,
            standard_value.described_value_domain AS described_value_domain,
            standard_value.notes AS notes,
            standard_value.usage_restrictions AS usage_restrictions,
            standard_value.examples AS examples,
            [(standard_value)-[:QUALIFIES_VARIABLE {catalogue:$data_model_name, version_number:$data_model_version}]->(qualified_variable:VariableClassInstance)<-[:HAS_INSTANCE]-(qualified_variable_root) | {
                uid:qualified_variable_root.uid, name:qualified_variable.label }] AS qualifies_variables,
            {dataset_class_name:dataset_class_value.label, ordinal:toInteger(has_variable_class_rel.ordinal)} AS dataset_class,
            head([(standard_root)<-[:HAS_VARIABLE_CLASS]-(catalogue:DataModelCatalogue) | catalogue.name]) AS catalogue_name,
            [(standard_value)-[:REFERENCES_CODELIST]->(codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]-()-[:LATEST]->
                (codelist_value:CTCodelistNameValue) | {uid:codelist_root.uid, name:codelist_value.name }] AS referenced_codelists,
            [(standard_value)-[mt_rel:HAS_MAPPING_TARGET]->(class_variable_value:VariableClassInstance)
                <-[:HAS_INSTANCE]-(class_variable_root:VariableClass) WHERE mt_rel.version_number=$data_model_version
                | {uid:class_variable_root.uid, name:class_variable_value.label}] AS has_mapping_targets
        """
