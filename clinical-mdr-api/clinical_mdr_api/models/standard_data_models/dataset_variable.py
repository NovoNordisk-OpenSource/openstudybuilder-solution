from typing import Annotated

from pydantic import ConfigDict, Field

from clinical_mdr_api.models.utils import BaseModel


class SimpleMappingTarget(BaseModel):
    uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class SimpleImplementsVariable(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]


class SimpleDataset(BaseModel):
    ordinal: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name: Annotated[str, Field()]


class SimpleReferencedCodelist(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            description="The uid of the referenced codelist",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="The name of the referenced codelist",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class DatasetVariable(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[str, Field()]
    label: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    title: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    simple_datatype: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    question_text: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    prompt: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    completion_instructions: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    implementation_notes: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    mapping_instructions: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    role: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    core: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    described_value_domain: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    value_list: Annotated[list[str], Field()] = []
    dataset: Annotated[SimpleDataset, Field()]
    data_model_ig_names: Annotated[
        list[str],
        Field(
            description="Versions of associated data model implementation guides",
        ),
    ]
    implements_variable: Annotated[
        SimpleImplementsVariable | None, Field(json_schema_extra={"nullable": True})
    ] = None
    has_mapping_target: Annotated[
        SimpleMappingTarget | None, Field(json_schema_extra={"nullable": True})
    ] = None
    catalogue_name: Annotated[str, Field()]
    referenced_codelist: Annotated[
        SimpleReferencedCodelist | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_repository_output(cls, input_dict: dict):
        return cls(
            uid=input_dict.get("uid"),
            label=input_dict.get("standard_value").get("label"),
            title=input_dict.get("standard_value").get("title"),
            description=input_dict.get("standard_value").get("description"),
            simple_datatype=input_dict.get("standard_value").get("simple_datatype"),
            role=input_dict.get("standard_value").get("role"),
            core=input_dict.get("standard_value").get("core"),
            question_text=input_dict.get("question_text"),
            prompt=input_dict.get("prompt"),
            completion_instructions=input_dict.get("completion_instructions"),
            implementation_notes=input_dict.get("implementation_notes"),
            mapping_instructions=input_dict.get("mapping_instructions"),
            described_value_domain=input_dict.get("described_value_domain"),
            value_list=(
                input_dict.get("value_list") if input_dict.get("value_list") else []
            ),
            catalogue_name=input_dict.get("catalogue_name"),
            data_model_ig_names=input_dict.get("data_model_ig_names"),
            dataset=SimpleDataset(
                name=input_dict.get("dataset").get("name"),
                ordinal=input_dict.get("dataset").get("ordinal"),
            ),
            implements_variable=(
                SimpleImplementsVariable(
                    uid=input_dict.get("implements_variable").get("uid"),
                    name=input_dict.get("implements_variable").get("name"),
                )
                if input_dict.get("implements_variable")
                else None
            ),
            has_mapping_target=(
                SimpleMappingTarget(
                    uid=input_dict.get("has_mapping_target").get("uid"),
                    name=input_dict.get("has_mapping_target").get("name"),
                )
                if input_dict.get("has_mapping_target")
                else None
            ),
            referenced_codelist=(
                SimpleReferencedCodelist(
                    uid=input_dict.get("referenced_codelist").get("uid"),
                    name=input_dict.get("referenced_codelist").get("name"),
                )
                if input_dict.get("referenced_codelist")
                else None
            ),
        )
