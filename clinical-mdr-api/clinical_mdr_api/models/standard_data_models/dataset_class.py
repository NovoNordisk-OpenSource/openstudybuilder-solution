from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class SimpleDataModel(BaseModel):
    data_model_name: Annotated[str, Field()]
    ordinal: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class SimpleDataset(BaseModel):
    uid: Annotated[str, Field()]
    dataset_name: Annotated[str, Field()]


class DatasetClass(BaseModel):
    uid: Annotated[str, Field()]
    label: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    title: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    catalogue_name: Annotated[str, Field()]
    parent_class: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    data_models: Annotated[list[SimpleDataModel], Field()]

    @classmethod
    def from_repository_output(cls, input_dict: dict):
        return cls(
            uid=input_dict.get("uid"),
            label=input_dict.get("standard_value").get("label"),
            title=input_dict.get("standard_value").get("title"),
            description=input_dict.get("standard_value").get("description"),
            catalogue_name=input_dict.get("catalogue_name"),
            parent_class=input_dict.get("parent_class_name"),
            data_models=[
                SimpleDataModel(
                    data_model_name=data_model.get("data_model_name"),
                    ordinal=data_model.get("ordinal"),
                )
                for data_model in input_dict.get("data_models")
            ],
        )
