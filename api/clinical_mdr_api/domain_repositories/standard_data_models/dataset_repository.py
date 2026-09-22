from typing import Any

from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    Dataset,
    DatasetInstance,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.dataset import (
    Dataset as DatasetAPIModel,
)
from common.exceptions import ValidationException


class DatasetRepository(StandardDataModelRepository):
    root_class = Dataset
    value_class = DatasetInstance
    return_model = DatasetAPIModel

    # pylint: disable=unused-argument
    def generic_match_clause(self, versioning_relationship: str):
        standard_data_model_label = self.root_class.__label__
        standard_data_model_value_label = self.value_class.__label__
        return f"""MATCH (standard_root:{standard_data_model_label})-[:HAS_INSTANCE]->
                (standard_value:{standard_data_model_value_label})<-[has_dataset:HAS_DATASET]-
                (data_model_ig_value:DataModelIGValue {{version_number: $data_model_ig_version}})<-[:HAS_VERSION]-(data_model_ig_root:DataModelIGRoot {{uid:$data_model_ig_name}})
                MATCH (standard_value)-[implements:IMPLEMENTS_DATASET_CLASS]->(dataset_class_value)<-[:HAS_DATASET_CLASS]-(:DataModelValue)<-[:IMPLEMENTS]-(data_model_ig_value)
                MATCH (dataset_class_value)<-[:HAS_INSTANCE]-(dataset_class:DatasetClass)
"""

    def create_query_filter_statement(self, **kwargs) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_standard,
            filter_query_parameters,
        ) = super().create_query_filter_statement(**kwargs)
        filter_parameters = []

        ValidationException.raise_if(
            not kwargs.get("data_model_ig_name")
            or not kwargs.get("data_model_ig_version"),
            msg="Please provide data_model_ig_name and data_model_ig_version params",
        )

        data_model_ig_name = kwargs.get("data_model_ig_name")
        data_model_ig_version = kwargs.get("data_model_ig_version")

        filter_by_implements_dataset_class_version = (
            "implements.version_number = $data_model_ig_version"
        )
        filter_parameters.append(filter_by_implements_dataset_class_version)

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

    def sort_by(self) -> dict[str, bool] | None:
        return {"data_model_ig.ordinal": True}

    def specific_alias_clause(self) -> str:
        return """
            *,
            standard_root.uid AS uid,
            standard_value.label AS label,
            standard_value.title AS title,
            standard_value.description AS description,
            {dataset_class_name:dataset_class_value.label, dataset_class_uid:dataset_class.uid} AS implemented_dataset_class,
            head([(standard_value)<-[has_dataset:HAS_DATASET]-(data_model_ig_value:DataModelIGValue) | 
            {ordinal:toInteger(has_dataset.ordinal), data_model_ig_name:data_model_ig_value.name}]) AS data_model_ig
        """
