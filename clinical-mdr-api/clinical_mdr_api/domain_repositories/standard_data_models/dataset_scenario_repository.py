from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DatasetScenario,
    DatasetScenarioInstance,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.dataset_scenario import (
    DatasetScenario as DatasetScenarioAPIModel,
)
from common.exceptions import ValidationException


class DatasetScenarioRepository(StandardDataModelRepository):
    root_class = DatasetScenario
    value_class = DatasetScenarioInstance
    return_model = DatasetScenarioAPIModel

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
                (standard_value:{standard_data_model_value_label})<-[has_dataset_scenario:HAS_DATASET_SCENARIO]-
                (dataset_value:DatasetInstance)<-[:HAS_DATASET]-(data_model_ig_value:DataModelIGValue)
                <-[:HAS_VERSION]-(data_model_ig_root:DataModelIGRoot)"""

    def create_query_filter_statement(self, **kwargs) -> tuple[str, dict]:
        (
            filter_statements_from_standard,
            filter_query_parameters,
        ) = super().create_query_filter_statement()
        filter_parameters = []

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

        filter_by_has_dataset_scenario_version = (
            "has_dataset_scenario.version_number = $data_model_ig_version"
        )
        filter_parameters.append(filter_by_has_dataset_scenario_version)

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
        WITH *,
            standard_value.label AS label,
            head([(standard_root)<-[:HAS_DATASET_SCENARIO]-(catalogue:DataModelCatalogue) | catalogue.name]) AS catalogue_name,
            {ordinal:has_dataset_scenario.ordinal, name:dataset_value.label} AS dataset,
            apoc.coll.toSet([(standard_value)<-[:HAS_DATASET_SCENARIO]-
                (:DatasetInstance)<-[:HAS_DATASET]-(data_model_ig_value:DataModelIGValue) 
                | data_model_ig_value.name]) AS data_model_ig_names
        """
