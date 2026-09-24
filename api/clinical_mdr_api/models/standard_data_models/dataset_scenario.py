from typing import Annotated, Any

from pydantic import Field

from clinical_mdr_api.models.standard_data_models.dataset_variable import (
    SimpleDatasetForDatasetVariable,
)
from clinical_mdr_api.models.utils import BaseModel


class DatasetScenario(BaseModel):
    uid: Annotated[str, Field()]
    label: Annotated[str, Field()]
    catalogue_name: Annotated[str, Field()]
    dataset: Annotated[SimpleDatasetForDatasetVariable, Field()]
    data_model_ig_names: Annotated[list[str], Field()]

    @classmethod
    def from_repository_output(cls, input_dict: dict[str, Any]):
        return cls(
            uid=input_dict.get("standard_root").get("uid"),
            label=input_dict.get("standard_value").get("label"),
            catalogue_name=input_dict["catalogue_name"],
            dataset=SimpleDatasetForDatasetVariable(
                ordinal=input_dict.get("dataset").get("ordinal"),
                uid=input_dict.get("dataset").get("uid"),
            ),
            data_model_ig_names=input_dict["data_model_ig_names"],
        )
