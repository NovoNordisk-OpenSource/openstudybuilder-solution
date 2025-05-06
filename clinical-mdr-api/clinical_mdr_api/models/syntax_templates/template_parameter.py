from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    TemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel


class TemplateParameter(BaseModel):
    name: Annotated[
        str | None,
        Field(
            description="The name of the template parameter. E.g. 'Intervention', 'Indication', 'Activity', ...",
            json_schema_extra={"nullable": True},
        ),
    ]

    terms: Annotated[
        list[TemplateParameterTerm],
        Field(description="The possible terms of the template parameter."),
    ] = []


class ComplexTemplateParameter(BaseModel):
    name: str | None = None
    format: str | None = None
    parameters: Annotated[list[TemplateParameter], Field()] = []
    terms: Annotated[
        list[TemplateParameterTerm],
        Field(description="The possible terms of the template parameter."),
    ] = []
