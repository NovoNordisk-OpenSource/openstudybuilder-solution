from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_instances.endpoint import EndpointAR
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.endpoint_template import (
    EndpointTemplateNameUidLibrary,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    IndexedTemplateParameterTerm,
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class Endpoint(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True, "format": "html"})
    ] = None
    name_plain: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    start_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    end_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    change_description: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    possible_actions: Annotated[
        list[str] | None,
        Field(
            description=(
                "Holds those actions that can be performed on the endpoint. "
                "Actions are: 'approve', 'edit', 'inactivate', 'reactivate' and 'delete'."
            ),
            json_schema_extra={"nullable": True},
        ),
    ] = None

    template: Annotated[EndpointTemplateNameUidLibrary | None, Field()] = None
    parameter_terms: Annotated[
        list[MultiTemplateParameterTerm] | None,
        Field(
            description="Holds the parameter terms that are used within the endpoint. The terms are ordered as they occur in the endpoint name.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    # objective: Objective | None= None
    library: Annotated[Library | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    study_count: Annotated[
        int, Field(description="Count of studies referencing endpoint")
    ] = 0

    @classmethod
    def from_endpoint_ar(cls, endpoint_ar: EndpointAR) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(endpoint_ar.get_parameters()):
            terms: list[IndexedTemplateParameterTerm] = []
            for index, parameter_term in enumerate(parameter.parameters):
                indexed_template_parameter_term = IndexedTemplateParameterTerm(
                    index=index + 1,
                    uid=parameter_term.uid,
                    name=parameter_term.value,
                    type=parameter.parameter_name,
                )
                terms.append(indexed_template_parameter_term)
            conjunction = parameter.conjunction

            parameter_terms.append(
                MultiTemplateParameterTerm(
                    conjunction=conjunction, position=position + 1, terms=terms
                )
            )
        return cls(
            uid=endpoint_ar.uid,
            name=endpoint_ar.name,
            name_plain=endpoint_ar.name_plain,
            start_date=endpoint_ar.item_metadata.start_date,
            end_date=endpoint_ar.item_metadata.end_date,
            status=endpoint_ar.item_metadata.status.value,
            version=endpoint_ar.item_metadata.version,
            change_description=endpoint_ar.item_metadata.change_description,
            author_username=endpoint_ar.item_metadata.author_username,
            possible_actions=sorted(
                {_.value for _ in endpoint_ar.get_possible_actions()}
            ),
            template=EndpointTemplateNameUidLibrary(
                name=endpoint_ar.template_name,
                name_plain=endpoint_ar.template_name_plain,
                uid=endpoint_ar.template_uid,
                sequence_id=endpoint_ar.template_sequence_id,
                library_name=endpoint_ar.template_library_name,
            ),
            library=Library.from_library_vo(endpoint_ar.library),
            study_count=endpoint_ar.study_count,
            parameter_terms=parameter_terms,
        )


class EndpointVersion(Endpoint):
    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class EndpointEditInput(PatchInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the endpoint template.",
        ),
    ]
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]


class EndpointCreateInput(PostInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the endpoint template.",
        ),
    ]
    endpoint_template_uid: Annotated[
        str,
        Field(
            description="The unique id of the endpoint template that is used as the basis for the new endpoint.",
            min_length=1,
        ),
    ]
    library_name: Annotated[
        str | None,
        Field(
            description="If specified: The name of the library to which the endpoint will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
            "If not specified: The library of the endpoint template will be used.",
            min_length=1,
        ),
    ] = None
