from typing import Annotated, Any

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class SimpleDataModelForDatasetClass(BaseModel):
    data_model_name: Annotated[str, Field()]
    ordinal: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class SimpleDatasetForDatasetClass(BaseModel):
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
    parent_class_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    data_model: Annotated[SimpleDataModelForDatasetClass, Field()]

    @classmethod
    def from_repository_output(cls, input_dict: dict[str, Any]):
        return cls(
            uid=input_dict.get("standard_root").get("uid"),
            label=input_dict.get("standard_value").get("label"),
            title=input_dict.get("standard_value").get("title"),
            description=input_dict.get("standard_value").get("description"),
            catalogue_name=input_dict["catalogue_name"],
            parent_class_name=input_dict.get("parent_class_name"),
            data_model=SimpleDataModelForDatasetClass(
                data_model_name=input_dict.get("data_model", {}).get("name"),
                ordinal=input_dict.get("data_model", {}).get("ordinal"),
            ),
        )
