from typing import Sequence

from src.scripts.entities.cdisc_data_models.data_model_variable import (
    DataModelVariable,
)
from src.scripts.entities.cdisc_data_models.utils import (
    extract_variables_from_json_data,
    extract_variables_from_csv_data,
)


class DataModelClass:
    def __init__(self, name: str):
        self.name = name

        self.__variables: set[DataModelVariable] = set()

    def get_variables(self) -> Sequence[DataModelVariable]:
        return list(self.__variables)

    def __add_variable(self, variable: DataModelVariable):
        self.__variables.add(variable)

    def __add_variables(self, variables: Sequence[DataModelVariable]):
        for variable in variables:
            self.__add_variable(variable)

    def drop_variables(self) -> None:
        self.__variables = set()

    def set_attributes(
        self,
        title: str,
        label: str,
        description: str,
        ordinal: str,
        href: str,
        implements_class: str,
        prior_version: str,
        subclasses: "list(str)" = [],
    ):
        self.title: str = title
        self.label: str = label
        self.description: str = description
        self.ordinal: str = ordinal
        self.href: str = href
        self.implements_class: str = implements_class
        self.subclasses: list(str) = subclasses
        self.prior_version: str = prior_version

    def load_variables_from_json_data(
        self,
        class_json_data,
        catalogue,
        data_model_import,
        data_model_type,
        is_class_dataset: bool = False,
    ) -> None:
        if catalogue == "ADAM":
            for _variable_set in class_json_data.get("analysisVariableSets", []):
                variables = extract_variables_from_json_data(
                    json_data=_variable_set,
                    catalogue=catalogue,
                    data_model_import=data_model_import,
                    data_model_type=data_model_type,
                    is_class_dataset=is_class_dataset,
                )
                self.__add_variables(variables)
        else:
            variables = extract_variables_from_json_data(
                json_data=class_json_data,
                catalogue=catalogue,
                data_model_import=data_model_import,
                data_model_type=data_model_type,
                is_class_dataset=is_class_dataset,
            )

            self.__add_variables(variables)

    def load_variables_from_csv_data(
        self,
        class_csv_data,
        catalogue,
        data_model_import,
        data_model_type,
        variables_data,
        is_class_dataset: bool = False,
    ) -> None:
        variables = extract_variables_from_csv_data(
            class_csv_data=class_csv_data,
            catalogue=catalogue,
            data_model_import=data_model_import,
            data_model_type=data_model_type,
            variables_data=variables_data,
            is_class_dataset=is_class_dataset,
        )

        self.__add_variables(variables)
