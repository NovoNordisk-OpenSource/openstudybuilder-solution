from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_pre_instances.objective_pre_instance import (
    ObjectivePreInstanceAR,
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

IS_CONFIRMATORY_TESTING_DESC = (
    "Indicates if pre-instance is related to confirmatory testing. Defaults to false"
)


class ObjectivePreInstance(BaseModel):
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
    is_confirmatory_testing: Annotated[
        bool, Field(description=IS_CONFIRMATORY_TESTING_DESC)
    ] = False
    parameter_terms: Annotated[
        list[MultiTemplateParameterTerm],
        Field(
            description="Holds the parameter terms that are used within the objective. The terms are ordered as they occur in the objective name.",
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
    library: Annotated[Library | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    possible_actions: list[str] = []

    @classmethod
    def from_objective_pre_instance_ar(
        cls, objective_pre_instance_ar: ObjectivePreInstanceAR
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(
            objective_pre_instance_ar.get_parameters()
        ):
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
            uid=objective_pre_instance_ar.uid,
            sequence_id=objective_pre_instance_ar.sequence_id,
            template_uid=objective_pre_instance_ar.template_uid,
            template_name=objective_pre_instance_ar.template_name,
            name=objective_pre_instance_ar.name,
            name_plain=objective_pre_instance_ar.name_plain,
            start_date=objective_pre_instance_ar.item_metadata.start_date,
            end_date=objective_pre_instance_ar.item_metadata.end_date,
            status=objective_pre_instance_ar.item_metadata.status.value,
            version=objective_pre_instance_ar.item_metadata.version,
            change_description=objective_pre_instance_ar.item_metadata.change_description,
            author_username=objective_pre_instance_ar.item_metadata.author_username,
            library=Library.from_library_vo(objective_pre_instance_ar.library),
            is_confirmatory_testing=(
                False
                if objective_pre_instance_ar.is_confirmatory_testing is None
                else objective_pre_instance_ar.is_confirmatory_testing
            ),
            parameter_terms=parameter_terms,
            indications=objective_pre_instance_ar.indications,
            categories=objective_pre_instance_ar.categories,
            possible_actions=sorted(
                {_.value for _ in objective_pre_instance_ar.get_possible_actions()}
            ),
        )


class ObjectivePreInstanceCreateInput(PreInstancePostInput):
    is_confirmatory_testing: Annotated[
        bool, Field(description=IS_CONFIRMATORY_TESTING_DESC)
    ] = False
    indication_uids: list[str]
    category_uids: list[str]


class ObjectivePreInstanceEditInput(PreInstancePatchInput):
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]


class ObjectivePreInstanceIndexingsInput(PatchInputModel):
    is_confirmatory_testing: Annotated[
        bool, Field(description=IS_CONFIRMATORY_TESTING_DESC)
    ] = False
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


class ObjectivePreInstanceVersion(ObjectivePreInstance):
    """
    Class for storing Objective Pre-Instances and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
