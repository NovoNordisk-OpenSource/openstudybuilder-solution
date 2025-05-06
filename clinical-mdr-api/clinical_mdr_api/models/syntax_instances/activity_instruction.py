from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_instances.activity_instruction import (
    ActivityInstructionAR,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.activity_instruction_template import (
    ActivityInstructionTemplateNameUidLibrary,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class ActivityInstructionNameUid(BaseModel):
    uid: str
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name_plain: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class ActivityInstruction(ActivityInstructionNameUid):
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
    template: ActivityInstructionTemplateNameUidLibrary | None
    parameter_terms: Annotated[
        list[MultiTemplateParameterTerm],
        Field(
            description="""Holds the parameter terms that are used within the activity
        instruction. The terms are ordered as they occur in the activity instruction name.""",
        ),
    ] = []
    library: Annotated[Library | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    study_count: Annotated[
        int, Field(description="Count of studies referencing activity instruction")
    ] = 0
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

    @classmethod
    def from_activity_instruction_ar(
        cls, activity_instruction_ar: ActivityInstructionAR
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(activity_instruction_ar.get_parameters()):
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
            uid=activity_instruction_ar.uid,
            name=activity_instruction_ar.name,
            name_plain=activity_instruction_ar.name_plain,
            start_date=activity_instruction_ar.item_metadata.start_date,
            end_date=activity_instruction_ar.item_metadata.end_date,
            status=activity_instruction_ar.item_metadata.status.value,
            version=activity_instruction_ar.item_metadata.version,
            change_description=activity_instruction_ar.item_metadata.change_description,
            author_username=activity_instruction_ar.item_metadata.author_username,
            template=ActivityInstructionTemplateNameUidLibrary(
                name=activity_instruction_ar.template_name,
                name_plain=activity_instruction_ar.template_name_plain,
                uid=activity_instruction_ar.template_uid,
                sequence_id=activity_instruction_ar.template_sequence_id,
                library_name=activity_instruction_ar.template_library_name,
            ),
            library=Library.from_library_vo(activity_instruction_ar.library),
            study_count=activity_instruction_ar.study_count,
            parameter_terms=parameter_terms,
            possible_actions=sorted(
                {_.value for _ in activity_instruction_ar.get_possible_actions()}
            ),
        )


class ActivityInstructionVersion(ActivityInstruction):
    """
    Class for storing Activity Instructions and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class ActivityInstructionEditInput(PatchInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput] | None,
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the activity instruction template.",
        ),
    ] = None
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]


class ActivityInstructionCreateInput(PostInputModel):
    activity_instruction_template_uid: Annotated[
        str,
        Field(
            description="The unique id of the activity instruction template that is used as the basis for the new activity instruction.",
            min_length=1,
        ),
    ]
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the activity instruction template.",
        ),
    ]
    library_name: Annotated[
        str | None,
        Field(
            description="If specified: The name of the library to which the criteria will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* criteria can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
            "If not specified: The library of the criteria template will be used.",
            min_length=1,
        ),
    ] = None
