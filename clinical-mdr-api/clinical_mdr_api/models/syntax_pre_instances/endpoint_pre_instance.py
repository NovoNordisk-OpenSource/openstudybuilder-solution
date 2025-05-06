from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_pre_instances.endpoint_pre_instance import (
    EndpointPreInstanceAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermModel,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_pre_instances.generic_pre_instance import (
    PreInstancePatchInput,
    PreInstancePostInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel


class EndpointPreInstance(BaseModel):
    uid: str
    sequence_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    template_uid: str
    template_name: str
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
    parameter_terms: Annotated[
        list[MultiTemplateParameterTerm],
        Field(
            description="Holds the parameter terms that are used within the endpoint. The terms are ordered as they occur in the endpoint name.",
        ),
    ] = []
    indications: Annotated[
        list[SimpleTermModel],
        Field(
            description="The study indications, conditions, diseases or disorders in scope for the pre-instance.",
        ),
    ] = []
    categories: Annotated[
        list[SimpleCTTermNameAndAttributes],
        Field(description="A list of categories the pre-instance belongs to."),
    ] = []
    sub_categories: Annotated[
        list[SimpleCTTermNameAndAttributes],
        Field(description="A list of sub-categories the pre-instance belongs to."),
    ] = []
    library: Annotated[Library | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    possible_actions: list[str] = []

    @classmethod
    def from_endpoint_pre_instance_ar(
        cls, endpoint_pre_instance_ar: EndpointPreInstanceAR
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(endpoint_pre_instance_ar.get_parameters()):
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
            uid=endpoint_pre_instance_ar.uid,
            sequence_id=endpoint_pre_instance_ar.sequence_id,
            template_uid=endpoint_pre_instance_ar.template_uid,
            template_name=endpoint_pre_instance_ar.template_name,
            name=endpoint_pre_instance_ar.name,
            name_plain=endpoint_pre_instance_ar.name_plain,
            start_date=endpoint_pre_instance_ar.item_metadata.start_date,
            end_date=endpoint_pre_instance_ar.item_metadata.end_date,
            status=endpoint_pre_instance_ar.item_metadata.status.value,
            version=endpoint_pre_instance_ar.item_metadata.version,
            change_description=endpoint_pre_instance_ar.item_metadata.change_description,
            author_username=endpoint_pre_instance_ar.item_metadata.author_username,
            library=Library.from_library_vo(endpoint_pre_instance_ar.library),
            parameter_terms=parameter_terms,
            indications=endpoint_pre_instance_ar.indications,
            categories=endpoint_pre_instance_ar.categories,
            sub_categories=endpoint_pre_instance_ar.sub_categories,
            possible_actions=sorted(
                {_.value for _ in endpoint_pre_instance_ar.get_possible_actions()}
            ),
        )


class EndpointPreInstanceCreateInput(PreInstancePostInput):
    indication_uids: list[str]
    category_uids: list[str]
    sub_category_uids: list[str]


class EndpointPreInstanceEditInput(PreInstancePatchInput):
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]


class EndpointPreInstanceIndexingsInput(PatchInputModel):
    indication_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the study indications, conditions, diseases or disorders to attach the pre-instance to.",
        ),
    ] = None
    category_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the categories to attach the pre-instance to.",
        ),
    ] = None
    sub_category_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the sub_categories to attach the pre-instance to.",
        ),
    ] = None


class EndpointPreInstanceVersion(EndpointPreInstance):
    """
    Class for storing Endpoint Pre-Instances and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
