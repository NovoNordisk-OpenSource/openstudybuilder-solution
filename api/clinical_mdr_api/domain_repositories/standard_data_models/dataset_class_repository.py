from typing import Any

from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DatasetClass,
    DatasetClassInstance,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.dataset_class import (
    DatasetClass as DatasetClassAPIModel,
)
from common.exceptions import ValidationException


class DatasetClassRepository(StandardDataModelRepository):
    root_class = DatasetClass
    value_class = DatasetClassInstance
    return_model = DatasetClassAPIModel

    # pylint: disable=unused-argument
    def generic_match_clause(self, versioning_relationship: str):
        standard_data_model_label = self.root_class.__label__
        standard_data_model_value_label = self.value_class.__label__
        query = f"""MATCH (standard_root:{standard_data_model_label})-[:HAS_INSTANCE]->
                (standard_value:{standard_data_model_value_label})<-[hdc:HAS_DATASET_CLASS]-(data_model_value:DataModelValue)
            """
        return query

    def specific_alias_clause(self) -> str:
        return """
            *,
            standard_root.uid AS uid,
            standard_value.label AS label,
            standard_value.title AS title,
            standard_value.description AS description,
            {name: data_model_value.name, ordinal: hdc.ordinal} AS data_model,
            toInteger(apoc.text.split(hdc.ordinal, "\\.")[0]) AS split_ordinal0,
            toInteger(coalesce(apoc.text.split(hdc.ordinal, "\\.")[1], 0)) AS split_ordinal1,
            head([(standard_root)<-[:HAS_DATASET_CLASS]-(catalogue:DataModelCatalogue) | catalogue.name]) AS catalogue_name,
            head([(standard_value)-[:HAS_PARENT_CLASS]->(parent_class:DatasetClassInstance) | parent_class.label]) AS parent_class_name
        """

    def sort_by(self) -> dict[str, bool] | None:
        return {
            "split_ordinal0": True,
            "split_ordinal1": True,
        }

    def create_query_filter_statement(self, **kwargs) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_standard,
            filter_query_parameters,
        ) = super().create_query_filter_statement(**kwargs)

        if not kwargs.get("find_by_uid"):
            ValidationException.raise_if(
                not kwargs.get("data_model_name"),
                msg="Please provide data_model_name parameter",
            )

            data_model_name = kwargs.get("data_model_name")

            filter_by_data_model_name = "data_model_value.name = $data_model_name"

            filter_query_parameters["data_model_name"] = data_model_name

            if filter_statements_from_standard != "":
                filter_statements_to_return = " AND ".join(
                    [filter_statements_from_standard, filter_by_data_model_name]
                )
            else:
                filter_statements_to_return = "WHERE " + filter_by_data_model_name
            return filter_statements_to_return, filter_query_parameters
        return filter_statements_from_standard, filter_query_parameters
