from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_instances.objective import ObjectiveAR
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.objective_template import (
    ObjectiveTemplateNameUidLibrary,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class Objective(BaseModel):
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
    possible_actions: list[str] = Field(
        description=(
            "Holds those actions that can be performed on the objective. "
            "Actions are: 'approve', 'edit', 'inactivate', 'reactivate' and 'delete'."
        ),
        default_factory=list,
    )

    template: Annotated[ObjectiveTemplateNameUidLibrary | None, Field()] = None
    parameter_terms: list[MultiTemplateParameterTerm] = Field(
        description="Holds the parameter terms that are used within the objective. The terms are ordered as they occur in the objective name.",
        default_factory=list,
    )
    library: Annotated[Library | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    study_count: Annotated[
        int, Field(description="Count of studies referencing objective")
    ] = 0

    @classmethod
    def from_objective_ar(cls, objective_ar: ObjectiveAR) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(objective_ar.get_parameters()):
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
            uid=objective_ar.uid,
            name=objective_ar.name,
            name_plain=objective_ar.name_plain,
            start_date=objective_ar.item_metadata.start_date,
            end_date=objective_ar.item_metadata.end_date,
            status=objective_ar.item_metadata.status.value,
            version=objective_ar.item_metadata.version,
            change_description=objective_ar.item_metadata.change_description,
            author_username=objective_ar.item_metadata.author_username,
            possible_actions=sorted(
                {_.value for _ in objective_ar.get_possible_actions()}
            ),
            template=ObjectiveTemplateNameUidLibrary(
                name=objective_ar.template_name,
                name_plain=objective_ar.template_name_plain,
                uid=objective_ar.template_uid,
                sequence_id=objective_ar.template_sequence_id,
                library_name=objective_ar.template_library_name,
            ),
            library=Library.from_library_vo(objective_ar.library),
            study_count=objective_ar.study_count,
            parameter_terms=parameter_terms,
        )


class ObjectiveVersion(Objective):
    """
    Class for storing Objectives and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class ObjectiveEditInput(PatchInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput] | None,
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the objective template.",
        ),
    ] = None
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]


class ObjectiveCreateInput(PostInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput] | None,
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the objective template.",
        ),
    ] = None
    objective_template_uid: Annotated[
        str,
        Field(
            description="The unique id of the objective template that is used as the basis for the new objective.",
            min_length=1,
        ),
    ]
    library_name: Annotated[
        str | None,
        Field(
            description="If specified: The name of the library to which the objective will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
            "If not specified: The library of the objective template will be used.",
            min_length=1,
        ),
    ] = None
