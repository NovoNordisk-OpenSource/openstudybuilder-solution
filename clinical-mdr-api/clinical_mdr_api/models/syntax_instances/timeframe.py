from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_instances.timeframe import TimeframeAR
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
    TemplateParameterComplexValue,
)
from clinical_mdr_api.models.syntax_templates.timeframe_template import (
    TimeframeTemplateNameUidLibrary,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel
from clinical_mdr_api.utils import extract_parameters


class Timeframe(BaseModel):
    uid: str
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
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
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on the timeframe. "
                "Actions are: 'approve', 'edit', 'inactivate', 'reactivate' and 'delete'."
            )
        ),
    ] = []

    template: TimeframeTemplateNameUidLibrary | None = None
    parameter_terms: Annotated[
        list[MultiTemplateParameterTerm],
        Field(
            description="Holds the parameter terms that are used within the timeframe. The terms are ordered as they occur in the timeframe name.",
        ),
    ] = []
    library: Annotated[Library | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    study_count: Annotated[
        int, Field(description="Count of studies referencing endpoint")
    ] = 0

    @classmethod
    def from_timeframe_ar(cls, timeframe_ar: TimeframeAR) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(timeframe_ar.get_parameters()):
            terms: list[IndexedTemplateParameterTerm] = []
            if (
                hasattr(parameter, "parameter_template")
                and parameter.parameter_template is not None
            ):
                # This branch of the code is called if particular parameter of parameter list uses parameter template
                # If yes the abstraction of complex parameter is created to allow UI to recreate ParameterTemplate
                # with related parameter templates. So the definition of parameter template is sent along with parameters.
                param_names = extract_parameters(parameter.parameter_template)
                param_list = []
                for i, param_name in enumerate(param_names):
                    param_term = parameter.parameters[i]
                    indexed_template_parameter_term = IndexedTemplateParameterTerm(
                        name=param_term.value,
                        uid=param_term.uid,
                        index=1,
                        type=param_name,
                    )
                    param_list.append(indexed_template_parameter_term)
                template_parameter_complex_value = TemplateParameterComplexValue(
                    position=position + 1,
                    conjunction="",
                    terms=param_list,
                    format_string=parameter.parameter_template,
                )
                parameter_terms.append(template_parameter_complex_value)
            else:
                # Regular way of handling simple parameters for object
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
            uid=timeframe_ar.uid,
            name=timeframe_ar.name,
            name_plain=timeframe_ar.name_plain,
            start_date=timeframe_ar.item_metadata.start_date,
            end_date=timeframe_ar.item_metadata.end_date,
            status=timeframe_ar.item_metadata.status.value,
            version=timeframe_ar.item_metadata.version,
            change_description=timeframe_ar.item_metadata.change_description,
            author_username=timeframe_ar.item_metadata.author_username,
            possible_actions=sorted(
                {_.value for _ in timeframe_ar.get_possible_actions()}
            ),
            template=TimeframeTemplateNameUidLibrary(
                name=timeframe_ar.template_name,
                name_plain=timeframe_ar.template_name_plain,
                uid=timeframe_ar.template_uid,
                sequence_id=timeframe_ar.template_sequence_id,
                library_name=timeframe_ar.template_library_name,
            ),
            library=Library.from_library_vo(timeframe_ar.library),
            parameter_terms=parameter_terms,
            study_count=timeframe_ar.study_count,
        )


class TimeframeVersion(Timeframe):
    """
    Class for storing Timeframes and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class TimeframeEditInput(PatchInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput] | None,
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the timeframe template.",
        ),
    ] = None
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]


class TimeframeCreateInput(PostInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput] | None,
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the timeframe template.",
        ),
    ] = None
    timeframe_template_uid: Annotated[
        str,
        Field(
            description="The unique id of the timeframe template that is used as the basis for the new timeframe.",
            min_length=1,
        ),
    ]
    library_name: Annotated[
        str | None,
        Field(
            description="If specified: The name of the library to which the timeframe will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
            "If not specified: The library of the timeframe template will be used.",
            min_length=1,
        ),
    ] = None
