from datetime import datetime
from typing import Annotated, Self

from pydantic.fields import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_instances.criteria import CriteriaAR
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.criteria_template import (
    CriteriaTemplateNameUidLibrary,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class CriteriaTemplateWithType(CriteriaTemplateNameUidLibrary):
    type: SimpleCTTermNameAndAttributes | None


class Criteria(BaseModel):
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
        list[str] | None,
        Field(
            description=(
                "Holds those actions that can be performed on the criteria. "
                "Actions are: None"
            ),
            json_schema_extra={"nullable": True},
        ),
    ] = None

    template: CriteriaTemplateNameUidLibrary | None = None
    parameter_terms: Annotated[
        list[MultiTemplateParameterTerm] | None,
        Field(
            description="Holds the parameter terms that are used within the criteria. The terms are ordered as they occur in the criteria name.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    library: Library | None = None

    study_count: Annotated[
        int, Field(description="Count of studies referencing criteria")
    ] = 0

    @classmethod
    def from_criteria_ar(
        cls,
        criteria_ar: CriteriaAR,
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(criteria_ar.get_parameters()):
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
            uid=criteria_ar.uid,
            name=criteria_ar.name,
            name_plain=criteria_ar.name_plain,
            start_date=criteria_ar.item_metadata.start_date,
            end_date=criteria_ar.item_metadata.end_date,
            status=criteria_ar.item_metadata.status.value,
            version=criteria_ar.item_metadata.version,
            change_description=criteria_ar.item_metadata.change_description,
            author_username=criteria_ar.item_metadata.author_username,
            possible_actions=sorted(
                {_.value for _ in criteria_ar.get_possible_actions()}
            ),
            template=CriteriaTemplateNameUidLibrary(
                name=criteria_ar.template_name,
                name_plain=criteria_ar.template_name_plain,
                uid=criteria_ar.template_uid,
                sequence_id=criteria_ar.template_sequence_id,
                guidance_text=criteria_ar.guidance_text,
                library_name=criteria_ar.template_library_name,
            ),
            library=Library.from_library_vo(criteria_ar.library),
            study_count=criteria_ar.study_count,
            parameter_terms=parameter_terms,
        )


class CriteriaWithType(Criteria):
    template: CriteriaTemplateWithType | None

    @classmethod
    def from_criteria_ar(cls, criteria_ar: CriteriaAR) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(criteria_ar.get_parameters()):
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
            uid=criteria_ar.uid,
            name=criteria_ar.name,
            name_plain=criteria_ar.name_plain,
            start_date=criteria_ar.item_metadata.start_date,
            end_date=criteria_ar.item_metadata.end_date,
            status=criteria_ar.item_metadata.status.value,
            version=criteria_ar.item_metadata.version,
            change_description=criteria_ar.item_metadata.change_description,
            author_username=criteria_ar.item_metadata.author_username,
            possible_actions=sorted(
                {_.value for _ in criteria_ar.get_possible_actions()}
            ),
            template=CriteriaTemplateWithType(
                name=criteria_ar.template_name,
                name_plain=criteria_ar.template_name_plain,
                uid=criteria_ar.template_uid,
                sequence_id=criteria_ar.template_sequence_id,
                guidance_text=criteria_ar.guidance_text,
                type=criteria_ar._template.template_type,
                library_name=criteria_ar.template_library_name,
            ),
            library=Library.from_library_vo(criteria_ar.library),
            study_count=criteria_ar.study_count,
            parameter_terms=parameter_terms,
        )


class CriteriaVersion(CriteriaWithType):
    """
    Class for storing Criteria and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class CriteriaEditInput(PatchInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the criteria template.",
        ),
    ]
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]


class CriteriaCreateInput(PostInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the criteria template.",
        ),
    ]
    criteria_template_uid: Annotated[
        str,
        Field(
            description="The unique id of the criteria template that is used as the basis for the new criteria.",
            min_length=1,
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


class CriteriaUpdateWithCriteriaKeyInput(PatchInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the criteria template.",
        ),
    ]
    criteria_template_uid: Annotated[
        str,
        Field(
            description="The unique id of the criteria template that is used as the basis for the new criteria.",
            min_length=1,
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
    key_criteria: Annotated[
        bool,
        Field(
            description="New value to set for the key_criteria property of the selection",
        ),
    ]
