from typing import Annotated, Any

from pydantic import Field

from clinical_mdr_api.models.standard_data_models.dataset_variable import (
    SimpleMappingTarget,
)
from clinical_mdr_api.models.utils import BaseModel


class SimpleReferencedCodelistForVariableClass(BaseModel):
    uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class SimpleDatasetClassForVariableClass(BaseModel):
    ordinal: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    dataset_class_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class SimpleVariableClass(BaseModel):
    uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class VariableClass(BaseModel):
    uid: Annotated[str, Field()]
    label: Annotated[str, Field()]
    title: Annotated[str, Field()]
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    implementation_notes: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    mapping_instructions: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    core: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    completion_instructions: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    prompt: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    question_text: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    simple_datatype: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    role: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    described_value_domain: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    notes: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    usage_restrictions: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    examples: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    dataset_class: Annotated[SimpleDatasetClassForVariableClass, Field()]
    catalogue_name: Annotated[str, Field()]
    has_mapping_targets: Annotated[
        list[SimpleMappingTarget] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    referenced_codelists: Annotated[
        list[SimpleReferencedCodelistForVariableClass] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    qualifies_variables: Annotated[
        list[SimpleVariableClass] | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_repository_output(cls, input_dict: dict[str, Any]):
        return cls(
            uid=input_dict.get("standard_root").get("uid"),
            label=input_dict.get("standard_value").get("label"),
            title=input_dict.get("standard_value").get("title"),
            description=input_dict.get("standard_value").get("description"),
            implementation_notes=input_dict.get("standard_value").get(
                "implementation_notes"
            ),
            mapping_instructions=input_dict.get("standard_value").get(
                "mapping_instructions"
            ),
            core=input_dict.get("standard_value").get("core"),
            completion_instructions=input_dict.get("standard_value").get(
                "completion_instructions"
            ),
            prompt=input_dict.get("standard_value").get("prompt"),
            question_text=input_dict.get("standard_value").get("question_text"),
            simple_datatype=input_dict.get("standard_value").get("simple_datatype"),
            role=input_dict.get("standard_value").get("role"),
            described_value_domain=input_dict.get("standard_value").get(
                "described_value_domain"
            ),
            notes=input_dict.get("standard_value").get("notes"),
            usage_restrictions=input_dict.get("standard_value").get(
                "usage_restrictions"
            ),
            examples=input_dict.get("standard_value").get("examples"),
            catalogue_name=input_dict["catalogue_name"],
            dataset_class=SimpleDatasetClassForVariableClass(
                dataset_class_name=input_dict.get("dataset_class").get(
                    "dataset_class_name"
                ),
                ordinal=input_dict.get("dataset_class").get("ordinal"),
            ),
            referenced_codelists=(
                [
                    SimpleReferencedCodelistForVariableClass(
                        uid=cl.get("uid"),
                        name=cl.get("name"),
                    )
                    for cl in input_dict.get("referenced_codelists")
                ]
                or None
            ),
            has_mapping_targets=(
                [
                    SimpleMappingTarget(
                        uid=target.get("uid"),
                        name=target.get("name"),
                    )
                    for target in input_dict.get("has_mapping_targets")
                ]
            ),
            qualifies_variables=(
                [
                    SimpleVariableClass(
                        uid=variable.get("uid"),
                        name=variable.get("name"),
                    )
                    for variable in input_dict.get("qualifies_variables")
                ]
            ),
        )
