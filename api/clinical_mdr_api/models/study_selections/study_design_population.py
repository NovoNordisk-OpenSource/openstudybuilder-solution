"""Pydantic models for study design populations."""

from datetime import datetime
from typing import Annotated

from pydantic import Field, model_validator

from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel
from common.config import settings


class StudyDesignPopulationInput(PostInputModel):
    group_id: Annotated[
        str | None,
        Field(
            description="Group identifier for the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="The name of the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    definition: Annotated[
        str | None,
        Field(
            description="Definition of the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    notes: Annotated[
        str | None,
        Field(
            description="Optional notes for the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @model_validator(mode="after")
    def validate_at_least_one_field_is_set(self):
        if not any([self.group_id, self.name, self.definition, self.notes]):
            raise ValueError(
                "At least one of 'group_id', 'name', 'definition' or 'notes' must be provided."
            )
        return self


class StudyDesignPopulationPatchInput(PatchInputModel):
    group_id: Annotated[
        str | None,
        Field(
            description="Group identifier for the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="The name of the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    definition: Annotated[
        str | None,
        Field(
            description="Definition of the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    notes: Annotated[
        str | None,
        Field(
            description="Optional notes for the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class StudyDesignPopulation(BaseModel):
    uid: Annotated[
        str, Field(description="The unique identifier of the study design population.")
    ]
    group_id: Annotated[
        str | None,
        Field(
            description="Group identifier for the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="The name of the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    definition: Annotated[
        str | None,
        Field(
            description="Definition of the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    notes: Annotated[
        str | None,
        Field(
            description="Optional notes for the study design population.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    order: Annotated[
        int | None,
        Field(
            description="The ordering of the selection.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    start_date: Annotated[
        datetime | None,
        Field(
            description="The point in time when this version was created.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class StudyDesignPopulationVersion(StudyDesignPopulation):
    study_uid: Annotated[str, Field(description="The unique id of the study.")]
    study_version: Annotated[
        str | None,
        Field(
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    start_date: Annotated[
        datetime,
        Field(description="The point in time when this version was created."),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            description="The point in time when this version was superseded.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    status: Annotated[
        str | None,
        Field(
            description="Status of the study at the time of this version.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    change_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    changes: Annotated[
        list[str],
        Field(
            description="List of changes between the current and the previous version."
        ),
    ]


class StudySelectionDesignPopulationNewOrder(BaseModel):
    new_order: Annotated[
        int,
        Field(
            description="new order of the selected study design population",
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ]
