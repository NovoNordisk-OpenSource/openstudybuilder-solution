from typing import Sequence

from src.scripts.entities.cdisc_data_models.data_model_variable import (
    DataModelVariable,
)

from src.scripts.entities.cdisc_data_models.utils import (
    extract_variables_from_json_data,
)


class DataModelScenario:
    def __init__(self, href: str):
        self.href = href

        self.__variables: set[DataModelVariable] = set()

    def get_variables(self) -> Sequence[DataModelVariable]:
        return list(self.__variables)

    def __add_variable(self, variable: DataModelVariable):
        self.__variables.add(variable)

    def add_variables(self, variables: Sequence[DataModelVariable]):
        for variable in variables:
            self.__add_variable(variable)

    def set_attributes(
        self,
        # will serve as uid
        title: str,
        # scenario in JSON file
        label: str,
        ordinal: str,
        dataset_href: str,
    ):
        self.title: str = title
        self.label: str = label
        self.ordinal: str = ordinal
        self.dataset_href: str = dataset_href

    def load_variables_from_json_data(
        self,
        scenario_json_data,
        catalogue,
        data_model_import,
        data_model_type,
    ) -> None:
        variables = extract_variables_from_json_data(
            json_data=scenario_json_data,
            catalogue=catalogue,
            data_model_import=data_model_import,
            data_model_type=data_model_type,
            is_class_dataset=False,
        )

        self.add_variables(variables)
