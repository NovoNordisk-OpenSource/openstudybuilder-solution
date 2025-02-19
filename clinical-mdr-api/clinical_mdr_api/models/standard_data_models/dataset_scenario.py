from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.standard_data_models.dataset_variable import SimpleDataset
from clinical_mdr_api.models.utils import BaseModel


class DatasetScenario(BaseModel):
    uid: Annotated[str, Field()]
    label: Annotated[str, Field()]
    catalogue_name: Annotated[str, Field()]
    dataset: Annotated[SimpleDataset, Field()]
    data_model_ig_names: Annotated[list[str], Field()]

    @classmethod
    def from_repository_output(cls, input_dict: dict):
        return cls(
            uid=input_dict.get("uid"),
            label=input_dict.get("standard_value").get("label"),
            catalogue_name=input_dict.get("catalogue_name"),
            dataset=SimpleDataset(
                ordinal=input_dict.get("dataset").get("ordinal"),
                name=input_dict.get("dataset").get("name"),
            ),
            data_model_ig_names=input_dict.get("data_model_ig_names"),
        )
