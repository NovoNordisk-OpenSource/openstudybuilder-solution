from datetime import datetime
from typing import Annotated, Any, Callable, Self

from pydantic.fields import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domain_repositories.models.syntax import FootnoteTemplateRoot
from clinical_mdr_api.domains.syntax_instances.footnote import FootnoteAR
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTermNameAndAttributes,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.footnote_template import (
    FootnoteTemplateNameUidLibrary,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class FootnoteTemplateWithType(FootnoteTemplateNameUidLibrary):
    type: Annotated[
        CTTermNameAndAttributes | None, Field(json_schema_extra={"nullable": True})
    ] = None


class Footnote(BaseModel):
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
                "Holds those actions that can be performed on the footnote. "
                "Actions are: None"
            ),
            json_schema_extra={
                "nullable": True,
                "remove_from_wildcard": True,
                "exclude_from_model_validate": True,
            },
        ),
    ] = None
    template: FootnoteTemplateWithType | None = None
    parameter_terms: Annotated[
        list[MultiTemplateParameterTerm] | None,
        Field(
            description="Holds the parameter terms that are used within the footnote. The terms are ordered as they occur in the footnote name.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    library: Library | None = None
    study_count: Annotated[
        int, Field(description="Count of studies referencing footnote")
    ] = 0

    @classmethod
    def from_footnote_ar(
        cls,
        footnote_ar: FootnoteAR,
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(footnote_ar.get_parameters()):
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
            uid=footnote_ar.uid,
            name=footnote_ar.name,
            name_plain=footnote_ar.name_plain,
            start_date=footnote_ar.item_metadata.start_date,
            end_date=footnote_ar.item_metadata.end_date,
            status=footnote_ar.item_metadata.status.value,
            version=footnote_ar.item_metadata.version,
            change_description=footnote_ar.item_metadata.change_description,
            author_username=footnote_ar.item_metadata.author_username,
            possible_actions=sorted(
                {_.value for _ in footnote_ar.get_possible_actions()}
            ),
            template=FootnoteTemplateWithType(
                name=footnote_ar.template_name,
                name_plain=footnote_ar.name_plain,
                uid=footnote_ar.template_uid,
                sequence_id=footnote_ar.template_sequence_id,
                library_name=footnote_ar.template_library_name,
            ),
            library=Library.from_library_vo(footnote_ar.library),
            study_count=footnote_ar.study_count,
            parameter_terms=parameter_terms,
        )


class FootnoteWithType(Footnote):
    template: FootnoteTemplateWithType | None

    @classmethod
    def from_footnote_ar(
        cls,
        footnote_ar: FootnoteAR,
        syntax_template_node: FootnoteTemplateRoot,
        get_footnote_type_name: Callable[[str], Any],
        get_footnote_type_attributes: Callable[[str], Any],
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(footnote_ar.get_parameters()):
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
            uid=footnote_ar.uid,
            name=footnote_ar.name,
            name_plain=footnote_ar.name_plain,
            start_date=footnote_ar.item_metadata.start_date,
            end_date=footnote_ar.item_metadata.end_date,
            status=footnote_ar.item_metadata.status.value,
            version=footnote_ar.item_metadata.version,
            change_description=footnote_ar.item_metadata.change_description,
            author_username=footnote_ar.item_metadata.author_username,
            possible_actions=sorted(
                {_.value for _ in footnote_ar.get_possible_actions()}
            ),
            template=FootnoteTemplateWithType(
                name=footnote_ar.template_name,
                name_plain=footnote_ar.name_plain,
                uid=footnote_ar.template_uid,
                sequence_id=footnote_ar.template_sequence_id,
                type=CTTermNameAndAttributes.from_ct_term_ars(
                    ct_term_name_ar=get_footnote_type_name(syntax_template_node),
                    ct_term_attributes_ar=get_footnote_type_attributes(
                        syntax_template_node
                    ),
                ),
                library_name=footnote_ar.template_library_name,
            ),
            library=Library.from_library_vo(footnote_ar.library),
            study_count=footnote_ar.study_count,
            parameter_terms=parameter_terms,
        )


class FootnoteVersion(FootnoteWithType):
    """
    Class for storing Footnote and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class FootnoteEditInput(PatchInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the footnote template.",
        ),
    ]
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]


class FootnoteCreateInput(PostInputModel):
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the footnote template.",
        ),
    ]
    footnote_template_uid: Annotated[
        str,
        Field(
            description="The unique id of the footnote template that is used as the basis for the new footnote.",
            min_length=1,
        ),
    ]
    library_name: Annotated[
        str | None,
        Field(
            description="If specified: The name of the library to which the footnote will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* footnote can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
            "If not specified: The library of the footnote template will be used.",
            min_length=1,
        ),
    ] = None
