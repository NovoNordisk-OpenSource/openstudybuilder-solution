from typing import Annotated, Any

from pydantic import ConfigDict, Field

from clinical_mdr_api.models.utils import BaseModel


class SimpleDatasetClass(BaseModel):
    dataset_class_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    dataset_class_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class SimpleDataModelIG(BaseModel):
    ordinal: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    data_model_ig_name: Annotated[str, Field()]


class Dataset(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[str, Field()]
    label: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    title: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    implemented_dataset_class: Annotated[
        SimpleDatasetClass | None, Field(json_schema_extra={"nullable": True})
    ] = None
    data_model_ig: Annotated[SimpleDataModelIG, Field()]

    @classmethod
    def from_repository_output(cls, input_dict: dict[str, Any]):
        return cls(
            uid=input_dict.get("standard_root").get("uid"),
            label=input_dict.get("standard_value").get("label"),
            title=input_dict.get("standard_value").get("title"),
            description=input_dict.get("standard_value").get("description"),
            implemented_dataset_class=(
                SimpleDatasetClass(
                    dataset_class_uid=input_dict.get("implemented_dataset_class").get(
                        "dataset_class_uid"
                    ),
                    dataset_class_name=input_dict.get("implemented_dataset_class").get(
                        "dataset_class_name"
                    ),
                )
                if input_dict.get("implemented_dataset_class")
                else None
            ),
            data_model_ig=SimpleDataModelIG(
                ordinal=input_dict.get("data_model_ig").get("ordinal"),
                data_model_ig_name=input_dict.get("data_model_ig").get(
                    "data_model_ig_name"
                ),
            ),
        )
